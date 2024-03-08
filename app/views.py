from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash # for security purpose when store pw in db
from .forms import LoginForm, RegistrationForm
from .models import db, User
from sqlalchemy.exc import IntegrityError
from .utils import is_valid_password
import stripe
import os

main_blueprint = Blueprint('main', __name__)

# Price IDs for different subscription plans
price_ids = {
    'weekly': 'price_1Om2zYJuJzcfSKx8xpaqnWQN',
    'monthly': 'price_1Om2EKJuJzcfSKx8iBN5hANS',
    'yearly': 'price_1Om2EYJuJzcfSKx8nnoBFPZI'
}

# route for homepage
@main_blueprint.route('/')
def index():
    return render_template('main.html')

# route for login page
@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # return to dashboard if user has been authenticated
    if current_user.is_authenticated:
        # Check if the current user is an admin and redirect accordingly
        if current_user.is_admin:
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('main.dashboard'))
    
    # create instance for login form
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next') # for post login redirection
            # If the user is admin, redirect to the admin dashboard instead of the user dashboard
            if user.is_admin:
                # Redirect to an admin-specific page if the user is an admin
                return redirect(next_page) if next_page else redirect(url_for('admin.index'))
            else:
                # Redirect to next page if exists, otherwise dashboard
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

# route for registration
@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if not is_valid_password(form.password.data):
            # If the password is not valid, flash a message to the user
            flash('Password must have at least 1 capital letter, 1 numeric, and be at least 8 characters long', 'danger')
            return render_template('register.html', form=form)
        
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user is None:
            # hash the provided pw with strong hash func (in progress)
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
            db.session.add(new_user) 
            try:
                db.session.commit() # add new user to db
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect(url_for('main.login'))
            except IntegrityError:
                db.session.rollback() # rollback the session in case of error
                flash('This email already exists.', 'danger')
        else:
            flash('A user with that email already exists.', 'danger')
    return render_template('register.html', form=form)

# route to dashboard
@main_blueprint.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# route for logout
@main_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_blueprint.route('/subscription')
def subscription():
    return render_template('subscription.html', stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))

# route for subscription
@main_blueprint.route('/subscribe', methods=['POST'])
def subscribe():
    name = request.form['name']
    email = request.form['email']
    plan = request.form['plan']
    
    try:
        # Create a customer
        customer = stripe.Customer.create(
            name=name,
            email=email
        )

        # Subscribe the customer to the selected plan
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_ids[plan]}],
            payment_behavior='default_incomplete'
        )

        # Assuming subscription creation was successful, redirect to success page
        return redirect(url_for('main.subscription_success'))

    except Exception as e:
        # Log the error and/or send it back to the template
        print(e)  # Consider using logging instead of print for production applications

        # Optionally, use flash messages to show errors on the current page
        flash('There was an error processing your subscription. Please try again.', 'danger')

        # Stay on the current page, potentially showing an error message
        # Make sure your form or subscription page can display flash messages or handle errors
        return redirect(url_for('main.subscription'))  # Adjust 'main.index' as necessary for your app structure

# route for success subscription
@main_blueprint.route('/success')
def subscription_success():
    return render_template('success.html')

# register the blueprint with the app
def configure_routes(app):
    app.register_blueprint(main_blueprint)