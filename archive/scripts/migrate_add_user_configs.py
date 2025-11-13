#!/usr/bin/env python3
"""
Migration: Add Per-User Configuration Columns
Adds columns for Telegram, Gemini AI, and Auto Upload isolation
"""

import sqlite3
import os
import json

DB_FILE = 'jadwalstream.db'

def migrate():
    print("=" * 60)
    print("  Migration: Add User Configuration Columns")
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
        print(f"   Current columns: {len(columns)} columns")
        
        changes_made = []
        
        # ===== TELEGRAM COLUMNS =====
        print("\n📱 Adding Telegram columns...")
        
        if 'telegram_bot_token' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN telegram_bot_token TEXT DEFAULT NULL')
            changes_made.append('telegram_bot_token')
            print("   ✅ Added telegram_bot_token")
        else:
            print("   ⚠️  telegram_bot_token already exists")
        
        if 'telegram_chat_id' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN telegram_chat_id TEXT DEFAULT NULL')
            changes_made.append('telegram_chat_id')
            print("   ✅ Added telegram_chat_id")
        else:
            print("   ⚠️  telegram_chat_id already exists")
        
        if 'telegram_enabled' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN telegram_enabled BOOLEAN DEFAULT 0')
            changes_made.append('telegram_enabled')
            print("   ✅ Added telegram_enabled")
        else:
            print("   ⚠️  telegram_enabled already exists")
        
        # ===== GEMINI AI COLUMNS =====
        print("\n🤖 Adding Gemini AI columns...")
        
        if 'gemini_api_key' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN gemini_api_key TEXT DEFAULT NULL')
            changes_made.append('gemini_api_key')
            print("   ✅ Added gemini_api_key")
        else:
            print("   ⚠️  gemini_api_key already exists")
        
        if 'gemini_model' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN gemini_model TEXT DEFAULT 'gemini-2.0-flash-exp'")
            changes_made.append('gemini_model')
            print("   ✅ Added gemini_model")
        else:
            print("   ⚠️  gemini_model already exists")
        
        if 'gemini_custom_prompt' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN gemini_custom_prompt TEXT DEFAULT NULL')
            changes_made.append('gemini_custom_prompt')
            print("   ✅ Added gemini_custom_prompt")
        else:
            print("   ⚠️  gemini_custom_prompt already exists")
        
        # ===== AUTO UPLOAD COLUMNS =====
        print("\n📤 Adding Auto Upload columns...")
        
        if 'auto_upload_enabled' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN auto_upload_enabled BOOLEAN DEFAULT 0')
            changes_made.append('auto_upload_enabled')
            print("   ✅ Added auto_upload_enabled")
        else:
            print("   ⚠️  auto_upload_enabled already exists")
        
        if 'auto_upload_offset_hours' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN auto_upload_offset_hours INTEGER DEFAULT 2')
            changes_made.append('auto_upload_offset_hours')
            print("   ✅ Added auto_upload_offset_hours")
        else:
            print("   ⚠️  auto_upload_offset_hours already exists")
        
        if 'auto_upload_check_interval' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN auto_upload_check_interval INTEGER DEFAULT 30')
            changes_made.append('auto_upload_check_interval')
            print("   ✅ Added auto_upload_check_interval")
        else:
            print("   ⚠️  auto_upload_check_interval already exists")
        
        conn.commit()
        
        # ===== MIGRATE GLOBAL CONFIGS TO ADMIN =====
        print("\n📋 Migrating global configs to admin user...")
        
        # Migrate Telegram config
        if os.path.exists('telegram_config.json'):
            try:
                with open('telegram_config.json', 'r') as f:
                    telegram_config = json.load(f)
                
                cursor.execute('''
                    UPDATE users 
                    SET telegram_bot_token = ?,
                        telegram_chat_id = ?,
                        telegram_enabled = ?
                    WHERE username = 'admin'
                ''', (
                    telegram_config.get('bot_token'),
                    telegram_config.get('chat_id'),
                    1 if telegram_config.get('enabled') else 0
                ))
                print("   ✅ Migrated Telegram config to admin")
            except Exception as e:
                print(f"   ⚠️  Could not migrate Telegram config: {e}")
        
        # Migrate Gemini config
        if os.path.exists('gemini_config.json'):
            try:
                with open('gemini_config.json', 'r') as f:
                    gemini_config = json.load(f)
                
                cursor.execute('''
                    UPDATE users 
                    SET gemini_api_key = ?,
                        gemini_model = ?,
                        gemini_custom_prompt = ?
                    WHERE username = 'admin'
                ''', (
                    gemini_config.get('api_key'),
                    gemini_config.get('model', 'gemini-2.0-flash-exp'),
                    gemini_config.get('custom_prompt')
                ))
                print("   ✅ Migrated Gemini config to admin")
            except Exception as e:
                print(f"   ⚠️  Could not migrate Gemini config: {e}")
        
        # Migrate Auto Upload config
        if os.path.exists('auto_upload_config.json'):
            try:
                with open('auto_upload_config.json', 'r') as f:
                    auto_config = json.load(f)
                
                cursor.execute('''
                    UPDATE users 
                    SET auto_upload_enabled = ?,
                        auto_upload_offset_hours = ?,
                        auto_upload_check_interval = ?
                    WHERE username = 'admin'
                ''', (
                    1 if auto_config.get('enabled') else 0,
                    auto_config.get('upload_offset_hours', 2),
                    auto_config.get('check_interval_minutes', 30)
                ))
                print("   ✅ Migrated Auto Upload config to admin")
            except Exception as e:
                print(f"   ⚠️  Could not migrate Auto Upload config: {e}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("  ✅ Migration Complete!")
        print("=" * 60)
        
        if changes_made:
            print(f"\n📝 Added {len(changes_made)} new columns:")
            for col in changes_made:
                print(f"   ✅ {col}")
        else:
            print("\n⚠️  No new columns added (already exist)")
        
        # Show current user configurations
        print("\n📊 Current User Configurations:")
        cursor.execute('''
            SELECT username, 
                   telegram_enabled, telegram_bot_token IS NOT NULL as has_telegram,
                   gemini_api_key IS NOT NULL as has_gemini,
                   auto_upload_enabled
            FROM users 
            ORDER BY is_admin DESC, username
        ''')
        
        print("\n{:<15} {:<10} {:<12} {:<12} {:<12}".format(
            "Username", "Telegram", "Has Bot", "Has Gemini", "Auto Upload"
        ))
        print("-" * 60)
        
        for row in cursor.fetchall():
            username, tg_enabled, has_tg, has_gemini, auto_enabled = row
            tg_status = "✅ Enabled" if tg_enabled else "⚠️  Disabled"
            bot_status = "✅ Yes" if has_tg else "❌ No"
            gemini_status = "✅ Yes" if has_gemini else "❌ No"
            auto_status = "✅ Enabled" if auto_enabled else "⚠️  Disabled"
            
            print("{:<15} {:<10} {:<12} {:<12} {:<12}".format(
                username, tg_status, bot_status, gemini_status, auto_status
            ))
        
        print("\n💡 Next steps:")
        print("   1. Users can configure Telegram bot via /telegram_settings")
        print("   2. Users can configure Gemini API via /gemini-settings")
        print("   3. Users can enable Auto Upload via /bulk-upload-queue")
        
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
