#!/usr/bin/env python3
"""
Complete Google Drive Authentication with authorization code
"""
import sys
import json
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import Flow

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def complete_authentication(redirect_url):
    """Complete authentication with redirect URL"""
    
    # Parse the redirect URL to get the code
    parsed = urlparse(redirect_url)
    query_params = parse_qs(parsed.query)
    
    if 'code' not in query_params:
        print("Error: No authorization code found in URL")
        print("Make sure you copied the complete redirect URL")
        return False
    
    code = query_params['code'][0]
    print(f"Authorization code extracted: {code[:20]}...")
    
    # Load client secrets
    with open('client_secret.json', 'r') as f:
        client_config = json.load(f)
    
    # Load saved state
    try:
        with open('.gdrive_auth_state.json', 'r') as f:
            auth_state = json.load(f)
    except:
        auth_state = {'redirect_uri': 'http://localhost:8080'}
    
    # Create flow
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=auth_state.get('redirect_uri', 'http://localhost:8080')
    )
    
    # Exchange code for token
    print("Exchanging authorization code for token...")
    flow.fetch_token(code=code)
    
    creds = flow.credentials
    
    # Save credentials
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    with open('gdrive_token.json', 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print()
    print("="*70)
    print("✓ Authentication successful!")
    print("="*70)
    print(f"Token saved to: gdrive_token.json")
    print()
    print("You can now upload backups to Google Drive:")
    print("  python3 upload_to_gdrive.py")
    print()
    
    # Cleanup
    try:
        import os
        os.remove('.gdrive_auth_state.json')
    except:
        pass
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 complete_auth_gdrive.py 'http://localhost:8080/?code=...'")
        print()
        print("If you haven't generated the auth URL yet, run:")
        print("  python3 simple_auth_gdrive.py")
        sys.exit(1)
    
    redirect_url = sys.argv[1]
    success = complete_authentication(redirect_url)
    
    if not success:
        sys.exit(1)
