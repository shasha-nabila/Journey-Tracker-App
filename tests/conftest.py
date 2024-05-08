import pytest
from app import create_app, db

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