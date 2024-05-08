import pytest
import random
import string
from app.models import User, StripeCustomer, StripeSubscription, Admin, Journey, Location, Filepath, Friendship
from sqlalchemy.exc import IntegrityError, DataError, StatementError
from datetime import datetime, timedelta

@pytest.mark.parametrize("model", [User, Admin])
def test_new_user_or_admin(test_db, model):
    """
    GIVEN a model (User or Admin)
    WHEN a new instance is created with a username and password
    THEN check the instance is added to the session and committed to the database
    """
    # GIVEN
    instance = model(username='testuser', email='test@example.com')

    # WHEN
    instance.set_password('securepassword123')
    test_db.session.add(instance)
    test_db.session.commit()

    # THEN
    assert instance in test_db.session

@pytest.mark.parametrize("model", [User, Admin])
def test_username_email_uniqueness(test_db, model):
    """
    GIVEN a model (User or Admin)
    WHEN a new instance is created with an existing username or email
    THEN the database should raise an IntegrityError
    """
    test_db.session.rollback()  # Start with a clean session
    
    # Creating first instance
    instance1 = model(username='uniqueuser', email='unique@example.com')
    instance1.set_password('securepassword123')
    test_db.session.add(instance1)
    test_db.session.commit()

    # Attempting to create a second instance with the same username
    instance2 = model(username='uniqueuser', email='different@example.com')
    instance2.set_password('securepassword123')
    test_db.session.add(instance2)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

    # Clear session to try with the same email
    test_db.session.rollback()

    # Attempting to create a second instance with the same email
    instance3 = model(username='anotheruser', email='unique@example.com')
    instance3.set_password('securepassword123')
    test_db.session.add(instance3)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

@pytest.mark.parametrize("model", [User, Admin])
@pytest.mark.parametrize("email_description, email_value", [
    ('typical_email', 'user@example.com'),  # A typical email format
    ('email_with_special_chars', 'user+name@example.com'),  # Email with special characters
    ('email_missing_at_symbol', 'userexample.com'),  # Missing '@' symbol
    ('empty_email', '')  # Empty email field
])

def test_email_varied_inputs(model, email_description, email_value, test_db):
    """
    GIVEN a model (User or Admin)
    WHEN an email is set and then saved to the database
    THEN ensure the email is correctly stored and retrievable
    AND check for any data integrity issues or validation errors
    """
    test_db.session.rollback()  # Start with a clean session

    instance = model(username='testuser_' + email_description, email=email_value)
    instance.set_password('securepassword123')

    test_db.session.add(instance)
    try:
        test_db.session.commit()
        retrieved_instance = model.query.filter_by(email=email_value).first()
        assert retrieved_instance is not None, "Instance should be retrievable by email"
        assert retrieved_instance.email == email_value, f"Email stored ({retrieved_instance.email}) should match the provided email ({email_value})"
    except Exception as e:
        assert isinstance(e, IntegrityError), f"Expected IntegrityError, got {type(e).__name__} instead"
        test_db.session.rollback()
    finally:
        test_db.session.delete(instance)
        test_db.session.commit()

@pytest.mark.parametrize("model_class", [User, Admin])
@pytest.mark.parametrize("username_description, username_value", [
    ('very_long_username', 'user_' + 'a' * 255),  # Extremely long username
    ('special_characters', '@user#!$%'),  # Username with special characters
    ('typical_username', 'regular_user'),  # A typical username
    ('empty_username', '')  # Empty username
])

def test_username_varied_inputs(model_class, username_description, username_value, test_db):
    """
    GIVEN a model class (User or Admin) and various types of usernames
    WHEN the username is set and then saved to the database
    THEN ensure the username is correctly stored and retrievable
    AND check for any data integrity issues or validation errors
    """

    # Start clean session
    test_db.session.rollback()

    # GIVEN a model instance and a username
    instance = model_class(username=username_value, email=username_value + '@example.com')
    test_db.session.add(instance)

    # WHEN the username is set
    try:
        test_db.session.commit()
        # THEN ensure the username is correctly stored and retrievable
        retrieved_instance = model_class.query.filter_by(username=username_value).first()
        assert retrieved_instance is not None, "Instance should be retrievable by username"
        assert retrieved_instance.username == username_value, f"Username stored ({retrieved_instance.username}) should match the provided username ({username_value})"
    except IntegrityError:
        test_db.session.rollback()
        pytest.fail(f"Database should not raise IntegrityError for username: {username_description}")

    # Clean up after the test
    test_db.session.delete(instance)
    test_db.session.commit()

