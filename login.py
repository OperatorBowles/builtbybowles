import hashlib
import os

users = {}

def new_user():
    # Add a new user
    username = input('Please enter a username: ') # The users username
    password = input('Please enter your password: ') # The users password

    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    users[username] = { # Store the salt and key
        'salt': salt,
        'key': key
    }

def check_login():
    username = input('Please enter your username: ')
    password = input('Please enter your password: ')

    salt = users[username]['salt'] # Get the salt
    key = users[username]['key'] # Get the key
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

    if key == new_key:
        print('Passwords are the same')
    else:
        print('Passwords are not the same')

def main():
    new_user()
    check_login()

main()