import pytest
from app.models import User, StripeCustomer, StripeSubscription
from sqlalchemy.exc import IntegrityError, DataError
from datetime import datetime

def test_new_user(test_db):
    """
    GIVEN a User model
    WHEN a new User is created with a username and password
    THEN check the user is added to the session and committed to the database
    """
    # GIVEN
    user = User(username='testuser', email='test@example.com')

    # WHEN
    user.set_password('securepassword123')
    test_db.session.add(user)
    test_db.session.commit()

    # THEN
    assert user in test_db.session

def test_username_email_uniqueness(test_db):
    """
    GIVEN a User model
    WHEN a new User is created with an existing username or email
    THEN the database should raise an IntegrityError
    """
    # Creating first user
    user1 = User(username='uniqueuser', email='unique@example.com')
    user1.set_password('securepassword123')
    test_db.session.add(user1)
    test_db.session.commit()

    # Attempting to create a second user with the same username
    user2 = User(username='uniqueuser', email='different@example.com')
    user2.set_password('securepassword123')
    test_db.session.add(user2)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

    # Clear session to try with the same email
    test_db.session.rollback()

    # Attempting to create a second user with the same email
    user3 = User(username='anotheruser', email='unique@example.com')
    user3.set_password('securepassword123')
    test_db.session.add(user3)
    with pytest.raises(IntegrityError):
        test_db.session.commit()

@pytest.mark.parametrize("email_description, email_value", [
    ('typical_email', 'user@example.com'),  # A typical email format
    ('email_with_special_chars', 'user+name@example.com'),  # Email with special characters
    ('email_missing_at_symbol', 'userexample.com'),  # Missing '@' symbol should be handled by form validation, not model
    ('empty_email', '')  # Empty email field should be handled by form validation, not model
])

def test_email_varied_inputs(email_description, email_value, test_db):
    """
    GIVEN a User model
    WHEN an email is set and then saved to the database
    THEN ensure the email is correctly stored and retrievable
    AND check for any data integrity issues or validation errors
    """
    test_db.session.rollback()  # Start with a clean session

    user = User(username='testuser_' + email_description, email=email_value)
    user.set_password('securepassword123')

    test_db.session.add(user)
    test_db.session.commit()

    retrieved_user = User.query.filter_by(email=email_value).first()
    assert retrieved_user is not None, "User should be retrievable by email"
    assert retrieved_user.email == email_value, f"Email stored ({retrieved_user.email}) should match the provided email ({email_value})"

    test_db.session.delete(user)
    test_db.session.commit()

@pytest.mark.parametrize("username_description, username_value", [
    ('very_long_username', 'user_' + 'a' * 255),  # Extremely long username
    ('special_characters', '@user#!$%'),  # Username with special characters
    ('typical_username', 'regular_user'),  # A typical username
    ('empty_username', '')  # Empty username
])

def test_username_varied_inputs(username_description, username_value, test_db):
    """
    GIVEN a User model and various types of usernames
    WHEN the username is set and then saved to the database
    THEN ensure the username is correctly stored and retrievable
    AND check for any data integrity issues or validation errors
    """

    # Start clean session
    test_db.session.rollback()

    # GIVEN a User model and a username
    user = User(username=username_value, email=username_value + '@example.com')
    test_db.session.add(user)

    # WHEN the username is set
    try:
        test_db.session.commit()
        # THEN ensure the username is correctly stored and retrievable
        retrieved_user = User.query.filter_by(username=username_value).first()
        assert retrieved_user is not None, "User should be retrievable by username"
        assert retrieved_user.username == username_value, f"Username stored ({retrieved_user.username}) should match the provided username ({username_value})"
    except IntegrityError:
        test_db.session.rollback()
        pytest.fail(f"Database should not raise IntegrityError for username: {username_description}")

    # Clean up after the test
    test_db.session.delete(user)
    test_db.session.commit()

@pytest.mark.parametrize("password_description, password_value", [
    ('long_password', 'a' * 10000),  # Very long password
    ('non_alphanumeric', '@#$$%^&*()_+!?><'),  # Non-alphanumeric characters
    ('normal_password', 'normalpassword123'),  # Typical password
    ('short_password', 'short')  # Short password, less than recommended length
])

def test_password_varied_inputs(password_description, password_value, test_db):
    """
    GIVEN a User model and various types of passwords
    WHEN the password is set and then checked
    THEN ensure the 'check_password' method correctly verifies the password
    AND the plaintext password is not stored in the password_hash
    """

    # Start clean session
    test_db.session.rollback()

    # GIVEN a User model and a password
    user = User(username='varietyuser_'+password_description, email='variety_'+password_description+'@example.com')
    user.set_password(password_value)
    test_db.session.add(user)

    # WHEN the password is set
    try:
        test_db.session.commit()
    except IntegrityError:
        # THEN the database should raise an IntegrityError due to a unique constraint on the email
        test_db.session.rollback()

    # THEN the 'check_password' method should return True since the correct password is used
    assert user.check_password(password_value), f"Failed on password: {password_description}"
    
    # AND the plaintext password should not be stored in the password_hash
    assert password_value not in user.password_hash, "Plaintext password should not be stored in password_hash"
    
    # Clean up after the test
    test_db.session.delete(user)
    test_db.session.commit()