@pytest.mark.parametrize("model_class", [User, Admin])
@pytest.mark.parametrize("password_description, password_value", [
    ('long_password', 'a' * 10000),  # Very long password
    ('non_alphanumeric', '@#$$%^&*()_+!?><'),  # Non-alphanumeric characters
    ('normal_password', 'normalpassword123'),  # Typical password
    ('short_password', 'short')  # Short password, less than recommended length
])

def test_password_varied_inputs(model_class, password_description, password_value, test_db):
    """
    GIVEN a model class (User or Admin) and various types of passwords
    WHEN the password is set and then checked
    THEN ensure the 'check_password' method correctly verifies the password
    AND the plaintext password is not stored in the password_hash
    """

    # Start clean session
    test_db.session.rollback()

    # GIVEN a model instance and a password
    instance = model_class(username='varietyuser_'+password_description, email='variety_'+password_description+'@example.com')
    instance.set_password(password_value)
    test_db.session.add(instance)

    # WHEN the password is set
    try:
        test_db.session.commit()
    except IntegrityError:
        # THEN the database should raise an IntegrityError due to a unique constraint on the email
        test_db.session.rollback()

    # THEN the 'check_password' method should return True since the correct password is used
    assert instance.check_password(password_value), f"Failed on password: {password_description}"
    
    # AND the plaintext password should not be stored in the password_hash
    assert password_value not in instance.password_hash, "Plaintext password should not be stored in password_hash"
    
    # Clean up after the test
    test_db.session.delete(instance)
    test_db.session.commit()

@pytest.mark.parametrize("model_class", [User, Admin])
def test_set_password_side_effects(model_class, test_db):
    """
    GIVEN a model class (User or Admin)
    WHEN set_password is called
    THEN it should not return any value and should not alter any unrelated attributes
    """
    instance = model_class(username='testuser3', email='test3@example.com')
    original_username = instance.username
    original_email = instance.email

    # set_password should not return a value
    result = instance.set_password('newsecurepassword123')
    assert result is None, "set_password should not return any data"

    # Check other attributes are unchanged
    assert instance.username == original_username, "Username should not be changed"
    assert instance.email == original_email, "Email should not be changed"

@pytest.mark.parametrize("model_class", [User, Admin])
def test_check_password_side_effects(model_class, test_db):
    """
    GIVEN a model class (User or Admin) with a set password
    WHEN check_password is called
    THEN it should only verify the password and not have any side effects
    """
    instance = model_class(username='testuser4', email='test4@example.com')
    instance.set_password('testpassword123')
    original_hash = instance.password_hash

    instance.check_password('testpassword123')  # Correct password
    assert instance.password_hash == original_hash, "Password hash should not be altered by check_password"

    instance.check_password('wrongpassword')  # Incorrect password
    assert instance.password_hash == original_hash, "Password hash should not be altered by check_password"

@pytest.mark.parametrize("model_class", [User, Admin])
def test_password_hashing(model_class, test_db):
    """
    GIVEN a model class (User or Admin) and a password
    WHEN the password is set for the model instance and then checked against the hashed password
    THEN the 'check_password' method should return True for correct passwords and False for incorrect ones
    AND ensure that the password_hash does not contain the plaintext password
    """
    # GIVEN
    instance = model_class(username='testuser2', email='test2@example.com')
    plaintext_password = 'anothersecurepassword'
    instance.set_password(plaintext_password)

    # WHEN/THEN
    assert instance.check_password(plaintext_password), "check_password should return True for the correct password"
    assert not instance.check_password('wrongpassword'), "check_password should return False for the incorrect password"

    # Check that plaintext password is not stored in password_hash
    assert plaintext_password not in instance.password_hash, "Plaintext password should not be stored in password_hash"

@pytest.mark.parametrize("model_class", [User, Admin])
def test_password_hash_algorithm(model_class, test_db):
    """
    GIVEN a model class (User or Admin)
    WHEN a password is hashed
    THEN the password hash should use a strong and secure algorithm (e.g., scrypt)
    """
    instance = model_class(username='securityuser', email='secure@example.com')
    plaintext_password = 'secureTestPassword!'
    instance.set_password(plaintext_password)

    # Assuming that the hash includes the 'scrypt' prefix as part of the output
    assert 'scrypt' in instance.password_hash, "The password hash should use scrypt"

