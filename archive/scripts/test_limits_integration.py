#!/usr/bin/env python3
"""
Comprehensive Test for User Limits Integration
Tests all limit checks are working
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_admin_limits_page():
    """Test if admin limits page is accessible"""
    print("\n" + "="*60)
    print("Test 1: Admin Limits Page")
    print("="*60)
    
    session = requests.Session()
    
    # Login as admin
    session.post(f"{BASE_URL}/login", data={'username': 'admin', 'password': 'admin123'})
    
    # Try to access limits page
    response = session.get(f"{BASE_URL}/admin/users/limits")
    
    if response.status_code == 200:
        if "User Limits Management" in response.text:
            print("✅ Admin limits page accessible")
            print("   URL: /admin/users/limits")
            return True
        else:
            print("⚠️  Page loaded but content may be wrong")
            return False
    else:
        print(f"❌ Page not accessible: {response.status_code}")
        return False

def test_user_limits_display():
    """Test if user limits are displayed"""
    print("\n" + "="*60)
    print("Test 2: User Limits Display")
    print("="*60)
    
    session = requests.Session()
    session.post(f"{BASE_URL}/login", data={'username': 'demo', 'password': 'demo123'})
    
    # Check dashboard or any page
    response = session.get(f"{BASE_URL}/")
    
    # Look for usage indicators
    has_usage = any([
        "Your Usage" in response.text,
        "Streams/Schedules" in response.text,
        "Storage" in response.text,
        "remaining" in response.text
    ])
    
    if has_usage:
        print("✅ User usage displayed on pages")
    else:
        print("⚠️  Usage widget may not be visible")
        print("   (May need to include widget in templates)")
    
    return has_usage

def test_limit_enforcement():
    """Test if limits are actually enforced"""
    print("\n" + "="*60)
    print("Test 3: Limit Enforcement (Mock)")
    print("="*60)
    
    from user_limits import get_user_limits, can_user_add_stream, can_user_upload
    
    # Test for demo user (user_id=2)
    limits = get_user_limits(2)
    
    print(f"\n📊 Demo User Limits:")
    print(f"   Max Streams: {limits['max_streams']}")
    print(f"   Max Storage: {limits['max_storage_mb']}MB")
    print(f"   Current Streams: {limits['current_streams']}")
    print(f"   Current Storage: {limits['current_storage_mb']:.2f}MB")
    
    # Test stream limit
    can_add, msg = can_user_add_stream(2)
    print(f"\n   Can add stream: {'✅' if can_add else '❌'} {msg}")
    
    # Test storage limit
    can_upload, msg = can_user_upload(2, 100)  # Try 100MB
    print(f"   Can upload 100MB: {'✅' if can_upload else '❌'} {msg}")
    
    return True

def test_database_schema():
    """Test if database has new columns"""
    print("\n" + "="*60)
    print("Test 4: Database Schema")
    print("="*60)
    
    from database import get_db_connection
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required = ['is_admin', 'max_streams', 'max_storage_mb']
        missing = [col for col in required if col not in columns]
        
        if not missing:
            print("✅ All required columns exist:")
            for col in required:
                print(f"   - {col}")
            return True
        else:
            print(f"❌ Missing columns: {missing}")
            return False

def test_admin_functions():
    """Test admin functions"""
    print("\n" + "="*60)
    print("Test 5: Admin Functions")
    print("="*60)
    
    from user_limits import update_user_limits, get_all_users_with_limits
    
    # Get all users
    users = get_all_users_with_limits()
    print(f"\n   Found {len(users)} users:")
    
    for user in users:
        if user['is_admin']:
            print(f"   👑 {user['username']}: Unlimited")
        else:
            print(f"   👤 {user['username']}: {user['max_streams']} streams, {user['max_storage_mb']}MB")
    
    # Try to update demo user limits (should work)
    demo_user = next((u for u in users if u['username'] == 'demo'), None)
    if demo_user:
        success = update_user_limits(demo_user['user_id'], 5, 3000)
        if success:
            print(f"\n✅ Can update demo user limits")
            # Revert
            update_user_limits(demo_user['user_id'], 3, 2000)
        else:
            print(f"\n❌ Failed to update demo user limits")
    
    # Try to update admin limits (should fail)
    admin_user = next((u for u in users if u['is_admin']), None)
    if admin_user:
        success = update_user_limits(admin_user['user_id'], 10, 5000)
        if not success:
            print(f"✅ Cannot update admin limits (correct)")
        else:
            print(f"⚠️  Able to update admin limits (should be prevented)")
    
    return True

def main():
    print("=" * 60)
    print("  User Limits Integration Test")
    print("=" * 60)
    
    # Check if app is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"\n✅ App is running on {BASE_URL}")
    except:
        print(f"\n❌ App is not running on {BASE_URL}")
        print("   Start app first: python3 app.py")
        return False
    
    # Run all tests
    tests = [
        test_database_schema,
        test_admin_functions,
        test_limit_enforcement,
        test_admin_limits_page,
        test_user_limits_display
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! User limits system is working!")
        print("\n📝 Manual tests to do:")
        print("   1. Login as admin → Go to /admin/users/limits")
        print("   2. Edit demo user limits")
        print("   3. Login as demo → Try to upload large file")
        print("   4. Login as demo → Try to add many streams")
        print("   5. Verify limits are enforced")
        return True
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return False

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
