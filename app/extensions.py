from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin
from flask_babel import Babel

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
admin = Admin(template_mode='Bootstrap4')
babel = Babel()