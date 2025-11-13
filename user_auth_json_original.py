import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

USERS_FILE = 'users.json'

class User(UserMixin):
    def __init__(self, id, username, password_hash, role='demo'):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def get_user_by_username(username):
    """Get user by username"""
    users = load_users()
    if username in users:
        data = users[username]
        role = data.get('role')
        if not role and username == 'admin':
            role = 'admin'
        if not role:
            role = 'demo'
        return User(username, username, data['password_hash'], role)
    return None

def get_user_by_id(user_id):
    """Get user by ID (username is used as ID)"""
    return get_user_by_username(user_id)

def create_user(username, password, role='demo'):
    """Create a new user with role"""
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        'username': username,
        'password_hash': generate_password_hash(password),
        'role': role
    }
    save_users(users)
    return True, "User created successfully"

def authenticate_user(username, password):
    """Authenticate user with username and password"""
    users = load_users()
    if username not in users:
        return None
    
    if check_password_hash(users[username]['password_hash'], password):
        data = users[username]
        role = data.get('role')
        if not role and username == 'admin':
            role = 'admin'
        if not role:
            role = 'demo'
        return User(username, username, data['password_hash'], role)
    return None

def change_password(username, new_password):
    """Change user password"""
    users = load_users()
    if username not in users:
        return False, "User not found"
    
    users[username]['password_hash'] = generate_password_hash(new_password)
    save_users(users)
    return True, "Password changed successfully"

def change_role(username, new_role):
    """Change user role"""
    users = load_users()
    if username not in users:
        return False, "User not found"
    users[username]['role'] = new_role
    save_users(users)
    return True, "Role updated successfully"

def list_users():
    """List all users as dict {username: {password_hash, role}}"""
    return load_users()

def initialize_default_user():
    """Create default admin user if no users exist"""
    users = load_users()
    if not users:
        create_user('admin', 'admin123', role='admin')
        print("Default admin user created: username='admin', password='admin123' (role=admin)")
        print("PLEASE CHANGE THE DEFAULT PASSWORD AFTER FIRST LOGIN!")


def delete_user(username):
    """Delete a user"""
    users = load_users()
    if username not in users:
        return False, "User not found"
    
    if username == 'admin':
        return False, "Cannot delete admin user"
    
    del users[username]
    save_users(users)
    return True, f"User '{username}' deleted successfully"

def change_user_password(username, new_password):
    """Change user password by admin"""
    users = load_users()
    if username not in users:
        return False, "User not found"
    
    if len(new_password) < 4:
        return False, "Password must be at least 4 characters"
    
    users[username]['password_hash'] = generate_password_hash(new_password)
    save_users(users)
    return True, f"Password for '{username}' changed successfully"
