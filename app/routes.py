from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import OperationalError, ProgrammingError
from werkzeug.utils import secure_filename
import os
import json
from .models import (
    db, User, Traveller, Trip, ActivityPlanned, ActivityType, TravelAgency, Destination,
    get_activity_types, get_difficulty_levels
)
from .utils import generate_itinerary
from .storage import upload_file_to_supabase, delete_file_from_supabase, get_activity_image_url, get_logo_url


# ⬇️ Maak een Blueprint aan i.p.v. rechtstreeks met app werken
main = Blueprint('main', __name__)

def _get_destinations_safe():
    """Safely get destinations with fallback if table doesn't exist"""
    try:
        # Check if table exists first
        from sqlalchemy import inspect
        from sqlalchemy.exc import OperationalError, ProgrammingError
        
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'Destination' not in tables:
                # Table doesn't exist, return defaults
                return _create_default_destinations()
        except (OperationalError, ProgrammingError, AttributeError):
            # Can't inspect tables (e.g., SQLite without proper setup), try query anyway
            pass
        
        # Try to query the table
        destinations = Destination.query.filter_by(is_active=True).order_by(Destination.name).all()
        if not destinations:
            # Create default destination objects if table is empty
            return _create_default_destinations()
        return destinations
    except (OperationalError, ProgrammingError, AttributeError, TypeError) as e:
        # Database errors - table doesn't exist or can't be queried
        import traceback
        print(f"Error getting destinations (table may not exist): {e}")
        # Fallback if Destination table doesn't exist yet
        return _create_default_destinations()
    except Exception as e:
        # Other unexpected errors
        import traceback
        print(f"Unexpected error getting destinations: {e}")
        print(traceback.format_exc())
        return _create_default_destinations()

def _create_default_destinations():
    """Create default destination objects"""
    class DestinationObj:
        def __init__(self, name, flag_emoji=None, country_code=None, image_path=None):
            self.name = name
            self.flag_emoji = flag_emoji
            self.country_code = country_code
            self.image_path = image_path
    
    return [
        DestinationObj(name='South Africa', flag_emoji='🇿🇦', country_code='SA', image_path='img/south-africa.webp'),
        DestinationObj(name='Morocco', flag_emoji='🇲🇦', country_code='MO', image_path='img/morocco.jpg')
    ]

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        # If user doesn't exist (e.g., database was reset), clear session
        if not user:
            session.pop('user_id', None)
            return render_template('index.html')
        # Agencies should only see activities, not trips
        if user.role == 'AGENCY':
            return redirect(url_for('main.activities'))
        trips = Trip.query.filter_by(user_id=user.user_id).all()
        return render_template('trips.html', trips=trips, user=user, activity_types=get_activity_types())
    return render_template('index.html')

@main.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    # If user doesn't exist (e.g., database was reset), clear session and redirect
    if not user:
        session.pop('user_id', None)
        flash("Your session has expired. Please log in again.", "info")
        return redirect(url_for('main.login'))
    
    # Agencies should see agency homepage
    if user.role == 'AGENCY':
        return render_template('home.html', user=user)
    
    trips = Trip.query.filter_by(user_id=user.user_id).all()
    
    return render_template('home.html', user=user, trips=trips)


@main.route('/register', methods=['GET'])
def register():
    """Keuzepagina voor registratie type"""
    return render_template('register.html')

@main.route('/register_traveller', methods=['GET', 'POST'])
def register_traveller():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        role = 'TRAVELLER'

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for('main.register_traveller'))
        
        new_user = User(
            name=name,
            email=email,
            phone_number=phone_number,
            role=role,
            created_at=datetime.now(),
        )
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.user_id
        flash("Registration successful!", "success")
        return redirect(url_for('main.home'))
        
    return render_template('register_traveller.html')

@main.route('/register_agency', methods=['GET', 'POST'])
def register_agency():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        role = 'AGENCY'

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for('main.register_agency'))
        
        new_user = User(
            name=name,
            email=email,
            phone_number=phone_number,
            role=role,
            created_at=datetime.now(),
        )
        db.session.add(new_user)
        db.session.commit()

        # Create TravelAgency record
        new_agency = TravelAgency(
            name=name,
            contact_info="",
            website="",
            user_id=new_user.user_id,
            created_at=datetime.utcnow()
        )
        db.session.add(new_agency)
        db.session.commit()

        session['user_id'] = new_user.user_id
        flash("Registration successful!", "success")
        return redirect(url_for('main.activities'))
        
    return render_template('agency_register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.user_id
            flash(f"Welcome {user.name}", "success")
            return redirect(url_for('main.home'))
        else:
            flash("User not found.", "error")
            return redirect(url_for('main.login'))
        
    return render_template('login.html')

@main.route('/agency_login', methods=['GET', 'POST'])
def agency_login():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            if user.role != 'AGENCY':
                flash("This account is not registered as an agency.", "error")
                return redirect(url_for('main.agency_login'))
            session['user_id'] = user.user_id
            flash(f"Welcome {user.name}", "success")
            return redirect(url_for('main.home'))
        else:
            flash("Agency not found.", "error")
            return redirect(url_for('main.agency_login'))
        
    return render_template('agency_login.html')

@main.route('/logout') 
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('main.index'))



