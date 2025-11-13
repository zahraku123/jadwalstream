#!/usr/bin/env python3
"""
Migration: Add missing schedule fields
Adds: privacy_status, auto_start, auto_stop, made_for_kids
"""
import sqlite3
import sys
from datetime import datetime

DB_FILE = 'jadwalstream.db'

def migrate():
    print("="*70)
    print("MIGRATION: Add Schedule Fields")
    print("="*70)
    print(f"Database: {DB_FILE}")
    print(f"Time: {datetime.now()}")
    print()
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(schedules)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Existing columns: {len(existing_columns)}")
        for col in existing_columns:
            print(f"   - {col}")
        print()
        
        # Define new columns to add
        new_columns = [
            ('privacy_status', "TEXT DEFAULT 'unlisted'"),
            ('auto_start', "INTEGER DEFAULT 0"),
            ('auto_stop', "INTEGER DEFAULT 0"),
            ('made_for_kids', "INTEGER DEFAULT 0"),
        ]
        
        added_count = 0
        skipped_count = 0
        
        print("🔄 Adding new columns...")
        for col_name, col_type in new_columns:
            if col_name in existing_columns:
                print(f"   ⏭️  {col_name:20} - Already exists, skipping")
                skipped_count += 1
            else:
                try:
                    sql = f"ALTER TABLE schedules ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"   ✅ {col_name:20} - Added ({col_type})")
                    added_count += 1
                except Exception as e:
                    print(f"   ❌ {col_name:20} - Error: {e}")
                    raise
        
        conn.commit()
        
        # Verify
        print()
        print("🔍 Verifying changes...")
        cursor.execute("PRAGMA table_info(schedules)")
        all_columns = [col[1] for col in cursor.fetchall()]
        print(f"📊 Total columns now: {len(all_columns)}")
        
        print()
        print("="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        print(f"✅ Columns added: {added_count}")
        print(f"⏭️  Columns skipped: {skipped_count}")
        print(f"📊 Total columns: {len(all_columns)}")
        print()
        
        if added_count > 0:
            print("✅ Migration completed successfully!")
        else:
            print("ℹ️  No changes needed (columns already exist)")
        
        print("="*70)
        
        conn.close()
        return True
        
    except Exception as e:
        print()
        print("="*70)
        print("❌ MIGRATION FAILED")
        print("="*70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
