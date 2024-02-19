# Include imports here
from app import db, login_manager
from sqalchemy.sql import func
from flask_login import UserMixin

# Database models here
# class Users(db.Model, UserMixin):
#   id = db.Column(db.Integer, primary_key=True)
# Relationships with other models