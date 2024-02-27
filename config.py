# config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class ConfigClass:
    SECRET_KEY = 'WeRiize119'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Other configurations
