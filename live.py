import os
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime
import pytz
import time
import logging
import json

# ================= CONFIG =================
EXCEL_FILE = 'live_stream_data.xlsx'
DEFAULT_TIMEZONE = 'Asia/Jakarta'
DRY_RUN = False
STREAM_MAPPING_FILE = 'stream_mapping.json'

def load_stream_mapping(token_file):
    try:
        with open(STREAM_MAPPING_FILE, 'r') as f:
            mapping_data = json.load(f)
            if token_file in mapping_data:
                # Extract stream IDs and titles from the token's mapping
                stream_mapping = {}
                for stream_id, stream_info in mapping_data[token_file].items():
                    stream_mapping[stream_info['title']] = stream_id
                return stream_mapping
            else:
                logging.error(f"Token file {token_file} not found in {STREAM_MAPPING_FILE}")
                return {}
    except Exception as e:
        logging.error(f"Error loading stream mapping: {e}")
        return {}
# =========================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_youtube_service(token_file):
    creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/youtube'])
    youtube = build('youtube', 'v3', credentials=creds)
    logging.info(f"✅ Authenticated with token: {token_file}")
    return youtube

def get_stream_id_from_name(name, token_file):
    # Load stream mapping for this token
    stream_mapping = load_stream_mapping(token_file)
    reverse_mapping = {v: k for k, v in stream_mapping.items()}
    
    # First try to find it as a name
    stream_id = stream_mapping.get(name)
    if stream_id:
        logging.info(f"Resolved stream name '{name}' → ID '{stream_id}'")
        return stream_id
    
    # If not found, check if it's actually an ID
    if name in reverse_mapping:
        stream_id = name
        name = reverse_mapping[name]
        logging.info(f"Found stream ID '{stream_id}' → name '{name}'")
        return stream_id
    
    logging.warning(f"Stream name/ID '{name}' not found in stream mapping for {token_file}")
    return None

def schedule_live_stream(youtube, title, description, scheduled_start_time,
                         privacy_status, auto_start=False, auto_stop=False, made_for_kids=False,
                         use_existing_stream=False, streamNameExisting=None, token_file=None):
    try:
        # Validasi bro
        if use_existing_stream:
            if not streamNameExisting or pd.isna(streamNameExisting) or str(streamNameExisting).strip() == "":
                raise ValueError("streamNameExisting harus diisi jika useExistingStream=True bro!")
            
            stream_input = streamNameExisting.strip()
            
            # Load stream mapping for this token
            stream_mapping = load_stream_mapping(token_file)
            reverse_mapping = {v: k for k, v in stream_mapping.items()}
            
            # If it's an ID, get the name for display
            display_name = reverse_mapping.get(stream_input, stream_input)
            
            stream_id = get_stream_id_from_name(stream_input, token_file)
            if not stream_id:
                raise ValueError(f"Stream name/ID '{display_name}' tidak ditemukan di mapping untuk token {token_file} bro!")
            
            logging.info(f"Using existing stream: '{display_name}' (ID: {stream_id})")
        else:
            # Create new stream
            stream_body = {
                'snippet': {'title': f"Stream Key for: {title}"},
                'cdn': {'frameRate': 'variable', 'ingestionType': 'rtmp', 'resolution': 'variable'}
            }
            logging.info("-> Creating new LiveStream...")
            live_stream_response = youtube.liveStreams().insert(
                part='snippet,cdn', body=stream_body
            ).execute()
            stream_id = live_stream_response['id']
            logging.info(f"-> LiveStream ID: {stream_id}")

        # Create broadcast
        broadcast_body = {
            'snippet': {
                'title': title,
                'description': description,
                'scheduledStartTime': scheduled_start_time
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids
            },
            'contentDetails': {
                'enableDvr': True,
                'enableClosedCaptions': True,
                'enableAutoStart': auto_start,
                'enableAutoStop': auto_stop
            }
        }
        logging.info("-> Creating LiveBroadcast...")
        broadcast_response = youtube.liveBroadcasts().insert(
            part='snippet,status,contentDetails',
            body=broadcast_body
        ).execute()
        broadcast_id = broadcast_response['id']
        logging.info(f"-> LiveBroadcast ID: {broadcast_id}")

        # Bind broadcast ke stream
        logging.info("-> Binding LiveBroadcast to LiveStream...")
        youtube.liveBroadcasts().bind(
            part='id,contentDetails',
            id=broadcast_id,
            streamId=stream_id
        ).execute()

        logging.info(f"✅ Scheduled: {title} (Video ID: {broadcast_id})")
        return broadcast_id, stream_id

    except Exception as e:
        logging.error(f"Error scheduling live stream '{title}': {e}")
        raise

