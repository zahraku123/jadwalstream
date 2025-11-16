from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from modules.database.database import (
    get_user_by_username as db_get_user_by_username,
    get_user_by_id as db_get_user_by_id,
    create_user as db_create_user,
    update_user_role,
    update_user_password,
    update_user_status,
    delete_user as db_delete_user,
    list_all_users
)

class User(UserMixin):
    def __init__(self, id, username, password_hash, role='user', status='approved'):
        self.id = str(id)  # Flask-Login requires string ID
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.status = status

def get_user_by_username(username):
    """Get user by username"""
    user_data = db_get_user_by_username(username)
    if user_data:
        return User(
            user_data['id'],
            user_data['username'],
            user_data['password_hash'],
            user_data.get('role', 'user'),
            user_data.get('status', 'approved')
        )
    return None

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return None
    
    user_data = db_get_user_by_id(user_id_int)
    if user_data:
        return User(
            user_data['id'],
            user_data['username'],
            user_data['password_hash'],
            user_data.get('role', 'user'),
            user_data.get('status', 'approved')
        )
    return None

def create_user(username, password, role='user', status='approved', expiry_days=None, whatsapp=None):
    """Create a new user with role and status"""
    # Check if user already exists
    if get_user_by_username(username):
        return False, "Username already exists"

    try:
        password_hash = generate_password_hash(password)
        user_id = db_create_user(username, password_hash, role, status, expiry_days, whatsapp)
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

def authenticate_user(username, password):
    """Authenticate user with username and password"""
    user_data = db_get_user_by_username(username)
    if not user_data:
        return None
    
    # Check if user is approved
    if user_data.get('status', 'approved') != 'approved':
        return None  # User not approved yet
    
    if check_password_hash(user_data['password_hash'], password):
        return User(
            user_data['id'],
            user_data['username'],
            user_data['password_hash'],
            user_data.get('role', 'user'),
            user_data.get('status', 'approved')
        )
    return None

def change_password(username, new_password):
    """Change user password"""
    if not get_user_by_username(username):
        return False, "User not found"
    
    try:
        password_hash = generate_password_hash(new_password)
        if update_user_password(username, password_hash):
            return True, "Password changed successfully"
        return False, "Failed to update password"
    except Exception as e:
        return False, f"Error changing password: {str(e)}"

def change_role(username, new_role):
    """Change user role"""
    if not get_user_by_username(username):
        return False, "User not found"
    
    try:
        if update_user_role(username, new_role):
            return True, "Role updated successfully"
        return False, "Failed to update role"
    except Exception as e:
        return False, f"Error changing role: {str(e)}"

def list_users():
    """List all users as dict {username: {password_hash, role, status}}"""
    try:
        users_list = list_all_users()
        # Convert to old format for backward compatibility
        users_dict = {}
        for user in users_list:
            users_dict[user['username']] = {
                'username': user['username'],
                'role': user.get('role', 'demo'),
                'status': user.get('status', 'approved'),
                'password_hash': '[hidden]'  # Don't expose password hashes
            }
        return users_dict
    except Exception as e:
        print(f"Error listing users: {e}")
        return {}

def initialize_default_user():
    """Create default admin user if no users exist"""
    users_dict = list_users()
    if not users_dict:
        success, msg = create_user('admin', 'admin123', role='admin')
        if success:
            print("Default admin user created: username='admin', password='admin123' (role=admin)")
            print("PLEASE CHANGE THE DEFAULT PASSWORD AFTER FIRST LOGIN!")
        else:
            print(f"Failed to create default admin user: {msg}")
    
    # Create demo user if it doesn't exist (now with 'user' role)
    if 'demo' not in users_dict:
        create_user('demo', 'demo123', role='user')
        print("Default demo user created: username='demo', password='demo123' (role=user)")

def delete_user(username):
    """Delete a user"""
    if username == 'admin':
        return False, "Cannot delete admin user"
    
    user = get_user_by_username(username)
    if not user:
        return False, "User not found"
    
    try:
        if db_delete_user(username):
            return True, f"User '{username}' deleted successfully"
        return False, "Failed to delete user"
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"

def change_user_password(username, new_password):
    """Change user password by admin"""
    if not get_user_by_username(username):
        return False, "User not found"
    
    if len(new_password) < 4:
        return False, "Password must be at least 4 characters"
    
    try:
        password_hash = generate_password_hash(new_password)
        if update_user_password(username, password_hash):
            return True, f"Password for '{username}' changed successfully"
        return False, "Failed to update password"
    except Exception as e:
        return False, f"Error changing password: {str(e)}"

def approve_user(username):
    """Approve a pending user"""
    if not get_user_by_username(username):
        return False, "User not found"
    
    try:
        if update_user_status(username, 'approved'):
            return True, f"User '{username}' approved successfully"
        return False, "Failed to approve user"
    except Exception as e:
        return False, f"Error approving user: {str(e)}"

def reject_user(username):
    """Reject a pending user"""
    if not get_user_by_username(username):
        return False, "User not found"
    
    try:
        if update_user_status(username, 'rejected'):
            return True, f"User '{username}' rejected"
        return False, "Failed to reject user"
    except Exception as e:
        return False, f"Error rejecting user: {str(e)}"
