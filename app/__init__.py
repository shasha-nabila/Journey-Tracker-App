from flask import Flask
from dotenv import load_dotenv
from .extensions import db, login_manager, migrate, babel

import stripe
import os
import click

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Stripe API key
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    app.config.from_object('config.ConfigClass')  # refer the class in config.py

    from .extensions import admin
    from .admin import UserAdmin, MyAdminIndexView

    # initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app, index_view=MyAdminIndexView())
    babel.init_app(app)

    login_manager.login_view = 'main.login'  # endpoint for login page

    # import admin views
    from .models import User
    admin.add_view(UserAdmin(User, db.session))

    # import and register blueprints
    from .views import main_blueprint
    app.register_blueprint(main_blueprint)

    # command line syntax to create admin user:
    # flask create-admin [username] [email] [password]
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("email")
    @click.argument("password")
    def create_admin(username, email, password):
        from .models import Admin, db  # Import here to avoid circular dependencies
        admin = Admin(username=username, email=email)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user {username} created successfully.")

    return app

# load a user/admin from db
@login_manager.user_loader
def load_user(user_id):
    from .models import User, Admin
    # will return user/admin object based on user id
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
    else:
        user = User.query.get(int(user_id))
        return user