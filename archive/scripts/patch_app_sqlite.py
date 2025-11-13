#!/usr/bin/env python3
"""
App.py SQLite Patcher
Automatically patch app.py to use SQLite instead of JSON with user isolation
"""

import os
import shutil
from datetime import datetime

APP_FILE = 'app.py'
BACKUP_SUFFIX = '.json_backup'

def backup_app():
    """Backup original app.py"""
    if not os.path.exists(APP_FILE + BACKUP_SUFFIX):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{APP_FILE}.backup_{timestamp}"
        shutil.copy2(APP_FILE, backup_file)
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    else:
        print("⚠️  Backup already exists, skipping")
        return APP_FILE + BACKUP_SUFFIX

def read_file(filepath):
    """Read file content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    """Write file content"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def patch_imports(content):
    """Add database imports after existing imports"""
    
    # Find the line with "from user_auth import"
    import_line = "from user_auth import User, get_user_by_id, authenticate_user, initialize_default_user, create_user, list_users, change_role, delete_user, change_user_password"
    
    if import_line in content:
        # Add SQLite imports after user_auth import
        new_imports = """from user_auth import User, get_user_by_id, authenticate_user, initialize_default_user, create_user, list_users, change_role, delete_user, change_user_password

# SQLite Database imports
from database_helpers import (
    get_video_database as get_video_database_sqlite,
    get_thumbnail_database as get_thumbnail_database_sqlite,
    get_live_streams_data,
    get_looped_videos_data,
    get_bulk_upload_queue_data,
    get_stream_mapping as get_stream_mapping_sqlite,
    add_video_to_db,
    delete_video_from_db,
    add_thumbnail_to_db,
    delete_thumbnail_from_db,
    add_live_stream_to_db,
    delete_live_stream_from_db,
    update_stream_status,
    add_schedule_to_db,
    update_schedule_in_db,
    delete_schedule_from_db,
    add_looped_video_to_db,
    update_looped_video_in_db,
    add_bulk_upload_to_db,
    update_bulk_upload_in_db,
    save_stream_mapping_data,
    delete_stream_mapping_data,
    delete_token_mappings_data
)
from database import get_schedules, get_all_schedules, init_database
"""
        content = content.replace(import_line, new_imports)
        print("✅ Added SQLite imports")
    
    return content

def patch_video_functions(content):
    """Replace JSON video functions with SQLite wrappers"""
    
    # Replace get_video_database function
    old_func = """def get_video_database():
    if not os.path.exists(VIDEO_DB_FILE):
        return []
    try:
        with open(VIDEO_DB_FILE, 'r') as f:
            data = json.load(f)
            # Handle both list and dict formats
            if isinstance(data, list):
                return data
            return []
    except:
        return []"""
    
    new_func = """def get_video_database():
    \"\"\"Get videos for current user from SQLite\"\"\"
    try:
        return get_video_database_sqlite()
    except Exception as e:
        print(f"Error getting videos: {e}")
        return []"""
    
    if old_func in content:
        content = content.replace(old_func, new_func)
        print("✅ Patched get_video_database()")
    
    # Replace save_video_database function
    old_save = """def save_video_database(videos):
    with open(VIDEO_DB_FILE, 'w') as f:
        json.dump(videos, f, indent=4)"""
    
    new_save = """def save_video_database(videos):
    \"\"\"DEPRECATED - use add_video_to_db or delete_video_from_db instead\"\"\"
    # This function is kept for backward compatibility but does nothing
    # All video operations now use individual add/delete functions
    pass"""
    
    if old_save in content:
        content = content.replace(old_save, new_save)
        print("✅ Patched save_video_database()")
    
    return content

def patch_thumbnail_functions(content):
    """Replace JSON thumbnail functions with SQLite wrappers"""
    
    # Replace get_thumbnail_database function
    old_func = """def get_thumbnail_database():
    if not os.path.exists(THUMBNAIL_DB_FILE):
        return []
    try:
        with open(THUMBNAIL_DB_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except:
        return []"""
    
    new_func = """def get_thumbnail_database():
    \"\"\"Get thumbnails for current user from SQLite\"\"\"
    try:
        return get_thumbnail_database_sqlite()
    except Exception as e:
        print(f"Error getting thumbnails: {e}")
        return []"""
    
    if old_func in content:
        content = content.replace(old_func, new_func)
        print("✅ Patched get_thumbnail_database()")
    
    # Replace save_thumbnail_database function
    old_save = """def save_thumbnail_database(thumbnails):
    with open(THUMBNAIL_DB_FILE, 'w') as f:
        json.dump(thumbnails, f, indent=4)"""
    
    new_save = """def save_thumbnail_database(thumbnails):
    \"\"\"DEPRECATED - use add_thumbnail_to_db or delete_thumbnail_from_db instead\"\"\"
    pass"""
    
    if old_save in content:
        content = content.replace(old_save, new_save)
        print("✅ Patched save_thumbnail_database()")
    
    return content

