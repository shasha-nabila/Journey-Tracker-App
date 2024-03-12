from . import db
from flask_login import LoginManager, UserMixin # for user authentication
from werkzeug.security import generate_password_hash, check_password_hash
from .utils import parse_gpx, info_parse_gpx

# user data-model will extends the base for database models with user authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    # method to set user pw (store the hased ver of the pw)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # method to check pw if matches the stored hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Waypoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(255))

    @classmethod
    def save_waypoints_to_database(cls, file_path):
        points = parse_gpx(file_path)
        for lat, lon in points:
            waypoint = cls(latitude=lat, longitude=lon)
            db.session.add(waypoint)
        db.session.commit()
    
        
    def save_info_to_database(cls, file_path):
        info = info_parse_gpx(file_path)
        for point_info in info:
            waypoint = cls(name=point_info['name'],
                           latitude=point_info['latitude'],
                           longitude=point_info['longitude'],
                           address=point_info['address'])
            db.session.add(waypoint)
        db.session.commit()
    














