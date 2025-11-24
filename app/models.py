from datetime import date, datetime

from flask_sqlalchemy import SQLAlchemy  # type: ignore[import]
from sqlalchemy import Enum, Numeric, event, func, select  # type: ignore[import]

db = SQLAlchemy()

# -----------------------------
# ENUM TYPES (USER-DEFINED)
# -----------------------------
# Deze moet je definiëren overeenkomstig wat je in Supabase hebt ingesteld.
pref_kind_enum = Enum('ADVENTURE', 'CULTURE', 'RELAXATION', 'NATURE', name='pref_kind', create_type=True)
fitness_level_enum = Enum('LOW', 'MEDIUM', 'HIGH', name='fitness_level_enum', create_type=True)
activity_difficulty_enum = Enum('EASY', 'MODERATE', 'HARD', name='activity_difficulty_enum', create_type=True)


# -----------------------------
# GEBRUIKERS EN REIZEN
# -----------------------------
class User(db.Model):  # niet van BaseModel erven omdat created_at/updated_at anders niet matchen
    __tablename__ = 'User'

    user_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=True, name='Name')
    email = db.Column(db.Text, nullable=True, unique=True, name='Email')
    phone_number = db.Column(db.Text, nullable=True, name='Phone_Number')
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )

    trips = db.relationship('Trip', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'


class Trip(db.Model):
    __tablename__ = 'Trip'

    trip_id = db.Column(db.BigInteger, primary_key=True, name='Trip_id')
    start_date = db.Column(db.Date, nullable=True, name='Start_Date')
    end_date = db.Column(db.Date, nullable=True, name='End_Date')
    number_of_travellers = db.Column(Numeric, nullable=True, name='Number_Of_Travellers')
<<<<<<< Updated upstream
    preferences = db.Column(pref_kind_enum, nullable=True)

=======
    preferences = db.Column(
    db.Enum('CULTURE', 'ADVENTURE', 'RELAXATION', 'NATURE', name='pref_kind'),
    nullable=True
) 
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    destination = db.Column(db.Text, nullable=True, name='Destination')
    user_id = db.Column(db.BigInteger, db.ForeignKey('User.user_id'), nullable=True, name='User_id')
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )

    travellers = db.relationship('Traveller', backref='trip', lazy=True)
    planned_activities = db.relationship('ActivityPlanned', backref='trip', lazy=True)
    hotel_bookings = db.relationship('HotelBooking', backref='trip', lazy=True)

    def __repr__(self):
        return f'<Trip {self.trip_id}>'


class Traveller(db.Model):
    __tablename__ = 'Travellers'

    traveller_id = db.Column(db.BigInteger, primary_key=True, name='Traveller_id')
    name = db.Column(db.Text, nullable=True, name='Name')
    birth_date = db.Column(db.Date, nullable=False)
    fitness = db.Column(fitness_level_enum, nullable=True)
    trip_id = db.Column(db.BigInteger, db.ForeignKey('Trip.Trip_id'), nullable=True, name='Trip_id')
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        name='created_at',
    )

    # ✅ Automatisch leeftijd berekenen
    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def __repr__(self):
        return f'<Traveller {self.traveller_id}>'

# -----------------------------
# TRAVEL AGENCIES
# -----------------------------
class TravelAgency(db.Model):
    __tablename__ = 'Travel_agencies'

    agency_id = db.Column(db.BigInteger, primary_key=True, name='Agency_id')
    name = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.Text, nullable=True)
    website = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    activities = db.relationship('ActivityType', backref='agency', lazy=True)

    def __repr__(self):
        return f'<TravelAgency {self.name}>'


# -----------------------------
# ACTIVITEITEN
# -----------------------------
class ActivityType(db.Model):
    __tablename__ = 'Activity_type'

    activity_type_id = db.Column(db.BigInteger, primary_key=True, name='Activity_type_id')
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    destination = db.Column(db.Text, nullable=False)
    difficulty = db.Column(activity_difficulty_enum, nullable=True)
    agency_id = db.Column(db.BigInteger, db.ForeignKey('Travel_agencies.Agency_id'), nullable=False, name='Agency_id')
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    planned_activities = db.relationship('ActivityPlanned', backref='activity_type', lazy=True)

    def __repr__(self):
        return f'<ActivityType {self.name}>'


class ActivityPlanned(db.Model):
    __tablename__ = 'Activity_planned'

    trip_id = db.Column(db.BigInteger, db.ForeignKey('Trip.Trip_id'), primary_key=True, nullable=False, name='Trip_id')
    activity_type_id = db.Column(db.BigInteger, db.ForeignKey('Activity_type.Activity_type_id'), primary_key=True, nullable=False, name='Activity_type_id')
    date = db.Column(db.Date, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )

    def __repr__(self):
        return f'<ActivityPlanned trip={self.trip_id} activity={self.activity_type_id}>'


# -----------------------------
# HOTELS EN BOEKINGEN
# -----------------------------
class Hotel(db.Model):
    __tablename__ = 'Hotel'

    hotel_id = db.Column(db.BigInteger, primary_key=True, name='Hotel_id')
    adress = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )

    bookings = db.relationship('HotelBooking', backref='hotel', lazy=True)

    def __repr__(self):
        return f'<Hotel {self.hotel_id}>'


class HotelBooking(db.Model):
    __tablename__ = 'Hotel_Booking'

    booking_id = db.Column(db.BigInteger, primary_key=True, name='Booking_id')
    trip_id = db.Column(db.BigInteger, db.ForeignKey('Trip.Trip_id'), nullable=False, name='Trip_id')
    check_in_time = db.Column(db.DateTime(timezone=True), nullable=True, name='check-in time')
    check_out_time = db.Column(db.DateTime(timezone=True), nullable=True, name='check-out time')
    hotel_id = db.Column(db.BigInteger, db.ForeignKey('Hotel.Hotel_id'), nullable=False, name='Hotel_id')
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )

    def __repr__(self):
        return f'<HotelBooking {self.booking_id}>'


def _register_sqlite_autoincrement(model, pk_field):
    """Ensure SQLite assigns IDs even though the schema mirrors Supabase bigints."""

    pk_column = getattr(model, pk_field).property.columns[0]

    @event.listens_for(model, 'before_insert')
    def _set_pk(mapper, connection, target):
        if connection.dialect.name != 'sqlite':
            return
        if getattr(target, pk_field) is not None:
            return
        max_id = connection.execute(select(func.max(pk_column))).scalar()
        setattr(target, pk_field, (max_id or 0) + 1)


for model, field in [
    (User, 'user_id'),
    (Trip, 'trip_id'),
    (Traveller, 'traveller_id'),
    (TravelAgency, 'agency_id'),
    (ActivityType, 'activity_type_id'),
    (Hotel, 'hotel_id'),
    (HotelBooking, 'booking_id'),
]:
    _register_sqlite_autoincrement(model, field)
