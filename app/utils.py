from datetime import datetime, timedelta
from .models import ActivityType, ActivityPlanned, db
import random


def get_matching_activities(destination, preferences):
    """
    Haal activiteiten op op basis van bestemming en voorkeuren.
    preferences = bv. 'CULTURE, NATURE'
    """
    pref_list = []
    if preferences:
        pref_list = [p.strip().upper() for p in preferences.split(",")]

    all_activities = ActivityType.query.filter_by(destination=destination).all()

    if not all_activities:
        return []

    # Filter op preferences (indien beschikbaar)
    if pref_list:
        filtered = [a for a in all_activities if a.type.upper() in pref_list]
        if filtered:
            return filtered

    return all_activities  # fallback


def generate_itinerary(trip):
    """
    Genereert een dag-per-dag planning en slaat hem op in ActivityPlanned.
    """
    start = trip.start_date
    end = trip.end_date
    
    if not start or not end:
        return None

    days = (end - start).days + 1

    possible = get_matching_activities(trip.destination, trip.preferences)

    if not possible:
        return None

    # Oude planning verwijderen
    ActivityPlanned.query.filter_by(trip_id=trip.trip_id).delete()

    itinerary = []

    for i in range(days):
        date = start + timedelta(days=i)
        activity = random.choice(possible)

        planned = ActivityPlanned(
            trip_id=trip.trip_id,
            activity_type_id=activity.activity_type_id,
            date=date,
            created_at=datetime.utcnow()
        )

        db.session.add(planned)
        itinerary.append(planned)

    db.session.commit()
    return itinerary