from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request
from werkzeug.exceptions import HTTPException
from .models import Admin

class UserAdmin(ModelView):
    column_list = ('username',)
    column_searchable_list = ['username']
    list_template = 'admin/model/numbered_list.html'

    def is_accessible(self):
        # Example check if current_user is an instance of an Admin model
        return current_user.is_authenticated and isinstance(current_user, Admin)
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.url))
        # or show a custom 403 error page
        raise HTTPException('You do not have permission to view this page.', 403)
