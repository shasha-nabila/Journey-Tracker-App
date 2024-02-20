# database model
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin # for user authentication
from werkzeug.security import generate_password_hash, check_password_hash

# init with no parameters (will configured with the app later)
db = SQLAlchemy()
login_manager = LoginManager() #to handle user authentication
login_manager.login_view = 'main.login'  # endpoint for login page

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

# load a user from db
@login_manager.user_loader
def load_user(user_id):
    # will return user object based on user id
    return User.query.get(int(user_id))