#hiermee kan de user een trip aanmaken
@main.route('/trips', methods=['GET'])
def trips():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    # Agencies should only see activities, not trips
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))

    trips = (
        Trip.query
        .filter_by(user_id=user.user_id)
        .order_by(Trip.created_at.desc())
        .all()
    )
    return render_template('trips.html', trips=trips, user=user)

@main.route('/trips/create', methods=['GET', 'POST'])
def create_trip():
    """Create a new trip with 6-step wizard"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))
    
    # Get data from models
    destinations = _get_destinations_safe()
    activity_types = get_activity_types()
    
    if request.method == 'POST':
        # Get form data from all steps
        destination = request.form.get('destination')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        preferences = request.form.get('preferences')
        required_activity_ids = request.form.get('required_activity_ids', '')
        excluded_activity_ids = request.form.get('excluded_activity_ids', '')
        
        # Get individual preference scores
        preference_scores = {
            "CULTURE": int(request.form.get('pref_CULTURE', 3)),
            "ADVENTURE": int(request.form.get('pref_ADVENTURE', 3)),
            "RELAXATION": int(request.form.get('pref_RELAXATION', 3)),
            "NATURE": int(request.form.get('pref_NATURE', 3))
        }
        
        # Parse dates
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        
        # Validation
        if not destination:
            flash("Please select a destination.", "error")
            return redirect(url_for('main.create_trip'))
        
        if not start_date or not end_date:
            flash("Please select start and end dates.", "error")
            return redirect(url_for('main.create_trip'))
        
        if end_date < start_date:
            flash("End date cannot be before start date.", "error")
            return redirect(url_for('main.create_trip'))
        
        # Create trip
        new_trip = Trip(
            created_at=datetime.now(),
            start_date=start_date,
            end_date=end_date,
            number_of_travellers=0,  # Will be updated when travellers are added
            preferences=preferences if preferences else None,
            destination=destination,
            user_id=user.user_id,
            required_activity_ids=required_activity_ids if required_activity_ids else None,
            excluded_activity_ids=excluded_activity_ids if excluded_activity_ids else None,
            preference_scores=json.dumps(preference_scores)
        )
        db.session.add(new_trip)
        db.session.commit()
        
        # Get travellers from form (Step 3)
        traveller_names = request.form.getlist('traveller_name[]')
        traveller_birth_dates = request.form.getlist('traveller_birth_date[]')
        traveller_fitness = request.form.getlist('traveller_fitness[]')
        
        # Add travellers
        for i, name in enumerate(traveller_names):
            if name and i < len(traveller_birth_dates) and traveller_birth_dates[i]:
                try:
                    birth_date = datetime.strptime(traveller_birth_dates[i], "%Y-%m-%d").date()
                    fitness = traveller_fitness[i] if i < len(traveller_fitness) else None
                    
                    traveller = Traveller(
                        name=name,
                        birth_date=birth_date,
                        fitness=fitness if fitness else None,
                        trip_id=new_trip.trip_id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(traveller)
                except ValueError:
                    continue
        
        new_trip.number_of_travellers = len([n for n in traveller_names if n])
        db.session.commit()
        
        # Generate itinerary immediately if we have travellers
        travellers = Traveller.query.filter_by(trip_id=new_trip.trip_id).all()
        if travellers:
            from .utils import generate_itinerary
            result = generate_itinerary(new_trip)
            if result is None:
                flash("Trip created successfully! Note: Add traveller details to generate itinerary.", "success")
            elif result == "NO_COORDINATES":
                flash("Trip created successfully! Note: Activities for this destination exist but are missing coordinates (latitude/longitude). Please add coordinates to activities to generate an itinerary.", "success")
            elif result == "AGE_FILTERED":
                traveller_ages = [t.age for t in travellers]
                max_age = max(traveller_ages) if traveller_ages else 0
                flash(f"Trip created successfully! Note: No activities found suitable for traveller age ({max_age} years). Activities may have age restrictions that exclude this traveller.", "success")
            elif result is False:
                flash("Trip created successfully! Note: No suitable activities found for itinerary. Please check that activities exist for this destination with coordinates.", "success")
            elif result:
                flash("Trip created successfully! Itinerary generated.", "success")
        else:
            flash("Trip created successfully! Note: Add travellers to generate itinerary.", "success")
        
        return redirect(url_for('main.trips'))
    
    # GET: Show creation form
    # Get activities for filtering (will be filtered by destination and age in template)
    all_activities = ActivityType.query.all()
    # Serialize activities for JavaScript
    activities_data = [{
        'activity_type_id': a.activity_type_id,
        'name': a.name,
        'description': a.description or '',
        'destination': a.destination,
        'min_age': a.min_age,
        'max_age': a.max_age
    } for a in all_activities]
    return render_template(
        'create_trip.html', 
        activities=activities_data, 
        user=user,
        destinations=destinations,
        activity_types=activity_types
    )

@main.route('/trips/<int:trip_id>/edit', methods=['GET', 'POST'])
def edit_trip(trip_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    trip = Trip.query.get_or_404(trip_id)

    if request.method == 'POST':
        destination = request.form.get('destination')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        preferences = request.form.get('preferences')
        required_activity_ids = request.form.get('required_activity_ids', '')
        excluded_activity_ids = request.form.get('excluded_activity_ids', '')

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        if end_date and start_date and end_date < start_date:
            flash("End date cannot be before start date.", "error")
            return redirect(url_for('main.edit_trip', trip_id=trip_id))

        # Check if destination changed - if so, clear all planned activities
        old_destination = trip.destination
        destination_changed = old_destination and old_destination != destination
        
        if destination_changed:
            # Delete all planned activities for this trip
            ActivityPlanned.query.filter_by(trip_id=trip_id).delete()
            # Clear required/excluded activity IDs since they're from old destination
            required_activity_ids = ''
            excluded_activity_ids = ''
            flash(f"Destination changed from {old_destination} to {destination}. All previously planned activities have been removed.", "info")

        trip.destination = destination
        trip.start_date = start_date
        trip.end_date = end_date
        trip.preferences = preferences
        trip.required_activity_ids = required_activity_ids if required_activity_ids else None
        trip.excluded_activity_ids = excluded_activity_ids if excluded_activity_ids else None
        
        # Update preference scores
        preference_scores = {
            "CULTURE": int(request.form.get('pref_CULTURE', 3)),
            "ADVENTURE": int(request.form.get('pref_ADVENTURE', 3)),
            "RELAXATION": int(request.form.get('pref_RELAXATION', 3)),
            "NATURE": int(request.form.get('pref_NATURE', 3))
        }
        trip.preference_scores = json.dumps(preference_scores)
        
        # Handle traveller updates
        # 1. Delete removed travellers
        deleted_ids = request.form.get('deleted_traveller_ids', '')
        if deleted_ids:
            for tid in deleted_ids.split(','):
                if tid.strip():
                    try:
                        traveller = Traveller.query.get(int(tid))
                        if traveller and traveller.trip_id == trip_id:
                            db.session.delete(traveller)
                    except ValueError:
                        pass
        
        # 2. Update existing travellers
        existing_travellers = Traveller.query.filter_by(trip_id=trip_id).all()
        for traveller in existing_travellers:
            name = request.form.get(f'traveller_name_{traveller.traveller_id}')
            birth = request.form.get(f'traveller_birth_{traveller.traveller_id}')
            fitness = request.form.get(f'traveller_fitness_{traveller.traveller_id}')
            
            if name:
                traveller.name = name
            if birth:
                traveller.birth_date = datetime.strptime(birth, "%Y-%m-%d").date()
            traveller.fitness = fitness if fitness else None
        
        # 3. Add new travellers
        new_traveller_ids = request.form.getlist('new_traveller_ids')
        for temp_id in new_traveller_ids:
            name = request.form.get(f'new_traveller_name_{temp_id}')
            birth = request.form.get(f'new_traveller_birth_{temp_id}')
            fitness = request.form.get(f'new_traveller_fitness_{temp_id}')
            
            if name:
                birth_date = datetime.strptime(birth, "%Y-%m-%d").date() if birth else None
                new_traveller = Traveller(
                    trip_id=trip_id,
                    name=name,
                    birth_date=birth_date,
                    fitness=fitness if fitness else None
                )
                db.session.add(new_traveller)
        
        # Update number of travellers
        db.session.flush()  # Ensure all changes are reflected
        trip.number_of_travellers = Traveller.query.filter_by(trip_id=trip_id).count()

        db.session.commit()
        
        # Auto-regenerate itinerary if trip has travellers and dates
        travellers = Traveller.query.filter_by(trip_id=trip.trip_id).all()
        if travellers and trip.start_date and trip.end_date:
            from .utils import generate_itinerary
            result = generate_itinerary(trip)
            if result is None:
                flash("Trip updated successfully! Note: Add traveller details to generate itinerary.", "success")
            elif result == "NO_COORDINATES":
                flash("Trip updated successfully! Note: Activities for this destination exist but are missing coordinates (latitude/longitude). Please add coordinates to activities to generate an itinerary.", "success")
            elif result == "AGE_FILTERED":
                traveller_ages = [t.age for t in travellers]
                max_age = max(traveller_ages) if traveller_ages else 0
                flash(f"Trip updated successfully! Note: No activities found suitable for traveller age ({max_age} years). Activities may have age restrictions that exclude this traveller.", "success")
            elif result is False:
                flash("Trip updated successfully! Note: No suitable activities found for itinerary. Please check that activities exist for this destination with coordinates.", "success")
            elif result:
                flash("Trip updated and itinerary regenerated successfully!", "success")
        else:
            flash("Trip updated successfully!", "success")
        
        return redirect(url_for('main.trips'))

    # Get activities for activity selection
    from .models import ActivityType
    all_activities = ActivityType.query.all()
    activities_data = [{
        'activity_type_id': a.activity_type_id,
        'name': a.name,
        'description': a.description or '',
        'destination': a.destination,
        'min_age': a.min_age,
        'max_age': a.max_age
    } for a in all_activities]
    
    # Serialize travellers for JavaScript
    travellers_data = [{
        'traveller_id': t.traveller_id,
        'name': t.name,
        'birth_date': t.birth_date.isoformat() if t.birth_date else None,
        'fitness': t.fitness
    } for t in trip.travellers]
    
    # Parse preference scores for template
    preference_scores_dict = {}
    if trip.preference_scores:
        try:
            preference_scores_dict = json.loads(trip.preference_scores)
        except (json.JSONDecodeError, TypeError):
            preference_scores_dict = {}
    
    # Check if trip has any planned activities
    has_planned_activities = ActivityPlanned.query.filter_by(trip_id=trip_id).first() is not None
    
    return render_template(
        'edit_trip.html', 
        trip=trip, 
        activities=activities_data, 
        travellers_data=travellers_data, 
        preference_scores=preference_scores_dict, 
        user=user,
        destinations=_get_destinations_safe(),
        activity_types=get_activity_types(),
        has_planned_activities=has_planned_activities
    )

@main.route('/delete_trip/<int:trip_id>', methods=['POST'])
def delete_trip(trip_id):
    """Delete a trip"""
    if 'user_id' not in session:
        flash("You must be logged in to delete trips.", "error")
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if user and user.role == 'AGENCY':
        flash("Agencies cannot delete trips.", "error")
        return redirect(url_for('main.activities'))
    
    trip = Trip.query.get_or_404(trip_id)
    
    # Verify trip belongs to current user
    if trip.user_id != session.get('user_id'):
        flash("You cannot delete someone else's trip.", "error")
        return redirect(url_for('main.trips'))
    
    # Delete related records first (cascade should handle this, but being explicit)
    from .models import Traveller, ActivityPlanned
    Traveller.query.filter_by(trip_id=trip.trip_id).delete()
    ActivityPlanned.query.filter_by(trip_id=trip.trip_id).delete()
    
    # Delete the trip
    db.session.delete(trip)
    db.session.commit()
    
    flash("Trip deleted successfully!", "success")
    return redirect(url_for('main.trips'))

@main.route('/travellers/<int:trip_id>', methods=['GET', 'POST'])
def travellers(trip_id): 
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    # Agencies should not access travellers/trips
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))
    
    trip = Trip.query.get_or_404(trip_id)

    if trip.user_id != session.get('user_id'):
        flash("You cannot view travellers for this trip.", "error")
        return redirect(url_for('main.trips'))

    if request.method == 'POST':
        # Voeg nieuwe traveller toe
        if 'add' in request.form:  
            name = request.form.get('name')
            birth_date_str = request.form.get('birth_date')
            fitness = request.form.get('fitness')

            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except Exception:
                flash("Ongeldige geboortedatum.", "error")
                return redirect(url_for('main.travellers', trip_id=trip.trip_id))

            new_traveller = Traveller(
                name=name,
                birth_date=birth_date,
                fitness=fitness if fitness else None,
                trip_id=trip.trip_id,
                created_at=datetime.utcnow()
            )
            db.session.add(new_traveller)
            trip.number_of_travellers = (trip.number_of_travellers or 0) + 1
            db.session.commit()
            flash("Traveller added!", "success")
            return redirect(url_for('main.travellers', trip_id=trip.trip_id))

        # Edit bestaande traveller
        if 'edit' in request.form:  
            traveller_id = int(request.form.get('traveller_id'))
            traveller = Traveller.query.get_or_404(traveller_id)
            traveller.name = request.form.get('name')
            traveller.fitness = request.form.get('fitness')
            try:
                traveller.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date()
            except Exception:
                flash("Ongeldige geboortedatum.", "error")
                return redirect(url_for('main.travellers', trip_id=trip.trip_id))

            db.session.commit()
            flash("Traveller updated!", "success")
            return redirect(url_for('main.travellers', trip_id=trip.trip_id))

        # Delete traveller
        if 'delete' in request.form:
            traveller_id = int(request.form.get('traveller_id'))
            traveller = Traveller.query.get_or_404(traveller_id)
            
            # Verify traveller belongs to this trip
            if traveller.trip_id != trip.trip_id:
                flash("You cannot delete this traveller.", "error")
                return redirect(url_for('main.travellers', trip_id=trip.trip_id))
            
            db.session.delete(traveller)
            trip.number_of_travellers = max((trip.number_of_travellers or 1) - 1, 0)
            db.session.commit()
            flash("Traveller deleted!", "success")
            return redirect(url_for('main.travellers', trip_id=trip.trip_id))

    travellers = Traveller.query.filter_by(trip_id=trip.trip_id).all()
    return render_template('travellers.html', trip=trip, travellers=travellers, user=user)  


@main.route('/activities', methods=['GET'])
def activities():
    """Show all activities (for both travellers and agencies)"""
    agencies = TravelAgency.query.all()

    # Huidige user opzoeken
    current_user = None
    is_agency = False

    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        if current_user and current_user.role == 'AGENCY':
            is_agency = True

    # Get all activities
    all_activities = ActivityType.query.options(joinedload(ActivityType.agency)).order_by(ActivityType.created_at.desc()).all()
    
    # Get destinations from database
    destinations = _get_destinations_safe()
    destination_names = [d.name for d in destinations]
    
    # Get filter parameters (support multiple values)
    selected_destination = request.args.get('destination', None)
    selected_difficulties = request.args.getlist('difficulty')  # Multiple values
    selected_types = request.args.getlist('type')  # Multiple values
    selected_durations = request.args.getlist('duration')  # Multiple values
    selected_ages = request.args.getlist('age')  # Multiple values
    selected_agencies = request.args.getlist('agency')  # Multiple values
    view_mode = request.args.get('view', 'list')  # 'list' or 'map'
    
    # Apply filters
    activities = all_activities
    
    if selected_destination:
        activities = [a for a in activities if a.destination == selected_destination]
    
    if selected_difficulties:
        activities = [a for a in activities if a.difficulty in selected_difficulties]
    
    if selected_types:
        activities = [a for a in activities if a.type in selected_types]
    
    if selected_durations:
        # Duration ranges: '1-2', '3-4', '5+'
        def matches_duration(activity):
            if not activity.duration:
                return False
            for dur in selected_durations:
                if dur == '1-2' and 1 <= activity.duration <= 2:
                    return True
                elif dur == '3-4' and 3 <= activity.duration <= 4:
                    return True
                elif dur == '5+' and activity.duration >= 5:
                    return True
            return False
        activities = [a for a in activities if matches_duration(a)]
    
    if selected_ages:
        # Age ranges: 'kids' (0-12), 'teens' (13-17), 'adults' (18+)
        def matches_age(activity):
            for age in selected_ages:
                if age == 'kids' and (activity.min_age is None or activity.min_age <= 12):
                    return True
                elif age == 'teens' and (activity.min_age is None or activity.min_age <= 17) and (activity.max_age is None or activity.max_age >= 13):
                    return True
                elif age == 'adults' and (activity.min_age is None or activity.min_age <= 65):
                    return True
            return False
        activities = [a for a in activities if matches_age(a)]
    
    if selected_agencies:
        agency_ids = []
        for ag in selected_agencies:
            try:
                agency_ids.append(int(ag))
            except ValueError:
                pass
        if agency_ids:
            activities = [a for a in activities if a.agency_id in agency_ids]
    
    # Prepare activities data for map view (JSON)
    activities_json = []
    for a in activities:
        if a.latitude and a.longitude:
            # Build picture URL using the proper helper function
            picture_url = get_activity_image_url(a.picture) if a.picture else None
            
            activities_json.append({
                'id': a.activity_type_id,
                'name': a.name,
                'type': a.type,
                'destination': a.destination,
                'latitude': a.latitude,
                'longitude': a.longitude,
                'difficulty': a.difficulty,
                'duration': a.duration,
                'description': a.description,
                'picture': picture_url,
                'agency': a.agency.name if a.agency else None
            })

    return render_template(
        'activities.html',
        activities=activities,
        activities_json=activities_json,
        agencies=agencies,
        current_user=current_user,
        is_agency=is_agency,
        destinations=destination_names,
        selected_destination=selected_destination,
        selected_difficulties=selected_difficulties,
        selected_types=selected_types,
        selected_durations=selected_durations,
        selected_ages=selected_ages,
        selected_agencies=selected_agencies,
        view_mode=view_mode,
        difficulty_levels=get_difficulty_levels(),
        activity_types=get_activity_types()
    )

@main.route('/my_activities', methods=['GET', 'POST'])
def my_activities():
    """Show and manage agency's own activities"""
    if 'user_id' not in session:
        flash("You must be logged in to view your activities.", "error")
        return redirect(url_for('main.login'))
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'AGENCY':
        flash("This page is only available for agencies.", "error")
        return redirect(url_for('main.activities'))
    
    user_agency = TravelAgency.query.filter_by(user_id=current_user.user_id).first()
    
    if not user_agency:
        # Create agency record if it doesn't exist
        user_agency = TravelAgency(
            name=current_user.name or "User Added",
            contact_info="",
            website="",
            user_id=current_user.user_id,
            created_at=datetime.utcnow()
        )
        db.session.add(user_agency)
        db.session.commit()

    # ---------- POST: nieuwe activity toevoegen ----------
    if request.method == 'POST':
        name        = request.form.get('name')
        type_       = request.form.get('type')
        difficulty  = request.form.get('difficulty')
        destination = request.form.get('destination')
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # sliders
        score_culture    = int(request.form.get('score_culture', 3))
        score_adventure  = int(request.form.get('score_adventure', 3))
        score_relaxation = int(request.form.get('score_relaxation', 3))
        score_nature     = int(request.form.get('score_nature', 3))

        # Age suitability
        min_age_str = request.form.get('min_age')
        max_age_str = request.form.get('max_age')
        min_age = int(min_age_str) if min_age_str and min_age_str.strip() else None
        max_age = int(max_age_str) if max_age_str and max_age_str.strip() else None

        # Duration
        duration_str = request.form.get('duration')
        duration = int(duration_str) if duration_str and duration_str.strip() else None

        # Picture upload to Supabase Storage
        picture_path = None
        if 'picture' in request.files:
            picture_file = request.files['picture']
            if picture_file and picture_file.filename:
                bucket_name = current_app.config.get('SUPABASE_BUCKET_ACTIVITIES', 'activities')
                success, result = upload_file_to_supabase(picture_file, bucket_name)
                if success:
                    picture_path = result
                else:
                    flash(f"Warning: Could not upload image. {result}", "error")

        if not name or not type_ or not destination:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('main.my_activities'))

        new_activity = ActivityType(
            name=name,
            type=type_,
            difficulty=difficulty,
            destination=destination,
            description=description,
            score_culture=score_culture,
            score_adventure=score_adventure,
            score_relaxation=score_relaxation,
            score_nature=score_nature,
            latitude=float(latitude),
            longitude=float(longitude),
            min_age=min_age,
            max_age=max_age,
            duration=duration,
            picture=picture_path,
            agency_id=user_agency.agency_id,
            created_at=datetime.utcnow()
        )
        db.session.add(new_activity)
        db.session.commit()

        flash("Activity added successfully!", "success")
        return redirect(url_for('main.my_activities'))

    # ---------- GET: lijst tonen ----------
    activities = ActivityType.query.filter_by(
        agency_id=user_agency.agency_id
    ).options(joinedload(ActivityType.agency)).order_by(ActivityType.created_at.desc()).all()

    return render_template(
        'activities.html',
        activities=activities,
        agencies=[user_agency],
        current_user=current_user,
        is_agency=True,
        is_my_activities=True,
        destinations=_get_destinations_safe(),
        difficulty_levels=get_difficulty_levels(),
        activity_types=get_activity_types()
    )


