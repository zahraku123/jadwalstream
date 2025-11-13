#!/usr/bin/env python3
"""
Migration Script: JSON to SQLite
Migrate all JSON data to SQLite database with per-user isolation
"""

import json
import os
import sys
from datetime import datetime
import pandas as pd
import shutil
from database import (
    init_database, create_user, add_video, add_thumbnail,
    add_live_stream, add_schedule, add_looped_video,
    add_bulk_upload_item, save_stream_mapping, save_stream_timer,
    DB_FILE
)

# File paths
USERS_FILE = 'users.json'
VIDEO_DB_FILE = 'video_database.json'
THUMBNAIL_DB_FILE = 'thumbnail_database.json'
LIVE_STREAMS_FILE = 'live_streams.json'
LOOPED_VIDEOS_FILE = 'looped_videos.json'
BULK_UPLOAD_FILE = 'bulk_upload_queue.json'
STREAM_MAPPING_FILE = 'stream_mapping.json'
STREAM_TIMERS_FILE = 'stream_timers.json'
EXCEL_FILE = 'live_stream_data.xlsx'

# Backup folder
BACKUP_FOLDER = 'json_backups'

def backup_json_files():
    """Backup all JSON files before migration"""
    print("\n📦 Creating backup of JSON files...")
    
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_subfolder = os.path.join(BACKUP_FOLDER, f'backup_{timestamp}')
    os.makedirs(backup_subfolder, exist_ok=True)
    
    files_to_backup = [
        USERS_FILE, VIDEO_DB_FILE, THUMBNAIL_DB_FILE, LIVE_STREAMS_FILE,
        LOOPED_VIDEOS_FILE, BULK_UPLOAD_FILE, STREAM_MAPPING_FILE,
        STREAM_TIMERS_FILE, EXCEL_FILE
    ]
    
    backed_up = 0
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_subfolder, file))
            backed_up += 1
            print(f"  ✓ Backed up: {file}")
    
    print(f"✅ Backup completed: {backed_up} files backed up to {backup_subfolder}")
    return backup_subfolder

def load_json(filepath, default=None):
    """Load JSON file with default fallback"""
    if default is None:
        default = {}
    
    if not os.path.exists(filepath):
        return default
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️  Warning: Could not load {filepath}: {e}")
        return default

def migrate_users():
    """Migrate users from users.json to SQLite"""
    print("\n👥 Migrating users...")
    
    users_data = load_json(USERS_FILE, {})
    
    if not users_data:
        print("  ⚠️  No users found in users.json")
        return {}
    
    user_id_map = {}  # Map username to new user_id
    
    for username, user_info in users_data.items():
        try:
            user_id = create_user(
                username=username,
                password_hash=user_info.get('password_hash', ''),
                role=user_info.get('role', 'demo')
            )
            user_id_map[username] = user_id
            print(f"  ✓ Migrated user: {username} (ID: {user_id}, Role: {user_info.get('role')})")
        except Exception as e:
            print(f"  ✗ Failed to migrate user {username}: {e}")
    
    print(f"✅ Users migrated: {len(user_id_map)}/{len(users_data)}")
    return user_id_map

def migrate_videos(default_user_id):
    """Migrate videos from video_database.json to SQLite"""
    print("\n🎬 Migrating videos...")
    
    videos_data = load_json(VIDEO_DB_FILE, [])
    
    if not videos_data:
        print("  ℹ️  No videos found")
        return
    
    migrated = 0
    for video in videos_data:
        try:
            add_video(default_user_id, video)
            migrated += 1
        except Exception as e:
            print(f"  ✗ Failed to migrate video {video.get('id')}: {e}")
    
    print(f"✅ Videos migrated: {migrated}/{len(videos_data)}")

def migrate_thumbnails(default_user_id):
    """Migrate thumbnails from thumbnail_database.json to SQLite"""
    print("\n🖼️  Migrating thumbnails...")
    
    thumbnails_data = load_json(THUMBNAIL_DB_FILE, [])
    
    if not thumbnails_data:
        print("  ℹ️  No thumbnails found")
        return
    
    migrated = 0
    for thumbnail in thumbnails_data:
        try:
            add_thumbnail(default_user_id, thumbnail)
            migrated += 1
        except Exception as e:
            print(f"  ✗ Failed to migrate thumbnail {thumbnail.get('id')}: {e}")
    
    print(f"✅ Thumbnails migrated: {migrated}/{len(thumbnails_data)}")