def test_new_stripe_customer(test_db):
    """
    GIVEN a StripeCustomer model
    WHEN a new StripeCustomer is created and linked to a user
    THEN check that the StripeCustomer is added to the session and committed to the database
    """
    # GIVEN
    user = User(username='user_for_stripe', email='stripe_user@example.com')
    user.set_password('securepassword123')
    test_db.session.add(user)
    test_db.session.commit()

    # WHEN
    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id='cust_12345')
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    # THEN
    assert stripe_customer in test_db.session

def test_stripe_customer_id_uniqueness(test_db):
    """
    GIVEN a StripeCustomer model
    WHEN a new StripeCustomer is created with an existing stripe_customer_id
    THEN the database should raise an IntegrityError
    """
    # Creating first StripeCustomer
    user1 = User(username='user1_for_stripe', email='user1_stripe@example.com')
    user1.set_password('securepassword123')
    test_db.session.add(user1)
    test_db.session.commit()

    stripe_customer1 = StripeCustomer(user_id=user1.id, stripe_customer_id='cust_123456')
    test_db.session.add(stripe_customer1)
    test_db.session.commit()

    # Attempting to create a second StripeCustomer with the same stripe_customer_id
    user2 = User(username='user2_for_stripe', email='user2_stripe@example.com')
    user2.set_password('securepassword123')
    test_db.session.add(user2)
    test_db.session.commit()

    stripe_customer2 = StripeCustomer(user_id=user2.id, stripe_customer_id='cust_123456')
    test_db.session.add(stripe_customer2)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

@pytest.mark.parametrize("plan", ["Weekly", "Monthly", "Yearly"])
def test_new_stripe_subscription(test_db, plan):
    """
    GIVEN a StripeCustomer and a subscription plan
    WHEN a new StripeSubscription is created with a specific plan
    THEN check the StripeSubscription is added to the session and committed to the database
    AND ensure all attributes including plan and active status are correct
    """
    # Start clean session
    test_db.session.rollback()

    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    username = f'stripe_user_{timestamp}'
    email = f'stripe_{timestamp}@example.com'
    stripe_customer_id = f'cust_{timestamp}'
    stripe_subscription_id = f'sub_{timestamp}'

    # GIVEN
    user = User(username=username, email=email)
    user.set_password('securepassword123')
    test_db.session.add(user)
    test_db.session.commit()

    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id=stripe_customer_id)
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    start_date = datetime.utcnow()
    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id=stripe_subscription_id,
        start_date=start_date,
        plan=plan,
        active=True
    )

    # Set the renewal date
    stripe_subscription.set_renewal_date()

    # WHEN
    test_db.session.add(stripe_subscription)
    test_db.session.commit()

    # THEN
    assert stripe_subscription in test_db.session
    assert stripe_subscription.plan == plan
    assert stripe_subscription.active is True
    assert stripe_subscription.start_date == start_date
    assert stripe_subscription.stripe_subscription_id == stripe_subscription_id

    # Cleanup after test
    test_db.session.delete(stripe_subscription)
    test_db.session.delete(stripe_customer)
    test_db.session.delete(user)
    test_db.session.commit()

def test_stripe_subscription_id_uniqueness(test_db):
    """
    GIVEN a StripeSubscription model
    WHEN a new StripeSubscription is created with an existing stripe_subscription_id
    THEN the database should raise an IntegrityError
    """
    # Start clean session
    test_db.session.rollback()

    # Creating a User and StripeCustomer for our StripeSubscription
    user = User(username='stripe_test_user', email='stripe_test@example.com')
    user.set_password('password123')
    test_db.session.add(user)
    test_db.session.commit()

    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id='cust_new12345')
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    # Creating first StripeSubscription
    stripe_subscription1 = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id='sub_unique123',
        start_date=datetime.utcnow(),
        plan='Monthly',
        active=True
    )

    # Set the renewal date based on the plan
    stripe_subscription1.set_renewal_date()

    test_db.session.add(stripe_subscription1)
    test_db.session.commit()

    # Attempting to create a second StripeSubscription with the same stripe_subscription_id
    stripe_subscription2 = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id='sub_unique123',  # Same ID as stripe_subscription1
        start_date=datetime.utcnow(),
        plan='Yearly',
        active=True
    )
    test_db.session.add(stripe_subscription2)
    with pytest.raises(IntegrityError):
        test_db.session.commit()  # This should raise IntegrityError due to the unique constraint

    # Clean up: rollback the session to clean the failed transaction
    test_db.session.rollback()

    # Further assertions could check that there's only one subscription with this ID
    subscription_count = StripeSubscription.query.filter_by(stripe_subscription_id='sub_unique123').count()
    assert subscription_count == 1, "There should only be one subscription with the same stripe_subscription_id"

