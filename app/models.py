from .extensions import db
from flask_login import UserMixin # for user authentication
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import relationship

# user data model will extends the base for database models with user authentication
class User(UserMixin, db.Model):
    __tablename__ = 'user'  # Explicitly setting the table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    stripe_customer = relationship('StripeCustomer', backref='user', uselist=False, cascade="all, delete-orphan")

    # method to set user pw (store the hased ver of the pw)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # method to check pw if matches the stored hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
# stripe data model
class StripeCustomer(db.Model):
    __tablename__ = 'stripe_customer'  # Explicitly setting the table name
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=False)
    stripe_subscription = relationship('StripeSubscription', backref='customer', uselist=False, cascade="all, delete-orphan")

class StripeSubscription(db.Model):
    __tablename__ = 'stripe_subscription'  # Explicitly setting the table name
    id = db.Column(db.Integer, primary_key=True)
    stripe_customer_id = db.Column(db.Integer, db.ForeignKey('stripe_customer.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    plan = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

# admin data model
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Journey(db.Model):
    __tablename__ = 'journey'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    total_distance = db.Column(db.Float, nullable = False)
    upload_time = db.Column(db.DateTime, nullable=False) 
    locations = relationship('Location', backref = 'journey', lazy = True)
    

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key = True)
    journey_id = db.Column(db.Integer, db.ForeignKey('journey.id'), nullable = False)
    init_latitude = db.Column(db.Float, nullable = False)
    init_longitude = db.Column(db.Float, nullable = False)
    goal_latitude = db.Column(db.Float, nullable = False)
    goal_longitude = db.Column(db.Float, nullable = False)
