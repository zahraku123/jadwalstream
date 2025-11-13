"""
YouTube Scheduler - Database-Based Multi-User Version
Reads schedules from database and processes per-user
"""
import schedule
import time
import logging
from datetime import datetime, timedelta
import pytz
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_all_pending_schedules, update_schedule_status, get_user_by_id, get_db_connection
from live import schedule_live_stream
from kunci import get_youtube_service
import telegram_notifier

# ================= CONFIG =================
SCHEDULE_TIMES = ["00:23", "00:37", "00:39"]  # Jakarta time
TIMEZONE = "Asia/Jakarta"
# =========================================

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jadwal_scheduler.log'),
        logging.StreamHandler()
    ]
)

jakarta_tz = pytz.timezone(TIMEZONE)

def get_user_token_path(user_id, token_file):
    """Get token path for specific user"""
    # Per-user token folder
    user_token_path = os.path.join('tokens', f'user_{user_id}', token_file)
    
    if os.path.exists(user_token_path):
        return user_token_path
    
    # Fallback to root tokens folder (legacy)
    legacy_path = os.path.join('tokens', token_file)
    if os.path.exists(legacy_path):
        logging.warning(f"Using legacy token path for user {user_id}: {legacy_path}")
        return legacy_path
    
    return None

def process_schedule(schedule):
    """Process a single schedule from database"""
    schedule_id = schedule['id']
    user_id = schedule['user_id']
    title = schedule['title']
    
    logging.info(f"\n{'='*60}")
    logging.info(f"[SCHEDULE {schedule_id}] Processing: {title}")
    logging.info(f"[SCHEDULE {schedule_id}] User ID: {user_id}")
    logging.info(f"{'='*60}")
    
    try:
        # Get user info
        user = get_user_by_id(user_id)
        if not user:
            logging.error(f"[SCHEDULE {schedule_id}] User {user_id} not found!")
            return False
        
        username = user['username']
        logging.info(f"[SCHEDULE {schedule_id}] Username: {username}")
        
        # Get schedule data
        description = schedule.get('description', '')
        scheduled_start_time = schedule['scheduled_start_time']
        token_file = schedule.get('token_file', '')
        stream_name = schedule.get('stream_name', '')
        repeat_daily = bool(schedule.get('repeat_daily', 0))
        
        logging.info(f"[SCHEDULE {schedule_id}] Token file: {token_file}")
        logging.info(f"[SCHEDULE {schedule_id}] Scheduled time: {scheduled_start_time}")
        logging.info(f"[SCHEDULE {schedule_id}] Repeat daily: {repeat_daily}")
        
        # Get user's token path
        token_path = get_user_token_path(user_id, token_file)
        
        if not token_path:
            error_msg = f"Token file not found: {token_file} for user {username}"
            logging.error(f"[SCHEDULE {schedule_id}] {error_msg}")
            telegram_notifier.notify_schedule_error(title, error_msg, user_id=user_id)
            return False
        
        logging.info(f"[SCHEDULE {schedule_id}] Using token: {token_path}")
        
        # Get YouTube service
        try:
            youtube = get_youtube_service(token_file)
        except Exception as e:
            error_msg = f"Failed to authenticate with token: {str(e)}"
            logging.error(f"[SCHEDULE {schedule_id}] {error_msg}")
            telegram_notifier.notify_schedule_error(title, error_msg, user_id=user_id)
            return False
        
        # Create YouTube live broadcast
        logging.info(f"[SCHEDULE {schedule_id}] Creating YouTube broadcast...")
        
        broadcast_id, stream_id = schedule_live_stream(
            youtube=youtube,
            title=title,
            description=description,
            scheduled_start_time=scheduled_start_time,
            privacy_status='unlisted',
            auto_start=False,
            auto_stop=False,
            made_for_kids=False,
            use_existing_stream=bool(stream_name),
            streamNameExisting=stream_name if stream_name else None,
            token_file=token_file
        )
        
        broadcast_link = f"https://studio.youtube.com/video/{broadcast_id}/livestreaming"
        
        logging.info(f"[SCHEDULE {schedule_id}] ✅ Broadcast created!")
        logging.info(f"[SCHEDULE {schedule_id}] Broadcast ID: {broadcast_id}")
        logging.info(f"[SCHEDULE {schedule_id}] Stream ID: {stream_id}")
        logging.info(f"[SCHEDULE {schedule_id}] Link: {broadcast_link}")
        
        # Upload thumbnail if exists
        thumbnail = schedule.get('thumbnail', '')
        if thumbnail:
            thumbnail_path = thumbnail if thumbnail.startswith('thumbnails/') else f'thumbnails/{thumbnail}'
            if os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=broadcast_id,
                        media_body=thumbnail_path
                    ).execute()
                    logging.info(f"[SCHEDULE {schedule_id}] ✅ Thumbnail uploaded")
                except Exception as e:
                    logging.warning(f"[SCHEDULE {schedule_id}] Failed to upload thumbnail: {e}")
        
        # Update database - mark as completed
        update_schedule_status(schedule_id, success=True, broadcast_id=broadcast_id, broadcast_link=broadcast_link)
        logging.info(f"[SCHEDULE {schedule_id}] ✅ Database updated")
        
        # Send Telegram notification to user
        try:
            telegram_notifier.notify_schedule_created(
                title=title,
                scheduled_time=scheduled_start_time,
                broadcast_link=broadcast_link,
                user_id=user_id
            )
            logging.info(f"[SCHEDULE {schedule_id}] ✅ Telegram notification sent")
        except Exception as e:
            logging.warning(f"[SCHEDULE {schedule_id}] Failed to send Telegram notification: {e}")
        
        # Handle repeat_daily
        if repeat_daily:
            try:
                # Create new schedule for tomorrow
                from database import add_schedule
                
                # Parse current scheduled time
                current_time = datetime.strptime(scheduled_start_time, '%Y-%m-%d %H:%M:%S')
                next_time = current_time + timedelta(days=1)
                
                new_schedule_data = {
                    'title': title,
                    'description': description,
                    'scheduled_start_time': next_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'video_file': schedule.get('video_file', ''),
                    'thumbnail': thumbnail,
                    'stream_name': stream_name,
                    'stream_id': schedule.get('stream_id', ''),
                    'token_file': token_file,
                    'repeat_daily': 1,
                    'success': 0
                }
                
                add_schedule(user_id, new_schedule_data)
                logging.info(f"[SCHEDULE {schedule_id}] ✅ Next schedule created for {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
            except Exception as e:
                logging.error(f"[SCHEDULE {schedule_id}] Failed to create repeat schedule: {e}")
        
        logging.info(f"[SCHEDULE {schedule_id}] ✅ COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        logging.error(f"[SCHEDULE {schedule_id}] ❌ ERROR: {e}", exc_info=True)
        try:
            telegram_notifier.notify_schedule_error(title, str(e), user_id=user_id)
        except:
            pass
        return False

def run_scheduler():
    """Main scheduler function - processes all pending schedules from database"""
    now_jakarta = datetime.now(jakarta_tz)
    
    logging.info(f"\n{'='*70}")
    logging.info(f"🔴 YouTube Scheduler Running")
    logging.info(f"⏰ Time: {now_jakarta.strftime('%Y-%m-%d %H:%M:%S')} WIB")
    logging.info(f"{'='*70}")
    
    try:
        # Get all pending schedules from database (all users)
        pending_schedules = get_all_pending_schedules()
        
        if not pending_schedules:
            logging.info("📭 No pending schedules")
            logging.info(f"{'='*70}\n")
            return
        
        logging.info(f"📋 Found {len(pending_schedules)} pending schedule(s)")
        
        # Group by user for better logging
        schedules_by_user = {}
        for schedule in pending_schedules:
            user_id = schedule['user_id']
            if user_id not in schedules_by_user:
                schedules_by_user[user_id] = []
            schedules_by_user[user_id].append(schedule)
        
        logging.info(f"👥 Users with pending schedules: {len(schedules_by_user)}")
        for uid, scheds in schedules_by_user.items():
            user = get_user_by_id(uid)
            username = user['username'] if user else f"User {uid}"
            logging.info(f"   - {username}: {len(scheds)} schedule(s)")
        
        # Process each schedule
        successful = 0
        failed = 0
        
        for schedule in pending_schedules:
            if process_schedule(schedule):
                successful += 1
            else:
                failed += 1
            
            # Small delay between schedules
            time.sleep(2)
        
        logging.info(f"\n{'='*70}")
        logging.info(f"✅ Scheduler Completed")
        logging.info(f"   Successful: {successful}")
        logging.info(f"   Failed: {failed}")
        logging.info(f"   Total: {len(pending_schedules)}")
        logging.info(f"{'='*70}\n")
        
    except Exception as e:
        logging.error(f"❌ Scheduler error: {e}", exc_info=True)
        logging.info(f"{'='*70}\n")

def schedule_jobs():
    """Setup scheduled jobs"""
    for t in SCHEDULE_TIMES:
        schedule.every().day.at(t).do(run_scheduler)
        logging.info(f"⏰ Scheduler set for {t} WIB daily")

def main():
    """Main entry point"""
    logging.info("="*70)
    logging.info("🚀 YouTube Auto-Scheduler Starting (DATABASE MODE)")
    logging.info("="*70)
    logging.info(f"📅 Schedule times: {', '.join(SCHEDULE_TIMES)} WIB")
    logging.info(f"🌍 Timezone: {TIMEZONE}")
    logging.info(f"💾 Mode: Multi-User Database-Based")
    logging.info("="*70)
    
    schedule_jobs()
    
    logging.info("✅ Scheduler active. Waiting for scheduled times...")
    logging.info("💡 Tip: Schedules are processed per-user from database")
    logging.info("="*70 + "\n")
    
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
