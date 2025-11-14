"""
Admin User Limits Routes
Add these routes to app.py for user limits management
"""

from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from user_limits import (
    get_all_users_with_limits,
    update_user_limits,
    get_user_limits
)
from database import get_db_connection
import os

def require_admin(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        # Check if user is admin
        from database import get_user_by_id
        user_data = get_user_by_id(int(current_user.id))
        if not user_data or not user_data.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Add these routes to app.py:

@app.route('/admin/users/limits')
@login_required
@require_admin
def admin_user_limits():
    """Admin page to manage user limits"""
    users = get_all_users_with_limits()
    return render_template('admin_user_limits.html', users=users)

@app.route('/admin/users/update_limits', methods=['POST'])
@login_required
@require_admin
def admin_update_limits():
    """Update user limits"""
    user_id = int(request.form.get('user_id'))
    max_streams = int(request.form.get('max_streams', 0))
    max_storage_mb = int(request.form.get('max_storage_mb', 0))
    
    success = update_user_limits(user_id, max_streams, max_storage_mb)
    
    if success:
        flash(f'User limits updated successfully!', 'success')
    else:
        flash('Failed to update limits (cannot modify admin users)', 'error')
    
    return redirect(url_for('admin_user_limits'))

@app.route('/admin/users/reset_usage', methods=['POST'])
@login_required
@require_admin
def admin_reset_usage():
    """Reset user usage (delete all data)"""
    user_id = int(request.form.get('user_id'))
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if admin
            cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row and row['is_admin']:
                return jsonify({'success': False, 'message': 'Cannot reset admin user'})
            
            # Get files to delete
            cursor.execute('SELECT filename FROM videos WHERE user_id = ?', (user_id,))
            videos = cursor.fetchall()
            
            cursor.execute('SELECT filename FROM thumbnails WHERE user_id = ?', (user_id,))
            thumbnails = cursor.fetchall()
            
            cursor.execute('SELECT output_filename FROM looped_videos WHERE user_id = ? AND status = "completed"', (user_id,))
            looped = cursor.fetchall()
            
            # Delete files
            video_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
            thumbnail_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thumbnails')
            looped_folder = os.path.join(video_folder, 'done')
            
            for row in videos:
                filepath = os.path.join(video_folder, row['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            for row in thumbnails:
                filepath = os.path.join(thumbnail_folder, row['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            for row in looped:
                if row['output_filename']:
                    filepath = os.path.join(looped_folder, row['output_filename'])
                    if os.path.exists(filepath):
                        os.remove(filepath)
            
            # Delete database records (CASCADE will handle related records)
            cursor.execute('DELETE FROM videos WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM thumbnails WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM looped_videos WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM bulk_upload_queue WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM live_streams WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM schedules WHERE user_id = ?', (user_id,))
            
            conn.commit()
            
            return jsonify({'success': True, 'message': 'User data reset successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Example of how to check limits in existing routes:
"""
@app.route('/upload-video', methods=['POST'])
@login_required
def upload_video():
    user_id = int(current_user.id)
    
    # Check storage limit before upload
    from user_limits import can_user_upload, get_user_limits
    
    # Calculate upload size
    files = request.files.getlist('video_files')
    total_size_mb = sum(file.content_length for file in files if file) / (1024 * 1024)
    
    can_upload, message = can_user_upload(user_id, total_size_mb)
    if not can_upload:
        flash(message, 'error')
        return redirect(url_for('video_gallery'))
    
    # Continue with upload...
"""

# Example of how to check stream limits:
"""
@app.route('/add-live-stream', methods=['POST'])
@login_required
def add_live_stream():
    user_id = int(current_user.id)
    
    # Check stream limit
    from user_limits import can_user_add_stream
    
    can_add, message = can_user_add_stream(user_id)
    if not can_add:
        flash(message, 'error')
        return redirect(url_for('live_streams'))
    
    # Continue with adding stream...
"""