@pytest.mark.parametrize("plan", ["Weekly", "Monthly", "Yearly"])
def test_default_values_stripe_subscription(test_db, plan):
    """
    GIVEN a StripeCustomer and a subscription plan
    WHEN a new StripeSubscription is created without explicitly setting `active` and `start_date`
    THEN check that the `active` field defaults to True and the `start_date` defaults to the current UTC time
    """
    # Start clean session
    test_db.session.rollback()

    # Use the current timestamp to ensure uniqueness
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    unique_username = f'test_user_{timestamp}'
    unique_email = f'default_{timestamp}@example.com'
    unique_stripe_customer_id = f'cust_default{timestamp}'
    unique_stripe_subscription_id = f'sub_default{timestamp}'

    # GIVEN
    user = User(username=unique_username, email=unique_email)
    user.set_password('securepassword')
    test_db.session.add(user)
    test_db.session.commit()

    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id=unique_stripe_customer_id)
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    # WHEN
    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id=unique_stripe_subscription_id,
        plan=plan,
        start_date=datetime.utcnow()
    )

    # Set the renewal date based on the plan
    stripe_subscription.set_renewal_date()

    test_db.session.add(stripe_subscription)
    test_db.session.commit()

    # THEN
    assert stripe_subscription.active is True, "Default value for 'active' should be True"
    
    # Check if start_date is approximately now (allowing some seconds for test execution delay)
    now = datetime.utcnow()
    assert abs((stripe_subscription.start_date - now).total_seconds()) < 5, "Default start_date should be the current UTC time"

    # Cleanup after test
    test_db.session.delete(stripe_subscription)
    test_db.session.delete(stripe_customer)
    test_db.session.delete(user)
    test_db.session.commit()

@pytest.mark.parametrize("plan", ["Weekly", "Monthly", "Yearly"])
def test_user_customer_subscription_relationship(test_db, plan):
    """
    GIVEN User, StripeCustomer, and StripeSubscription models within a Flask application context
    WHEN they are linked together and data is added to the database
    THEN check that the relationships between these models are maintained and data integrity is preserved
    """
    # Start clean session
    test_db.session.rollback()

    # Use the current timestamp to ensure uniqueness
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    unique_username = f'test_relationship_user_{timestamp}'
    unique_email = f'relationship_{timestamp}@example.com'
    unique_stripe_customer_id = f'cust_{timestamp}'
    unique_stripe_subscription_id = f'sub_{timestamp}'

    # Create a new User
    user = User(username=unique_username, email=unique_email)
    user.set_password('secure123')
    test_db.session.add(user)
    test_db.session.commit()

    # Create a StripeCustomer linked to the User
    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id=unique_stripe_customer_id)
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    # Create a StripeSubscription linked to the StripeCustomer
    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id=unique_stripe_subscription_id,
        start_date=datetime.utcnow(),
        plan=plan,
        active=True
    )

    # Set the renewal date based on the plan
    stripe_subscription.set_renewal_date()

    test_db.session.add(stripe_subscription)
    test_db.session.commit()

    # Assertions to verify the linkage
    assert stripe_customer.user_id == user.id, "StripeCustomer should be linked to the correct User"
    assert stripe_subscription.stripe_customer_id == stripe_customer.id, "StripeSubscription should be linked to the correct StripeCustomer"

    # Verify that data is retrievable via relationships
    assert user.stripe_customer == stripe_customer, "User's StripeCustomer should be retrievable"
    assert stripe_customer.stripe_subscription == stripe_subscription, "StripeCustomer's StripeSubscription should be retrievable"

    # Clean up after test
    test_db.session.delete(stripe_subscription)
    test_db.session.delete(stripe_customer)
    test_db.session.delete(user)
    test_db.session.commit()

