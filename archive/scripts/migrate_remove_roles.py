#!/usr/bin/env python3
"""
Migration: Remove Roles, Add Per-User Limits
- Remove role system (admin, demo, silver, gold, platinum)
- Add max_streams (jumlah live stream/jadwal allowed)
- Add max_storage_mb (storage limit in MB)
- Admin gets unlimited (null values)
"""

import sqlite3
import os

DB_FILE = 'jadwalstream.db'

def migrate():
    print("=" * 60)
    print("  Migration: Remove Roles → Add Per-User Limits")
    print("=" * 60)
    
    if not os.path.exists(DB_FILE):
        print(f"\n❌ Database not found: {DB_FILE}")
        return False
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        print("\n🔧 Checking current schema...")
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"   Current columns: {', '.join(columns)}")
        
        # Add new columns if not exist
        if 'max_streams' not in columns:
            print("\n📝 Adding max_streams column...")
            cursor.execute('ALTER TABLE users ADD COLUMN max_streams INTEGER DEFAULT NULL')
            print("   ✅ Added max_streams")
        
        if 'max_storage_mb' not in columns:
            print("\n📝 Adding max_storage_mb column...")
            cursor.execute('ALTER TABLE users ADD COLUMN max_storage_mb INTEGER DEFAULT NULL')
            print("   ✅ Added max_storage_mb")
        
        if 'is_admin' not in columns:
            print("\n📝 Adding is_admin column...")
            cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
            print("   ✅ Added is_admin")
        
        # Set admin flag based on existing role
        print("\n🔄 Converting roles to admin flag...")
        cursor.execute("UPDATE users SET is_admin = 1 WHERE role = 'admin'")
        print(f"   ✅ Set is_admin=1 for admin users")
        
        # Set default limits for non-admin users (null = unlimited for admin)
        print("\n🔄 Setting default limits...")
        
        # Get all users
        cursor.execute("SELECT id, username, role, is_admin FROM users")
        users = cursor.fetchall()
        
        for user_id, username, role, is_admin in users:
            if is_admin:
                # Admin gets unlimited (NULL)
                cursor.execute('''
                    UPDATE users 
                    SET max_streams = NULL, max_storage_mb = NULL 
                    WHERE id = ?
                ''', (user_id,))
                print(f"   ✅ {username}: unlimited (admin)")
            else:
                # Non-admin gets default limits based on old role
                if role == 'silver':
                    max_streams, max_storage = 5, 5000  # 5 streams, 5GB
                elif role == 'gold':
                    max_streams, max_storage = 10, 10000  # 10 streams, 10GB
                elif role == 'platinum':
                    max_streams, max_storage = 20, 20000  # 20 streams, 20GB
                else:  # demo or other
                    max_streams, max_storage = 3, 2000  # 3 streams, 2GB
                
                cursor.execute('''
                    UPDATE users 
                    SET max_streams = ?, max_storage_mb = ? 
                    WHERE id = ?
                ''', (max_streams, max_storage, user_id))
                print(f"   ✅ {username}: {max_streams} streams, {max_storage}MB (converted from {role})")
        
        # Note: We keep the role column for backward compatibility
        # but it won't be used for permission checks anymore
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("  ✅ Migration Complete!")
        print("=" * 60)
        
        # Show summary
        print("\n📊 User Limits Summary:")
        cursor.execute('''
            SELECT username, is_admin, max_streams, max_storage_mb 
            FROM users 
            ORDER BY is_admin DESC, username
        ''')
        
        for username, is_admin, max_streams, max_storage in cursor.fetchall():
            if is_admin:
                print(f"   👑 {username}: UNLIMITED (admin)")
            else:
                streams = max_streams if max_streams else "unlimited"
                storage = f"{max_storage}MB" if max_storage else "unlimited"
                print(f"   👤 {username}: {streams} streams, {storage} storage")
        
        print("\n💡 Next steps:")
        print("   1. Admin can now adjust limits per user in admin panel")
        print("   2. Role column still exists but not used")
        print("   3. All checks now use max_streams and max_storage_mb")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

if __name__ == '__main__':
    import sys
    success = migrate()
    sys.exit(0 if success else 1)
