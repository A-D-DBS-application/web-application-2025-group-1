from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from .models import db, User, Traveller, Trip


# ⬇️ Maak een Blueprint aan i.p.v. rechtstreeks met app werken
main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return f'Logged in as {user.email}'
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        if User.query.filter_by(email=email).first() is None:
            new_user = User(email=email)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect(url_for('main.index'))
        return 'Email already registered'
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('main.index'))
        return 'User not found'
    return render_template('login.html')

@main.route('/logout') 
def logout():
    session.pop('user_id', None)
    session.clear
    return redirect(url_for('main.index'))

#hiermee kan de user de itinerary zien
@main.route('/itinerary')
def itinerary():
    return render_template('itinerary.html')

#hiermee kan de user een trip aanmaken
@main.route('/create_trip', methods=['GET', 'POST'])
def create_trip():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        num_travellers = int(request.form.get('num_travellers'))
        preference = request.form.get('preference')
        destination = request.form.get('destination')

        new_trip = Trip(
            created_at=datetime.now(),
            Start_Date=start_date,
            End_Date=end_date,
            Number_Of_Travelers=num_travellers,
            preferences=preference,
            User_id=session['user_id']
        )
        db.session.add(new_trip)
        db.session.commit()

        for i in range(num_travellers):
            traveller = Traveller(
                created_at=datetime.now(),
                age=None,
                fitness=None,
                Trip_id=new_trip.Trip_id
            )
            db.session.add(traveller)

        db.session.commit()

        return redirect(url_for('main.itinerary', trip_id=new_trip.Trip_id))

    return render_template('create_trip.html')

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
