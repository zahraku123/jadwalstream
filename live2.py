import os
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime
import pytz
import time
import logging

# ================= CONFIG =================
EXCEL_FILE = 'live_stream_data.xlsx'
DEFAULT_TIMEZONE = 'Asia/Jakarta'
DRY_RUN = False  # True = simulasi tanpa upload
# =========================================

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===== AUTHENTIKASI YOUTUBE API =====
def get_youtube_service(token_file):
    """Mendapatkan service object YouTube API untuk token tertentu."""
    try:
        creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/youtube'])
        youtube = build('youtube', 'v3', credentials=creds)
        logging.info(f"✅ Authenticated with token: {token_file}")
        return youtube
    except Exception as e:
        logging.error(f"Error authenticating with token '{token_file}': {e}")
        raise

# ===== JADWALKAN LIVE STREAM =====
def schedule_live_stream(youtube, title, description, scheduled_start_time,
                         privacy_status, auto_start=False, auto_stop=False, made_for_kids=False):
    """Membuat Live Stream + Live Broadcast dan mengikatnya."""
    try:
        # 1. Create liveStream
        stream_body = {
            'snippet': {'title': f"Stream Key for: {title}"},
            'cdn': {'frameRate': 'variable', 'ingestionType': 'rtmp', 'resolution': 'variable'}
        }
        logging.info("-> Creating LiveStream...")
        live_stream_response = youtube.liveStreams().insert(
            part='snippet,cdn', body=stream_body
        ).execute()
        stream_id = live_stream_response['id']
        logging.info(f"-> LiveStream ID: {stream_id}")

        # 2. Create liveBroadcast
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

        # 3. Bind LiveBroadcast to LiveStream
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

# ===== MAIN PROGRAM =====
def main():
    logging.info("\n=== 🔴 YOUTUBE MULTI-CHANNEL LIVE STREAM SCHEDULER ===")
    
    try:
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        logging.error(f"Excel file '{EXCEL_FILE}' not found.")
        return

    required_columns = ['title', 'description', 'scheduledStartTime', 'tokenFile']
    for col in required_columns:
        if col not in df.columns:
            logging.error(f"Column '{col}' is missing in Excel file.")
            return

    total = len(df)

    for idx, row in df.iterrows():
        logging.info(f"\n[{idx+1}/{total}] Processing event...")
        try:
            title = str(row['title'])
            description = str(row['description'])
            privacy_status = str(row.get('privacyStatus', 'unlisted')).lower()
            if privacy_status not in ['private', 'unlisted', 'public']:
                logging.warning(f"Invalid privacyStatus '{privacy_status}', defaulting to 'unlisted'")
                privacy_status = 'unlisted'

            # Convert Excel time to UTC ISO 8601
            local_time = pd.to_datetime(row['scheduledStartTime'])
            local_tz = pytz.timezone(DEFAULT_TIMEZONE)
            utc_time = local_tz.localize(local_time).astimezone(pytz.utc)
            scheduled_start_time = utc_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')

            # Auto start/stop
            auto_start = bool(row.get('autoStart', False))
            auto_stop = bool(row.get('autoStop', False))
            # Made for kids
            made_for_kids = bool(row.get('madeForKids', False))

            # Pilih token sesuai channel
            token_file = str(row['tokenFile'])
            youtube = get_youtube_service(token_file)

            logging.info(f"Title: {title}")
            logging.info(f"Scheduled Time (UTC): {scheduled_start_time}")
            logging.info(f"Privacy: {privacy_status}, AutoStart: {auto_start}, AutoStop: {auto_stop}, MadeForKids: {made_for_kids}")

            if not DRY_RUN:
                broadcast_id, stream_id = schedule_live_stream(
                    youtube, title, description, scheduled_start_time,
                    privacy_status, auto_start, auto_stop, made_for_kids
                )
                logging.info(f"Link: https://studio.youtube.com/video/{broadcast_id}/livestreaming")
                time.sleep(2)
            else:
                logging.info("DRY_RUN: Skipping API calls.")

        except Exception as e:
            logging.error(f"Error processing row {idx+1}: {e}")
            continue

    logging.info("\n=== All live streams processed ===")

if __name__ == '__main__':
    main()
