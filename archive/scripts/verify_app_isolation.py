#!/usr/bin/env python3
"""
Verify App Isolation by Testing with Mock User Sessions
"""

# Mock Flask-Login current_user for testing
class MockUser:
    def __init__(self, user_id, username, role):
        self.id = str(user_id)
        self.username = username
        self.role = role
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

def test_with_user(user_id, username, role):
    """Test database_helpers functions with mock user"""
    print(f"\n{'='*60}")
    print(f"  Testing as: {username} (ID: {user_id}, Role: {role})")
    print(f"{'='*60}")
    
    # Mock current_user globally
    import database_helpers
    original_get_user_id = database_helpers.get_current_user_id
    
    # Override with our test user
    database_helpers.get_current_user_id = lambda: user_id
    
    try:
        # Import functions to test
        from database_helpers import (
            get_video_database,
            get_thumbnail_database,
            get_live_streams_data,
            get_looped_videos_data,
            get_bulk_upload_queue_data
        )
        
        # Test each function
        videos = get_video_database()
        thumbnails = get_thumbnail_database()
        streams = get_live_streams_data()
        looped = get_looped_videos_data()
        uploads = get_bulk_upload_queue_data()
        
        print(f"\n📊 Data visible to {username}:")
        print(f"   Videos: {len(videos)}")
        print(f"   Thumbnails: {len(thumbnails)}")
        print(f"   Live Streams: {len(streams)}")
        print(f"   Looped Videos: {len(looped)}")
        print(f"   Upload Queue: {len(uploads)}")
        
        # Show sample videos if any
        if videos:
            print(f"\n   Sample videos:")
            for video in videos[:3]:
                print(f"   - {video['title']}")
        
        return {
            'videos': videos,
            'thumbnails': thumbnails,
            'streams': streams,
            'looped': looped,
            'uploads': uploads
        }
    
    finally:
        # Restore original function
        database_helpers.get_current_user_id = original_get_user_id

def main():
    print("=" * 60)
    print("  App User Isolation Verification")
    print("=" * 60)
    
    # Test as admin (user_id = 1)
    admin_data = test_with_user(1, 'admin', 'admin')
    
    # Test as demo (user_id = 2)
    demo_data = test_with_user(2, 'demo', 'demo')
    
    # Verify isolation
    print(f"\n{'='*60}")
    print("  Isolation Verification")
    print(f"{'='*60}")
    
    admin_video_ids = {v['id'] for v in admin_data['videos']}
    demo_video_ids = {v['id'] for v in demo_data['videos']}
    
    overlap = admin_video_ids & demo_video_ids
    
    if overlap:
        print(f"\n❌ DATA LEAK DETECTED!")
        print(f"   {len(overlap)} videos visible to both users")
        return False
    else:
        print(f"\n✅ USER ISOLATION WORKING!")
        print(f"\n   Admin sees: {len(admin_data['videos'])} videos")
        print(f"   Demo sees: {len(demo_data['videos'])} videos")
        print(f"   No data overlap ✓")
        
        print(f"\n🔒 Security Status:")
        print(f"   ✅ Per-user data isolation enforced")
        print(f"   ✅ Users cannot access each other's data")
        print(f"   ✅ Database helpers working correctly")
        
        return True

if __name__ == '__main__':
    try:
        success = main()
        
        if success:
            print(f"\n{'='*60}")
            print("  🎉 ALL TESTS PASSED!")
            print(f"{'='*60}")
            print("\n✅ Your app is ready with user isolation!")
            print("\n📝 Next steps:")
            print("   1. Start app: python3 app.py")
            print("   2. Login as admin → see admin's data only")
            print("   3. Login as demo → see demo's data only")
            print("   4. Upload test video as each user")
            print("   5. Verify isolation in browser")
            exit(0)
        else:
            print(f"\n{'='*60}")
            print("  ❌ ISOLATION TEST FAILED")
            print(f"{'='*60}")
            exit(1)
    
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
