#!/usr/bin/env python3
"""
Test all pages that show tokens to verify per-user isolation
"""

import requests
import re

BASE_URL = "http://localhost:5000"

def get_tokens_from_page(session, url, page_name):
    """Extract token names from a page"""
    resp = session.get(url)
    if resp.status_code != 200:
        print(f"   ❌ Cannot access {page_name} (status: {resp.status_code})")
        return None
    
    # Look for token files in various formats
    # Method 1: In select dropdowns
    tokens_dropdown = re.findall(r'<option[^>]*>([^<]+\.json)</option>', resp.text)
    
    # Method 2: In table cells
    tokens_table = re.findall(r'<td[^>]*>([a-zA-Z0-9_]+\.json)</td>', resp.text)
    
    # Method 3: In any text content
    tokens_any = re.findall(r'(\w+_channel\.json)', resp.text)
    
    # Combine all found tokens
    all_tokens = set(tokens_dropdown + tokens_table + tokens_any)
    
    # Filter out common files
    excluded = {'client_secret.json', 'package.json', 'token.json'}
    tokens = [t for t in all_tokens if t not in excluded]
    
    return tokens

def test_user_pages(username, password):
    """Test all pages for a user"""
    print(f"\n{'='*60}")
    print(f"  Testing: {username}")
    print(f"{'='*60}")
    
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/login", data={
        'username': username,
        'password': password
    })
    
    if resp.status_code != 200:
        print(f"❌ Login failed")
        return {}
    
    print(f"✅ Login successful")
    
    pages = {
        'Home': '/',
        'Tokens': '/tokens',
        'Schedules': '/schedules',
        'Stream Keys': '/stream_keys',
        'Looped Videos': '/looped_videos'
    }
    
    results = {}
    
    for page_name, url in pages.items():
        print(f"\n   Checking {page_name}...")
        tokens = get_tokens_from_page(session, f"{BASE_URL}{url}", page_name)
        if tokens is not None:
            print(f"   Tokens found: {tokens if tokens else '(none)'}")
            results[page_name] = tokens
        else:
            results[page_name] = None
    
    return results

def main():
    print("="*60)
    print("  TOKEN ISOLATION - ALL PAGES TEST")
    print("="*60)
    
    admin_results = test_user_pages('admin', 'admin123')
    demo_results = test_user_pages('demo', 'demo123')
    
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    
    all_pass = True
    
    for page_name in ['Home', 'Tokens', 'Schedules', 'Stream Keys', 'Looped Videos']:
        admin_tokens = set(admin_results.get(page_name, []) or [])
        demo_tokens = set(demo_results.get(page_name, []) or [])
        
        print(f"\n{page_name}:")
        print(f"  Admin: {admin_tokens if admin_tokens else '(none)'}")
        print(f"  Demo: {demo_tokens if demo_tokens else '(none)'}")
        
        if admin_tokens and demo_tokens:
            overlap = admin_tokens & demo_tokens
            if overlap:
                print(f"  ❌ FAIL: Same tokens visible: {overlap}")
                all_pass = False
            else:
                print(f"  ✅ PASS: Different tokens, no overlap")
        elif not admin_tokens and not demo_tokens:
            print(f"  ✅ PASS: Both see no tokens (empty)")
        else:
            print(f"  ✅ PASS: Isolated")
    
    print("\n" + "="*60)
    if all_pass:
        print("  ✅ ALL TESTS PASSED")
        print("  🔒 Token isolation working on all pages!")
    else:
        print("  ❌ SOME TESTS FAILED")
        print("  ⚠️  Check the results above")
    print("="*60)

if __name__ == '__main__':
    main()
