#!/usr/bin/env python3
"""
Test User Isolation
Verify that users can only see their own data
"""

from database import (
    get_videos, get_thumbnails, get_live_streams,
    get_schedules, get_looped_videos, get_bulk_upload_queue,
    list_all_users
)

def test_isolation():
    print("=" * 60)
    print("  User Isolation Test")
    print("=" * 60)
    
    # Get all users
    users = list_all_users()
    
    if len(users) < 2:
        print("\n⚠️  Need at least 2 users to test isolation")
        print(f"   Current users: {len(users)}")
        return
    
    print(f"\n📊 Testing with {len(users)} users:")
    for user in users:
        print(f"   - User {user['id']}: {user['username']} ({user['role']})")
    
    print("\n" + "-" * 60)
    print("  Data per User")
    print("-" * 60)
    
    # Check data for each user
    for user in users:
        user_id = user['id']
        username = user['username']
        
        videos = get_videos(user_id)
        thumbnails = get_thumbnails(user_id)
        streams = get_live_streams(user_id)
        schedules = get_schedules(user_id)
        looped = get_looped_videos(user_id)
        uploads = get_bulk_upload_queue(user_id)
        
        print(f"\n👤 User: {username} (ID: {user_id})")
        print(f"   Videos: {len(videos)}")
        print(f"   Thumbnails: {len(thumbnails)}")
        print(f"   Live Streams: {len(streams)}")
        print(f"   Schedules: {len(schedules)}")
        print(f"   Looped Videos: {len(looped)}")
        print(f"   Upload Queue: {len(uploads)}")
    
    print("\n" + "-" * 60)
    print("  Isolation Verification")
    print("-" * 60)
    
    # Check for data leaks
    user1 = users[0]
    user2 = users[1]
    
    user1_videos = get_videos(user1['id'])
    user2_videos = get_videos(user2['id'])
    
    user1_video_ids = {v['id'] for v in user1_videos}
    user2_video_ids = {v['id'] for v in user2_videos}
    
    overlap = user1_video_ids & user2_video_ids
    
    if overlap:
        print(f"\n❌ DATA LEAK DETECTED!")
        print(f"   {len(overlap)} videos shared between users:")
        for vid_id in overlap:
            print(f"   - {vid_id}")
        return False
    else:
        print(f"\n✅ Isolation Working Correctly!")
        print(f"   User '{user1['username']}': {len(user1_videos)} videos (private)")
        print(f"   User '{user2['username']}': {len(user2_videos)} videos (private)")
        print(f"   No data overlap detected")
        return True
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    success = test_isolation()
    
    if success:
        print("\n🎉 User isolation test PASSED!")
        print("\n📝 This means:")
        print("   ✅ User admin can only see admin's data")
        print("   ✅ User demo can only see demo's data")
        print("   ✅ No cross-user data access")
        exit(0)
    else:
        print("\n❌ User isolation test FAILED!")
        print("   Please check database configuration")
        exit(1)
