from app import create_app, db

app = create_app()

# create db table within the app
with app.app_context():
    db.create_all()