@main.route('/edit_activity/<int:activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
    if 'user_id' not in session:
        flash("You must be logged in to edit activities.", "error")
        return redirect(url_for('main.login'))
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'AGENCY':
        flash("Only agencies can edit activities.", "error")
        return redirect(url_for('main.activities'))
    
    # Find the TravelAgency associated with this user
    user_agency = TravelAgency.query.filter_by(user_id=current_user.user_id).first()
    if not user_agency:
        flash("Agency not found.", "error")
        return redirect(url_for('main.activities'))
    
    # Get the activity and verify it belongs to this agency
    activity = ActivityType.query.get_or_404(activity_id)
    if activity.agency_id != user_agency.agency_id:
        flash("You can only edit your own activities.", "error")
        return redirect(url_for('main.my_activities'))
    
    # ------- POST: update activity -------
    if request.method == 'POST':
        activity.name        = request.form.get('name')
        # als het hidden veld 'type' om een of andere reden leeg is, oude waarde behouden
        activity.type        = request.form.get('type') or activity.type
        activity.difficulty  = request.form.get('difficulty')
        activity.destination = request.form.get('destination')
        activity.description = request.form.get('description')

        # scores veilig casten, met fallback op bestaande waarde of 3
        activity.score_culture    = int(request.form.get('score_culture')    or activity.score_culture    or 3)
        activity.score_adventure  = int(request.form.get('score_adventure')  or activity.score_adventure  or 3)
        activity.score_relaxation = int(request.form.get('score_relaxation') or activity.score_relaxation or 3)
        activity.score_nature     = int(request.form.get('score_nature')     or activity.score_nature     or 3)

        # Age suitability
        min_age_str = request.form.get('min_age')
        max_age_str = request.form.get('max_age')
        activity.min_age = int(min_age_str) if min_age_str and min_age_str.strip() else None
        activity.max_age = int(max_age_str) if max_age_str and max_age_str.strip() else None

        # Duration
        duration_str = request.form.get('duration')
        activity.duration = int(duration_str) if duration_str and duration_str.strip() else None

        # Picture upload to Supabase Storage
        if 'picture' in request.files:
            picture_file = request.files['picture']
            if picture_file and picture_file.filename:
                # Debug logging
                print(f"[EDIT ACTIVITY] Picture upload attempt:")
                print(f"  Filename: {picture_file.filename}")
                print(f"  Content type: {picture_file.content_type}")
                print(f"  Content length: {picture_file.content_length if hasattr(picture_file, 'content_length') else 'unknown'}")
                
                bucket_name = current_app.config.get('SUPABASE_BUCKET_ACTIVITIES', 'activities')
                print(f"  Bucket: {bucket_name}")
                
                # Check Supabase config
                supabase_url = current_app.config.get('SUPABASE_URL')
                supabase_key = current_app.config.get('SUPABASE_KEY')
                print(f"  SUPABASE_URL: {supabase_url}")
                print(f"  SUPABASE_KEY present: {bool(supabase_key)}")
                if supabase_key:
                    print(f"  SUPABASE_KEY length: {len(supabase_key)}")
                    print(f"  SUPABASE_KEY starts with eyJ: {supabase_key.startswith('eyJ')}")
                
                # Delete old picture if exists
                if activity.picture:
                    print(f"  Deleting old picture: {activity.picture}")
                    delete_file_from_supabase(activity.picture, bucket_name)
                
                # Upload new picture
                print(f"  Starting upload...")
                success, result = upload_file_to_supabase(picture_file, bucket_name)
                if success:
                    print(f"  ✅ Upload successful: {result}")
                    activity.picture = result
                else:
                    print(f"  ❌ Upload failed: {result}")
                    flash(f"Warning: Could not upload image. {result}", "error")

        if not activity.name or not activity.type or not activity.destination:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('main.edit_activity', activity_id=activity_id))

        db.session.commit()
        flash("Activity updated successfully!", "success")
        return redirect(url_for('main.my_activities'))
    
    # ------- GET: toon edit formulier -------
    return render_template(
        'edit_activity.html', 
        activity=activity, 
        user=current_user,
        destinations=_get_destinations_safe(),
        difficulty_levels=get_difficulty_levels(),
        activity_types=get_activity_types()
    )


