from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request
from werkzeug.exceptions import HTTPException

class UserAdmin(ModelView):
    column_list = ('username', 'member_since')
    column_searchable_list = ['username']
    list_template = 'admin/model/numbered_list.html'

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.url))
        # or show a custom 403 error page
        raise HTTPException('You do not have permission to view this page.', 403)
