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
    Given a database and a UUID generator,
    When a User model instance with a unique username and email is created and saved,
    Then provide a reusable User fixture with a unique username and email each time.
    """
    unique_username = f"user_{uuid.uuid4().hex}"  # Generate a unique username using UUID
    unique_email = f"test_{uuid.uuid4()}@example.com"  # Generate a unique email
    user = User(username=unique_username, email=unique_email)
    user.set_password('testpassword')
    test_db.session.add(user)
    test_db.session.commit()
    return user

@pytest.fixture(scope='module')
def journey(test_db, user):
    """
    Given a database and a user fixture,
    When a Journey instance linked to the user is created and saved,
    Then provide a reusable Journey fixture for tests.
    """
    journey = Journey(user_id=user.id, total_distance=100.0, upload_time=datetime.utcnow())
    test_db.session.add(journey)
    test_db.session.commit()
    return journey

@pytest.fixture
def create_user(test_db):
    """Helper function to create a user."""
    def _create_user(username, email):
        unique_username = f"{username}_{uuid.uuid4().hex}"  # Append UUID to provided username for uniqueness
        unique_email = f"test_{uuid.uuid4()}@example.com"  # Generate a unique email
        user = User(username=unique_username, email=unique_email)
        user.set_password('securepassword123')
        test_db.session.add(user)
        test_db.session.commit()
        return user
    return _create_user