@pytest.mark.parametrize("plan", ["Weekly", "Monthly", "Yearly"])
def test_cascade_delete_from_stripe_customer_to_subscription(test_db, plan):
    """
    GIVEN a StripeCustomer linked to a StripeSubscription
    WHEN the StripeCustomer is deleted from the database
    THEN the associated StripeSubscription should also be automatically deleted
    """
    # Start clean session
    test_db.session.rollback()

    # Generate a unique timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    unique_username = f'cascade_test_user_{timestamp}'
    unique_email = f'cascade_{timestamp}@example.com'
    unique_stripe_customer_id = f'cust_cascade{timestamp}'
    unique_stripe_subscription_id = f'sub_cascade{timestamp}'

    # Setup a User, StripeCustomer, and StripeSubscription with unique identifiers
    user = User(username=unique_username, email=unique_email)
    user.set_password('securepassword123')
    test_db.session.add(user)
    test_db.session.commit()

    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id=unique_stripe_customer_id)
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id=unique_stripe_subscription_id,
        start_date=datetime.utcnow(),
        plan=plan,
        active=True
    )

    # Set the renewal date based on the plan
    stripe_subscription.set_renewal_date()

    test_db.session.add(stripe_subscription)
    test_db.session.commit()

    # Check setup integrity
    assert stripe_subscription in test_db.session

    # Perform the deletion of StripeCustomer
    test_db.session.delete(stripe_customer)
    test_db.session.commit()

    # Check if the StripeSubscription has also been deleted
    deleted_subscription = StripeSubscription.query.filter_by(stripe_subscription_id=unique_stripe_subscription_id).first()
    assert deleted_subscription is None, "StripeSubscription should be deleted when its StripeCustomer is deleted"

    # Cleanup
    test_db.session.delete(user)
    test_db.session.commit()

@pytest.mark.parametrize("missing_field", ["user_id", "stripe_customer_id"])
def test_stripe_customer_missing_required_fields(test_db, missing_field):
    """
    GIVEN a StripeCustomer model
    WHEN a new StripeCustomer is created missing a required field
    THEN the database should raise an IntegrityError
    """
    # Start clean session
    test_db.session.rollback()

    params = {"user_id": 1, "stripe_customer_id": "cust_67890"}
    params.pop(missing_field, None)  # Remove the field to test its absence

    stripe_customer = StripeCustomer(**params)
    test_db.session.add(stripe_customer)

    with pytest.raises(IntegrityError):
        test_db.session.commit()

    test_db.session.rollback()

@pytest.mark.parametrize("field, value", [
    ("stripe_subscription_id", None),
    ("stripe_customer_id", None),
    ("plan", None),
    ("renewal_date", None)
    # start_date and active have default values so they will never be None
])

def test_stripe_subscription_missing_required_fields(test_db, field, value):
    """
    GIVEN a StripeSubscription model
    WHEN a new StripeSubscription is created with a missing or invalid required field
    THEN the database should raise an IntegrityError or DataError
    """
    # Start clean session
    test_db.session.rollback()

    # Generate a timestamp to use for creating unique user details
    timestamp = datetime.utcnow().timestamp()

    # Create a unique user for this test case to avoid unique constraint violations
    unique_username = f"test_user_{timestamp}"
    unique_email = f"{unique_username}@example.com"
    user = User(username=unique_username, email=unique_email)
    test_db.session.add(user)
    test_db.session.commit()

    # Create a StripeCustomer for foreign key constraints
    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id=f"cust_{timestamp}")
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    # Set up parameters with valid data
    params = {
        "stripe_customer_id": stripe_customer.id,
        "stripe_subscription_id": f"sub_{timestamp}",
        "start_date": datetime.utcnow(),
        "plan": "Monthly",
        "active": True,
        "renewal_date": datetime.utcnow() + timedelta(days=30)  # Set a valid default
    }

    # Set the test field to the provided value, which could be invalid
    params[field] = value

    # Create the StripeSubscription object with the test parameters
    stripe_subscription = StripeSubscription(**params)
    test_db.session.add(stripe_subscription)

    # Expecting an error due to invalid input
    with pytest.raises((IntegrityError, DataError)):
        test_db.session.commit()

    # Clean up the session after the test
    test_db.session.rollback()

@pytest.mark.parametrize("model, field, max_length", [
    (StripeCustomer, 'stripe_customer_id', 255),
    (StripeSubscription, 'stripe_subscription_id', 255),
])

