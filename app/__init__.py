from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app=Flask(__name__)
app.config.from_object('config')

# Creating database
db =  SQLAlchemy(app)

# Creating migration
migrate = Migrate(app, db, render_as_batch=True)

from app import views