def migrate_live_streams(default_user_id):
    """Migrate live streams from live_streams.json to SQLite"""
    print("\n📡 Migrating live streams...")
    
    streams_data = load_json(LIVE_STREAMS_FILE, [])
    
    if not streams_data:
        print("  ℹ️  No live streams found")
        return
    
    migrated = 0
    for stream in streams_data:
        try:
            add_live_stream(default_user_id, stream)
            migrated += 1
        except Exception as e:
            print(f"  ✗ Failed to migrate stream {stream.get('id')}: {e}")
    
    print(f"✅ Live streams migrated: {migrated}/{len(streams_data)}")

def migrate_schedules(default_user_id):
    """Migrate schedules from Excel to SQLite"""
    print("\n📅 Migrating schedules from Excel...")
    
    if not os.path.exists(EXCEL_FILE):
        print("  ℹ️  No Excel schedule file found")
        return
    
    try:
        df = pd.read_excel(EXCEL_FILE)
        
        if df.empty:
            print("  ℹ️  Excel file is empty")
            return
        
        migrated = 0
        for _, row in df.iterrows():
            try:
                schedule_data = {
                    'title': str(row.get('title', '')),
                    'description': str(row.get('description', '')),
                    'scheduled_start_time': str(row.get('scheduledStartTime', '')),
                    'video_file': str(row.get('videoFile', '')),
                    'thumbnail': str(row.get('thumbnailFile', '')),
                    'stream_name': str(row.get('streamNameExisting', '')),
                    'stream_id': str(row.get('streamIdExisting', '')),
                    'token_file': str(row.get('token_file', '')),
                    'repeat_daily': 1 if row.get('repeat_daily', False) else 0,
                    'success': 1 if row.get('success', False) else 0,
                    'broadcast_link': str(row.get('broadcastLink', ''))
                }
                
                # Clean up NaN values
                for key in schedule_data:
                    if schedule_data[key] == 'nan' or schedule_data[key] == 'None':
                        schedule_data[key] = ''
                
                add_schedule(default_user_id, schedule_data)
                migrated += 1
            except Exception as e:
                print(f"  ✗ Failed to migrate schedule: {e}")
        
        print(f"✅ Schedules migrated: {migrated}/{len(df)}")
    
    except Exception as e:
        print(f"  ✗ Error reading Excel file: {e}")

def migrate_looped_videos(default_user_id):
    """Migrate looped videos from looped_videos.json to SQLite"""
    print("\n🔁 Migrating looped videos...")
    
    looped_data = load_json(LOOPED_VIDEOS_FILE, [])
    
    if not looped_data:
        print("  ℹ️  No looped videos found")
        return
    
    migrated = 0
    for looped in looped_data:
        try:
            add_looped_video(default_user_id, looped)
            migrated += 1
        except Exception as e:
            print(f"  ✗ Failed to migrate looped video {looped.get('id')}: {e}")
    
    print(f"✅ Looped videos migrated: {migrated}/{len(looped_data)}")

def migrate_bulk_upload_queue(default_user_id):
    """Migrate bulk upload queue from bulk_upload_queue.json to SQLite"""
    print("\n📤 Migrating bulk upload queue...")
    
    queue_data = load_json(BULK_UPLOAD_FILE, [])
    
    if not queue_data:
        print("  ℹ️  No bulk upload items found")
        return
    
    migrated = 0
    for item in queue_data:
        try:
            add_bulk_upload_item(default_user_id, item)
            migrated += 1
        except Exception as e:
            print(f"  ✗ Failed to migrate upload item {item.get('id')}: {e}")
    
    print(f"✅ Bulk upload items migrated: {migrated}/{len(queue_data)}")

