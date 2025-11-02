from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'User'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    phone_number = db.Column(db.Numeric)

    def __repr__(self):
        return f'<User {self.user_id}>'
    
class Trip(db.Model):
    __tablename__ = 'Trip'
    trip_id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    number_of_travelers = db.Column(db.Integer)
    preferences = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'))

    def __repr__(self):
        return f'<Trip {self.trip_id}>'
    
class Traveller(db.Model):
    __tablename__ = 'Travellers'
    traveller_id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Date)
    fitness = db.Column(db.String) 
    trip_id = db.Column(db.Integer, db.ForeignKey('Trip.trip_id'))

    def __repr__(self):
        return f'<Traveller {self.traveller_id}>'