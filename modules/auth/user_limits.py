"""
User Limits Management
Functions to manage and check per-user limits (streams, storage)
"""

import os
from modules.database.database import get_db_connection

def get_user_limits(user_id: int) -> dict:
    """Get user limits and current usage"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute('''
            SELECT username, is_admin, max_streams, max_storage_mb 
            FROM users WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        user_info = dict(row)
        
        # If admin, return unlimited
        if user_info['is_admin']:
            return {
                'user_id': user_id,
                'username': user_info['username'],
                'is_admin': True,
                'max_streams': None,  # Unlimited
                'max_storage_mb': None,  # Unlimited
                'current_streams': 0,
                'current_storage_mb': 0,
                'streams_remaining': float('inf'),
                'storage_remaining_mb': float('inf'),
                'can_add_stream': True,
                'can_upload': True
            }
        
        # Count current streams (live_streams + schedules)
        cursor.execute('''
            SELECT COUNT(*) as count FROM live_streams WHERE user_id = ?
        ''', (user_id,))
        live_count = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM schedules WHERE user_id = ?
        ''', (user_id,))
        schedule_count = cursor.fetchone()['count']
        
        current_streams = live_count + schedule_count
        
        # Calculate storage usage
        current_storage_mb = calculate_user_storage(user_id)
        
        # Calculate remaining
        max_streams = user_info['max_streams'] or 0
        max_storage = user_info['max_storage_mb'] or 0
        
        streams_remaining = max_streams - current_streams
        storage_remaining = max_storage - current_storage_mb
        
        return {
            'user_id': user_id,
            'username': user_info['username'],
            'is_admin': False,
            'max_streams': max_streams,
            'max_storage_mb': max_storage,
            'current_streams': current_streams,
            'current_storage_mb': round(current_storage_mb, 2),
            'streams_remaining': streams_remaining,
            'storage_remaining_mb': round(storage_remaining, 2),
            'can_add_stream': streams_remaining > 0,
            'can_upload': storage_remaining > 0
        }

def calculate_user_storage(user_id: int) -> float:
    """Calculate total storage used by user in MB"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all video files
        cursor.execute('''
            SELECT filename FROM videos WHERE user_id = ?
        ''', (user_id,))
        
        video_files = cursor.fetchall()
        
        # Get all looped video files
        cursor.execute('''
            SELECT output_filename FROM looped_videos 
            WHERE user_id = ? AND status = 'completed'
        ''', (user_id,))
        
        looped_files = cursor.fetchall()
        
        # Get all thumbnails
        cursor.execute('''
            SELECT filename FROM thumbnails WHERE user_id = ?
        ''', (user_id,))
        
        thumbnail_files = cursor.fetchall()
    
    # Calculate total size
    total_bytes = 0
    video_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
    thumbnail_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thumbnails')
    looped_folder = os.path.join(video_folder, 'done')
    
    # Video files
    for row in video_files:
        filepath = os.path.join(video_folder, row['filename'])
        if os.path.exists(filepath):
            total_bytes += os.path.getsize(filepath)
    
    # Looped video files
    for row in looped_files:
        if row['output_filename']:
            filepath = os.path.join(looped_folder, row['output_filename'])
            if os.path.exists(filepath):
                total_bytes += os.path.getsize(filepath)
    
    # Thumbnail files
    for row in thumbnail_files:
        filepath = os.path.join(thumbnail_folder, row['filename'])
        if os.path.exists(filepath):
            total_bytes += os.path.getsize(filepath)
    
    # Convert to MB
    return total_bytes / (1024 * 1024)

def can_user_add_stream(user_id: int) -> tuple:
    """Check if user can add more streams. Returns (bool, message)"""
    limits = get_user_limits(user_id)
    
    if limits is None:
        return False, "User not found"
    
    if limits['is_admin']:
        return True, "Admin has unlimited streams"
    
    if limits['can_add_stream']:
        return True, f"Can add {limits['streams_remaining']} more streams"
    else:
        return False, f"Stream limit reached ({limits['max_streams']} max)"

def can_user_upload(user_id: int, file_size_mb: float = 0) -> tuple:
    """Check if user can upload file. Returns (bool, message)"""
    limits = get_user_limits(user_id)
    
    if limits is None:
        return False, "User not found"
    
    if limits['is_admin']:
        return True, "Admin has unlimited storage"
    
    if limits['storage_remaining_mb'] >= file_size_mb:
        remaining = limits['storage_remaining_mb'] - file_size_mb
        return True, f"{remaining:.2f}MB will remain after upload"
    else:
        return False, f"Storage limit exceeded. Only {limits['storage_remaining_mb']:.2f}MB available"

def update_user_limits(user_id: int, max_streams: int = None, max_storage_mb: int = None) -> bool:
    """Update user limits (admin only function)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user is admin (can't change admin limits)
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row and row['is_admin']:
            return False  # Can't change admin limits
        
        # Update limits
        cursor.execute('''
            UPDATE users 
            SET max_streams = ?, max_storage_mb = ?
            WHERE id = ?
        ''', (max_streams, max_storage_mb, user_id))
        
        return cursor.rowcount > 0

def get_all_users_with_limits() -> list:
    """Get all users with their limits and usage"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, is_admin, max_streams, max_storage_mb 
            FROM users 
            ORDER BY is_admin DESC, username
        ''')
        
        users = []
        for row in cursor.fetchall():
            user_dict = dict(row)
            
            # Get usage for each user
            limits = get_user_limits(user_dict['id'])
            user_dict.update(limits)
            
            users.append(user_dict)
        
        return users

def format_storage(mb: float) -> str:
    """Format storage size for display"""
    if mb is None or mb == float('inf'):
        return "Unlimited"
    elif mb < 1:
        return f"{mb * 1024:.1f}KB"
    elif mb < 1024:
        return f"{mb:.1f}MB"
    else:
        return f"{mb / 1024:.2f}GB"

def format_count(count: int, limit: int) -> str:
    """Format count vs limit for display"""
    if limit is None or limit == float('inf'):
        return f"{count} (Unlimited)"
    return f"{count}/{limit}"
