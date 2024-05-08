from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash # for security purpose when store pw in db
from .forms import LoginForm, RegistrationForm
from .models import db, User, Admin, StripeCustomer, StripeSubscription, Filepath, Journey, Location, Friendship
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime
from werkzeug.utils import secure_filename
from .utils import is_valid_password, allowed_file,parse_gpx, info_parse_gpx, create_and_append_csv, save_uploaded_file, create_map_html,create_route_image,upload_journey_database,upload_filepath_database,upload_location_database, create_multiple_route_map_html, find_active_subscription, parse_gpx_and_calculate_distance 
from config import ConfigClass

from flask import jsonify

import pandas as pd
import folium
import gpxpy
import stripe
import os
import csv
import app

main_blueprint = Blueprint('main', __name__)

# Price IDs for different subscription plans
price_ids = {
    'Weekly': 'price_1Om2zYJuJzcfSKx8xpaqnWQN',
    'Monthly': 'price_1Om2EKJuJzcfSKx8iBN5hANS',
    'Yearly': 'price_1Om2EYJuJzcfSKx8nnoBFPZI'
}

# route for homepage
@main_blueprint.route('/')
def index():
    return render_template('landing.html')

# route for main page
@main_blueprint.route('/main')
def main():
    return render_template('main.html')

# route for login page
@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Return to appropriate dashboard if user has been authenticated
    if current_user.is_authenticated:
        # Check if the authenticated user is an admin
        if isinstance(current_user, Admin):
            return redirect(url_for('admin.index'))  # Redirect to admin dashboard
        else:
            active_subscription = find_active_subscription(current_user)
            if active_subscription == 'No Subscription':
                flash('No active subscription found. Please subscribe to fully utilize the app.', 'danger')
                return redirect(url_for('main.membership'))
            return redirect(url_for('main.dashboard'))  # Redirect to user dashboard

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        admin = Admin.query.filter_by(username=form.username.data).first()

        if user:
            if not user.check_password(form.password.data):
                form.password.errors.append('Invalid password')
            else:
                login_user(user)
                # Check for active subscription
                active_subscription = find_active_subscription(user)
                if active_subscription == 'No Subscription':
                    flash('No active subscription found. Please subscribe to fully utilize the app.', 'danger')
                    return redirect(url_for('main.membership'))

                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        elif admin:
            if not admin.check_password(form.password.data):
                form.password.errors.append('Invalid password')
            else:
                login_user(admin)
                return redirect(url_for('admin.index'))
        else:
            flash('Invalid username', 'danger')
    return render_template('login.html', form=form)

# make sure the username is unique
# route for registration
@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if not is_valid_password(form.password.data):
            # If the password is not valid, flash a message to the user
            flash('Password must have at least 1 capital letter, 1 numeric, and be at least 8 characters long', 'danger')
            return render_template('register.html', form=form)
        
        existing_email = User.query.filter_by(email=form.email.data).first()
        existing_user = User.query.filter_by(username=form.username.data).first()

        if existing_email:
            form.email.errors.append('An account with this email already exists')
        elif existing_user:
            form.username.errors.append('This username is taken. Please choose a different one')
        else:
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
                flash('An error occurred while creating the account', 'danger')

    return render_template('register.html', form=form)

@main_blueprint.route('/dashboard')
@login_required
def dashboard():
    # Use the utility function to check for active subscription
    active_subscription = find_active_subscription(current_user)

    if active_subscription == 'No Subscription':
        flash('No active subscription found. Please subscribe to access the dashboard.', 'danger')
        return redirect(url_for('main.membership'))

    return render_template('dashboard.html')

# route for logout
@main_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# route for subscription plan
@main_blueprint.route('/subscription')
@login_required
def subscription():
    plan = request.args.get('plan', default='Monthly', type=str)  # Get the plan from query parameter
    return render_template('subscription.html', plan=plan, stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))

# route for membership
@main_blueprint.route('/membership')
@login_required
def membership():
    # Get the StripeCustomer associated with the current user
    stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
    current_plan = None
    renewal_date = None

    if stripe_customer:
        # Get the active StripeSubscription associated with the StripeCustomer
        stripe_subscription = StripeSubscription.query.filter_by(
            stripe_customer_id=stripe_customer.id,
            active=True
        ).first()
        if stripe_subscription:
            current_plan = stripe_subscription.plan
            # Get the renewal date
            renewal_date = stripe_subscription.renewal_date

    return render_template('membership.html', current_plan=current_plan, renewal_date=renewal_date)

