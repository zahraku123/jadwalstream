#!/usr/bin/env python3
"""
Migration: Add repeat_daily to live_streams table
"""
import sqlite3
import sys
from datetime import datetime

DB_FILE = 'jadwalstream.db'

def migrate():
    print("="*70)
    print("MIGRATION: Add Live Streams Fields")
    print("="*70)
    print(f"Database: {DB_FILE}")
    print(f"Time: {datetime.now()}")
    print()
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(live_streams)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Existing columns: {len(existing_columns)}")
        for col in existing_columns:
            print(f"   - {col}")
        print()
        
        # Define new column to add
        new_column = ('repeat_daily', "INTEGER DEFAULT 0")
        
        col_name, col_type = new_column
        
        print("🔄 Adding new column...")
        if col_name in existing_columns:
            print(f"   ⏭️  {col_name} - Already exists, skipping")
            added = False
        else:
            try:
                sql = f"ALTER TABLE live_streams ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                print(f"   ✅ {col_name} - Added ({col_type})")
                added = True
            except Exception as e:
                print(f"   ❌ {col_name} - Error: {e}")
                raise
        
        conn.commit()
        
        # Verify
        print()
        print("🔍 Verifying changes...")
        cursor.execute("PRAGMA table_info(live_streams)")
        all_columns = [col[1] for col in cursor.fetchall()]
        print(f"📊 Total columns now: {len(all_columns)}")
        
        print()
        print("="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        print(f"✅ Column added: {1 if added else 0}")
        print(f"📊 Total columns: {len(all_columns)}")
        print()
        
        if added:
            print("✅ Migration completed successfully!")
        else:
            print("ℹ️  No changes needed (column already exists)")
        
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
