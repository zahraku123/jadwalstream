#!/usr/bin/env python3
"""
Upload backup file to Google Drive
"""
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime

def upload_backup_to_gdrive(backup_file_path):
    """Upload backup file to Google Drive"""
    
    # Load credentials from gdrive_token.json
    token_file = 'gdrive_token.json'
    
    if not os.path.exists(token_file):
        print("Error: gdrive_token.json not found")
        print("Please authenticate first by running: python3 auth_gdrive.py")
        return False
    
    print(f"Using token file: {token_file}")
    
    try:
        # Load credentials
        creds = Credentials.from_authorized_user_file(
            token_file, 
            ['https://www.googleapis.com/auth/drive.file']
        )
        
        # Build Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # Create folder name with timestamp
        folder_name = f"JadwalStream_Backups"
        
        # Check if folder exists
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])
        
        if folders:
            folder_id = folders[0]['id']
            print(f"Using existing folder: {folder_name}")
        else:
            # Create folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"Created new folder: {folder_name}")
        
        # Upload file
        file_name = os.path.basename(backup_file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(backup_file_path, resumable=True)
        
        print(f"Uploading {file_name}...")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        print(f"✓ Upload successful!")
        print(f"  File ID: {file.get('id')}")
        print(f"  File Name: {file.get('name')}")
        print(f"  Link: {file.get('webViewLink')}")
        
        return True
        
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        return False

if __name__ == "__main__":
    # Find the latest backup file
    backup_dir = "/root/backupjadwalstream"
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.tar.gz')]
    
    if not backup_files:
        print("No backup files found in /root/backupjadwalstream")
        exit(1)
    
    # Get the latest backup
    latest_backup = sorted(backup_files)[-1]
    backup_path = os.path.join(backup_dir, latest_backup)
    
    print(f"Backup file: {backup_path}")
    print(f"Size: {os.path.getsize(backup_path) / (1024*1024):.2f} MB")
    print("")
    
    # Upload to Google Drive
    success = upload_backup_to_gdrive(backup_path)
    
    if success:
        print("\n✓ Backup uploaded to Google Drive successfully!")
    else:
        print("\n✗ Failed to upload backup to Google Drive")
        exit(1)
