#!/usr/bin/env python3
"""
Patch App.py untuk User Limits System
1. Add import statements for user_limits
2. Add admin routes for limits management
3. Replace role checks with limit checks
"""

import re
import os

def backup_file(filepath):
    """Create backup of file"""
    backup_path = f"{filepath}.before_limits"
    if not os.path.exists(backup_path):
        with open(filepath, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✅ Backup created: {backup_path}")
    else:
        print(f"⚠️  Backup already exists: {backup_path}")

def add_imports(content):
    """Add user_limits imports"""
    
    # Find the database imports section
    import_marker = "from database import get_schedules, get_all_schedules, init_database"
    
    if import_marker in content and "from user_limits import" not in content:
        new_imports = """from database import get_schedules, get_all_schedules, init_database
from user_limits import (
    get_user_limits,
    can_user_add_stream,
    can_user_upload,
    update_user_limits,
    get_all_users_with_limits,
    calculate_user_storage
)"""
        content = content.replace(import_marker, new_imports)
        print("✅ Added user_limits imports")
    
    return content

def add_require_admin_decorator(content):
    """Add require_admin decorator"""
    
    decorator_code = """
# Admin-only decorator (checks is_admin instead of role)
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        from database import get_user_by_id
        user_data = get_user_by_id(int(current_user.id))
        if not user_data or not user_data.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

"""
    
    # Add after demo_readonly decorator
    marker = "# Decorator to check if user is demo role\ndef demo_readonly"
    
    if marker in content and "def require_admin(f):" not in content:
        content = content.replace(marker, decorator_code + marker)
        print("✅ Added require_admin decorator")
    
    return content

def add_admin_routes(content):
    """Add admin routes for user limits management"""
    
    routes_code = """
# ===== ADMIN USER LIMITS MANAGEMENT =====

@app.route('/admin/users/limits')
@login_required
@require_admin
def admin_user_limits():
    \"\"\"Admin page to manage user limits\"\"\"
    users = get_all_users_with_limits()
    return render_template('admin_user_limits.html', users=users)

@app.route('/admin/users/update_limits', methods=['POST'])
@login_required
@require_admin
def admin_update_limits():
    \"\"\"Update user limits\"\"\"
    user_id = int(request.form.get('user_id'))
    max_streams = int(request.form.get('max_streams', 0))
    max_storage_mb = int(request.form.get('max_storage_mb', 0))
    
    success = update_user_limits(user_id, max_streams, max_storage_mb)
    
    if success:
        flash('User limits updated successfully!', 'success')
    else:
        flash('Failed to update limits (cannot modify admin users)', 'error')
    
    return redirect(url_for('admin_user_limits'))

@app.route('/admin/users/reset_usage', methods=['POST'])
@login_required
@require_admin
def admin_reset_usage():
    \"\"\"Reset user usage (delete all data)\"\"\"
    user_id = int(request.form.get('user_id'))
    
    try:
        from database import get_db_connection
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
            for row in videos:
                filepath = os.path.join(VIDEO_FOLDER, row['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            for row in thumbnails:
                filepath = os.path.join(THUMBNAIL_FOLDER, row['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            looped_folder = os.path.join(VIDEO_FOLDER, 'done')
            for row in looped:
                if row['output_filename']:
                    filepath = os.path.join(looped_folder, row['output_filename'])
                    if os.path.exists(filepath):
                        os.remove(filepath)
            
            # Delete database records
            cursor.execute('DELETE FROM videos WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM thumbnails WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM looped_videos WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM bulk_upload_queue WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM live_streams WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM schedules WHERE user_id = ?', (user_id,))
            
            return jsonify({'success': True, 'message': 'User data reset successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

"""
    
    # Add before the "if __name__ == '__main__':" section
    marker = "if __name__ == '__main__':"
    
    if marker in content and "@app.route('/admin/users/limits')" not in content:
        content = content.replace(marker, routes_code + "\n" + marker)
        print("✅ Added admin limit routes")
    
    return content

def remove_role_functions(content):
    """Comment out old role-based helper functions"""
    
    # Comment out role_max_streams and related functions
    functions_to_comment = [
        "def role_max_streams(role):",
        "def role_can_manage(role):",
        "def role_can_add_streams(role):"
    ]
    
    for func in functions_to_comment:
        if func in content:
            # Find the function and comment it out
            pattern = rf"({func}.*?)(?=\ndef [a-z_]+\(|@app\.route)"
            matches = list(re.finditer(pattern, content, re.DOTALL))
            if matches:
                for match in matches:
                    func_code = match.group(1)
                    commented = "\n# DEPRECATED: Using user limits instead of roles\n# " + func_code.replace("\n", "\n# ")
                    content = content.replace(func_code, commented)
                print(f"✅ Commented out: {func}")
    
    return content

def main():
    print("=" * 60)
    print("  Patching App.py for User Limits System")
    print("=" * 60)
    
    app_file = 'app.py'
    
    if not os.path.exists(app_file):
        print(f"\n❌ {app_file} not found!")
        return False
    
    # Backup
    print("\n📦 Creating backup...")
    backup_file(app_file)
    
    # Read content
    print("\n📖 Reading app.py...")
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply patches
    print("\n🔧 Applying patches...")
    content = add_imports(content)
    content = add_require_admin_decorator(content)
    content = add_admin_routes(content)
    content = remove_role_functions(content)
    
    # Write back
    print("\n💾 Writing patched app.py...")
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "=" * 60)
    print("  ✅ Patching Complete!")
    print("=" * 60)
    
    print("\n📝 Summary of changes:")
    print("   ✅ Added user_limits imports")
    print("   ✅ Added require_admin decorator")
    print("   ✅ Added admin limit management routes")
    print("   ✅ Commented out old role-based functions")
    
    print("\n🔄 Next steps:")
    print("   1. Restart app: pkill -f app.py && python3 app.py &")
    print("   2. Access: http://localhost:5000/admin/users/limits")
    print("   3. Test limit management")
    
    print("\n⚠️  Note: Upload/stream routes still need manual limit checks")
    print("   See admin_limits_routes.py for examples")
    
    return True

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
