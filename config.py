# config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class ConfigClass:
    SECRET_KEY = 'WeRiize119'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = 'gpx'
    HEADER_INFO = ['name_1', 'latitude_1', 'longitude_1', 'address_1','name_2', 'latitude_2', 'longitude_2', 'address_2']
    HEADER_DISTANCE = ['distance']
    # Other configurations