@main.route('/agencies')
def agencies():
    current_user = None
    is_agency = False
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        if current_user and current_user.role == 'AGENCY':
            is_agency = True
    
    # Get all agencies with their user information
    all_agencies = TravelAgency.query.order_by(TravelAgency.name).all()
    
    def find_agency_logo(agency):
        """Get logo path for an agency from database (contact_info field)"""
        # Logo is stored in contact_info field
        # Can be: Supabase path, or full URL (http/https)
        if agency and agency.contact_info:
            return agency.contact_info
        return None
    
    # Get user information and logo for each agency
    agencies_with_users = []
    for agency in all_agencies:
        user = User.query.get(agency.user_id)
        logo_path = find_agency_logo(agency)
        agencies_with_users.append({
            'agency': agency,
            'user': user,
            'logo': logo_path
        })
    
    return render_template('agencies.html', user=current_user, agencies=agencies_with_users, is_agency=is_agency, current_user=current_user)

@main.route('/my_agency', methods=['GET', 'POST'])
def my_agency():
    """Redirect to profile page - agency info is now managed there"""
    return redirect(url_for('main.profile'))

@main.route('/generate_itinerary/<int:trip_id>')
def generate(trip_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    # Agencies should not access itinerary generation
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))
    
    trip = Trip.query.get_or_404(trip_id)

    if trip.user_id != session.get('user_id'):
        flash("You cannot generate an itinerary for someone else's trip.", "error")
        return redirect(url_for('main.trips'))

    created = generate_itinerary(trip)

    if created is None:
        flash("First add travellers details", "error")
        return redirect(url_for('main.travellers', trip_id=trip.trip_id))
    elif created == "NO_COORDINATES":
        flash("Some activities are missing location coordinates. Please contact support.", "error")
        return redirect(url_for('main.trips'))
    elif created == "AGE_FILTERED":
        flash("No activities found that match the age requirements of all travellers.", "error")
        return redirect(url_for('main.trips'))
    elif not created:
        flash("No suitable activities were found for this trip.", "error")
        return redirect(url_for('main.trips'))

    flash("Itinerary successfully generated!", "success")
    return redirect(url_for('main.itinerary_view', trip_id=trip.trip_id))


