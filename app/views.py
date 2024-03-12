from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash # for security purpose when store pw in db
from .forms import LoginForm, RegistrationForm
from .models import db, User
from sqlalchemy.exc import IntegrityError
from .utils import is_valid_password
import stripe
from config import ConfigClass
import os
from .utils import allowed_file,parse_gpx,info_parse_gpx,create_and_append_csv,calculate_distance,save_uploaded_file,create_map_html
import gpxpy
import folium
from werkzeug.utils import secure_filename
import pandas as pd


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
        return redirect(url_for('.dashboard'))
    
    # create instance for login form
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next') # for post login redirection
            # redirect to next page if exist, otherwise dashboard
            return redirect(next_page) if next_page else redirect(url_for('.dashboard'))
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

@main_blueprint.route('/map', methods=['GET', 'POST'])
def map():
    if request.method == 'POST':

        if not os.path.exists(ConfigClass.UPLOAD_FOLDER):
            os.makedirs(ConfigClass.UPLOAD_FOLDER)

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if  file and allowed_file(file.filename):
            file_path = save_uploaded_file(file, ConfigClass.UPLOAD_FOLDER)
            
            coordinates = parse_gpx(file_path)
            info = info_parse_gpx(file_path)

            # Create CSV for points
            points_csv_file = 'points.csv'
            create_and_append_csv(points_csv_file, ConfigClass.HEADER_INFO, [[point['name'], point['latitude'], point['longitude'], point['address']] for point in info])
            
            # Create CSV for distance
            distance_csv_file = 'distance.csv'
            distances = [calculate_distance(info[i], info[i+1]) for i in range(len(info)-1)]
            create_and_append_csv(distance_csv_file, ConfigClass.HEADER_DISTANCE, [[distance] for distance in distances])

            m = folium.Map(location=coordinates[0], zoom_start=17)
            
            initial_coordinate = coordinates[0]
            goal_coordinate = coordinates[-1]
            initial_marker = folium.Marker(initial_coordinate, tooltip='Departure', icon=folium.Icon(color='green')).add_to(m)
            goal_marker = folium.Marker(goal_coordinate, tooltip='Arrival', icon=folium.Icon(color='green')).add_to(m)
             
            # Create and get map HTML
            map_html_content = create_map_html(coordinates)
                    
            return render_template('map_api.html', map_html_content=map_html_content, distances = distances,)

        else:
            return redirect(request.url)
    
    return render_template('map.html')

# register the blueprint with the app
def configure_routes(app):
    app.register_blueprint(main_blueprint)