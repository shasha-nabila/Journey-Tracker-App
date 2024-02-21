from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .models import db, login_manager, User
from .views import main_blueprint

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config.from_object('config.ConfigClass')  # refer the class in config.py

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # import and register blueprints
    from .views import main_blueprint
    app.register_blueprint(main_blueprint)

    return app

# load a user from db
@login_manager.user_loader
def load_user(user_id):
    # will return user object based on user id
    return User.query.get(int(user_id))