@main.route('/itinerary/<int:trip_id>')
def itinerary_view(trip_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    # Agencies should not access itinerary views
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))
    
    trip = Trip.query.get_or_404(trip_id)
    activities = (
        ActivityPlanned.query.filter_by(trip_id=trip_id)
        .join(ActivityType)
        .order_by(ActivityPlanned.date)
        .all()
    )
    return render_template('itinerary.html', trip=trip, activities=activities, user=user)

@main.route('/itinerary/select')
def itinerary_select():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    # Agencies should not access itinerary selection
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))
    
    trips = Trip.query.filter_by(user_id=user.user_id).all()
    return render_template('itinerary_select.html', trips=trips, user=user)


@main.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile/account management page"""
    if 'user_id' not in session:
        flash("You must be logged in to view your profile.", "error")
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('main.login'))
    
    # Get agency if user is an agency
    agency = None
    if user.role == 'AGENCY':
        agency = TravelAgency.query.filter_by(user_id=user.user_id).first()
        if not agency:
            # Create agency record if it doesn't exist
            agency = TravelAgency(
                name=user.name or "My Agency",
                contact_info="",
                website="",
                user_id=user.user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(agency)
            db.session.commit()
    
    if request.method == 'POST':
        field = request.form.get('field', '')
        
        if field == 'name':
            name = request.form.get('name', '').strip()
            if not name:
                flash("Name is required.", "error")
                return redirect(url_for('main.profile'))
            user.name = name
            # Also update agency name if user is an agency
            if agency:
                agency.name = name
            flash("Name updated successfully!", "success")
            
        elif field == 'email':
            email = request.form.get('email', '').strip()
            if not email:
                flash("Email is required.", "error")
                return redirect(url_for('main.profile'))
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.user_id != user.user_id:
                flash("This email is already registered to another account.", "error")
                return redirect(url_for('main.profile'))
            user.email = email
            flash("Email updated successfully!", "success")
            
        elif field == 'phone':
            phone_number = request.form.get('phone_number', '').strip()
            user.phone_number = phone_number if phone_number else None
            flash("Phone number updated successfully!", "success")
        
        elif field == 'website' and agency:
            website = request.form.get('website', '').strip()
            agency.website = website if website else None
            agency.updated_at = datetime.utcnow()
            flash("Website updated successfully!", "success")
        
        elif field == 'logo' and agency:
            if 'logo' in request.files:
                logo_file = request.files['logo']
                if logo_file and logo_file.filename:
                    bucket_name = current_app.config.get('SUPABASE_BUCKET_LOGOS', 'logos')
                    
                    # Delete old logo if exists
                    if agency.contact_info:
                        delete_file_from_supabase(agency.contact_info, bucket_name)
                    
                    # Upload new logo
                    success, result = upload_file_to_supabase(logo_file, bucket_name)
                    if success:
                        agency.contact_info = result
                        agency.updated_at = datetime.utcnow()
                        flash("Logo updated successfully!", "success")
                    else:
                        flash(f"Could not upload logo: {result}", "error")
                else:
                    flash("Please select a file to upload.", "error")
        
        db.session.commit()
        return redirect(url_for('main.profile'))
    
    # GET: Show profile page
    trip_count = 0
    if user.role == 'TRAVELLER':
        trip_count = Trip.query.filter_by(user_id=user.user_id).count()
    
    return render_template('profile.html', user=user, agency=agency, trip_count=trip_count)


@main.route('/test-supabase')
def test_supabase():
    """Test route to check Supabase configuration"""
    from .storage import get_supabase_client
    
    results = {
        'package_installed': False,
        'config_url': None,
        'config_key': None,
        'client_initialized': False,
        'error': None
    }
    
    # Check if package is installed
    try:
        import supabase
        results['package_installed'] = True
    except ImportError as e:
        results['error'] = f"Supabase package not installed: {e}"
        return f"<h1>Supabase Test</h1><pre>{json.dumps(results, indent=2)}</pre>"
    
    # Check configuration
    try:
        results['config_url'] = current_app.config.get('SUPABASE_URL', 'Not set')
        results['config_key'] = 'Set' if current_app.config.get('SUPABASE_KEY') else 'Not set'
    except Exception as e:
        results['error'] = f"Error reading config: {e}"
        return f"<h1>Supabase Test</h1><pre>{json.dumps(results, indent=2)}</pre>"
    
    # Try to initialize client
    try:
        client = get_supabase_client()
        if client:
            results['client_initialized'] = True
        else:
            results['error'] = "Client returned None"
    except Exception as e:
        results['error'] = f"Error initializing client: {e}"
    
    return f"<h1>Supabase Test</h1><pre>{json.dumps(results, indent=2)}</pre>"


@main.route('/itinerary/<int:trip_id>/share')
def itinerary_public(trip_id):
    """Public shareable view of an itinerary (no login required)"""
    trip = Trip.query.get_or_404(trip_id)
    activities = (
        ActivityPlanned.query.filter_by(trip_id=trip_id)
        .join(ActivityType)
        .order_by(ActivityPlanned.date)
        .all()
    )
    
    # Get current user if logged in (for navbar display)
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    
    return render_template('itinerary_public.html', trip=trip, activities=activities, user=user, is_public=True)