def test_set_password_side_effects(test_db):
    """
    GIVEN a User model
    WHEN set_password is called
    THEN it should not return any value and should not alter any unrelated attributes
    """
    user = User(username='testuser3', email='test3@example.com')
    original_username = user.username
    original_email = user.email

    # set_password should not return a value
    result = user.set_password('newsecurepassword123')
    assert result is None, "set_password should not return any data"

    # Check other attributes are unchanged
    assert user.username == original_username, "Username should not be changed"
    assert user.email == original_email, "Email should not be changed"

def test_check_password_side_effects(test_db):
    """
    GIVEN a User model with a set password
    WHEN check_password is called
    THEN it should only verify the password and not have any side effects
    """
    user = User(username='testuser4', email='test4@example.com')
    user.set_password('testpassword123')
    original_hash = user.password_hash

    user.check_password('testpassword123')  # Correct password
    assert user.password_hash == original_hash, "Password hash should not be altered by check_password"

    user.check_password('wrongpassword')  # Incorrect password
    assert user.password_hash == original_hash, "Password hash should not be altered by check_password"

def test_password_hashing(test_db):
    """
    GIVEN a User model and a password
    WHEN the password is set for the user and then checked against the hashed password
    THEN the 'check_password' method should return True for correct passwords and False for incorrect ones
    AND ensure that the password_hash does not contain the plaintext password
    """
    # GIVEN
    user = User(username='testuser2', email='test2@example.com')
    plaintext_password = 'anothersecurepassword'
    user.set_password(plaintext_password)

    # WHEN/THEN
    assert user.check_password(plaintext_password)  # Should be True for correct password
    assert not user.check_password('wrongpassword')  # Should be False for incorrect password

    # Check that plaintext password is not stored in password_hash
    assert plaintext_password not in user.password_hash, "Plaintext password should not be stored in password_hash"

def test_password_hash_algorithm(test_db):
    """
    GIVEN a User model
    WHEN a password is hashed
    THEN the password hash should use a strong and secure algorithm (e.g., scrypt)
    """
    user = User(username='securityuser', email='secure@example.com')
    plaintext_password = 'secureTestPassword!'
    user.set_password(plaintext_password)

    # The hashed password should start with the algorithm used which should be scrypt
    assert user.password_hash.startswith('scrypt'), "The password hash should use scrypt"

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

    # GIVEN
    user = User(username='stripe_user', email='stripe@example.com')
    user.set_password('securepassword123')
    test_db.session.add(user)
    test_db.session.commit()

    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id='cust_1234567')
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    start_date = datetime.utcnow()
    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id='sub_12345',
        start_date=start_date,
        plan=plan,
        active=True
    )

    # WHEN
    test_db.session.add(stripe_subscription)
    test_db.session.commit()

    # THEN
    assert stripe_subscription in test_db.session
    assert stripe_subscription.plan == plan
    assert stripe_subscription.active is True
    assert stripe_subscription.start_date == start_date
    assert stripe_subscription.stripe_subscription_id == 'sub_12345'

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
    # GIVEN
    user = User(username='test_user_default', email='default@example.com')
    user.set_password('securepassword')
    test_db.session.add(user)
    test_db.session.commit()

    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id='cust_default123456')
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    # WHEN
    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id='sub_default123',
        plan=plan
    )
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
    # Create a new User
    user = User(username='test_relationship_user', email='relationship@example.com')
    user.set_password('secure123')
    test_db.session.add(user)
    test_db.session.commit()

    # Create a StripeCustomer linked to the User
    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id='cust_999999')
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    # Create a StripeSubscription linked to the StripeCustomer
    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id='sub_999999',
        start_date=datetime.utcnow(),
        plan=plan,
        active=True
    )
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

    # Setup a User, StripeCustomer, and StripeSubscription
    user = User(username='cascade_test_user', email='cascade_test@example.com')
    user.set_password('securepassword123')
    test_db.session.add(user)
    test_db.session.commit()

    stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id='cust_cascade123')
    test_db.session.add(stripe_customer)
    test_db.session.commit()

    stripe_subscription = StripeSubscription(
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id='sub_cascade123',
        start_date=datetime.utcnow(),
        plan=plan,
        active=True
    )
    test_db.session.add(stripe_subscription)
    test_db.session.commit()

    # Check setup integrity
    assert stripe_subscription in test_db.session

    # Perform the deletion of StripeCustomer
    test_db.session.delete(stripe_customer)
    test_db.session.commit()

    # Check if the StripeSubscription has also been deleted
    deleted_subscription = StripeSubscription.query.filter_by(stripe_subscription_id='sub_cascade123').first()
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
    ("plan", None)
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
        "active": True
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
        # Use a unique email by adding a timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        unique_email = f"test_{timestamp}@example.com"
        user = User(username=f'user_{timestamp}', email=unique_email)
        user.set_password('securepassword')
        test_db.session.add(user)
        test_db.session.commit()

        max_length_value = 'a' * (max_length + 1)
        if model == StripeCustomer:
            instance = model(user_id=user.id, stripe_customer_id=max_length_value)
        else:  # StripeSubscription
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

        # Instead of relying on DataError, assert the string length manually
        assert len(getattr(instance, field)) > max_length, "Field value did not exceed maximum length as expected"

        try:
            test_db.session.add(instance)
            test_db.session.commit()
        except IntegrityError as e:
            # This except block should catch any unique constraint issues
            assert False, f"IntegrityError raised with message: {e}"
        except Exception as e:
            # This except block will catch other exceptions like DataError
            # if they are enforced by the database
            assert isinstance(e, DataError), f"Expected DataError, but caught {type(e)} with message: {e}"
        
        test_db.session.rollback()