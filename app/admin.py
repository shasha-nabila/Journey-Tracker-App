from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request
from werkzeug.exceptions import HTTPException
from .models import Admin

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
        'subscription.plan': lambda v, c, m, p: m.subscription.plan if m.subscription else 'No Subscription',
        'subscription.active': lambda v, c, m, p: 'Active' if m.subscription and m.subscription.active else 'Inactive',
        'subscription.start_date': lambda v, c, m, p: m.subscription.start_date.strftime('%Y-%m-%d') if m.subscription else 'N/A'
    }

    def is_accessible(self):
        # Example check if current_user is an instance of an Admin model
        return current_user.is_authenticated and isinstance(current_user, Admin)
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.url))
        # or show a custom 403 error page
        raise HTTPException('You do not have permission to view this page.', 403)
