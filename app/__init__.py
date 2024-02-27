from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

import stripe
import os
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Stripe API key
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    app.config.from_object('config.ConfigClass')  # refer the class in config.py

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'main.login'  # endpoint for login page

    # import and register blueprints
    from .views import main_blueprint
    app.register_blueprint(main_blueprint)

    return app

# load a user from db
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    # will return user object based on user id
    return User.query.get(int(user_id))