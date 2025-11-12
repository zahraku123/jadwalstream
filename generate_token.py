#!/usr/bin/env python3
"""
Token Generator for Multiple YouTube API Projects
Creates OAuth tokens for different Google Cloud Projects

Usage:
    python3 generate_token.py <token_name> <credentials_file>
    
Example:
    python3 generate_token.py project2 client_secret_project2.json
"""

import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# YouTube API scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

TOKENS_FOLDER = 'tokens'

def create_token(token_name, credentials_file):
    """
    Create a new OAuth token for YouTube API
    
    Args:
        token_name: Name for the token file (e.g., 'project2')
        credentials_file: Path to client_secret.json file
    """
    
    # Ensure tokens folder exists
    os.makedirs(TOKENS_FOLDER, exist_ok=True)
    
    # Check if credentials file exists
    if not os.path.exists(credentials_file):
        print(f"❌ Error: Credentials file not found: {credentials_file}")
        print("\nPlease download OAuth 2.0 credentials from:")
        print("https://console.cloud.google.com/apis/credentials")
        return False
    
    token_file = os.path.join(TOKENS_FOLDER, f'{token_name}.json')
    
    # Check if token already exists
    if os.path.exists(token_file):
        print(f"⚠️  Warning: Token file already exists: {token_file}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return False
    
    print(f"\n🔑 Creating token: {token_name}")
    print(f"📄 Using credentials: {credentials_file}")
    print("\n" + "="*60)
    
    try:
        # Run OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file,
            SCOPES
        )
        
        # Use local server method (opens browser automatically)
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',
            success_message='Authorization successful! You can close this window.'
        )
        
        # Save the credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print("\n" + "="*60)
        print(f"✅ Token created successfully!")
        print(f"📁 Saved to: {token_file}")
        
        # Test the token
        print("\n🧪 Testing token...")
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Get channel info
        request = youtube.channels().list(
            part='snippet,statistics',
            mine=True
        )
        response = request.execute()
        
        if response.get('items'):
            channel = response['items'][0]
            snippet = channel['snippet']
            stats = channel['statistics']
            
            print("\n✅ Token is valid!")
            print(f"📺 Channel: {snippet['title']}")
            print(f"👥 Subscribers: {stats.get('subscriberCount', 'Hidden')}")
            print(f"📹 Videos: {stats.get('videoCount', '0')}")
            print(f"👁️  Views: {stats.get('viewCount', '0')}")
        else:
            print("⚠️  Token created but couldn't fetch channel info")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating token: {e}")
        print("\nCommon issues:")
        print("1. OAuth consent screen not configured")
        print("2. Test user not added (if using External user type)")
        print("3. YouTube Data API v3 not enabled")
        print("4. Invalid credentials file")
        return False

def list_tokens():
    """List all existing tokens"""
    if not os.path.exists(TOKENS_FOLDER):
        print("No tokens folder found.")
        return
    
    tokens = [f for f in os.listdir(TOKENS_FOLDER) if f.endswith('.json')]
    
    if not tokens:
        print("No tokens found.")
        return
    
    print("\n📋 Existing tokens:")
    print("="*60)
    
    for token_file in sorted(tokens):
        token_name = token_file.replace('.json', '')
        token_path = os.path.join(TOKENS_FOLDER, token_file)
        
        # Try to load and test token
        try:
            creds = Credentials.from_authorized_user_file(
                token_path,
                SCOPES
            )
            
            # Check if token is valid
            if creds and creds.valid:
                status = "✅ Valid"
            elif creds and creds.expired and creds.refresh_token:
                status = "🔄 Expired (can refresh)"
            else:
                status = "❌ Invalid"
            
            print(f"  {token_name:20} {status}")
            
        except Exception as e:
            print(f"  {token_name:20} ❌ Error: {str(e)[:30]}")
    
    print("="*60)

def test_token(token_name):
    """Test if a token is working"""
    token_file = os.path.join(TOKENS_FOLDER, f'{token_name}.json')
    
    if not os.path.exists(token_file):
        print(f"❌ Token not found: {token_file}")
        return False
    
    print(f"\n🧪 Testing token: {token_name}")
    print("="*60)
    
    try:
        creds = Credentials.from_authorized_user_file(
            token_file,
            SCOPES
        )
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            print("🔄 Token expired, refreshing...")
            creds.refresh(Request())
            
            # Save refreshed token
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            print("✅ Token refreshed!")
        
        # Test with YouTube API
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Get channel info
        request = youtube.channels().list(
            part='snippet,statistics',
            mine=True
        )
        response = request.execute()
        
        if response.get('items'):
            channel = response['items'][0]
            snippet = channel['snippet']
            stats = channel['statistics']
            
            print("\n✅ Token is working!")
            print(f"📺 Channel: {snippet['title']}")
            print(f"👥 Subscribers: {stats.get('subscriberCount', 'Hidden')}")
            print(f"📹 Videos: {stats.get('videoCount', '0')}")
            print(f"👁️  Views: {stats.get('viewCount', '0')}")
            
            # Check quota usage
            print("\n📊 Quota Info:")
            print("Check usage at: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas")
            
            return True
        else:
            print("❌ No channel found")
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing token: {e}")
        return False

def print_usage():
    """Print usage instructions"""
    print("""
🔑 YouTube Token Generator - Multiple Projects Support

Usage:
    python3 generate_token.py <command> [arguments]

Commands:
    create <name> <credentials_file>    Create new token
    list                                 List all tokens
    test <name>                         Test existing token
    help                                Show this help

Examples:
    # Create token for project 2
    python3 generate_token.py create project2 client_secret_project2.json
    
    # Create token for project 3
    python3 generate_token.py create project3 client_secret_project3.json
    
    # List all tokens
    python3 generate_token.py list
    
    # Test a token
    python3 generate_token.py test project2

Setup Guide:
    1. Create new Google Cloud Project
    2. Enable YouTube Data API v3
    3. Configure OAuth consent screen
    4. Create OAuth 2.0 Desktop credentials
    5. Download credentials as JSON
    6. Run: python3 generate_token.py create <name> <credentials.json>
    7. Authorize in browser
    8. Token saved to tokens/ folder
    9. Use in web UI by selecting token from dropdown

Documentation:
    See: MULTIPLE_API_PROJECTS_GUIDE.md for detailed setup guide
""")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        if len(sys.argv) != 4:
            print("❌ Error: Invalid arguments")
            print("Usage: python3 generate_token.py create <name> <credentials_file>")
            print("Example: python3 generate_token.py create project2 client_secret_project2.json")
            sys.exit(1)
        
        token_name = sys.argv[2]
        credentials_file = sys.argv[3]
        
        success = create_token(token_name, credentials_file)
        sys.exit(0 if success else 1)
    
    elif command == 'list':
        list_tokens()
        sys.exit(0)
    
    elif command == 'test':
        if len(sys.argv) != 3:
            print("❌ Error: Invalid arguments")
            print("Usage: python3 generate_token.py test <name>")
            print("Example: python3 generate_token.py test project2")
            sys.exit(1)
        
        token_name = sys.argv[2]
        success = test_token(token_name)
        sys.exit(0 if success else 1)
    
    elif command == 'help':
        print_usage()
        sys.exit(0)
    
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)
