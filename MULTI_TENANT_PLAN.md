# Multi-Tenant System Implementation Plan

## 🎯 Objective
Implement a multi-tenant system where each user has isolated data (videos, thumbnails, schedules, live streams) that cannot be accessed by other users.

---

## 🏗️ System Architecture

### 1. **Folder Structure Per User**

```
/root/jadwalstream/
├── videos/
│   ├── admin/           # Video milik user admin
│   ├── user123/         # Video milik user123
│   ├── demo/            # Video milik demo (read-only)
│   └── .gitkeep
├── thumbnails/
│   ├── admin/
│   ├── user123/
│   ├── demo/
│   └── .gitkeep
├── tokens/
│   ├── admin/
│   ├── user123/
│   ├── demo/
│   └── .gitkeep
└── data/
    ├── admin/
    │   ├── video_database.json
    │   ├── thumbnail_database.json
    │   ├── live_streams.json
    │   └── stream_mapping.json
    ├── user123/
    │   ├── video_database.json
    │   ├── thumbnail_database.json
    │   ├── live_streams.json
    │   └── stream_mapping.json
    └── demo/
        └── (read-only shared data)
```

---

## 📊 Database Schema Changes

### Add to ALL Records:

```json
{
  "id": "unique-id",
  "owner": "username",           // ← NEW FIELD
  "created_by": "username",      // ← NEW FIELD
  "created_at": "2025-11-04 10:00:00",
  "updated_at": "2025-11-04 10:00:00",  // ← NEW FIELD
  // ... existing fields
}
```

### Files to Update:
1. `video_database.json` - Add `owner`, `created_by`, `updated_at`
2. `thumbnail_database.json` - Add `owner`, `created_by`, `updated_at`
3. `live_streams.json` - Add `owner`, `created_by`, `updated_at`
4. `stream_mapping.json` - Per user (tidak perlu field owner)
5. Excel schedules - Add column `owner`

---

## 🔧 Helper Functions to Create

### File: `app.py` (or new file `multi_tenant.py`)

```python
import os
from flask_login import current_user

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
VIDEO_DIR = os.path.join(BASE_DIR, 'videos')
THUMBNAIL_DIR = os.path.join(BASE_DIR, 'thumbnails')
TOKEN_DIR = os.path.join(BASE_DIR, 'tokens')

def get_user_folder(folder_type, username=None):
    """
    Get user-specific folder path
    
    Args:
        folder_type: 'videos', 'thumbnails', 'tokens', 'data'
        username: username (default: current_user.username)
    
    Returns:
        /root/jadwalstream/videos/username/
    """
    if username is None:
        username = current_user.username
    
    base_folders = {
        'videos': VIDEO_DIR,
        'thumbnails': THUMBNAIL_DIR,
        'tokens': TOKEN_DIR,
        'data': DATA_DIR
    }
    
    base = base_folders.get(folder_type)
    if not base:
        raise ValueError(f"Invalid folder_type: {folder_type}")
    
    user_folder = os.path.join(base, username)
    
    # Create if not exists
    os.makedirs(user_folder, exist_ok=True)
    
    return user_folder


def get_user_database_path(db_type, username=None):
    """
    Get user-specific database file path
    
    Args:
        db_type: 'video', 'thumbnail', 'live_streams', 'stream_mapping'
        username: username (default: current_user.username)
    
    Returns:
        /root/jadwalstream/data/username/video_database.json
    """
    if username is None:
        username = current_user.username
    
    db_files = {
        'video': 'video_database.json',
        'thumbnail': 'thumbnail_database.json',
        'live_streams': 'live_streams.json',
        'stream_mapping': 'stream_mapping.json'
    }
    
    filename = db_files.get(db_type)
    if not filename:
        raise ValueError(f"Invalid db_type: {db_type}")
    
    user_data_dir = get_user_folder('data', username)
    return os.path.join(user_data_dir, filename)


def filter_by_owner(items, owner=None):
    """
    Filter list of items by owner
    
    Args:
        items: List of dict items with 'owner' field
        owner: username to filter (default: current_user.username)
    
    Returns:
        Filtered list
    """
    if owner is None:
        owner = current_user.username
    
    # Admin can see all
    if current_user.role == 'admin':
        return items
    
    # Filter by owner
    return [item for item in items if item.get('owner') == owner]


def ensure_user_folders(username):
    """
    Create all necessary folders for new user
    
    Called when new user is created
    """
    folders = ['videos', 'thumbnails', 'tokens', 'data']
    
    for folder_type in folders:
        folder_path = get_user_folder(folder_type, username)
        print(f"Created folder: {folder_path}")
    
    # Initialize empty database files
    db_types = ['video', 'thumbnail', 'live_streams', 'stream_mapping']
    for db_type in db_types:
        db_path = get_user_database_path(db_type, username)
        if not os.path.exists(db_path):
            # Initialize with empty array or dict
            if db_type == 'stream_mapping':
                with open(db_path, 'w') as f:
                    json.dump({}, f, indent=2)
            else:
                with open(db_path, 'w') as f:
                    json.dump([], f, indent=2)
            print(f"Initialized database: {db_path}")


def check_ownership(item_id, item_type, username=None):
    """
    Check if user owns the item
    
    Args:
        item_id: ID of the item
        item_type: 'video', 'thumbnail', 'live_stream', etc.
        username: username to check (default: current_user.username)
    
    Returns:
        True if user owns item or is admin, False otherwise
    """
    if username is None:
        username = current_user.username
    
    # Admin can access all
    if current_user.role == 'admin':
        return True
    
    # Load appropriate database and check owner
    # Implementation depends on item_type
    
    return False
```

