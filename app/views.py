from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash # for security purpose when store pw in db
from .forms import LoginForm, RegistrationForm
from .models import db, User, Admin, StripeCustomer, StripeSubscription
from sqlalchemy.exc import IntegrityError
from .utils import is_valid_password
from datetime import datetime

import stripe
import os

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
    return render_template('main.html')

# route for login page
@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # return to dashboard if user has been authenticated
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # create instance for login form
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        admin = Admin.query.filter_by(username=form.username.data).first()

        # Check if the username exists either as a user or an admin
        if user:
            if not user.check_password(form.password.data):
                form.password.errors.append('Invalid password')
            else:
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        elif admin:
            if not admin.check_password(form.password.data):
                form.password.errors.append('Invalid password')
            else:
                login_user(admin)
                return redirect(url_for('admin.index'))
        else:
            # Username doesn't exist in both User and Admin tables
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

# route for subscription plan
@main_blueprint.route('/subscription')
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
    if stripe_customer:
        # Get the active StripeSubscription associated with the StripeCustomer
        stripe_subscription = StripeSubscription.query.filter_by(
            stripe_customer_id=stripe_customer.id,
            active=True
        ).first()
        if stripe_subscription:
            current_plan = stripe_subscription.plan

    return render_template('membership.html', current_plan=current_plan)

# route for payment
@main_blueprint.route('/subscribe', methods=['POST'])
def subscribe():
    if not current_user.is_authenticated:
        flash('Please log in to subscribe.', 'danger')
        return redirect(url_for('main.login'))

    name = request.form['name']
    email = request.form['email']
    plan = request.form['plan']

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
        db.session.add(stripe_subscription)
        db.session.commit()

        return redirect(url_for('main.subscription_success'))

    except Exception as e:
        current_app.logger.error(f'Error creating Stripe subscription: {e}')
        flash(f'There was an error processing your subscription: {str(e)}', 'danger')
        return redirect(url_for('main.subscription'))

# route for success subscription
@main_blueprint.route('/success')
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

# register the blueprint with the app
def configure_routes(app):
    app.register_blueprint(main_blueprint)
