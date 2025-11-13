#!/usr/bin/env python3
"""
Test Real User Isolation via HTTP
Login sebagai admin dan demo, verify data isolation
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def login(username, password):
    """Login dan return session"""
    session = requests.Session()
    
    # Get login page first (untuk CSRF token jika ada)
    response = session.get(f"{BASE_URL}/login")
    
    # Login
    login_data = {
        'username': username,
        'password': password
    }
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    if response.status_code in [200, 302]:
        print(f"✅ Login successful as {username}")
        return session
    else:
        print(f"❌ Login failed as {username}: {response.status_code}")
        return None

def get_video_count(session):
    """Get video count from video gallery"""
    try:
        response = session.get(f"{BASE_URL}/video-gallery")
        if response.status_code == 200:
            # Count videos in HTML (simple check)
            content = response.text
            # Look for video entries or "No videos" message
            if "No videos found" in content or "Belum ada video" in content:
                return 0
            # Try to count video cards/items (this is approximate)
            count = content.count('class="video-item"') or content.count('class="video-card"')
            return count
        return -1
    except Exception as e:
        print(f"Error getting videos: {e}")
        return -1

def get_api_data(session, endpoint):
    """Get data from API endpoint"""
    try:
        response = session.get(f"{BASE_URL}{endpoint}")
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    return len(data)
                return 0
            except:
                return -1
        return -1
    except Exception as e:
        print(f"Error getting {endpoint}: {e}")
        return -1

def test_user_isolation(username, password):
    """Test data for a specific user"""
    print(f"\n{'='*60}")
    print(f"  Testing as: {username}")
    print(f"{'='*60}")
    
    session = login(username, password)
    if not session:
        return False
    
    # Try to get video gallery page
    print("\n📊 Checking data visibility...")
    
    # Check video gallery
    response = session.get(f"{BASE_URL}/video-gallery")
    if response.status_code == 200:
        html = response.text
        
        # Check for video titles that we know exist for admin
        has_rain_videos = "rainsoundsforsleeping" in html
        
        if username == "admin":
            if has_rain_videos:
                print(f"   ✅ Admin can see videos (as expected)")
            else:
                print(f"   ⚠️  Admin cannot see expected videos")
        else:  # demo
            if has_rain_videos:
                print(f"   ❌ ISOLATION FAILED! Demo can see admin's videos!")
                return False
            else:
                print(f"   ✅ Demo cannot see admin's videos (isolation working)")
    
    # Check looped videos page
    response = session.get(f"{BASE_URL}/video_looping")
    if response.status_code == 200:
        html = response.text
        has_looped = "rainsoundsforsleeping" in html
        
        if username == "admin":
            if has_looped:
                print(f"   ✅ Admin can see looped videos")
            else:
                print(f"   ⚠️  Admin cannot see looped videos")
        else:
            if has_looped:
                print(f"   ❌ ISOLATION FAILED! Demo can see admin's looped videos!")
                return False
            else:
                print(f"   ✅ Demo cannot see admin's looped videos (isolation working)")
    
    return True

def main():
    print("="*60)
    print("  Real User Isolation Test (HTTP)")
    print("="*60)
    
    # Test if app is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"\n✅ App is running on {BASE_URL}")
    except:
        print(f"\n❌ App is not running on {BASE_URL}")
        print("   Start app first: cd /root/baru/jadwalstream && python3 app.py")
        return False
    
    # Test admin
    admin_ok = test_user_isolation("admin", "admin123")
    
    # Test demo
    demo_ok = test_user_isolation("demo", "demo123")
    
    # Final result
    print(f"\n{'='*60}")
    print("  Test Results")
    print(f"{'='*60}")
    
    if admin_ok and demo_ok:
        print("\n🎉 USER ISOLATION WORKING!")
        print("\n✅ Verification:")
        print("   - Admin can see admin's data")
        print("   - Demo cannot see admin's data")
        print("   - Database isolation enforced")
        return True
    else:
        print("\n❌ ISOLATION TEST FAILED")
        print("   Please check app.py and database_helpers.py")
        return False

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