---

## 📝 Functions to Modify in app.py

### Current vs New Approach

#### Before (Global):
```python
def get_video_database():
    if os.path.exists(VIDEO_DATABASE_FILE):
        with open(VIDEO_DATABASE_FILE, 'r') as f:
            return json.load(f)
    return []
```

#### After (Per User):
```python
def get_video_database(username=None):
    db_path = get_user_database_path('video', username)
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            videos = json.load(f)
            return filter_by_owner(videos, username)
    return []
```

### List of Functions to Update:

**Video Management:**
1. `get_video_database()` - Add username parameter
2. `save_video_database()` - Add username parameter
3. `upload_video()` - Save to user folder + set owner field
4. `delete_video()` - Check ownership before delete
5. `serve_video()` - Check ownership before serving

**Thumbnail Management:**
6. `get_thumbnail_database()` - Add username parameter
7. `save_thumbnail_database()` - Add username parameter
8. `upload_thumbnail()` - Save to user folder + set owner field
9. `delete_thumbnail()` - Check ownership before delete
10. `serve_thumbnail()` - Check ownership before serving

**Live Streams:**
11. `get_live_streams()` - Add username parameter
12. `save_live_streams()` - Add username parameter
13. `add_live_stream()` - Set owner field
14. `edit_live_stream()` - Check ownership
15. `start_live_stream_now()` - Check ownership
16. `cancel_live_stream()` - Check ownership

**Schedules:**
17. `add_schedule()` - Set owner field in Excel
18. `update_schedule()` - Check ownership
19. `delete_schedule()` - Check ownership
20. `run_schedule_now()` - Check ownership

**Tokens:**
21. `get_token_files()` - Filter by user folder
22. `create_token()` - Save to user folder
23. `delete_token()` - Check ownership

**Stream Keys:**
24. `fetch_stream_keys()` - Save to user mapping
25. Load stream mapping - Per user

**Routes to Add Owner Field:**
- All video gallery routes
- All thumbnail gallery routes
- All live stream routes
- All schedule routes
- All token routes
- All stream key routes

---

## 🔄 Migration Script

### File: `migrate_to_multitenant.py`

