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
        # Agencies should only see activities, not trips
        if user and user.role == 'AGENCY':
            return redirect(url_for('main.activities'))
        trips = Trip.query.filter_by(user_id=user.user_id).all()
        return render_template('trips.html', trips=trips, user=user, activity_types=get_activity_types())
    return render_template('index.html')

@main.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    # Agencies should see agency homepage
    if user and user.role == 'AGENCY':
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
        num_travellers = int(request.form.get('num_travellers'))
        preferences = request.form.get('preferences')
        required_activity_ids = request.form.get('required_activity_ids', '')
        excluded_activity_ids = request.form.get('excluded_activity_ids', '')

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        if end_date and start_date and end_date < start_date:
            flash("End date cannot be before start date.", "error")
            return redirect(url_for('main.edit_trip', trip_id=trip_id))

        trip.destination = destination
        trip.start_date = start_date
        trip.end_date = end_date
        trip.number_of_travellers = num_travellers
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
    
    return render_template(
        'edit_trip.html', 
        trip=trip, 
        activities=activities_data, 
        travellers_data=travellers_data, 
        preference_scores=preference_scores_dict, 
        user=user,
        destinations=_get_destinations_safe(),
        activity_types=get_activity_types()
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
    
    # Check if a specific destination was requested
    selected_destination = request.args.get('destination', None)
    activities = all_activities
    if selected_destination:
        activities = [a for a in all_activities if a.destination == selected_destination]

    return render_template(
        'activities.html',
        activities=activities,
        agencies=agencies,
        current_user=current_user,
        is_agency=is_agency,
        destinations=destination_names,
        selected_destination=selected_destination,
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

        # Picture upload
        picture_path = None
        if 'picture' in request.files:
            picture_file = request.files['picture']
            if picture_file and picture_file.filename:
                # Create uploads/activities directory if it doesn't exist
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'activities')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                filename = secure_filename(picture_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                picture_file.save(file_path)
                # Store relative path for database
                picture_path = f"uploads/activities/{unique_filename}"

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

        # Picture upload
        if 'picture' in request.files:
            picture_file = request.files['picture']
            if picture_file and picture_file.filename:
                # Create uploads/activities directory if it doesn't exist
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'activities')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Delete old picture if exists
                if activity.picture:
                    old_picture_path = os.path.join(current_app.root_path, 'static', activity.picture)
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)
                
                # Generate unique filename
                filename = secure_filename(picture_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                picture_file.save(file_path)
                # Store relative path for database
                activity.picture = f"uploads/activities/{unique_filename}"

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
    
    # Simple direct mapping of agency names to logo files
    agency_logo_mapping = {
        'Jaron Decaluwé': 'uploads/logos/Logo_Jaron_Decaluwe.png',
        'Cape Adventures Co.': 'uploads/logos/Logo_Cape_Adventures_Co.png',
        'Cape Adventure Co.': 'uploads/logos/Logo_Cape_Adventures_Co.png',
        'Cape Adventure Co': 'uploads/logos/Logo_Cape_Adventures_Co.png',
        'African Heritage Tours': 'uploads/logos/Logo_African_Heritage_Tours.png',
        'Atlas Adventures': 'uploads/logos/Logo_Atlas_Adventures.png',
        'Axelle Vanbesien': 'uploads/logos/Logo_Axelle_Vanbesien.png',
        'Marrakech Cultural Experiences': 'uploads/logos/Logo_Marrakech_Cultural_Experiences.png',
        'Reisje': 'uploads/logos/Logo_Reisje.png',
        'Reiswinkeltje': 'uploads/logos/Logo_Reiswinkeltje.png',
        'Safari Horizons': 'uploads/logos/Logo_Safari_Horizons.png',
        'Sahara Nomad Tours': 'uploads/logos/Logo_Sahara_Nomad_Tours.png',
        'Wild Coast Experiences': 'uploads/logos/Logo_Wild_Coast_Experiences.png',
    }
    
    def find_agency_logo(agency_name):
        """Get logo path for an agency - check database first, then mapping"""
        # First check if logo is stored in database (contact_info field)
        agency = TravelAgency.query.filter_by(name=agency_name).first()
        if agency and agency.contact_info and agency.contact_info.startswith('uploads/'):
            return agency.contact_info
        
        # Otherwise use direct mapping
        return agency_logo_mapping.get(agency_name)
    
    # Get user information and logo for each agency
    agencies_with_users = []
    for agency in all_agencies:
        user = User.query.get(agency.user_id)
        logo_path = find_agency_logo(agency.name)
        # Also check for external URLs in contact_info
        if not logo_path and agency.contact_info and agency.contact_info.startswith('http'):
            logo_path = agency.contact_info
        agencies_with_users.append({
            'agency': agency,
            'user': user,
            'logo': logo_path
        })
    
    return render_template('agencies.html', user=current_user, agencies=agencies_with_users, is_agency=is_agency, current_user=current_user)

@main.route('/my_agency', methods=['GET', 'POST'])
def my_agency():
    if 'user_id' not in session:
        flash("You must be logged in to view your agency profile.", "error")
        return redirect(url_for('main.login'))
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'AGENCY':
        flash("This page is only available for agencies.", "error")
        return redirect(url_for('main.activities'))
    
    user_agency = TravelAgency.query.filter_by(user_id=current_user.user_id).first()
    
    if not user_agency:
        # Create agency record if it doesn't exist
        user_agency = TravelAgency(
            name=current_user.name or "My Agency",
            contact_info="",
            website="",
            user_id=current_user.user_id,
            created_at=datetime.utcnow()
        )
        db.session.add(user_agency)
        db.session.commit()
    
    if request.method == 'POST':
        # Update agency information
        website_url = request.form.get('website_url', '').strip()
        logo_url = request.form.get('logo_url', '').strip()
        
        user_agency.website = website_url
        user_agency.contact_info = logo_url  # Using contact_info to store logo URL
        user_agency.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash("Agency information updated successfully!", "success")
        return redirect(url_for('main.my_agency'))
    
    return render_template('my_agency.html', user=current_user, agency=user_agency)

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