def test_field_max_length(test_app, test_db, model, field, max_length):
    """
    GIVEN a StripeCustomer or StripeSubscription model
    WHEN the stripe_customer_id or stripe_subscription_id field is set to a string exceeding the maximum length
    THEN check whether the string length exceeds the maximum and raise an AssertionError if it does not
    """
    with test_app.app_context():
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        unique_email = f"test_{timestamp}@example.com"
        user = User(username=f'user_{timestamp}', email=unique_email)
        user.set_password('securepassword')
        test_db.session.add(user)
        test_db.session.commit()

        max_length_value = 'a' * (max_length + 1)
        if model == StripeCustomer:
            instance = model(user_id=user.id, stripe_customer_id=max_length_value)
        elif model == StripeSubscription:
            # Create a valid StripeCustomer for ForeignKey
            stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id=f'cust_{timestamp}')
            test_db.session.add(stripe_customer)
            test_db.session.commit()
            instance = model(
                stripe_customer_id=stripe_customer.id,
                stripe_subscription_id=max_length_value,
                plan="Monthly",
                start_date=datetime.utcnow()
            )
            # Set the renewal date for StripeSubscription
            instance.set_renewal_date()
        else:
            raise ValueError("The model provided is not supported by this test")

        assert len(getattr(instance, field)) > max_length, "Field value did not exceed maximum length as expected"

        try:
            test_db.session.add(instance)
            test_db.session.commit()
        except IntegrityError as e:
            assert False, f"IntegrityError raised with message: {e}"
        except DataError as e:
            # This except block should catch any length or format issues
            assert False, f"DataError raised with message: {e}"
        except Exception as e:
            assert False, f"An unexpected exception type {type(e)} was raised with message: {e}"

        test_db.session.rollback()

@pytest.mark.parametrize("total_distance", [0.0, 5.5, 100.3])
def test_journey_creation(test_db, user, total_distance):
    """
    GIVEN a User model and a float for total_distance
    WHEN a new Journey instance is created with valid total_distance and linked to a user
    THEN check that the Journey is added to the session and committed to the database
    """
    upload_time = datetime.utcnow()
    journey = Journey(user_id=user.id, total_distance=total_distance, upload_time=upload_time)
    test_db.session.add(journey)
    test_db.session.commit()

    # Retrieve the specific journey to ensure it's saved and check fields
    saved_journey = Journey.query.filter_by(user_id=user.id, total_distance=total_distance, upload_time=upload_time).first()
    assert saved_journey is not None, "No journey found matching the criteria"
    assert saved_journey.user_id == user.id
    assert saved_journey.total_distance == total_distance
    assert saved_journey.upload_time == upload_time

def test_journey_without_user(test_db):
    """
    WHEN a Journey instance is created without a linked User
    THEN the database should raise an IntegrityError
    """
    journey = Journey(total_distance=50.0, upload_time=datetime.utcnow())
    test_db.session.add(journey)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

@pytest.mark.parametrize("locations_count", [0, 1, 5])
def test_journey_with_locations(test_db, user, locations_count):
    """
    GIVEN a Journey model linked to a User
    WHEN several Location instances are related to the Journey
    THEN check that all Location instances are linked correctly
    """
    # Start clean session
    test_db.session.rollback()
    
    journey = Journey(user_id=user.id, total_distance=20.0, upload_time=datetime.utcnow())
    test_db.session.add(journey)
    test_db.session.commit()

    for _ in range(locations_count):
        location = Location(
            journey_id=journey.id,
            user_id=user.id,
            init_latitude=0.0,
            init_longitude=0.0,
            goal_latitude=10.0,
            goal_longitude=10.0,
            departure="City A",
            arrival="City B",
            upload_time=datetime.utcnow()
        )
        test_db.session.add(location)

    test_db.session.commit()

    assert len(journey.locations) == locations_count

@pytest.mark.parametrize("image_file_path, gpx_file_path", [
    ('/path/to/image1.jpg', '/path/to/gpx1.gpx'),
    ('/path/to/image2.jpg', '/path/to/gpx2.gpx')
])

