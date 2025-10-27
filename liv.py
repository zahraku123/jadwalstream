import os
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === KONFIGURASI ===
EXCEL_FILE = 'data.xlsx'
THUMBNAIL_FOLDER = 'thumbnails'
DRY_RUN = False  # True = simulasi tanpa upload ke YouTube

# === AUTHENTIKASI YOUTUBE API ===
def get_youtube_service():
    try:
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube'])
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logging.error(f"Error authenticating with YouTube API: {e}")
        raise

# === UPDATE VIDEO ===
def update_video(youtube, video_id, title, description, thumbnail_path, privacy, publish_at, made_for_kids):
    try:
        body = {
            'id': video_id,
            'snippet': {'title': title, 'description': description},
            'status': {
                'privacyStatus': privacy,
                'publishAt': publish_at,
                'selfDeclaredMadeForKids': made_for_kids
            }
        }
        # Update title + description
        youtube.videos().update(
            part='snippet,status',
            body=body
        ).execute()

        # Upload thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
    except Exception as e:
        logging.error(f"Error updating video {video_id}: {e}")
        raise

# === MAIN PROGRAM ===
def main():
    logging.info("\n=== :YOUTUBE TERNAK/TIERNAK 13 LATIN EDM ===")
    logging.info("-> Membaca data dari Excel...\n")

    try:
        df = pd.read_excel(EXCEL_FILE)
        youtube = get_youtube_service()
        total = len(df)

        for idx, row in df.iterrows():
            logging.info(f"[{idx+1}/{total}]")
            video_id = row['videoId']
            title = row['title']
            description = row['description']
            thumbnail_file = os.path.join(THUMBNAIL_FOLDER, row['thumbnail_path'])
            privacy = row.get('privacyStatus', 'private')
            publish_at = row.get('publishAt', None)
            made_for_kids = bool(row.get('madeForKids', False))

            logging.info("-> update snippet (title/description)")
            logging.info(f"-> set thumbnail: {os.path.basename(thumbnail_file)}")
            logging.info(f"-> update status (kids={made_for_kids}, publishAt={publish_at}, privacy={privacy})")

            if not DRY_RUN:
                update_video(youtube, video_id, title, description, thumbnail_file, privacy, publish_at, made_for_kids)
                logging.info("✅ selesai\n")
                time.sleep(1)

        logging.info("\n=== Semua video selesai diupdate! ===")
    except Exception as e:
        logging.error(f"Error in main program: {e}")

if __name__ == '__main__':
    main()