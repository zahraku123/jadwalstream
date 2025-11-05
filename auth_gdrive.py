#!/usr/bin/env python3
"""
Authenticate with Google Drive for backup uploads
"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_gdrive():
    """Authenticate with Google Drive and save credentials"""
    
    creds = None
    token_file = 'gdrive_token.json'
    
    # Check if token file exists
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secret.json'):
                print("Error: client_secret.json not found")
                print("Please download OAuth 2.0 credentials from Google Cloud Console")
                return False
            
            print("\n" + "="*60)
            print("GOOGLE DRIVE AUTHENTICATION")
            print("="*60)
            print("\nPlease follow the instructions below:")
            print("1. Open the URL that will be displayed")
            print("2. Sign in and authorize the application")
            print("3. Copy the authorization code")
            print("4. Paste it back here\n")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            
            # Try to run local server, if fails use console method
            try:
                creds = flow.run_local_server(port=8080, open_browser=False)
            except:
                print("Cannot start local server, using manual method...")
                auth_url, _ = flow.authorization_url(prompt='consent')
                print(f"\nPlease visit this URL to authorize:\n{auth_url}\n")
                code = input("Enter the authorization code: ")
                flow.fetch_token(code=code)
                creds = flow.credentials
        
        # Save credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print(f"\n✓ Authentication successful!")
        print(f"  Token saved to: {token_file}")
    else:
        print("✓ Already authenticated with Google Drive")
    
    return True

if __name__ == "__main__":
    success = authenticate_gdrive()
    
    if success:
        print("\nYou can now upload backups to Google Drive using upload_to_gdrive.py")
    else:
        print("\nAuthentication failed")
        exit(1)
