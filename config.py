# config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class ConfigClass:
    SECRET_KEY = 'WeRiize119'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = 'gpx'
    HEADER_INFO = ['name_init', 'latitude_init', 'longitude_init', 'address_init','name_goal', 'latitude_goal', 'longitude_goal', 'address_goal','upload_date','user_id']
    # Other configurations
