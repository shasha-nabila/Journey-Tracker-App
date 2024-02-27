import re

def is_valid_password(password_hash):
    # Password must have at least 1 capital letter, 1 numeric, and be at least 8 characters long
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password_hash))