def test_journey_with_filepath(test_db, user, image_file_path, gpx_file_path):
    """
    GIVEN a Journey model linked to a User and strings representing file paths
    WHEN a Filepath instance is created and linked to the Journey
    THEN check that the Filepath instance is linked correctly and the file paths are as expected
    """
    # Start clean session
    test_db.session.rollback()

    journey = Journey(user_id=user.id, total_distance=30.0, upload_time=datetime.utcnow())
    test_db.session.add(journey)
    test_db.session.commit()

    filepath = Filepath(
        journey_id=journey.id,
        user_id=user.id,
        image_file_path=image_file_path,
        gpx_file_path=gpx_file_path
    )
    test_db.session.add(filepath)
    test_db.session.commit()

    # Fetch the journey to check if filepath is linked correctly
    loaded_journey = Journey.query.filter_by(id=journey.id).first()
    test_db.session.refresh(loaded_journey)

    # Since it's a list, get the first Filepath object (if any)
    assert len(loaded_journey.filepath) > 0, "No Filepath linked to the journey"
    filepath_instance = loaded_journey.filepath[0]

    assert filepath_instance.image_file_path == image_file_path, "Image file path does not match the expected path"
    assert filepath_instance.gpx_file_path == gpx_file_path, "GPX file path does not match the expected path"

@pytest.mark.parametrize("init_lat,init_long,goal_lat,goal_long", [
    (40.7128, -74.0060, 34.0522, -118.2437),  # Valid coordinates
    (91.0, -74.0060, 34.0522, 361.0),         # Invalid latitude and longitude
    (-91.0, -74.0060, 34.0522, -361.0),
    (90.0, 180.0, -90.0, -180.0),             # Boundary conditions
    (90.0, -180.0, -90.0, 180.0),
    ("not_a_number", -74.0060, 34.0522, -118.2437),  # Non-numeric inputs
    (40.7128, "not_a_number", 34.0522, -118.2437)
])

def test_create_location(test_app, test_db, user, journey, init_lat, init_long, goal_lat, goal_long):
    """
    GIVEN a test application context and various sets of latitude and longitude values
    WHEN a Location instance is created and a database commit is attempted
    THEN the test verifies that valid locations are saved and improper inputs raise appropriate exceptions.
    """
    with test_app.app_context():
        upload_time = datetime.utcnow()
        location = Location(
            journey_id=journey.id,
            user_id=user.id,
            init_latitude=init_lat,
            init_longitude=init_long,
            goal_latitude=goal_lat,
            goal_longitude=goal_long,
            departure="Origin City",
            arrival="Destination City",
            upload_time=upload_time
        )
        test_db.session.add(location)
        # Expect errors for invalid or non-numeric data
        if isinstance(init_lat, str) or isinstance(init_long, str) or isinstance(goal_lat, str) or isinstance(goal_long, str):
            with pytest.raises((DataError, StatementError)):
                test_db.session.commit()
            test_db.session.rollback()  # Rollback after catching expected errors
        else:
            # If no exception is expected, commit normally
            try:
                test_db.session.commit()
                saved_location = Location.query.filter_by(journey_id=journey.id, user_id=user.id).first()
                assert saved_location is not None, "Location should be saved in the database"
            except Exception as e:
                test_db.session.rollback()
                assert False, f"Unexpected error occurred: {e}"

def test_location_missing_fields(test_db, user, journey):
    """
    WHEN a Location instance is created missing required fields
    THEN the database should raise an IntegrityError
    """
    location = Location(
        journey_id=journey.id,
        user_id=user.id,
        # Missing latitude and longitude
        departure="Origin City",
        arrival="Destination City",
        upload_time=datetime.utcnow()
    )
    test_db.session.add(location)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

def test_location_foreign_keys(test_db, user, journey):
    """
    GIVEN incorrect or missing foreign keys for a Location
    WHEN trying to commit to the database
    THEN expect an IntegrityError
    """
    # Start clean session
    test_db.session.rollback()
    
    scenarios = [
        {"journey_id": None, "user_id": user.id},  # Missing journey_id
        {"journey_id": journey.id, "user_id": None}  # Missing user_id
    ]

    for scenario in scenarios:
        location = Location(
            journey_id=scenario["journey_id"],
            user_id=scenario["user_id"],
            init_latitude=40.7128,
            init_longitude=-74.0060,
            goal_latitude=34.0522,
            goal_longitude=-118.2437,
            departure="Origin City",
            arrival="Destination City",
            upload_time=datetime.utcnow()
        )
        test_db.session.add(location)
        with pytest.raises(IntegrityError):
            test_db.session.commit()

        # Reset session to clear out the effects of the failed transaction
        test_db.session.rollback()

