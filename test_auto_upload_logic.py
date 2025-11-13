#!/usr/bin/env python3
"""Test auto upload logic"""
import sys
sys.path.insert(0, '/root/baru/jadwalstream')

from datetime import datetime, timedelta
import pytz
from database import get_bulk_upload_queue, get_all_users

TIMEZONE = 'Asia/Jakarta'

print("=== Testing Auto Upload Logic ===")

# Get current time
now = datetime.now(pytz.timezone(TIMEZONE))
print(f"\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# Get users
users = get_all_users()
print(f"\nTotal users: {len(users)}")

for user in users:
    user_id = user['id']
    username = user['username']
    
    # Get queue
    queue = get_bulk_upload_queue(user_id)
    queued_items = [item for item in queue if item['status'] == 'queued']
    
    if not queued_items:
        continue
    
    print(f"\n=== User: {username} (ID: {user_id}) ===")
    print(f"Queued items: {len(queued_items)}")
    
    # Check each item
    upload_offset = timedelta(hours=2)
    
    for i, item in enumerate(queued_items[:3], 1):
        print(f"\n{i}. {item['title']}")
        print(f"   Scheduled publish: {item.get('scheduled_publish_time', 'N/A')}")
        
        try:
            # Parse scheduled publish time
            scheduled_time = datetime.strptime(item['scheduled_publish_time'], '%Y-%m-%d %H:%M:%S')
            scheduled_time = pytz.timezone(TIMEZONE).localize(scheduled_time)
            
            # Calculate when to upload (X hours before publish time)
            upload_time = scheduled_time - upload_offset
            
            print(f"   Upload time: {upload_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Time diff: {(now - upload_time).total_seconds() / 3600:.2f} hours")
            
            # Check if should upload
            if now >= upload_time:
                print(f"   ✓ SHOULD UPLOAD NOW (scheduled time passed)")
            else:
                hours_until = (upload_time - now).total_seconds() / 3600
                print(f"   ✗ Not yet ({hours_until:.2f} hours until upload time)")
        except Exception as e:
            print(f"   ✗ Error parsing: {e}")

print("\n=== Done ===")
