#!/usr/bin/env python3
"""Check auto upload configuration in database"""
import sys
sys.path.insert(0, '/root/baru/jadwalstream')

from database import get_db_connection

print("=== Auto Upload Configuration ===")
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, auto_upload_enabled, 
               auto_upload_offset_hours, auto_upload_check_interval 
        FROM users
    ''')
    
    for row in cursor.fetchall():
        user = dict(row)
        enabled = "✓ ENABLED" if user['auto_upload_enabled'] else "✗ DISABLED"
        print(f"\nUser ID {user['id']} ({user['username']}):")
        print(f"  Status: {enabled}")
        print(f"  Upload offset: {user['auto_upload_offset_hours']} hours")
        print(f"  Check interval: {user['auto_upload_check_interval']} minutes")

print("\n=== Auto Upload Queue ===")
from database import get_bulk_upload_queue

for user_id in [1, 2, 3]:
    try:
        queue = get_bulk_upload_queue(user_id)
        if queue:
            print(f"\nUser ID {user_id}: {len(queue)} items in queue")
            queued = [item for item in queue if item['status'] == 'queued']
            print(f"  - Queued: {len(queued)}")
            if queued:
                for item in queued[:3]:
                    print(f"    • {item['title']} - scheduled: {item.get('scheduled_publish_time', 'N/A')}")
    except:
        pass

print("\n=== Done ===")
