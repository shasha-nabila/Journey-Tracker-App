import re
from .models import StripeSubscription

def is_valid_password(password_hash):
    # Password must have at least 1 capital letter, 1 numeric, and be at least 8 characters long
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password_hash))

def calculate_projected_revenue(db):
    # Assuming `db` is your SQLAlchemy session

    # Calculate the number of active subscriptions for each plan
    weekly_subs = db.session.query(StripeSubscription).filter_by(plan='Weekly', active=True).count()
    monthly_subs = db.session.query(StripeSubscription).filter_by(plan='Monthly', active=True).count()
    yearly_subs = db.session.query(StripeSubscription).filter_by(plan='Yearly', active=True).count()

    # Subscription rates
    rates = {'Weekly': 3, 'Monthly': 10, 'Yearly': 100}

    # Project revenue for 52 weeks
    projected_revenue = []
    for week in range(52):
        revenue = weekly_subs * rates['Weekly'] + (monthly_subs * rates['Monthly'] / 4) + (yearly_subs * rates['Yearly'] / 52)
        projected_revenue.append(revenue)
        weekly_subs += 0  # Update this if you expect changes in subscription numbers over time
        monthly_subs += 0  # Update this if you expect changes in subscription numbers over time
        yearly_subs += 0  # Update this if you expect changes in subscription numbers over time

    return projected_revenue