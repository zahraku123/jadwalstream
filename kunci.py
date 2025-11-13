from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os

# Configuration
TOKENS_FOLDER = 'tokens'  # Folder for token files

def get_youtube_service(token_path):
    """Membuat service YouTube API dengan token yang diberikan
    
    Args:
        token_path: Full path to token file (not just filename)
    """
    # If token_path is just filename (legacy support), add tokens folder
    if not os.path.dirname(token_path):
        token_path = os.path.join(TOKENS_FOLDER, token_path)
    
    creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/youtube'])
    return build('youtube', 'v3', credentials=creds)

def get_stream_keys(token_path):
    """Mengambil semua stream keys dari channel
    
    Args:
        token_path: Full path to token file (not just filename)
    """
    youtube = get_youtube_service(token_path)
    
    try:
        # Mengambil daftar livestreams
        request = youtube.liveStreams().list(
            part="snippet,cdn",
            mine=True,
            maxResults=50
        )
        response = request.execute()
        
        # Return mapping keyed by stream ID to avoid collisions on names.
        # Each value contains metadata (title and cdn info) so we can handle
        # duplicate names across channels/tokens.
        stream_keys = {}
        for item in response.get('items', []):
            stream_id = item.get('id', '')
            stream_name = str(item.get('snippet', {}).get('title', '') or '')  # ensure string
            if not stream_name:
                stream_name = f"Stream {stream_id}"  # fallback name
            cdn = item.get('cdn', {})
            stream_keys[stream_id] = {
                'title': stream_name,
                'cdn': cdn,
            }

        return stream_keys
    except Exception as e:
        print(f"Error getting stream keys: {e}")
        return {}

def save_stream_mapping(mapping, token_file=None):
    """Menyimpan mapping stream ke file JSON.

    Struktur file akan menjadi per-token, contoh:
    {
        "token1.json": {"streamName": "streamId", ...},
        "token2.json": { ... }
    }

    Jika token_file diberikan, mapping akan disimpan di bawah kunci token_file
    dan digabungkan dengan isi file yang sudah ada (tidak menimpa token lain).
    """
    try:
        existing = {}
        if os.path.exists('stream_mapping.json'):
            with open('stream_mapping.json', 'r') as f:
                try:
                    existing = json.load(f) or {}
                except Exception:
                    existing = {}

        if token_file:
            # ensure existing is a dict
            if not isinstance(existing, dict):
                existing = {}
            existing[token_file] = mapping
            to_save = existing
        else:
            # if no token_file provided, merge top-level keys
            if not isinstance(existing, dict):
                existing = {}
            # Merge mappings (shallow merge)
            for k, v in mapping.items():
                existing[k] = v
            to_save = existing

        with open('stream_mapping.json', 'w') as f:
            json.dump(to_save, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving stream mapping: {e}")
        return False

def load_stream_mapping():
    """Membaca mapping stream dari file JSON"""
    try:
        if os.path.exists('stream_mapping.json'):
            with open('stream_mapping.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading stream mapping: {e}")
    return {}
