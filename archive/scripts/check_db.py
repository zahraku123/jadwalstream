#!/usr/bin/env python3
import sqlite3
import sys

db_file = 'jadwalstream.db'

try:
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*60)
    print("DATABASE CHECK")
    print("="*60)
    
    # Check users
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    print(f"\n📊 USERS ({len(users)}):")
    for user in users:
        print(f"   - ID: {user['id']}, Username: {user['username']}")
    
    # Check schedules
    cursor.execute("SELECT COUNT(*) as total FROM schedules")
    schedules_count = cursor.fetchone()['total']
    print(f"\n📅 SCHEDULES: {schedules_count} total")
    
    if schedules_count > 0:
        cursor.execute("SELECT id, user_id, title, scheduled_start_time, success FROM schedules ORDER BY id DESC LIMIT 5")
        schedules = cursor.fetchall()
        print("   Latest 5:")
        for s in schedules:
            print(f"   - ID:{s['id']} User:{s['user_id']} Title:'{s['title']}' Time:{s['scheduled_start_time']} Success:{s['success']}")
    
    # Check videos
    cursor.execute("SELECT COUNT(*) as total FROM videos")
    videos_count = cursor.fetchone()['total']
    print(f"\n🎥 VIDEOS: {videos_count} total")
    
    if videos_count > 0:
        cursor.execute("SELECT id, user_id, title, filename FROM videos ORDER BY date_added DESC LIMIT 5")
        videos = cursor.fetchall()
        print("   Latest 5:")
        for v in videos:
            print(f"   - ID:{v['id']} User:{v['user_id']} Title:'{v['title']}' File:{v['filename']}")
    
    # Check thumbnails
    cursor.execute("SELECT COUNT(*) as total FROM thumbnails")
    thumbnails_count = cursor.fetchone()['total']
    print(f"\n🖼️  THUMBNAILS: {thumbnails_count} total")
    
    if thumbnails_count > 0:
        cursor.execute("SELECT id, user_id, title, filename FROM thumbnails ORDER BY date_added DESC LIMIT 5")
        thumbnails = cursor.fetchall()
        print("   Latest 5:")
        for t in thumbnails:
            print(f"   - ID:{t['id']} User:{t['user_id']} Title:'{t['title']}' File:{t['filename']}")
    
    # Check live streams
    cursor.execute("SELECT COUNT(*) as total FROM live_streams")
    streams_count = cursor.fetchone()['total']
    print(f"\n📡 LIVE STREAMS: {streams_count} total")
    
    if streams_count > 0:
        cursor.execute("SELECT id, user_id, title, status FROM live_streams ORDER BY created_at DESC LIMIT 5")
        streams = cursor.fetchall()
        print("   Latest 5:")
        for st in streams:
            print(f"   - ID:{st['id']} User:{st['user_id']} Title:'{st['title']}' Status:{st['status']}")
    
    print("\n" + "="*60)
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
