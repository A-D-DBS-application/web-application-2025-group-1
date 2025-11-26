from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from .models import db, User, Traveller, Trip, ActivityPlanned, ActivityType, TravelAgency
from .utils import generate_itinerary


# ⬇️ Maak een Blueprint aan i.p.v. rechtstreeks met app werken
main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        trips = Trip.query.filter_by(user_id=user.user_id).all()
        return render_template('trips.html', trips=trips)
    return render_template('index.html')

@main.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    trips = Trip.query.filter_by(user_id=user.user_id).all()
    
    return render_template('home.html', user=user, trips=trips)


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        role = request.form.get('role')

        if role not in ('TRAVELLER','AGENCY'):
            flash("Please choose a valid role.","error")
            return redirect(url_for('main.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for('main.register'))
        
        new_user = User(
            name=name,
            email=email,
            phone_number=phone_number,
            role = role,
            created_at=datetime.now(),
        )
        db.session.add(new_user)
        db.session.flush() #zodat user.user_id bestaat

        if role == 'AGENCY':
            agency = TravelAgency(
                name=name,
                contact_info=phone_number or "",
                website="",
                user_id =new_user.user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(agency)
        
        db.session.commit()

        session['user_id'] = new_user.user_id
        flash("Registration successful!", "success")
        return redirect(url_for('main.home'))
        
    return render_template('register.html')

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

    trips = Trip.query.filter_by(user_id=user.user_id).all()
    return render_template('trips.html', trips=trips)

@main.route('/travellers/<int:trip_id>', methods=['GET', 'POST'])
def travellers(trip_id): 
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

    travellers = Traveller.query.filter_by(trip_id=trip.trip_id).all()
    return render_template('travellers.html', trip=trip, travellers=travellers)  

@main.route('/travellers/<int:trip_id>/delete/<int:traveller_id>', methods=['POST'])
def delete_traveller(trip_id, traveller_id):
    trip = Trip.query.get_or_404(trip_id)
    traveller = Traveller.query.get_or_404(traveller_id)

    # check: hoort deze traveller bij de juiste gebruiker?
    if trip.user_id != session.get('user_id'):
        flash("You cannot delete a traveller from someone else's trip.", "error")
        return redirect(url_for('main.travellers', trip_id=trip_id))

    # verwijder traveller
    db.session.delete(traveller)

    # teller -1 doen
    trip.number_of_travellers = max((trip.number_of_travellers or 1) - 1, 0)

    db.session.commit()
    flash("Traveller deleted!", "success")
    return redirect(url_for('main.travellers', trip_id=trip_id))


@main.route('/activities', methods=['GET'])
def activities():
    all_activities = ActivityType.query.order_by(ActivityType.created_at.desc()).all()
    agencies = TravelAgency.query.all()
    return render_template('activities.html', activities=all_activities, agencies=agencies)

def get_current_user():
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

@main.route('/add_activity', methods=['POST'])
def add_activity(): #check of de soort user correct is (agency of reiziger)
    user = get_current_user()
    if not user:
        flash("You must be logged in to add activities.", "error")
        return redirect(url_for('main.login'))

    if user.role != 'Agency':
        flash("Only agencies can add activities.", "error")
        return redirect(url_for('main_activities'))

    agency = TravelAgency.query.filter_by(user_id=user.user_id).first()
    if not agency:
        flash("No agency profile found for this account.", "error")
        return redirect(url_for('main.activities'))

    name = request.form.get('name')
    type_ = request.form.get('type')
    difficulty = request.form.get('difficulty')
    destination = request.form.get('destination')
    agency_id = request.form.get('agency_id') or None

    if not name or not type_ or not destination:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for('main.activities'))

    new_activity = ActivityType(
        name=name,
        type=type_,
        difficulty=difficulty,
        destination=destination,
        agency_id=agency_id,
        created_at=datetime.utcnow()
    )
    db.session.add(new_activity)
    db.session.commit()

    flash("Activity added successfully!", "success")
    return redirect(url_for('main.activities'))

@main.route('/agencies')
def agencies():
    return render_template('agencies.html')

@main.route('/generate_itinerary/<int:trip_id>')
def generate(trip_id):
    trip = Trip.query.get_or_404(trip_id)

    if trip.user_id != session.get('user_id'):
        flash("You cannot generate an itinerary for someone else's trip.", "error")
        return redirect(url_for('main.trips'))

    created = generate_itinerary(trip)

    if not created:
        flash("No suitable activities were found for this trip.", "error")
        return redirect(url_for('main.trips'))

    flash("Itinerary successfully generated!", "success")
    return redirect(url_for('main.itinerary_view', trip_id=trip.trip_id))


@main.route('/itinerary/<int:trip_id>')
def itinerary_view(trip_id):
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
    trips = Trip.query.filter_by(user_id=user.user_id).all()
    return render_template('itinerary_select.html', trips=trips)