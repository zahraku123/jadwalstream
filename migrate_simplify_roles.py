#!/usr/bin/env python3
"""
Migrate: Simplify roles to only 'admin' and 'user'
Remove: demo, silver, gold, platinum
"""
import sqlite3

DB_FILE = 'jadwalstream.db'

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        print("=== Current Users and Roles ===")
        cursor.execute('SELECT id, username, role FROM users ORDER BY id')
        for row in cursor.fetchall():
            print(f"  User {row[0]}: {row[1]} - {row[2]}")
        
        print("\n=== Migrating Roles ===")
        
        # Migrate all non-admin roles to 'user'
        cursor.execute('''
            UPDATE users 
            SET role = 'user' 
            WHERE role != 'admin'
        ''')
        
        updated_count = cursor.rowcount
        print(f"  Updated {updated_count} user(s) to 'user' role")
        
        conn.commit()
        
        print("\n=== After Migration ===")
        cursor.execute('SELECT id, username, role FROM users ORDER BY id')
        for row in cursor.fetchall():
            print(f"  User {row[0]}: {row[1]} - {row[2]}")
        
        print("\n=== Role Summary ===")
        cursor.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role')
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} user(s)")
        
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
