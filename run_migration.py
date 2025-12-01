#!/usr/bin/env python3
"""
Database Migration Script for JadwalStream
Run this script to update database schema on existing installations
"""

from modules.database.database import migrate_database

if __name__ == '__main__':
    print("🔄 Starting database migration...")
    print("=" * 50)
    
    try:
        migrate_database()
        print("=" * 50)
        print("✅ Migration completed successfully!")
        print("\nYour database has been updated with:")
        print("  • synced_at column in playlist_cache table")
        print("  • Renamed playlist_title → title in playlist_cache table")
        print("  • All other missing columns added")
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ Migration failed: {e}")
        print("\nPlease check the error message above and try again.")
        exit(1)