def main():
    logging.info("\n=== 🔴 YOUTUBE SCHEDULER WITH STREAM NAME VALIDATION BRO ===")

    try:
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        logging.error(f"Excel file '{EXCEL_FILE}' not found bro!")
        return

    # Pastikan kolom ada
    required_columns = ['title', 'description', 'scheduledStartTime', 'tokenFile']
    for col in required_columns:
        if col not in df.columns:
            logging.error(f"Column '{col}' is missing in Excel file bro!")
            return

    # Pastikan kolom tambahan ada
    for col, default, dtype in [
        ('success', False, bool),
        ('streamId', '', str),
        ('broadcastLink', '', str),
        ('thumbnailFile', '', str),
        ('useExistingStream', False, bool),
        ('streamNameExisting', '', str)
    ]:
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].astype(dtype)

    total = len(df)
    for idx, row in df.iterrows():
        logging.info(f"\n[{idx+1}/{total}] Processing event bro...")
        try:
            title = str(row['title'])
            description = str(row['description'])
            privacy_status = str(row.get('privacyStatus', 'unlisted')).lower()
            if privacy_status not in ['private', 'unlisted', 'public']:
                privacy_status = 'unlisted'

            local_time = pd.to_datetime(row['scheduledStartTime'])
            local_tz = pytz.timezone(DEFAULT_TIMEZONE)
            utc_time = local_tz.localize(local_time).astimezone(pytz.utc)
            scheduled_start_time = utc_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')

            auto_start = bool(row.get('autoStart', False))
            auto_stop = bool(row.get('autoStop', False))
            made_for_kids = bool(row.get('madeForKids', False))
            token_file = str(row['tokenFile'])
            use_existing_stream = bool(row.get('useExistingStream', False))
            streamNameExisting = str(row.get('streamNameExisting', '')).strip()
            thumbnail_path = str(row.get('thumbnailFile', '')).strip()

            youtube = get_youtube_service(token_file)

            if not DRY_RUN:
                broadcast_id, stream_id = schedule_live_stream(
                    youtube, title, description, scheduled_start_time,
                    privacy_status, auto_start, auto_stop, made_for_kids,
                    use_existing_stream, streamNameExisting, token_file
                )

                # Upload thumbnail
                if thumbnail_path and os.path.exists(thumbnail_path):
                    try:
                        youtube.thumbnails().set(
                            videoId=broadcast_id,
                            media_body=thumbnail_path
                        ).execute()
                        logging.info(f"✅ Thumbnail uploaded: {thumbnail_path}")
                    except Exception as e:
                        logging.error(f"Failed to upload thumbnail for {title}: {e}")

                # Update Excel
                df.at[idx, 'success'] = True
                df.at[idx, 'streamId'] = str(stream_id)
                df.at[idx, 'broadcastLink'] = f"https://studio.youtube.com/video/{broadcast_id}/livestreaming"
                logging.info("Broadcast link saved to Excel bro")
                time.sleep(2)
            else:
                df.at[idx, 'success'] = False
                df.at[idx, 'streamId'] = ''
                df.at[idx, 'broadcastLink'] = ''

        except Exception as e:
            logging.error(f"Error processing row {idx+1}: {e}")
            df.at[idx, 'success'] = False
            df.at[idx, 'streamId'] = ''
            df.at[idx, 'broadcastLink'] = ''
            continue

    try:
        df.to_excel(EXCEL_FILE, index=False)
        logging.info(f"\n=== Excel file '{EXCEL_FILE}' updated successfully bro ===")
    except Exception as e:
        fallback_file = EXCEL_FILE.replace('.xlsx', '_updated.xlsx')
        try:
            df.to_excel(fallback_file, index=False)
            logging.info(f"Saved to fallback file '{fallback_file}' instead bro")
        except Exception as e2:
            logging.error(f"Failed to save fallback Excel file bro: {e2}")

if __name__ == '__main__':
    main()