# route for payment
@main_blueprint.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    if not current_user.is_authenticated:
        flash('Please log in to subscribe.', 'danger')
        return redirect(url_for('main.login'))

    name = request.form['name']
    email = request.form['email']
    plan = request.form['plan']

    # Check if name and email are provided
    if not name:
        flash('Please enter a name.', 'danger')
        return redirect(url_for('main.subscription'))
    
    if not email:
        flash('Please enter an email address.', 'danger')
        return redirect(url_for('main.subscription'))

    try:
        # Create a customer in Stripe
        customer = stripe.Customer.create(name=name, email=email)

        # Subscribe the customer to the selected plan in Stripe
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_ids[plan]}],
            payment_behavior='default_incomplete'
        )

        # After successfully creating a Stripe subscription, save details in your database
        # Ensure that the StripeCustomer is either found or created successfully
        stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
        if not stripe_customer:
            stripe_customer = StripeCustomer(user_id=current_user.id, stripe_customer_id=customer.id)
            db.session.add(stripe_customer)
            db.session.commit()

        # Now create the StripeSubscription instance
        stripe_subscription = StripeSubscription(
            stripe_customer_id=stripe_customer.id,
            stripe_subscription_id=subscription.id,
            plan=plan,
            active=True,
            start_date=datetime.utcnow().date()
        )
        stripe_subscription.set_renewal_date()
        db.session.add(stripe_subscription)
        db.session.commit()

        return redirect(url_for('main.subscription_success'))

    except Exception as e:
        current_app.logger.error(f'Error creating Stripe subscription: {e}')
        flash(f'There was an error processing your subscription: {str(e)}', 'danger')
        return redirect(url_for('main.subscription'))

# route for success subscription
@main_blueprint.route('/success')
@login_required
def subscription_success():
    return render_template('success.html')

# route for cancel plan
@main_blueprint.route('/cancel_plan', methods=['POST'])
@login_required
def cancel_plan():
    plan = request.form['plan']
    stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
    
    if stripe_customer:
        stripe_subscription = StripeSubscription.query.filter_by(
            stripe_customer_id=stripe_customer.id, 
            plan=plan, 
            active=True
        ).first()

        if stripe_subscription:
            # Update the subscription status to inactive
            stripe_subscription.active = False
            db.session.commit()
            
            # Optionally, cancel the subscription in Stripe as well
            stripe.Subscription.delete(stripe_subscription.stripe_subscription_id)

            flash('Your subscription has been successfully canceled.', 'success')
        else:
            flash('No active subscription found.', 'danger')
    else:
        flash('No customer record found.', 'danger')

    return redirect(url_for('main.membership'))

# route for change plan
@main_blueprint.route('/confirm_change_plan', methods=['POST'])
@login_required
def confirm_change_plan():
    new_plan = request.form['new_plan']
    current_plan = request.form['current_plan']
    return render_template('confirm_change_plan.html', new_plan=new_plan, current_plan=current_plan)

@main_blueprint.route('/change_plan', methods=['POST'])
@login_required
def change_plan():
    new_plan = request.form['new_plan']
    current_plan = request.form['current_plan']
    confirmation = request.form.get('confirm')

    if confirmation == 'yes':
        # Cancel the current plan and redirect to the subscription page
        stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
        
        if stripe_customer:
            stripe_subscription = StripeSubscription.query.filter_by(
                stripe_customer_id=stripe_customer.id,
                plan=current_plan,
                active=True
            ).first()

            if stripe_subscription:
                # Update the subscription status to inactive
                stripe_subscription.active = False
                db.session.commit()
                
                # Optionally, cancel the subscription in Stripe as well
                stripe.Subscription.delete(stripe_subscription.stripe_subscription_id)

                flash('Your current subscription has been successfully canceled.', 'success')
            else:
                flash('No active subscription found.', 'danger')
        else:
            flash('No customer record found.', 'danger')

        return redirect(url_for('main.subscription', plan=new_plan))
    else:
        # Redirect back to the membership page if the user does not confirm
        return redirect(url_for('main.membership'))

