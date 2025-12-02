from datetime import timedelta
from math import radians, sin, cos, sqrt, atan2

import numpy as np
from scipy.spatial import distance_matrix
from sqlalchemy import func

from .models import db, ActivityType, ActivityPlanned, Traveller


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
    Improved scoring: uses all preference scores for better matching.
    """
    import json
    score = 0

    # Bestemming match
    if trip.destination and activity.destination:
        if trip.destination.strip().lower() == activity.destination.strip().lower():
            score += 20

    # Use all preference scores if available (stored as JSON)
    preference_scores = {}
    if trip.preference_scores:
        try:
            preference_scores = json.loads(trip.preference_scores)
        except (json.JSONDecodeError, TypeError):
            preference_scores = {}
    
    # Activity preference scores
    activity_pref_map = {
        "CULTURE": activity.score_culture,
        "ADVENTURE": activity.score_adventure,
        "RELAXATION": activity.score_relaxation,
        "NATURE": activity.score_nature,
    }
    
    # If we have individual preference scores, use weighted sum
    if preference_scores:
        for pref_type, user_score in preference_scores.items():
            if pref_type in activity_pref_map and activity_pref_map[pref_type] is not None:
                # Weight: user preference (1-5) * activity score (0-10) * multiplier
                # Higher user preference = more weight
                score += int(user_score) * activity_pref_map[pref_type] * 2
    else:
        # Fallback to old method: only use main preference
        if trip.preferences and trip.preferences == activity.type:
            score += 40
        if trip.preferences in activity_pref_map and activity_pref_map[trip.preferences] is not None:
            score += activity_pref_map[trip.preferences] * 5

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
      - leeftijd van travellers (age suitability)
    """

    # Veiligheid: zorg dat start/end bestaan
    if not trip.start_date or not trip.end_date:
        # zonder data kunnen we geen dagplanning maken
        return False

    n_days = (trip.end_date - trip.start_date).days + 1
    if n_days <= 0:
        return False

    # Check of travellers zijn toegevoegd
    travellers = Traveller.query.filter_by(trip_id=trip.trip_id).all()
    if not travellers:
        return None  # Special return value to indicate travellers missing

    # Bereken leeftijden van travellers
    traveller_ages = [t.age for t in travellers]

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
        # Check if there are activities without coordinates
        activities_no_coords = (
            ActivityType.query
            .filter(
                func.lower(ActivityType.destination) == func.lower(trip.destination)
            )
            .filter(
                (ActivityType.latitude.is_(None)) | (ActivityType.longitude.is_(None))
            )
            .count()
        )
        if activities_no_coords > 0:
            # Return a specific error code to indicate missing coordinates
            return "NO_COORDINATES"
        return False

    # Filter activiteiten op basis van leeftijd
    # Een activiteit is geschikt als ALLE travellers binnen de leeftijdsrange vallen
    suitable_activities = []
    for activity in activities:
        # Check of de kolommen bestaan (voor backwards compatibility)
        min_age = getattr(activity, 'min_age', None)
        max_age = getattr(activity, 'max_age', None)
        
        # Als er geen leeftijdsbeperking is, is de activiteit geschikt
        if min_age is None and max_age is None:
            suitable_activities.append(activity)
            continue
        
        # Check of alle travellers binnen de leeftijdsrange vallen
        all_suitable = True
        for age in traveller_ages:
            if min_age is not None and age < min_age:
                all_suitable = False
                break
            if max_age is not None and age > max_age:
                all_suitable = False
                break
        
        if all_suitable:
            suitable_activities.append(activity)

    if not suitable_activities:
        # Check if it's an age filtering issue
        if traveller_ages:
            max_traveller_age = max(traveller_ages)
            min_traveller_age = min(traveller_ages)
            age_filtered_count = len([a for a in activities if 
                (a.min_age is not None and max_traveller_age < a.min_age) or
                (a.max_age is not None and min_traveller_age > a.max_age)])
            if age_filtered_count > 0:
                return "AGE_FILTERED"
        return False

    # Handle required and excluded activities
    required_ids = set()
    excluded_ids = set()
    
    if trip.required_activity_ids:
        required_ids = set(int(id.strip()) for id in trip.required_activity_ids.split(',') if id.strip())
    if trip.excluded_activity_ids:
        excluded_ids = set(int(id.strip()) for id in trip.excluded_activity_ids.split(',') if id.strip())
    
    # Filter out excluded activities
    suitable_activities = [a for a in suitable_activities if a.activity_type_id not in excluded_ids]
    
    # Check if all required activities are available and suitable
    required_activities = [a for a in suitable_activities if a.activity_type_id in required_ids]
    if len(required_activities) < len(required_ids):
        # Some required activities are not available or excluded
        missing = required_ids - set(a.activity_type_id for a in required_activities)
        return False  # Cannot create itinerary without all required activities

    # 2. Score berekenen
    scored = [(a, score_activity(a, trip)) for a in suitable_activities]

    # 3. Sorteren op score aflopend
    scored.sort(key=lambda x: x[1], reverse=True)

    # 4. Select activities: required first, then fill with top scored
    top_activities = []
    
    # Add required activities first (sorted by score)
    required_scored = [(a, s) for a, s in scored if a.activity_type_id in required_ids]
    required_scored.sort(key=lambda x: x[1], reverse=True)
    top_activities = [a for a, s in required_scored]
    
    # Fill remaining slots with other top-scored activities (excluding required ones)
    remaining_slots = n_days - len(top_activities)
    if remaining_slots > 0:
        other_activities = [a for a, s in scored if a.activity_type_id not in required_ids]
        top_activities.extend(other_activities[:remaining_slots])
    
    # Ensure we don't exceed n_days
    top_activities = top_activities[:n_days]

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
