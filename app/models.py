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
user_role_enum = Enum('TRAVELLER', 'AGENCY', name='user_role', create_type=True)

# -----------------------------
# GEBRUIKERS EN REIZEN
# -----------------------------
class User(db.Model):  # niet van BaseModel erven omdat created_at/updated_at anders niet matchen
    __tablename__ = 'User'

    user_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=True, name='Name')
    email = db.Column(db.Text, nullable=True, unique=True, name='Email')
    phone_number = db.Column(db.Text, nullable=True, name='Phone_Number')
    role = db.Column(user_role_enum, nullable=False, name='Role')
    #volgens chatgpt sterk aangeraden om nog een password aan toe te voegen
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )

    trips = db.relationship('Trip', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.user_id} ({self.role})>'


class Trip(db.Model):
    __tablename__ = 'Trip'

    trip_id = db.Column(db.BigInteger, primary_key=True, name='Trip_id')
    start_date = db.Column(db.Date, nullable=True, name='Start_Date')
    end_date = db.Column(db.Date, nullable=True, name='End_Date')

    number_of_travellers = db.Column(db.Integer, nullable=True, name='Number_Of_Travellers')
    preferences = db.Column(pref_kind_enum, nullable=True)

    number_of_travellers = db.Column(Numeric, nullable=True, name='Number_Of_Travellers')
    preferences = db.Column(
    db.Enum('CULTURE', 'ADVENTURE', 'RELAXATION', 'NATURE', name='pref_kind'),
    nullable=True
) 

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
    __tablename__ = 'Travel_agencies_id'   # exact zoals in de DB

    agency_id = db.Column(
        db.BigInteger,
        primary_key=True,
        name='Agency_id'                   # kolomnaam in de DB
    )

    name = db.Column(db.Text, nullable=False)          # eventueel name='Name' als je kolom zo heet
    contact_info = db.Column(db.Text, nullable=True)   # idem
    website = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        name='created_at',
        default=datetime.utcnow,
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey('User.user_id'),
        nullable=False,
        name='User_id'
    )

    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # relatie naar ActivityType
    activities = db.relationship(
        'ActivityType',
        back_populates='agency',
        lazy='dynamic',
    )

    def __repr__(self):
        return f'<TravelAgency {self.name}>'


class ActivityType(db.Model):
    __tablename__ = 'Activity_type'   # matcht de bestaande tabelnaam in de DB

    activity_type_id = db.Column(
        db.BigInteger,
        primary_key=True,
        name='Activity_type_id'       # kolom in de DB
    )

    name        = db.Column(db.String(120), nullable=False)
    type        = db.Column(db.String(30),  nullable=False)   # CULTURE / ADVENTURE / ...
    difficulty  = db.Column(db.String(20))                    # of een Enum als je dat later wil
    destination = db.Column(db.String(50),  nullable=False)

    description = db.Column(db.Text)

    score_culture    = db.Column(db.Integer, default=3)
    score_adventure  = db.Column(db.Integer, default=3)
    score_relaxation = db.Column(db.Integer, default=3)
    score_nature     = db.Column(db.Integer, default=3)
    latitude  = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    agency_id = db.Column(
        db.BigInteger,
        db.ForeignKey('Travel_agencies_id.Agency_id'),  # ⚠️ hier zit de echte FK
        name='Agency_id',
        nullable=False,
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # terug-relatie naar TravelAgency
    agency = db.relationship(
        'TravelAgency',
        back_populates='activities',
    )

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

    activity = db.relationship("ActivityType", backref="planned_instances")

    def __repr__(self):
        return f'<ActivityPlanned trip={self.trip_id} activity={self.activity_type_id}>'

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
]:
    _register_sqlite_autoincrement(model, field)
