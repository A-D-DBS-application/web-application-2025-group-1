from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, Numeric, BigInteger

db = SQLAlchemy()

# -----------------------------
# ENUM TYPES (USER-DEFINED)
# -----------------------------
# Deze moet je definiëren overeenkomstig wat je in Supabase hebt ingesteld.
pref_kind_enum = Enum('ADVENTURE', 'CULTURE', 'RELAX', name='pref_kind', create_type=False)
fitness_level_enum = Enum('LOW', 'MEDIUM', 'HIGH', name='fitness_level', create_type=False)
activity_difficulty_enum = Enum('EASY', 'MODERATE', 'HARD', name='activity_difficulty', create_type=False)


# -----------------------------
# BASISMODEL met tijdstempels
# -----------------------------
class BaseModel(db.Model):
    __abstract__ = True

    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)


# -----------------------------
# GEBRUIKERS EN REIZEN
# -----------------------------
class User(db.Model):  # niet van BaseModel erven omdat created_at/updated_at anders niet matchen
    __tablename__ = 'User'

    user_id = db.Column(BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=True, name='Name')
    email = db.Column(db.Text, nullable=True, unique=True, name='Email')
    phone_number = db.Column(db.Text, nullable=True, name='Phone_Number')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, name='created_at')

    trips = db.relationship('Trip', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'


class Trip(BaseModel):
    __tablename__ = 'Trip'

    trip_id = db.Column(BigInteger, primary_key=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    number_of_travelers = db.Column(Numeric, nullable=True)
    preferences = db.Column(pref_kind_enum, nullable=True)
    user_id = db.Column(BigInteger, db.ForeignKey('User.user_id'), nullable=True)

    travellers = db.relationship('Traveller', backref='trip', lazy=True)
    planned_activities = db.relationship('ActivityPlanned', backref='trip', lazy=True)
    hotel_bookings = db.relationship('HotelBooking', backref='trip', lazy=True)

    def __repr__(self):
        return f'<Trip {self.trip_id}>'


class Traveller(BaseModel):
    __tablename__ = 'Travellers'

    traveller_id = db.Column(BigInteger, primary_key=True)
    age = db.Column(db.Date, nullable=True)
    fitness = db.Column(fitness_level_enum, nullable=True)
    trip_id = db.Column(BigInteger, db.ForeignKey('Trip.trip_id'), nullable=True)

    def __repr__(self):
        return f'<Traveller {self.traveller_id}>'


# -----------------------------
# TRAVEL AGENCIES
# -----------------------------
class TravelAgency(BaseModel):
    __tablename__ = 'Travel_agencies'

    agency_id = db.Column(BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.Text, nullable=True)
    website = db.Column(db.Text, nullable=True)

    activities = db.relationship('ActivityType', backref='agency', lazy=True)

    def __repr__(self):
        return f'<TravelAgency {self.name}>'


# -----------------------------
# ACTIVITEITEN
# -----------------------------
class ActivityType(BaseModel):
    __tablename__ = 'Activity_type'

    activity_type_id = db.Column(BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    destination = db.Column(db.Text, nullable=False)
    difficulty = db.Column(activity_difficulty_enum, nullable=True)
    agency_id = db.Column(BigInteger, db.ForeignKey('Travel_agencies.agency_id'), nullable=False)

    planned_activities = db.relationship('ActivityPlanned', backref='activity_type', lazy=True)

    def __repr__(self):
        return f'<ActivityType {self.name}>'


class ActivityPlanned(BaseModel):
    __tablename__ = 'Activity_planned'

    trip_id = db.Column(BigInteger, db.ForeignKey('Trip.trip_id'), primary_key=True, nullable=False)
    activity_type_id = db.Column(BigInteger, db.ForeignKey('Activity_type.activity_type_id'), primary_key=True, nullable=False)
    date = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<ActivityPlanned trip={self.trip_id} activity={self.activity_type_id}>'


# -----------------------------
# HOTELS EN BOEKINGEN
# -----------------------------
class Hotel(BaseModel):
    __tablename__ = 'Hotel'

    hotel_id = db.Column(BigInteger, primary_key=True)
    adress = db.Column(db.Text, nullable=True)

    bookings = db.relationship('HotelBooking', backref='hotel', lazy=True)

    def __repr__(self):
        return f'<Hotel {self.hotel_id}>'


class HotelBooking(BaseModel):
    __tablename__ = 'Hotel_Booking'

    booking_id = db.Column(BigInteger, primary_key=True)
    trip_id = db.Column(BigInteger, db.ForeignKey('Trip.trip_id'), nullable=False)
    check_in_time = db.Column(db.DateTime(timezone=True), nullable=True)
    check_out_time = db.Column(db.DateTime(timezone=True), nullable=True)
    hotel_id = db.Column(BigInteger, db.ForeignKey('Hotel.hotel_id'), nullable=False)

    def __repr__(self):
        return f'<HotelBooking {self.booking_id}>'