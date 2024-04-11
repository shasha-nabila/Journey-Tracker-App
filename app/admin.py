from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request
from flask_admin import AdminIndexView, expose
from werkzeug.exceptions import HTTPException
from .models import Admin, StripeSubscription, StripeCustomer
from sqlalchemy.orm import aliased
from sqlalchemy import func
from .extensions import db
from .utils import calculate_projected_revenue

class UserAdmin(ModelView):
    column_list = (
        'username', 
        'subscription.plan',  # Access the plan from the StripeSubscription model
        'subscription.active',  # Access the active status from the StripeSubscription model
        'subscription.start_date'  # Access the start date from the StripeSubscription model
    )
    column_searchable_list = ['username']
    list_template = 'admin/model/numbered_list.html'
    
    # Rename the displayed names for the new columns
    column_labels = {
        'subscription.plan': 'Subscription Plan',
        'subscription.active': 'Subscription Status',
        'subscription.start_date': 'Subscription Start Date'
    }

    # Format the 'active' column to show meaningful text instead of True/False
    column_formatters = {
        'subscription.plan': lambda view, context, model, p: UserAdmin._format_plan(model),
        'subscription.active': lambda view, context, model, p: UserAdmin._format_active(model),
        'subscription.start_date': lambda view, context, model, p: UserAdmin._format_start_date(model)
    }

    # Find active subscription
    @staticmethod
    def _format_plan(user):
        # Alias for StripeCustomer to use in our subquery
        stripe_customer_alias = aliased(StripeCustomer)
        
        # Find the active subscription for this user
        active_subscription = StripeSubscription.query.join(
            stripe_customer_alias, 
            stripe_customer_alias.id == StripeSubscription.stripe_customer_id
        ).filter(
            stripe_customer_alias.user_id == user.id,
            StripeSubscription.active == True
        ).order_by(StripeSubscription.start_date.desc()).first()  # Assuming you want the latest subscription
        
        return active_subscription.plan if active_subscription else 'No Subscription'

    @staticmethod
    def _format_active(user):
        # Use the same logic as in _format_plan
        stripe_customer_alias = aliased(StripeCustomer)
        active_subscription = StripeSubscription.query.join(
            stripe_customer_alias, 
            stripe_customer_alias.id == StripeSubscription.stripe_customer_id
        ).filter(
            stripe_customer_alias.user_id == user.id,
            StripeSubscription.active == True
        ).order_by(StripeSubscription.start_date.desc()).first()
        
        return 'Active' if active_subscription else 'Inactive'

    @staticmethod
    def _format_start_date(user):
        # Use the same logic as in _format_plan
        stripe_customer_alias = aliased(StripeCustomer)
        active_subscription = StripeSubscription.query.join(
            stripe_customer_alias, 
            stripe_customer_alias.id == StripeSubscription.stripe_customer_id
        ).filter(
            stripe_customer_alias.user_id == user.id,
            StripeSubscription.active == True
        ).order_by(StripeSubscription.start_date.desc()).first()
    
        return active_subscription.start_date.strftime('%d-%m-%Y') if active_subscription else 'N/A'

    def is_accessible(self):
        # Example check if current_user is an instance of an Admin model
        return current_user.is_authenticated and isinstance(current_user, Admin)
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.url))
        # or show a custom 403 error page
        raise HTTPException('You do not have permission to view this page.', 403)

class MyAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        projected_revenue = calculate_projected_revenue(db)
        cumulative_revenue = [sum(projected_revenue[:i+1]) for i in range(len(projected_revenue))]
        
        # Calculate the number of active subscriptions for each plan
        plan_counts = db.session.query(
            StripeSubscription.plan,
            func.count(StripeSubscription.id)
        ).filter_by(active=True).group_by(StripeSubscription.plan).all()

        # Convert the query result to a dictionary {plan: count}
        plan_counts_dict = {plan: count for plan, count in plan_counts}

        # If specific plans are not found in the dictionary, set their count to 0
        plan_counts_dict.setdefault('Weekly', 0)
        plan_counts_dict.setdefault('Monthly', 0)
        plan_counts_dict.setdefault('Yearly', 0)

        return self.render(
            'admin/index.html',
            cumulative_revenue=cumulative_revenue,
            plan_counts=plan_counts_dict
        )