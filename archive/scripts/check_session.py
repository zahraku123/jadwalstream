#!/usr/bin/env python3
"""Check current session and user context"""
from flask import Flask
from flask_login import current_user
import sys
sys.path.insert(0, '/root/baru/jadwalstream')

# Import app
from app import app

with app.app_context():
    with app.test_request_context():
        print("Testing user context...")
        print(f"current_user authenticated: {hasattr(current_user, 'is_authenticated')}")
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            print(f"User ID: {current_user.id}")
            print(f"Username: {current_user.username}")
        else:
            print("No authenticated user in test context")

# Check database_helpers
from database_helpers import get_current_user_id
print(f"\nget_current_user_id() returns: {get_current_user_id()}")

# Test dengan user context
from user_auth import get_user_by_id
user = get_user_by_id(1)
print(f"\nUser 1 (admin): {user}")