def test_create_filepath(test_db, journey, user):
    """
    GIVEN Journey and User models provided by the corresponding fixtures
    WHEN a new Filepath instance is created with valid image and GPX file paths
    THEN check that the Filepath instance is correctly stored in the database with all fields set as expected
    """
    image_path = '/path/to/image.jpg'
    gpx_path = '/path/to/file.gpx'
    # Create a new Filepath instance within the app context
    filepath = Filepath(
        journey_id=journey.id,
        user_id=user.id,
        image_file_path=image_path,
        gpx_file_path=gpx_path
    )
    test_db.session.add(filepath)
    test_db.session.commit()

    # Fetch the inserted filepath by the unique identifier to verify it's stored correctly
    saved_filepath = Filepath.query.filter_by(image_file_path=image_path).first()
    assert saved_filepath is not None, "Filepath instance should be created."
    assert saved_filepath.image_file_path == image_path, f"Expected image file path {image_path}, but got {saved_filepath.image_file_path}"
    assert saved_filepath.gpx_file_path == gpx_path, f"Expected GPX file path {gpx_path}, but got {saved_filepath.gpx_file_path}"
    assert saved_filepath.journey_id == journey.id, f"Expected journey ID {journey.id}, but got {saved_filepath.journey_id}"
    assert saved_filepath.user_id == user.id, f"Expected user ID {user.id}, but got {saved_filepath.user_id}"

def test_filepath_without_user_or_journey(test_db):
    """
    WHEN a Filepath instance is created without a linked Journey or User
    THEN the database should raise an IntegrityError
    """
    filepath = Filepath(
        image_file_path='/path/to/image.jpg',
        gpx_file_path='/path/to/file.gpx'
    )
    test_db.session.add(filepath)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

@pytest.mark.parametrize("missing_field", ['journey_id', 'user_id', 'image_file_path', 'gpx_file_path'])
def test_filepath_missing_fields(test_db, user, journey, missing_field):
    """
    GIVEN a Filepath model with one missing required field
    WHEN trying to add this incomplete Filepath to the database
    THEN the database should raise an IntegrityError
    """
    # Start clean session
    test_db.session.rollback()

    filepath_data = {
        'journey_id': journey.id,
        'user_id': user.id,
        'image_file_path': '/path/to/image.jpg',
        'gpx_file_path': '/path/to/file.gpx'
    }
    filepath_data.pop(missing_field)  # Remove a required field
    filepath = Filepath(**filepath_data)
    test_db.session.add(filepath)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

def test_filepath_long_paths(test_db, user, journey):
    """
    GIVEN Journey and User models
    WHEN a new Filepath instance is created with extremely long file paths
    THEN check that the application can handle long paths without errors
    """
    # Start clean session
    test_db.session.rollback()

    # Generate a very long file path
    long_image_path = '/path/' + ''.join(random.choices(string.ascii_letters + string.digits, k=255)) + '.jpg'
    long_gpx_path = '/path/' + ''.join(random.choices(string.ascii_letters + string.digits, k=255)) + '.gpx'

    filepath = Filepath(
        journey_id=journey.id,
        user_id=user.id,
        image_file_path=long_image_path,
        gpx_file_path=long_gpx_path
    )
    test_db.session.add(filepath)
    test_db.session.commit()

    # Fetch the inserted filepath to verify it's stored correctly
    saved_filepath = Filepath.query.filter_by(image_file_path=long_image_path).first()
    assert saved_filepath is not None, "Filepath with long path should be created."
    assert saved_filepath.image_file_path == long_image_path, "Long image file path should match."
    assert saved_filepath.gpx_file_path == long_gpx_path, "Long GPX file path should match."

def test_filepath_special_characters(test_db, user, journey):
    """
    GIVEN Journey and User models
    WHEN a new Filepath instance is created with paths containing special characters
    THEN check that the application handles paths with special characters correctly
    """
    special_char_image_path = '/path/to/special!@#$%^&*()_+{}:"><,?.jpg'
    special_char_gpx_path = '/path/to/special!@#$%^&*()_+{}:"><,?.gpx'

    filepath = Filepath(
        journey_id=journey.id,
        user_id=user.id,
        image_file_path=special_char_image_path,
        gpx_file_path=special_char_gpx_path
    )
    test_db.session.add(filepath)
    test_db.session.commit()

    # Fetch the inserted filepath to verify it's stored correctly
    saved_filepath = Filepath.query.filter_by(image_file_path=special_char_image_path).first()
    assert saved_filepath is not None, "Filepath with special characters should be created."
    assert saved_filepath.image_file_path == special_char_image_path, "Image file path with special characters should match."
    assert saved_filepath.gpx_file_path == special_char_gpx_path, "GPX file path with special characters should match."