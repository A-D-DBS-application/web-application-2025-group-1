from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from .models import db, User, Traveller, Trip, ActivityPlanned, ActivityType
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


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for('main.register'))
        
        new_user = User(
            name=name,
            email=email,
            phone_number=phone_number,
            created_at=datetime.now(),
        )
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.user_id
        flash("Registration successful!", "success")
        return redirect(url_for('main.index'))
        
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.user_id
            flash(f"Logged in successfully as {user.name} !", "success")
            return redirect(url_for('main.index'))
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

        preferences_list = request.form.getlist('preferences')  # ✅ haalt meerdere waarden op
        preferences = ", ".join(preferences_list) if preferences_list else None

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

@main.route('/add_traveller', methods=['POST'])
def add_traveller():
    trip_id = request.form.get('trip_id')
    traveller_name = request.form.get('name')
    birth_date_str = request.form.get('birth_date')
    fitness = request.form.get('fitness')

    trip = Trip.query.get_or_404(trip_id)

    if trip.user_id != session['user_id']:
        flash("You cannot modify this trip.", "error")
        return redirect(url_for('main.trips'))

    # ⏳ Zet de datum-string van het formulier om naar een echte date
    birth_date = None
    if birth_date_str:
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Ongeldige geboortedatum.", "danger")
            return redirect(url_for('main.trips'))

    # ✅ Maak nieuwe traveller aan
    new_traveller = Traveller(
        name=traveller_name,
        birth_date=birth_date,
        fitness=fitness if fitness else None,
        trip_id=trip.trip_id,
        created_at=datetime.utcnow()
    )

    db.session.add(new_traveller)

    # ✅ Update aantal reizigers op de trip
    current = int(trip.number_of_travellers or 0)
    trip.number_of_travellers = current + 1

    db.session.commit()

    flash("Traveller added!", "success")
    return redirect(url_for('main.trips'))



@main.route('/edit_traveller/<int:traveller_id>', methods=['POST'])
def edit_traveller(traveller_id):
    traveller = Traveller.query.get_or_404(traveller_id)

    # Controleer of de gebruiker eigenaar is van de trip
    if traveller.trip.user_id != session.get('user_id'):
        flash("You cannot edit this traveller.", "error")
        return redirect(url_for('main.trips'))

    # Ophalen van de nieuwe gegevens
    name = request.form.get('name')
    date_of_birth = request.form.get('date_of_birth')
    fitness_level = request.form.get('fitness_level')

    # Bijwerken
    traveller.name = name
    traveller.birth_date = date_of_birth
    traveller.fitness = fitness_level

    db.session.commit()
    flash("Traveller updated successfully!", "success")
    return redirect(url_for('main.trips'))

@main.route('/activities')
def activities():
    return render_template('activities.html')

@main.route('/hotels')
def hotels():
    return render_template('hotels.html')

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


