from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from datetime import datetime
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
from .models import db, User, Traveller, Trip, ActivityPlanned, ActivityType, TravelAgency
from .utils import generate_itinerary


# ⬇️ Maak een Blueprint aan i.p.v. rechtstreeks met app werken
main = Blueprint('main', __name__)
#hallo
@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        # Agencies should only see activities, not trips
        if user and user.role == 'AGENCY':
            return redirect(url_for('main.activities'))
        trips = Trip.query.filter_by(user_id=user.user_id).all()
        return render_template('trips.html', trips=trips)
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
            flash(f"Logged in successfully as {user.name} !", "success")
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
            flash(f"Logged in successfully as {user.name}!", "success")
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
@main.route('/trips', methods=['GET', 'POST'])
def trips():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    # Agencies should only see activities, not trips
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))

    if request.method == 'POST':
        destination = request.form.get('destination')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        num_travellers = int(request.form.get('num_travellers'))
        preferences = request.form.get('preferences')

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        if start_date and end_date and end_date < start_date:
            flash("End date cannot be before start date.", "error")
            return redirect(url_for('main.trips'))

        if not destination:
            flash("Please enter a destination.", "error")
            return redirect(url_for('main.trips'))

        try:
            num_travellers = int(num_travellers)
        except (TypeError, ValueError):
            num_travellers = 1


        new_trip = Trip(
            created_at=datetime.now(),
            start_date=start_date,
            end_date=end_date,
            number_of_travellers=num_travellers,
            preferences=preferences if preferences else None,
            destination=destination,
            user_id=user.user_id
        )
        db.session.add(new_trip)
        db.session.commit()

        flash("Trip succesvol aangemaakt!", "success")
        return redirect(url_for('main.trips'))

    trips = (
        Trip.query
        .filter_by(user_id=user.user_id)
        .order_by(Trip.created_at.desc())
        .all()
    )
    return render_template('trips.html', trips=trips)

@main.route('/trips/<int:trip_id>/edit', methods=['GET', 'POST'])
def edit_trip(trip_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    trip = Trip.query.get_or_404(trip_id)

    if request.method == 'POST':
        destination = request.form.get('destination')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        num_travellers = int(request.form.get('num_travellers'))
        preferences = request.form.get('preferences')

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

        db.session.commit()
        flash("Trip updated successfully!", "success")
        return redirect(url_for('main.trips'))

    return render_template('edit_trip.html', trip=trip)

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
    return render_template('travellers.html', trip=trip, travellers=travellers)  


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
    activities = ActivityType.query.options(joinedload(ActivityType.agency)).order_by(ActivityType.created_at.desc()).all()

    return render_template(
        'activities.html',
        activities=activities,
        agencies=agencies,
        current_user=current_user,
        is_agency=is_agency
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
        is_my_activities=True
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
    return render_template('edit_activity.html', activity=activity)



@main.route('/hotels')
def hotels():
    return render_template('hotels.html')

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
    
    # Get user information for each agency
    agencies_with_users = []
    for agency in all_agencies:
        user = User.query.get(agency.user_id)
        agencies_with_users.append({
            'agency': agency,
            'user': user
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
    return render_template('itinerary.html', trip=trip, activities=activities)

@main.route('/itinerary/select')
def itinerary_select():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    # Agencies should not access itinerary selection
    if user and user.role == 'AGENCY':
        return redirect(url_for('main.activities'))
    
    trips = Trip.query.filter_by(user_id=user.user_id).all()
    return render_template('itinerary_select.html', trips=trips)