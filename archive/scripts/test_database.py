#!/usr/bin/env python3
"""
Database Testing Script
Test SQLite database after migration to verify data integrity
"""

import sys
import os
from database import (
    get_database_stats,
    list_all_users,
    get_videos,
    get_thumbnails,
    get_live_streams,
    get_schedules,
    get_looped_videos,
    get_bulk_upload_queue,
    get_stream_mappings
)

def print_separator(char="=", length=60):
    print(char * length)

def test_database_exists():
    """Test if database file exists"""
    print("\n🔍 Test 1: Database File Existence")
    from database import DB_FILE
    
    if os.path.exists(DB_FILE):
        size_mb = os.path.getsize(DB_FILE) / (1024 * 1024)
        print(f"✅ Database file exists: {DB_FILE}")
        print(f"   Size: {size_mb:.2f} MB")
        return True
    else:
        print(f"❌ Database file not found: {DB_FILE}")
        return False

def test_database_stats():
    """Test database statistics"""
    print("\n📊 Test 2: Database Statistics")
    
    try:
        stats = get_database_stats()
        
        print("   Table Statistics:")
        total_records = 0
        for table, count in stats.items():
            if table != 'db_size_mb':
                print(f"   - {table}: {count} records")
                total_records += count
        
        print(f"\n   Total Records: {total_records}")
        
        if 'db_size_mb' in stats:
            print(f"   Database Size: {stats['db_size_mb']} MB")
        
        print("✅ Statistics retrieved successfully")
        return True
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return False

def test_users():
    """Test users table"""
    print("\n👥 Test 3: Users Table")
    
    try:
        users = list_all_users()
        
        if not users:
            print("⚠️  Warning: No users found!")
            return False
        
        print(f"   Found {len(users)} users:")
        for user in users:
            print(f"   - ID {user['id']}: {user['username']} (Role: {user['role']})")
        
        # Check for admin user
        has_admin = any(user['role'] == 'admin' for user in users)
        if has_admin:
            print("✅ Admin user exists")
        else:
            print("⚠️  Warning: No admin user found!")
        
        return True
    except Exception as e:
        print(f"❌ Error testing users: {e}")
        return False

def test_videos(user_id=1):
    """Test videos table"""
    print(f"\n🎬 Test 4: Videos Table (User ID: {user_id})")
    
    try:
        videos = get_videos(user_id)
        
        print(f"   Found {len(videos)} videos")
        
        if videos:
            # Show first 3 videos
            for i, video in enumerate(videos[:3], 1):
                print(f"   {i}. {video['title']}")
                print(f"      File: {video['filename']}")
                print(f"      Source: {video.get('source', 'N/A')}")
            
            if len(videos) > 3:
                print(f"   ... and {len(videos) - 3} more videos")
        
        print("✅ Videos table accessible")
        return True
    except Exception as e:
        print(f"❌ Error testing videos: {e}")
        return False

def test_thumbnails(user_id=1):
    """Test thumbnails table"""
    print(f"\n🖼️  Test 5: Thumbnails Table (User ID: {user_id})")
    
    try:
        thumbnails = get_thumbnails(user_id)
        
        print(f"   Found {len(thumbnails)} thumbnails")
        
        if thumbnails:
            for i, thumb in enumerate(thumbnails[:3], 1):
                print(f"   {i}. {thumb['title']} - {thumb['filename']}")
            
            if len(thumbnails) > 3:
                print(f"   ... and {len(thumbnails) - 3} more thumbnails")
        
        print("✅ Thumbnails table accessible")
        return True
    except Exception as e:
        print(f"❌ Error testing thumbnails: {e}")
        return False

def test_live_streams(user_id=1):
    """Test live streams table"""
    print(f"\n📡 Test 6: Live Streams Table (User ID: {user_id})")
    
    try:
        streams = get_live_streams(user_id)
        
        print(f"   Found {len(streams)} live streams")
        
        if streams:
            for i, stream in enumerate(streams[:3], 1):
                print(f"   {i}. {stream['title']}")
                print(f"      Status: {stream.get('status', 'N/A')}")
                print(f"      Server: {stream.get('server_type', 'N/A')}")
            
            if len(streams) > 3:
                print(f"   ... and {len(streams) - 3} more streams")
        
        print("✅ Live streams table accessible")
        return True
    except Exception as e:
        print(f"❌ Error testing live streams: {e}")
        return False

