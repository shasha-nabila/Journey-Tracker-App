from . import db
from flask_login import LoginManager, UserMixin # for user authentication
from werkzeug.security import generate_password_hash, check_password_hash

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

# stripe database
class StripeCustomer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('stripe_customer', lazy=True))

class StripeSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stripe_customer_id = db.Column(db.Integer, db.ForeignKey('stripe_customer.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=False)
    plan = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    stripe_customer = db.relationship('StripeCustomer', backref=db.backref('subscriptions', lazy=True))