@main_blueprint.route('/map', methods=['GET', 'POST'])
@login_required
def map():

    if request.method == 'GET':
        # Use the utility function to check for active subscription
        active_subscription = find_active_subscription(current_user)
        
        if active_subscription == 'No Subscription':
            flash('No active subscription found. Please subscribe to access the upload map page.', 'danger')
            return redirect(url_for('main.membership'))
    else:
        redirect(request.url)
    
    if request.method == 'POST':

        if not os.path.exists(ConfigClass.UPLOAD_FOLDER):
            os.makedirs(ConfigClass.UPLOAD_FOLDER)

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']

        if file.filename == '':
            flash('No selected file.', 'danger')
            return redirect(request.url)
        
        if '.' in file.filename and file.filename.rsplit('.',1)[1].lower() in ConfigClass.ALLOWED_EXTENSIONS:
            pass
        else:
            flash('Invalid file type selected, please select a GPX file.', 'danger')
            return redirect(request.url)
        
        if  file and allowed_file(file.filename):
            gpx_file_path = save_uploaded_file(file, ConfigClass.UPLOAD_FOLDER)
            
            coordinates = parse_gpx(gpx_file_path)
            info = info_parse_gpx(gpx_file_path)

            # Create image file for route
            file_path = 'app/static/image'
            image_file_path = create_route_image(coordinates, file_path)

            # Create CSV for points
            points_csv_file = 'points.csv'
            create_and_append_csv(points_csv_file, ConfigClass.HEADER_INFO, [[point['name'], point['latitude'], point['longitude'], point['address']] for point in info],current_user.id)
              
            # Calculate total distance
            total_distance = parse_gpx_and_calculate_distance(gpx_file_path)

            #upload to Journey class
            new_journey = upload_journey_database(points_csv_file,current_user.id, total_distance)

            #upload to Filepath class
            upload_filepath_database(new_journey, image_file_path, gpx_file_path, current_user.id)

            #upload to Location class
            upload_location_database(points_csv_file, new_journey,current_user.id)
              
            # Create and get map HTML
            map_html_content = create_map_html(coordinates)
        
            return render_template('map_api.html', map_html_content=map_html_content, distances = total_distance,)

        else:
            return redirect(request.url)
    
    return render_template('map.html')

# Only current user map records
@main_blueprint.route('/map_record', methods=['GET','POST'])
@login_required
def records():
    if request.method == 'GET':
        # Use the utility function to check for active subscription
        active_subscription = find_active_subscription(current_user)

        if active_subscription == 'No Subscription':
            flash('No active subscription found. Please subscribe to access the map.', 'danger')
            return redirect(url_for('main.membership'))
        
        journeys = Journey.query.filter_by(user_id=current_user.id).order_by(Journey.upload_time.desc()).all()

        db.session.commit()
        
        return render_template('map_record.html', journeys=journeys)
    
    return redirect(request.url)

# Multiple records for both user & friends
@main_blueprint.route('/map_multi_record', methods=['GET','POST'])
@login_required
def multiRecords():
    if request.method == 'GET':
        # Use the utility function to check for active subscription
        active_subscription = find_active_subscription(current_user)

        if active_subscription == 'No Subscription':
            flash('No active subscription found. Please subscribe to access the map.', 'danger')
            return redirect(url_for('main.membership'))
        
        # Subquery to get IDs of friends of the current user
        friend_ids_subquery = (
            db.session.query(Friendship.friend_id)
            .filter(Friendship.user_id == current_user.id)
        )

        journeys = (
            db.session.query(Journey, User.username)
            .join(User, Journey.user_id == User.id)
            .filter(or_(Journey.user_id == current_user.id, Journey.user_id.in_(friend_ids_subquery)))
            .all()
        )

        db.session.commit()
        
        return render_template('map_multi_record.html', journeys=journeys)
    
    return redirect(request.url)

@main_blueprint.route('/map_record/submit-selected-journeys', methods=['POST'])
@login_required
def submit_selected_journey_map():
    
    selected_journeys = request.form.getlist('journey_ids')

    if not selected_journeys:
        flash('No track selected. Please select at least one track.', 'danger')
        return redirect(url_for('main.records'))
    
    gpx_file_paths = []

    for journey_id in selected_journeys:
        filepath_info = Filepath.query.filter_by(journey_id = journey_id).all()
        for entry in filepath_info:
            gpx_file_paths.append(entry.gpx_file_path)

    multiple_route_map_html_content = create_multiple_route_map_html(gpx_file_paths)

    return render_template('multiple_route_map_api.html', multiple_route_map_html_content = multiple_route_map_html_content)

# download data route
@main_blueprint.route('/download/<filename>')
@login_required
def download_gpx_file(filename):

    pure_filename = os.path.basename(filename)
    file_path = os.path.join(ConfigClass.UPLOAD_FOLDER, pure_filename )
    print(file_path)
    if not os.path.isfile(file_path):
        return "File not found.", 404
    with open(file_path, 'rb') as f:
        data = f.read()
    response = Response(data, mimetype='application/gpx+xml')
    response.headers.set('Content-Disposition', 'attachment', filename=filename)
    return response

