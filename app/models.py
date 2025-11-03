from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -----------------------------
# BASISMODEL met tijdstempels
# -----------------------------
class BaseModel(db.Model):
    __abstract__ = True  

    created_at = db.Column(db.DateTime(timezone=True))
    updated_at = db.Column(db.DateTime(timezone=True))


# -----------------------------
# GEBRUIKERS EN REIZEN
# -----------------------------
class User(BaseModel):
    __tablename__ = 'User'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    phone_number = db.Column(db.Numeric)

    # Relatie: één gebruiker → meerdere trips
    trips = db.relationship('Trip', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'


class Trip(BaseModel):
    __tablename__ = 'Trip'

    trip_id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    number_of_travelers = db.Column(db.Integer)
    preferences = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)

    travellers = db.relationship('Traveller', backref='trip', lazy=True)
    planned_activities = db.relationship('ActivityPlanned', backref='trip', lazy=True)
    hotel_bookings = db.relationship('HotelBooking', backref='trip', lazy=True)

    def __repr__(self):
        return f'<Trip {self.trip_id}>'


class Traveller(BaseModel):
    __tablename__ = 'Travellers'

    traveller_id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Date)
    fitness = db.Column(db.String)
    trip_id = db.Column(db.Integer, db.ForeignKey('Trip.trip_id'), nullable=False)

    def __repr__(self):
        return f'<Traveller {self.traveller_id}>'


# -----------------------------
# TRAVEL AGENCIES
# -----------------------------
class TravelAgency(BaseModel):
    __tablename__ = 'Travel_agencies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.Text)
    website = db.Column(db.Text)

    # Relatie: één agency → meerdere activiteiten
    activities = db.relationship('ActivityType', backref='agency', lazy=True)

    def __repr__(self):
        return f'<TravelAgency {self.name}>'


# -----------------------------
# ACTIVITEITEN
# -----------------------------
class ActivityType(BaseModel):
    __tablename__ = 'Activity_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text)
    destination = db.Column(db.Text)
    difficulty = db.Column(db.String)
    agency_id = db.Column(db.Integer, db.ForeignKey('Travel_agencies.id'))

    planned_activities = db.relationship('ActivityPlanned', backref='activity_type', lazy=True)

    def __repr__(self):
        return f'<ActivityType {self.name}>'


class ActivityPlanned(BaseModel):
    __tablename__ = 'Activity_planned'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('Trip.trip_id'), nullable=False)
    activity_type_id = db.Column(db.Integer, db.ForeignKey('Activity_type.id'), nullable=False)
    date = db.Column(db.Date)

    def __repr__(self):
        return f'<ActivityPlanned trip={self.trip_id} activity={self.activity_type_id}>'


# -----------------------------
# HOTELS EN BOEKINGEN
# -----------------------------
class Hotel(BaseModel):
    __tablename__ = 'Hotel'

    hotel_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.Text)

    bookings = db.relationship('HotelBooking', backref='hotel', lazy=True)

    def __repr__(self):
        return f'<Hotel {self.hotel_id}>'


class HotelBooking(BaseModel):
    __tablename__ = 'Hotel_Booking'

    booking_id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('Trip.trip_id'), nullable=False)
    check_in_time = db.Column(db.DateTime(timezone=True))
    check_out_time = db.Column(db.DateTime(timezone=True))
    hotel_id = db.Column(db.Integer, db.ForeignKey('Hotel.hotel_id'), nullable=False)

    def __repr__(self):
        return f'<HotelBooking {self.booking_id}>'