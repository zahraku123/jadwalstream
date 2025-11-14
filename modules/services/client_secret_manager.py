"""
Client Secret Manager
Helper functions to manage per-user YouTube API credentials
"""

import os
import json
from modules.database.database import get_db_connection

# Folder untuk store client secrets per user
CLIENT_SECRETS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets')

def get_user_client_secret_path(user_id: int) -> str:
    """Get client_secret path for user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT client_secret_path FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row and row['client_secret_path']:
            path = row['client_secret_path']
            # Return absolute path
            if os.path.isabs(path):
                return path
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        
        # Fallback to global client_secret.json if exists
        global_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secret.json')
        if os.path.exists(global_path):
            return global_path
        
        return None

def set_user_client_secret(user_id: int, file_content: bytes, filename: str = None) -> tuple:
    """
    Save client_secret for user
    Returns (success, message, filepath)
    """
    try:
        # Validate JSON
        try:
            data = json.loads(file_content)
            # Check if it's valid Google OAuth credentials
            if 'installed' not in data and 'web' not in data:
                return False, "Invalid client_secret format. Must be Google OAuth2 credentials.", None
        except json.JSONDecodeError:
            return False, "Invalid JSON file", None
        
        # Create folder if not exists
        os.makedirs(CLIENT_SECRETS_FOLDER, exist_ok=True)
        
        # Save file as client_secret_userID.json
        filename = f"client_secret_user{user_id}.json"
        filepath = os.path.join(CLIENT_SECRETS_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        # Update database
        relative_path = os.path.join('client_secrets', filename)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET client_secret_path = ? 
                WHERE id = ?
            ''', (relative_path, user_id))
        
        return True, f"Client secret uploaded successfully: {filename}", filepath
        
    except Exception as e:
        return False, f"Error saving client secret: {str(e)}", None

def has_client_secret(user_id: int) -> bool:
    """Check if user has client_secret configured"""
    path = get_user_client_secret_path(user_id)
    return path is not None and os.path.exists(path)

def get_client_secret_info(user_id: int) -> dict:
    """Get info about user's client_secret"""
    path = get_user_client_secret_path(user_id)
    
    if not path or not os.path.exists(path):
        return {
            'has_secret': False,
            'path': None,
            'filename': None,
            'is_global': False,
            'project_id': None
        }
    
    # Check if using global file
    is_global = 'client_secret.json' in path and 'client_secrets' not in path
    
    # Read project info
    project_id = None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if 'installed' in data:
                project_id = data['installed'].get('project_id', 'Unknown')
            elif 'web' in data:
                project_id = data['web'].get('project_id', 'Unknown')
    except:
        pass
    
    return {
        'has_secret': True,
        'path': path,
        'filename': os.path.basename(path),
        'is_global': is_global,
        'project_id': project_id
    }

def delete_user_client_secret(user_id: int) -> tuple:
    """Delete user's client_secret"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT client_secret_path FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row or not row['client_secret_path']:
                return False, "No client secret configured"
            
            path = row['client_secret_path']
            
            # Don't delete global client_secret.json
            if path == 'client_secret.json':
                return False, "Cannot delete global client secret"
            
            # Delete file
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
            if os.path.exists(full_path):
                os.remove(full_path)
            
            # Update database
            cursor.execute('UPDATE users SET client_secret_path = NULL WHERE id = ?', (user_id,))
            conn.commit()
            
            return True, "Client secret deleted successfully"
            
    except Exception as e:
        return False, f"Error deleting client secret: {str(e)}"

def get_user_tokens_folder(user_id: int) -> str:
    """Get tokens folder for user (for storing OAuth tokens)"""
    tokens_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tokens')
    user_folder = os.path.join(tokens_base, f'user_{user_id}')
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def list_user_tokens(user_id: int) -> list:
    """List all token files for user"""
    tokens_folder = get_user_tokens_folder(user_id)
    
    if not os.path.exists(tokens_folder):
        return []
    
    tokens = []
    for filename in os.listdir(tokens_folder):
        if filename.endswith('.json'):
            filepath = os.path.join(tokens_folder, filename)
            tokens.append({
                'filename': filename,
                'path': filepath,
                'size': os.path.getsize(filepath),
                'modified': os.path.getmtime(filepath)
            })
    
    return sorted(tokens, key=lambda x: x['modified'], reverse=True)