# Delete data route
@main_blueprint.route('/delete_journey/<int:journey_id>', methods=['POST'])
@login_required
def delete_journey(journey_id):
    # Check if the journey exists
    journey = Journey.query.get(journey_id)
    if not journey:
        # Handle case where the journey doesn't exist
        return jsonify({'status': 'error', 'message': 'Journey not found'}), 404
    
    # Get the associated Filepath record and delete its image file
    filepath_entry = Filepath.query.filter_by(journey_id=journey_id).first()
    if filepath_entry:
        image_path = filepath_entry.image_file_path
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Delete associated Location records
    Location.query.filter_by(journey_id=journey_id).delete()
    
    # Delete associated Filepath record
    Filepath.query.filter_by(journey_id=journey_id).delete()
    
    # Empty the row corresponding to the journey in points.csv
    points_csv_path = os.path.join(os.path.dirname(__file__), '..', 'points.csv')  # Adjust the path as needed
    with open(points_csv_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        
        # Update the row corresponding to the journey ID
        if journey_id < len(rows):
            rows[journey_id] = []

    with open(points_csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    
    # Check if all rows after the header are empty
    if all(not any(row) for row in rows[1:]):
        os.remove(points_csv_path)
        
    # Delete the journey from the database
    db.session.delete(journey)
    db.session.commit()

    # Check if the journey still exists in the database
    if Journey.query.get(journey_id):
        return jsonify({'status': 'error', 'message': 'Failed to delete journey'}), 500
    
    return jsonify({'status': 'success', 'message': 'Journey deleted successfully'})

# Create route for friends page
@main_blueprint.route('/friends')
@login_required
def friends():
    if request.method == 'GET':
        # Use the utility function to check for active subscription
        active_subscription = find_active_subscription(current_user)

        if active_subscription == 'No Subscription':
            flash('No active subscription found. Please subscribe to access friends page.', 'danger')
            return redirect(url_for('main.membership'))
        
        # Query the friends of the logged-in user
        friends = (
            User.query
            .join(Friendship, User.id == Friendship.friend_id)
            .filter(Friendship.user_id == current_user.id)
            .all()
        )
        return render_template('friends.html', friends=friends)
    return redirect(request.url)

# Search bar
@main_blueprint.route("/search")
@login_required
def search():
    # Query for input keywords
    q = request.args.get("q")

    if q:
        # Query all users list
        results = (
            User.query
            .join(Friendship, User.id == Friendship.friend_id)
            .filter(User.username.icontains(q))
            .filter(User.id != current_user.id)
            .order_by(Friendship.user_id == current_user.id) # Orders by whether the user is a friend of the current user
            .all()
        )
        
    else:
        results = []

    return render_template('friendsResults.html', results=results)

# For the "Find friends" page
@main_blueprint.route('/get_friends')
@login_required
def get_friends():
    # Query the friends of the logged-in user
    friends = (
        User.query
        .join(Friendship, User.id == Friendship.friend_id)
        .filter(Friendship.user_id == current_user.id)
        .all()
    )

    # Convert friends to JSON format
    friends_json = [{'username': friend.username} for friend in friends]

    return jsonify(friends_json)

@main_blueprint.route('/get_suggested_users')
@login_required
def get_suggested_users():
    # Subquery to get IDs of friends of the current user
    subquery = (
        db.session.query(Friendship.friend_id)
        .filter(Friendship.user_id == current_user.id)
    )

    # Query users who are not friends of the current user
    suggested_users = (
        User.query
        .filter(User.id != current_user.id)
        .filter(~User.id.in_(subquery))
        .limit(5)  # Limit to top 5 suggested users
        .all()
    )

    # Convert suggested users to JSON format
    suggested_users_json = [{'username': user.username} for user in suggested_users]

    return jsonify(suggested_users_json)

@main_blueprint.route('/delete_friendship/<string:friend_username>')
@login_required
def delete_friendship(friend_username):
    # Find the user object corresponding to the friend_username
    friend = User.query.filter_by(username=friend_username).first()

    # Check if the friend exists
    if friend is None:
        return jsonify({'error': 'User does not exist'})

    # Check if the friend is a friend of the current user
    if friend not in current_user.friends.all():
        return jsonify({'info': 'User is not your friend'})

    # Find Friendship instances
    instance1 = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend.id).first()
    instance2 = Friendship.query.filter_by(user_id=friend.id, friend_id=current_user.id).first()

    # Delete the Friendship instances if found
    if instance1:
        db.session.delete(instance1)
        db.session.delete(instance2)
        db.session.commit()
        return jsonify({'success': 'Friendship deleted successfully'})
    else:
        return jsonify({'error': 'Friendship not found'})

@main_blueprint.route('/add_friendship/<string:friend_username>')
@login_required
def add_friendship(friend_username):
    # Find the user object corresponding to the friend_username
    friend = User.query.filter_by(username=friend_username).first()

    # Check if the friend exists
    if friend is None:
        return jsonify({'error': 'User does not exist'})

    # Check if the friend is already a friend
    if friend in current_user.friends.all():
        return jsonify({'info': 'User is already your friend'})

    # Create new Friendship instances (reciprocal)
    friendship1 = Friendship(user_id=current_user.id, friend_id=friend.id)
    friendship2 = Friendship(user_id=friend.id, friend_id=current_user.id)
    db.session.add(friendship1)
    db.session.add(friendship2)
    db.session.commit()

    return jsonify({'success': 'Friend added successfully'})

# register the blueprint with the app
def configure_routes(app):
    app.register_blueprint(main_blueprint)