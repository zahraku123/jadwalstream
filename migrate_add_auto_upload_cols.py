#!/usr/bin/env python3
"""Add auto upload configuration columns to users table"""
import sqlite3
import os

DB_FILE = 'jadwalstream.db'

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        columns_to_add = []
        if 'auto_upload_enabled' not in columns:
            columns_to_add.append(('auto_upload_enabled', 'INTEGER DEFAULT 0'))
        if 'auto_upload_offset_hours' not in columns:
            columns_to_add.append(('auto_upload_offset_hours', 'INTEGER DEFAULT 2'))
        if 'auto_upload_check_interval' not in columns:
            columns_to_add.append(('auto_upload_check_interval', 'INTEGER DEFAULT 30'))
        
        if not columns_to_add:
            print("✓ All auto_upload columns already exist in users table")
            return
        
        # Add missing columns
        for col_name, col_def in columns_to_add:
            sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
            print(f"Adding column: {col_name}")
            cursor.execute(sql)
        
        conn.commit()
        print(f"✓ Successfully added {len(columns_to_add)} column(s) to users table")
        
        # Load config from file and update user 1
        if os.path.exists('auto_upload_config.json'):
            import json
            with open('auto_upload_config.json', 'r') as f:
                config = json.load(f)
            
            cursor.execute('''
                UPDATE users 
                SET auto_upload_enabled = ?,
                    auto_upload_offset_hours = ?,
                    auto_upload_check_interval = ?
                WHERE id = 1
            ''', (
                1 if config.get('enabled') else 0,
                config.get('upload_offset_hours', 2),
                config.get('check_interval_minutes', 30)
            ))
            conn.commit()
            print(f"✓ Migrated config from auto_upload_config.json to user_id=1")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=== Adding auto upload configuration columns to users table ===")
    migrate()
    print("=== Done ===")
