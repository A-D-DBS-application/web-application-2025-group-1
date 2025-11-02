from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from .models import db, User


@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return f'Logged in as {user.email}'
    return 'You are not logged in <a href="/login">login</a> <a href="/register">register</a>'


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        if User.query.filter_by(email=email).first() is None:
            new_user = User(email=email)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect(url_for('index'))
        return 'Email already registered'
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        return 'User not found'
    return render_template('login.html')


@app.route('/logout') 
def logout():
    session.pop('user_id', None)
    session.clear
    return redirect(url_for('index'))


#hiermee kan de user de itinerary zien
@app.route('/itinerary')
def itinerary():
    # hier zou je de gegenereerde reisroute tonen
    return render_template('itinerary.html')


#hiermee kan de user een trip aanmaken
@app.route('/create_trip', methods=['GET', 'POST'])
def create_trip():
    
    if 'user_id' not in session:      # Alleen ingelogde gebruikers mogen trips maken
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Haal formulierdata op
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        num_travellers = int(request.form.get('num_travellers'))
        preference = request.form.get('preference')
        destination = request.form.get('destination')

        # Maak nieuwe trip aan, de link met de database moet nog overeengestemd worden
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

        #Maak de travellers aan, later kan de leeftijd en fitness nog geupdated worden
        for i in range(num_travellers):
            traveller = Travellers(
                created_at=datetime.now(),
                age=None,  # kun je later opvragen
                fitness=None,
                Trip_id=new_trip.Trip_id
            )
            db.session.add(traveller)

        db.session.commit()

        # Redirect naar itinerary-pagina
        return redirect(url_for('itinerary', trip_id=new_trip.Trip_id))

    #Toon formulier als het een GET is
    return render_template('create_trip.html')



#hiermee kan een user de travellers age en fitness level aanpassen
@app.route('/edit_travellers/<int:trip_id>', methods=['GET', 'POST'])
def edit_travellers(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    travellers = Travellers.query.filter_by(Trip_id=trip_id).all()

    if request.method == 'POST':
        
        for traveller in travellers:
            age_field = f"age_{traveller.Traveller_id}"
            fitness_field = f"fitness_{traveller.Traveller_id}"

            traveller.age = request.form.get(age_field)
            traveller.fitness = request.form.get(fitness_field)

        db.session.commit()
        return redirect(url_for('itinerary', trip_id=trip_id))

    return render_template('edit_travellers.html', trip=trip, travellers=travellers)

