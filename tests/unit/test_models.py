import pytest
from app.models import User
from sqlalchemy.exc import IntegrityError

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