def test_schedules(user_id=1):
    """Test schedules table"""
    print(f"\n📅 Test 7: Schedules Table (User ID: {user_id})")
    
    try:
        schedules = get_schedules(user_id)
        
        print(f"   Found {len(schedules)} schedules")
        
        if schedules:
            for i, schedule in enumerate(schedules[:3], 1):
                print(f"   {i}. {schedule['title']}")
                print(f"      Time: {schedule.get('scheduled_start_time', 'N/A')}")
                print(f"      Repeat: {'Yes' if schedule.get('repeat_daily') else 'No'}")
            
            if len(schedules) > 3:
                print(f"   ... and {len(schedules) - 3} more schedules")
        
        print("✅ Schedules table accessible")
        return True
    except Exception as e:
        print(f"❌ Error testing schedules: {e}")
        return False

def test_looped_videos(user_id=1):
    """Test looped videos table"""
    print(f"\n🔁 Test 8: Looped Videos Table (User ID: {user_id})")
    
    try:
        looped = get_looped_videos(user_id)
        
        print(f"   Found {len(looped)} looped videos")
        
        if looped:
            completed = sum(1 for v in looped if v.get('status') == 'completed')
            pending = sum(1 for v in looped if v.get('status') == 'pending')
            print(f"   - Completed: {completed}")
            print(f"   - Pending: {pending}")
        
        print("✅ Looped videos table accessible")
        return True
    except Exception as e:
        print(f"❌ Error testing looped videos: {e}")
        return False

def test_bulk_upload_queue(user_id=1):
    """Test bulk upload queue table"""
    print(f"\n📤 Test 9: Bulk Upload Queue Table (User ID: {user_id})")
    
    try:
        queue = get_bulk_upload_queue(user_id)
        
        print(f"   Found {len(queue)} items in queue")
        
        if queue:
            queued = sum(1 for item in queue if item.get('status') == 'queued')
            uploaded = sum(1 for item in queue if item.get('status') == 'uploaded')
            failed = sum(1 for item in queue if item.get('status') == 'failed')
            
            print(f"   - Queued: {queued}")
            print(f"   - Uploaded: {uploaded}")
            print(f"   - Failed: {failed}")
        
        print("✅ Bulk upload queue table accessible")
        return True
    except Exception as e:
        print(f"❌ Error testing bulk upload queue: {e}")
        return False

def test_stream_mappings(user_id=1):
    """Test stream mappings table"""
    print(f"\n🔑 Test 10: Stream Mappings Table (User ID: {user_id})")
    
    try:
        mappings = get_stream_mappings(user_id)
        
        total_streams = sum(len(streams) for streams in mappings.values())
        
        print(f"   Found {len(mappings)} token files with {total_streams} stream mappings")
        
        if mappings:
            for token_file, streams in list(mappings.items())[:3]:
                print(f"   - {token_file}: {len(streams)} streams")
        
        print("✅ Stream mappings table accessible")
        return True
    except Exception as e:
        print(f"❌ Error testing stream mappings: {e}")
        return False

def test_user_isolation():
    """Test user data isolation"""
    print("\n🔒 Test 11: User Data Isolation")
    
    try:
        users = list_all_users()
        
        if len(users) < 2:
            print("⚠️  Need at least 2 users to test isolation")
            return True
        
        user1_id = users[0]['id']
        user2_id = users[1]['id']
        
        videos1 = get_videos(user1_id)
        videos2 = get_videos(user2_id)
        
        print(f"   User {user1_id} ({users[0]['username']}): {len(videos1)} videos")
        print(f"   User {user2_id} ({users[1]['username']}): {len(videos2)} videos")
        
        # Check if videos are isolated
        if videos1 and videos2:
            video1_ids = {v['id'] for v in videos1}
            video2_ids = {v['id'] for v in videos2}
            
            overlap = video1_ids & video2_ids
            if overlap:
                print(f"❌ Data leak detected! {len(overlap)} videos shared between users")
                return False
        
        print("✅ User data isolation working correctly")
        return True
    except Exception as e:
        print(f"❌ Error testing isolation: {e}")
        return False

def run_all_tests():
    """Run all database tests"""
    print_separator("=", 60)
    print("  SQLite Database Test Suite")
    print("  JadwalStream Application")
    print_separator("=", 60)
    
    tests = [
        test_database_exists,
        test_database_stats,
        test_users,
        test_videos,
        test_thumbnails,
        test_live_streams,
        test_schedules,
        test_looped_videos,
        test_bulk_upload_queue,
        test_stream_mappings,
        test_user_isolation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print_separator("=", 60)
    print("  Test Summary")
    print_separator("=", 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Database is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
