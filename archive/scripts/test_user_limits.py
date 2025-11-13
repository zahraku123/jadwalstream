#!/usr/bin/env python3
"""
Test User Limits System
"""

from user_limits import (
    get_user_limits,
    can_user_add_stream,
    can_user_upload,
    get_all_users_with_limits,
    format_storage,
    format_count
)

def test_limits():
    print("=" * 60)
    print("  User Limits System Test")
    print("=" * 60)
    
    # Get all users
    print("\n📊 All Users with Limits:")
    users = get_all_users_with_limits()
    
    for user in users:
        print(f"\n{'='*60}")
        if user['is_admin']:
            print(f"👑 {user['username']} (Admin)")
            print(f"   Streams: {user['current_streams']} (Unlimited)")
            print(f"   Storage: {format_storage(user['current_storage_mb'])}")
        else:
            print(f"👤 {user['username']}")
            print(f"   Streams: {format_count(user['current_streams'], user['max_streams'])}")
            print(f"   Storage: {format_storage(user['current_storage_mb'])} / {format_storage(user['max_storage_mb'])}")
            
            # Check permissions
            can_stream, stream_msg = can_user_add_stream(user['user_id'])
            can_up, upload_msg = can_user_upload(user['user_id'], 100)  # Test 100MB upload
            
            print(f"\n   Can add stream: {'✅' if can_stream else '❌'} {stream_msg}")
            print(f"   Can upload 100MB: {'✅' if can_up else '❌'} {upload_msg}")
    
    print("\n" + "=" * 60)
    print("  ✅ Test Complete")
    print("=" * 60)

if __name__ == '__main__':
    test_limits()
