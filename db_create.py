from config import SQALCHEMY_DATABASE_URI
from app import db
import os.path

db.create_all()