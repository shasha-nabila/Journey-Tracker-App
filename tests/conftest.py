import pytest
import uuid
from app import create_app, db
from app.models import User, Journey
from datetime import datetime

@pytest.fixture(scope='module')
def test_app():
    """
    GIVEN a Flask application
    WHEN the application is configured for testing
    THEN return a test client with an in-memory SQLite database and disabled CSRF protection
    """
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_db(test_app):
    """
    GIVEN the test application configured in the test_app fixture
    WHEN a test module is executed
    THEN provide a database instance that can be used for the duration of the test module
    """
    yield db

@pytest.fixture(scope='function')
def test_client(test_app):
    """
    GIVEN the test application configured in the test_app fixture
    WHEN a test function needs to simulate HTTP requests
    THEN provide a test client for the Flask application
    """
    return test_app.test_client()

@pytest.fixture(scope='module')
def user(test_db):
    """
    Creates a user fixture that can be used for tests requiring a User model, with a unique email each time.
    """
    unique_email = f"test_{uuid.uuid4()}@example.com"
    user = User(username='test_user', email=unique_email)
    user.set_password('testpassword')
    test_db.session.add(user)
    test_db.session.commit()
    return user

@pytest.fixture(scope='module')
def journey(test_db, user):
    """
    Creates a Journey instance linked to the user fixture for tests requiring a Journey model.
    """
    journey = Journey(user_id=user.id, total_distance=100.0, upload_time=datetime.utcnow())
    test_db.session.add(journey)
    test_db.session.commit()
    return journey