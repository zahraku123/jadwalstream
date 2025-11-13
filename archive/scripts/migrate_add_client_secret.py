#!/usr/bin/env python3
"""
Migration: Add client_secret support per user
Allows each user to have their own YouTube API credentials
"""

import sqlite3
import os

DB_FILE = 'jadwalstream.db'

def migrate():
    print("=" * 60)
    print("  Migration: Add Client Secret Per User")
    print("=" * 60)
    
    if not os.path.exists(DB_FILE):
        print(f"\n❌ Database not found: {DB_FILE}")
        return False
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        print("\n🔧 Checking current schema...")
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"   Current columns: {', '.join(columns)}")
        
        # Add client_secret_path column
        if 'client_secret_path' not in columns:
            print("\n📝 Adding client_secret_path column...")
            cursor.execute('ALTER TABLE users ADD COLUMN client_secret_path TEXT DEFAULT NULL')
            print("   ✅ Added client_secret_path")
        else:
            print("\n⚠️  client_secret_path already exists")
        
        # Create client_secrets folder
        secrets_folder = 'client_secrets'
        if not os.path.exists(secrets_folder):
            os.makedirs(secrets_folder)
            print(f"\n📁 Created folder: {secrets_folder}/")
        
        # Set default client_secret for admin (if global exists)
        if os.path.exists('client_secret.json'):
            print("\n📝 Setting default client_secret for admin...")
            cursor.execute("""
                UPDATE users 
                SET client_secret_path = 'client_secret.json' 
                WHERE username = 'admin' AND client_secret_path IS NULL
            """)
            print("   ✅ Admin will use global client_secret.json")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("  ✅ Migration Complete!")
        print("=" * 60)
        
        print("\n📊 Summary:")
        cursor.execute('''
            SELECT username, client_secret_path, is_admin 
            FROM users 
            ORDER BY is_admin DESC, username
        ''')
        
        for username, path, is_admin in cursor.fetchall():
            status = "✅ Set" if path else "⚠️  Not set"
            admin_badge = "👑" if is_admin else "👤"
            print(f"   {admin_badge} {username}: {status}")
            if path:
                print(f"      → {path}")
        
        print("\n💡 Next steps:")
        print("   1. Users can upload their client_secret.json via UI")
        print("   2. Each user will have isolated YouTube credentials")
        print("   3. Tokens will be stored per user")
        
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
