from datetime import timedelta
from math import radians, sin, cos, sqrt, atan2

import numpy as np
from scipy.spatial import distance_matrix
from sqlalchemy import func

from .models import db, ActivityType, ActivityPlanned


# -----------------------------------------
# Haversine distance (km) tussen 2 GPS punten
# -----------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    """
    Grote-cirkel-afstand in km tussen twee (lat, lon)-punten.
    """
    R = 6371.0  # straal aarde in km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


# -----------------------------------------
# Score een activiteit op basis van trip-voorkeuren
# -----------------------------------------
def score_activity(activity: ActivityType, trip):
    """
    Eenvoudige scoring: hoe beter de match met preference + bestemming,
    hoe hoger de score. Dit kun je later uitbreiden.
    """
    score = 0

    # Main preference match (CULTURE/ADVENTURE/...)
    if trip.preferences and trip.preferences == activity.type:
        score += 40

    # Bestemming match
    if trip.destination and activity.destination:
        if trip.destination.strip().lower() == activity.destination.strip().lower():
            score += 20

    # Gebruik de culture/adventure/relaxation/nature-scores van de activiteit
    pref_map = {
        "CULTURE": activity.score_culture,
        "ADVENTURE": activity.score_adventure,
        "RELAXATION": activity.score_relaxation,
        "NATURE": activity.score_nature,
    }
    if trip.preferences in pref_map and pref_map[trip.preferences] is not None:
        score += pref_map[trip.preferences] * 5  # gewicht

    return score


# -----------------------------------------
# Bouw een afstandsmatrix met SciPy
# -----------------------------------------
def build_distance_matrix(activities):
    """
    Maakt een NxN-matrix met afstanden tussen alle activiteiten.

    We gebruiken hier een Haversine-gebaseerde matrix, maar bouwen 'm
    vectorized met NumPy en SciPy.
    """
    if len(activities) == 0:
        return np.array([[]])

    # (N, 2) array: [ [lat, lon], ... ]
    coords = np.array(
        [[a.latitude, a.longitude] for a in activities],
        dtype=float
    )

    # SciPy distance_matrix werkt standaard euclidisch.
    # We gebruiken 'm om indices te combineren, maar vullen de echte
    # Haversine-afstanden in.
    base = distance_matrix(coords, coords)

    # Vervang euclidische afstand door Haversine (km)
    n = coords.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(coords[i, 0], coords[i, 1],
                          coords[j, 0], coords[j, 1])
            base[i, j] = d
            base[j, i] = d

    return base


# -----------------------------------------
# Hulpfuncties voor TSP (route lengte & 2-opt)
# -----------------------------------------
def route_length(order, dist_mat):
    """
    Totale afstand van een route (order is lijst indices).
    """
    if len(order) < 2:
        return 0.0
    total = 0.0
    for i in range(len(order) - 1):
        total += dist_mat[order[i], order[i + 1]]
    return total


def tsp_nearest_neighbor(dist_mat):
    """
    Simpele nearest-neighbor TSP startoplossing.
    """
    n = dist_mat.shape[0]
    if n == 0:
        return []
    if n == 1:
        return [0]

    unvisited = set(range(1, n))
    route = [0]
    current = 0

    while unvisited:
        # Kies dichtstbijzijnde nog niet bezochte node
        next_city = min(
            unvisited,
            key=lambda j: dist_mat[current, j]
        )
        route.append(next_city)
        unvisited.remove(next_city)
        current = next_city

    return route


def tsp_2opt(route, dist_mat, max_iter=50):
    """
    2-opt verbetering van een bestaande route.
    Probeer segmenten om te draaien als dat de totale afstand verlaagt.
    """
    improved = True
    iteration = 0
    n = len(route)

    if n <= 3:
        return route

    while improved and iteration < max_iter:
        improved = False
        iteration += 1

        for i in range(1, n - 2):
            for k in range(i + 1, n - 1):
                # huidige afstand van segmenten (i-1 -> i) + (k -> k+1)
                before = (
                    dist_mat[route[i - 1], route[i]]
                    + dist_mat[route[k], route[k + 1]]
                )
                # afstand na omdraaien segment (i -> k)
                after = (
                    dist_mat[route[i - 1], route[k]]
                    + dist_mat[route[i], route[k + 1]]
                )
                if after + 1e-6 < before:  # kleine marge voor numeriek gedoe
                    # draai segment om
                    route[i:k + 1] = reversed(route[i:k + 1])
                    improved = True
        # als in een hele iteratie niets beter wordt -> stop
    return route


def solve_tsp_scipy(activities):
    """
    Combineert:
      1) nearest neighbor voor start-oplossing
      2) 2-opt voor lokale verbetering

    Geeft een lijst ActivityType-objecten in logische volgorde terug.
    """
    if not activities:
        return []

    if len(activities) == 1:
        return activities

    dist_mat = build_distance_matrix(activities)

    # 1) start met nearest-neighbor
    route_idx = tsp_nearest_neighbor(dist_mat)

    # 2) verbeter met 2-opt
    route_idx = tsp_2opt(route_idx, dist_mat)

    # Map indices terug naar activiteiten
    ordered_activities = [activities[i] for i in route_idx]
    return ordered_activities


# -----------------------------------------
# Hoofdfunctie die door je route wordt aangeroepen
# -----------------------------------------
def generate_itinerary(trip):
    """
    Bouwt een itinerary voor de gegeven trip op basis van:
      - bestemming
      - trip.preferences
      - activiteit-scores
      - minimale totale afstand tussen activiteiten (TSP-achtig)
    """

    # Veiligheid: zorg dat start/end bestaan
    if not trip.start_date or not trip.end_date:
        # zonder data kunnen we geen dagplanning maken
        return False

    n_days = (trip.end_date - trip.start_date).days + 1
    if n_days <= 0:
        return False

    # 1. Alle activiteiten voor de bestemming + met coördinaten
    activities = (
        ActivityType.query
        .filter(
            func.lower(ActivityType.destination) == func.lower(trip.destination)
        )
        .filter(
            ActivityType.latitude.isnot(None),
            ActivityType.longitude.isnot(None)
        )
        .all()
    )

    if not activities:
        return False

    # 2. Score berekenen
    scored = [(a, score_activity(a, trip)) for a in activities]

    # 3. Sorteren op score aflopend
    scored.sort(key=lambda x: x[1], reverse=True)

    # 4. Neem de top N activiteiten (één per dag)
    top_activities = [a for a, s in scored[:n_days]]

    if not top_activities:
        return False

    # 5. Optimaliseer volgorde met SciPy/2-opt benadering
    optimal_order = solve_tsp_scipy(top_activities)

    # 6. Oude itinerary wissen
    ActivityPlanned.query.filter_by(trip_id=trip.trip_id).delete()
    db.session.commit()

    # 7. Activities per dag inplannen
    current_date = trip.start_date
    for act in optimal_order:
        planned = ActivityPlanned(
            trip_id=trip.trip_id,
            activity_type_id=act.activity_type_id,
            date=current_date
        )
        db.session.add(planned)
        current_date += timedelta(days=1)

    db.session.commit()
    return True
