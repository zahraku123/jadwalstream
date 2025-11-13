#!/usr/bin/env python3
"""
Test YouTube API page with login
"""

import requests

BASE_URL = "http://localhost:5000"

# Login
session = requests.Session()
response = session.post(f"{BASE_URL}/login", data={
    'username': 'admin',
    'password': 'admin123'
})

print(f"Login status: {response.status_code}")

# Try to access YouTube API page
response = session.get(f"{BASE_URL}/settings/youtube-api")
print(f"YouTube API page status: {response.status_code}")

if response.status_code != 200:
    print("\n=== Response content ===")
    print(response.text[:500])
    
    # Check if there's an error
    if "Error" in response.text or "Traceback" in response.text:
        print("\n=== Full error ===")
        print(response.text)
else:
    print("✅ Page loaded successfully!")
    
    # Check for specific elements
    if "YouTube API" in response.text:
        print("✅ Title found")
    if "Upload" in response.text:
        print("✅ Upload form found")