def patch_live_stream_functions(content):
    """Replace JSON live stream functions with SQLite wrappers"""
    
    old_func = """def get_live_streams():
    if not os.path.exists(LIVE_STREAMS_FILE):
        with open(LIVE_STREAMS_FILE, 'w') as f:
            json.dump([], f)
        return []
    try:
        with open(LIVE_STREAMS_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except:
        return []"""
    
    new_func = """def get_live_streams():
    \"\"\"Get live streams for current user from SQLite\"\"\"
    try:
        return get_live_streams_data()
    except Exception as e:
        print(f"Error getting live streams: {e}")
        return []"""
    
    if old_func in content:
        content = content.replace(old_func, new_func)
        print("✅ Patched get_live_streams()")
    
    old_save = """def save_live_streams(streams):
    with open(LIVE_STREAMS_FILE, 'w') as f:
        json.dump(streams, f, indent=4)"""
    
    new_save = """def save_live_streams(streams):
    \"\"\"DEPRECATED - use update_stream_status or individual functions\"\"\"
    pass"""
    
    if old_save in content:
        content = content.replace(old_save, new_save)
        print("✅ Patched save_live_streams()")
    
    return content

def patch_stream_mapping_functions(content):
    """Replace stream mapping functions"""
    
    old_func = """def get_stream_mapping():
    try:
        with open('stream_mapping.json', 'r') as f:
            return json.load(f)
    except:
        return {}"""
    
    new_func = """def get_stream_mapping():
    \"\"\"Get stream mappings for current user from SQLite\"\"\"
    try:
        return get_stream_mapping_sqlite()
    except Exception as e:
        print(f"Error getting stream mappings: {e}")
        return {}"""
    
    if old_func in content:
        content = content.replace(old_func, new_func)
        print("✅ Patched get_stream_mapping()")
    
    return content

def patch_schedule_functions(content):
    """Add helper to get schedules from SQLite"""
    
    # Find where schedules are loaded from Excel
    # We need to check if schedule-related routes exist and patch them
    
    # Add a helper function after imports section
    helper_code = """
# Helper function to get schedules for current user
def get_user_schedules():
    \"\"\"Get schedules for current user from SQLite\"\"\"
    try:
        if current_user.is_authenticated:
            user_id = int(current_user.id)
            return get_schedules(user_id)
        return []
    except Exception as e:
        print(f"Error getting schedules: {e}")
        return []
"""
    
    # Insert after the initialize_default_user() call
    marker = "initialize_default_user()"
    if marker in content and "def get_user_schedules():" not in content:
        content = content.replace(marker, marker + "\n" + helper_code)
        print("✅ Added get_user_schedules() helper")
    
    return content

def patch_init_database(content):
    """Add database initialization on app start"""
    
    # Find app = Flask(__name__) line
    marker = "app = Flask(__name__)"
    
    if marker in content:
        init_code = """app = Flask(__name__)

# Initialize SQLite database
try:
    init_database()
    print("✅ SQLite database initialized")
except Exception as e:
    print(f"⚠️  Database initialization error: {e}")"""
        
        content = content.replace(marker, init_code)
        print("✅ Added database initialization")
    
    return content

def main():
    """Main patch function"""
    print("=" * 60)
    print("  App.py SQLite Patcher")
    print("=" * 60)
    
    if not os.path.exists(APP_FILE):
        print(f"❌ Error: {APP_FILE} not found!")
        return 1
    
    # Backup
    print("\n📦 Creating backup...")
    backup_file = backup_app()
    
    # Read content
    print("\n📖 Reading app.py...")
    content = read_file(APP_FILE)
    
    # Apply patches
    print("\n🔧 Applying patches...")
    content = patch_imports(content)
    content = patch_init_database(content)
    content = patch_video_functions(content)
    content = patch_thumbnail_functions(content)
    content = patch_live_stream_functions(content)
    content = patch_stream_mapping_functions(content)
    content = patch_schedule_functions(content)
    
    # Write patched content
    print("\n💾 Writing patched app.py...")
    write_file(APP_FILE, content)
    
    print("\n" + "=" * 60)
    print("  ✅ Patching Complete!")
    print("=" * 60)
    print(f"\n📦 Backup: {backup_file}")
    print("🔄 Restart your app to apply changes:")
    print("   pkill -f 'python.*app.py'")
    print("   python3 app.py")
    print("\n⚠️  To rollback:")
    print(f"   cp {backup_file} {APP_FILE}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
