#!/usr/bin/env python3
"""Test bulk upload queue functionality"""
import sys
sys.path.insert(0, '/root/baru/jadwalstream')

from database import get_bulk_upload_queue, get_all_users

print("=== Testing Bulk Upload Queue ===\n")

# Get all users
users = get_all_users()

print(f"Total users: {len(users)}\n")

for user in users:
    user_id = user['id']
    username = user['username']
    
    print(f"User: {username} (ID: {user_id})")
    
    try:
        queue = get_bulk_upload_queue(user_id)
        print(f"  Queue items: {len(queue)}")
        
        if queue:
            for i, item in enumerate(queue[:3], 1):
                print(f"  {i}. {item['title'][:60]}")
                print(f"     Status: {item['status']}")
                print(f"     Scheduled: {item.get('scheduled_publish_time', 'N/A')}")
        else:
            print("  (empty queue)")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()

print("=== Done ===")