```python
#!/usr/bin/env python3
"""
Migration script to convert existing single-tenant to multi-tenant system
"""

import os
import json
import shutil
from datetime import datetime

# Configuration
DEFAULT_OWNER = 'admin'  # Assign all existing data to admin
BASE_DIR = '/root/jadwalstream'

def migrate_folders():
    """Create new folder structure and move existing files"""
    print("=" * 60)
    print("STEP 1: Migrating Folder Structure")
    print("=" * 60)
    
    # Create data folder
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    folders = ['videos', 'thumbnails', 'tokens']
    
    for folder in folders:
        old_path = os.path.join(BASE_DIR, folder)
        new_path = os.path.join(old_path, DEFAULT_OWNER)
        
        # Create admin folder
        os.makedirs(new_path, exist_ok=True)
        
        # Move existing files to admin folder
        if os.path.exists(old_path):
            for item in os.listdir(old_path):
                item_path = os.path.join(old_path, item)
                if os.path.isfile(item_path):
                    dest_path = os.path.join(new_path, item)
                    shutil.move(item_path, dest_path)
                    print(f"✓ Moved: {item} → {folder}/{DEFAULT_OWNER}/")
    
    print("\n✅ Folder structure migrated!\n")


def migrate_databases():
    """Add owner field to all database records"""
    print("=" * 60)
    print("STEP 2: Migrating Database Files")
    print("=" * 60)
    
    # Create admin data folder
    admin_data_dir = os.path.join(BASE_DIR, 'data', DEFAULT_OWNER)
    os.makedirs(admin_data_dir, exist_ok=True)
    
    db_files = {
        'video_database.json': [],
        'thumbnail_database.json': [],
        'live_streams.json': [],
        'stream_mapping.json': {}
    }
    
    for db_file, default_value in db_files.items():
        old_path = os.path.join(BASE_DIR, db_file)
        new_path = os.path.join(admin_data_dir, db_file)
        
        if os.path.exists(old_path):
            with open(old_path, 'r') as f:
                data = json.load(f)
            
            # Add owner field if it's a list
            if isinstance(data, list):
                updated_count = 0
                for item in data:
                    if 'owner' not in item:
                        item['owner'] = DEFAULT_OWNER
                        item['created_by'] = DEFAULT_OWNER
                        item['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        updated_count += 1
                
                print(f"✓ {db_file}: Added owner to {updated_count} records")
            
            # Move to new location
            with open(new_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Backup old file
            backup_path = old_path + '.backup'
            shutil.copy2(old_path, backup_path)
            print(f"  → Backed up to: {backup_path}")
            print(f"  → Moved to: {new_path}")
        else:
            # Create empty file
            with open(new_path, 'w') as f:
                json.dump(default_value, f, indent=2)
            print(f"✓ {db_file}: Created empty file")
    
    print("\n✅ Database files migrated!\n")


def migrate_excel_schedules():
    """Add owner column to Excel schedules"""
    print("=" * 60)
    print("STEP 3: Migrating Excel Schedules")
    print("=" * 60)
    
    try:
        import pandas as pd
        
        excel_file = os.path.join(BASE_DIR, 'live_stream_data.xlsx')
        
        if os.path.exists(excel_file):
            # Backup
            backup_file = excel_file + '.backup'
            shutil.copy2(excel_file, backup_file)
            print(f"✓ Backed up Excel: {backup_file}")
            
            # Read and update
            df = pd.read_excel(excel_file)
            
            if 'owner' not in df.columns:
                df['owner'] = DEFAULT_OWNER
                df['created_by'] = DEFAULT_OWNER
                df['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Save
                df.to_excel(excel_file, index=False)
                print(f"✓ Added owner column to {len(df)} schedule records")
            else:
                print("✓ Owner column already exists")
        else:
            print("⚠ Excel file not found, skipping...")
    
    except ImportError:
        print("⚠ pandas not installed, skipping Excel migration...")
    except Exception as e:
        print(f"❌ Error migrating Excel: {e}")
    
    print("\n✅ Excel migration completed!\n")


def create_demo_user_data():
    """Create read-only data for demo user"""
    print("=" * 60)
    print("STEP 4: Creating Demo User Data")
    print("=" * 60)
    
    demo_folders = ['videos', 'thumbnails', 'tokens', 'data']
    
    for folder in demo_folders:
        demo_path = os.path.join(BASE_DIR, folder, 'demo')
        os.makedirs(demo_path, exist_ok=True)
        print(f"✓ Created: {folder}/demo/")
    
    # Create empty databases for demo
    demo_data_dir = os.path.join(BASE_DIR, 'data', 'demo')
    db_files = ['video_database.json', 'thumbnail_database.json', 
                'live_streams.json', 'stream_mapping.json']
    
    for db_file in db_files:
        demo_db_path = os.path.join(demo_data_dir, db_file)
        if db_file == 'stream_mapping.json':
            default = {}
        else:
            default = []
        
        with open(demo_db_path, 'w') as f:
            json.dump(default, f, indent=2)
        print(f"✓ Created: data/demo/{db_file}")
    
    print("\n✅ Demo user data created!\n")


def verify_migration():
    """Verify migration completed successfully"""
    print("=" * 60)
    print("STEP 5: Verification")
    print("=" * 60)
    
    checks = {
        'Admin video folder': os.path.join(BASE_DIR, 'videos', 'admin'),
        'Admin data folder': os.path.join(BASE_DIR, 'data', 'admin'),
        'Demo data folder': os.path.join(BASE_DIR, 'data', 'demo'),
        'Admin video DB': os.path.join(BASE_DIR, 'data', 'admin', 'video_database.json'),
    }
    
    all_good = True
    for name, path in checks.items():
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {path}")
        if not exists:
            all_good = False
    
    print("\n" + "=" * 60)
    if all_good:
        print("✅ Migration completed successfully!")
    else:
        print("⚠️  Migration completed with warnings")
    print("=" * 60)


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  MULTI-TENANT MIGRATION SCRIPT".center(58) + "║")
    print("║" + "  Converting to user-isolated data structure".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    response = input("⚠️  This will modify your data structure. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return
    
    print("\n🚀 Starting migration...\n")
    
    try:
        migrate_folders()
        migrate_databases()
        migrate_excel_schedules()
        create_demo_user_data()
        verify_migration()
        
        print("\n📝 NEXT STEPS:")
        print("   1. Update user_auth.py to call ensure_user_folders() on user creation")
        print("   2. Update all functions in app.py to use new helper functions")
        print("   3. Test with admin user")
        print("   4. Test with regular user")
        print("   5. Test with demo user")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please restore from backups if needed.")


if __name__ == '__main__':
    main()
```

