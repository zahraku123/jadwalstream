#!/usr/bin/env python3
"""
Simple Google Drive Authentication - Generate URL only
"""
import json
from google_auth_oauthlib.flow import Flow

# Scopes for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def generate_auth_url():
    """Generate authentication URL"""
    
    # Load client secrets
    with open('client_secret.json', 'r') as f:
        client_config = json.load(f)
    
    # Create flow
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri='http://localhost:8080'
    )
    
    # Generate authorization URL
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    
    print("="*70)
    print("GOOGLE DRIVE AUTHENTICATION")
    print("="*70)
    print()
    print("STEP 1: Open this URL in your browser:")
    print()
    print(auth_url)
    print()
    print("="*70)
    print()
    print("STEP 2: After authorization, you will be redirected to a URL like:")
    print("http://localhost:8080/?code=4/0AdLIr...")
    print()
    print("STEP 3: Copy the FULL URL and run:")
    print("python3 complete_auth_gdrive.py 'PASTE_FULL_URL_HERE'")
    print()
    print("="*70)
    
    # Save state for later
    with open('.gdrive_auth_state.json', 'w') as f:
        json.dump({'state': state, 'redirect_uri': 'http://localhost:8080'}, f)
    
    return auth_url

if __name__ == "__main__":
    generate_auth_url()