def migrate_stream_mappings(default_user_id):
    """Migrate stream mappings from stream_mapping.json to SQLite"""
    print("\n🔑 Migrating stream mappings...")
    
    mappings_data = load_json(STREAM_MAPPING_FILE, {})
    
    if not mappings_data:
        print("  ℹ️  No stream mappings found")
        return
    
    migrated = 0
    for token_file, streams in mappings_data.items():
        if not streams:
            continue
        
        for stream_id, stream_data in streams.items():
            try:
                save_stream_mapping(default_user_id, token_file, stream_id, stream_data)
                migrated += 1
            except Exception as e:
                print(f"  ✗ Failed to migrate mapping {token_file}/{stream_id}: {e}")
    
    print(f"✅ Stream mappings migrated: {migrated}")

def migrate_stream_timers(default_user_id):
    """Migrate stream timers from stream_timers.json to SQLite"""
    print("\n⏱️  Migrating stream timers...")
    
    timers_data = load_json(STREAM_TIMERS_FILE, {})
    
    if not timers_data:
        print("  ℹ️  No stream timers found")
        return
    
    migrated = 0
    for stream_id, timer_data in timers_data.items():
        try:
            save_stream_timer(stream_id, default_user_id, timer_data)
            migrated += 1
        except Exception as e:
            print(f"  ✗ Failed to migrate timer for stream {stream_id}: {e}")
    
    print(f"✅ Stream timers migrated: {migrated}")

def main():
    """Main migration function"""
    print("=" * 60)
    print("  JSON to SQLite Migration Tool")
    print("  JadwalStream Application")
    print("=" * 60)
    
    # Check if database already exists
    if os.path.exists(DB_FILE):
        response = input(f"\n⚠️  Database file '{DB_FILE}' already exists!\nDo you want to overwrite it? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled.")
            sys.exit(0)
        
        # Backup existing database
        backup_db_path = f"{DB_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(DB_FILE, backup_db_path)
        print(f"✅ Existing database backed up to: {backup_db_path}")
        
        # Remove old database
        os.remove(DB_FILE)
    
    # Backup JSON files
    backup_folder = backup_json_files()
    
    # Initialize database
    print("\n🗄️  Initializing SQLite database...")
    init_database()
    print(f"✅ Database initialized: {DB_FILE}")
    
    # Migrate users first
    user_id_map = migrate_users()
    
    if not user_id_map:
        print("\n❌ No users to migrate. Creating default admin user...")
        default_user_id = create_user('admin', 'default_hash', 'admin')
        print(f"✅ Default admin user created (ID: {default_user_id})")
        print("⚠️  Please update password after migration!")
    else:
        # Use first admin user as default, or first user if no admin
        default_user_id = None
        for username, uid in user_id_map.items():
            if 'admin' in username.lower():
                default_user_id = uid
                break
        
        if not default_user_id:
            default_user_id = list(user_id_map.values())[0]
        
        print(f"\nℹ️  Using user ID {default_user_id} as default owner for existing data")
    
    # Migrate all other data
    migrate_videos(default_user_id)
    migrate_thumbnails(default_user_id)
    migrate_live_streams(default_user_id)
    migrate_schedules(default_user_id)
    migrate_looped_videos(default_user_id)
    migrate_bulk_upload_queue(default_user_id)
    migrate_stream_mappings(default_user_id)
    migrate_stream_timers(default_user_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("  ✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\n📊 Database Statistics:")
    
    from database import get_database_stats
    stats = get_database_stats()
    for table, count in stats.items():
        if table != 'db_size_mb':
            print(f"  - {table}: {count} records")
    
    if 'db_size_mb' in stats:
        print(f"\n💾 Database size: {stats['db_size_mb']} MB")
    
    print(f"\n📦 JSON backups saved to: {backup_folder}")
    print(f"🗄️  SQLite database: {DB_FILE}")
    
    print("\n⚠️  NEXT STEPS:")
    print("  1. Test the application with the new database")
    print("  2. Verify all data migrated correctly")
    print("  3. Update any passwords if needed")
    print("  4. Once confirmed working, you can delete JSON backups")
    print("\n💡 To rollback: Stop app, delete .db file, restore from json_backups/")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