---

## 🧪 Testing Checklist

After implementation, test these scenarios:

### Admin User:
- [ ] Can see all users' data (optional feature)
- [ ] Can manage own data
- [ ] Can create new users
- [ ] New user folders created automatically

### Regular User (user1):
- [ ] Can only see own videos
- [ ] Can only see own thumbnails
- [ ] Can only see own schedules
- [ ] Can only see own live streams
- [ ] Cannot see user2's data
- [ ] Cannot delete user2's items
- [ ] Cannot edit user2's items

### Demo User:
- [ ] Can see demo folder content
- [ ] Cannot upload anything
- [ ] Cannot delete anything
- [ ] Cannot edit anything

### Edge Cases:
- [ ] What if user tries to access other user's video by direct URL?
- [ ] What if user tries to delete other user's item by manipulating form?
- [ ] What happens when user is deleted? (cleanup folders)

---

## ⚠️ Important Considerations

### Security:
- All ownership checks must happen on **server-side**, not client-side
- Never trust user input (IDs, filenames, etc.)
- Validate ownership before ANY operation (view, edit, delete)

### Performance:
- Consider adding indexes if using database
- Cache user folder paths
- Avoid loading all users' data unnecessarily

### Storage:
- Monitor disk usage per user
- Consider adding quota limits
- Plan for cleanup of deleted users

### Backward Compatibility:
- Keep backup of old data
- Add fallback logic for old records without owner field
- Gradual migration if needed

---

## 📊 Estimated Impact

### Files to Modify:
- `app.py`: ~50-70 functions
- `user_auth.py`: ~3-5 functions
- Templates: ~10-15 files (optional - show owner info)

### New Files:
- `multi_tenant.py`: Helper functions
- `migrate_to_multitenant.py`: Migration script
- `MULTI_TENANT_PLAN.md`: This document

### Testing Time:
- Development: 4-6 hours
- Testing: 2-3 hours
- Debugging: 1-2 hours
- **Total: ~8-11 hours**

---

## 🚀 Implementation Order

1. ✅ Create helper functions (`multi_tenant.py`)
2. ✅ Update `user_auth.py` for folder creation
3. ✅ Run migration script
4. ✅ Update video management functions
5. ✅ Update thumbnail management functions
6. ✅ Update live stream functions
7. ✅ Update schedule functions
8. ✅ Update token management functions
9. ✅ Test admin user
10. ✅ Test regular user
11. ✅ Test demo user
12. ✅ Update templates (optional)
13. ✅ Documentation

---

## 📞 Contact & Support

If you need help during implementation:
- Review this document
- Check migration script logs
- Test incrementally (one feature at a time)
- Keep backups of all data

---

**Document Version:** 1.0  
**Created:** 2025-11-04  
**Last Updated:** 2025-11-04  
**Status:** 📝 Planning Phase
