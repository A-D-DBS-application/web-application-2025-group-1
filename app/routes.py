from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from .models import db, User, Traveller, Trip


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
    flash("You have been logged out.")
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
    try:
        current = int(trip.number_of_travelers) if trip.number_of_travelers else 0
    except Exception:
        current = 0
    trip.number_of_travellers = current + 1

    db.session.commit()

    flash("Traveller added!", "success")
    return redirect(url_for('main.trips'))



#hiermee kan een user de travellers age en fitness level aanpassen
@main.route('/edit_travellers/<int:trip_id>', methods=['GET', 'POST'])
def edit_travellers(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    travellers = Traveller.query.filter_by(Trip_id=trip_id).all()

    if request.method == 'POST':
        for traveller in travellers:
            age_field = f"age_{traveller.Traveller_id}"
            fitness_field = f"fitness_{traveller.Traveller_id}"
            traveller.age = request.form.get(age_field)
            traveller.fitness = request.form.get(fitness_field)
        db.session.commit()
        return redirect(url_for('main.itinerary', trip_id=trip_id))

    return render_template('edit_travellers.html', trip=trip, travellers=travellers)
