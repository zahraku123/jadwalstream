from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import pytz
import pandas as pd
import os
import json
from datetime import datetime
import pytz
import logging
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
import schedule
import subprocess
import threading
import time
import uuid
import requests
from werkzeug.utils import secure_filename
import shlex
import shutil
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# Modular imports
from modules.auth import (
    User, get_user_by_id, authenticate_user, initialize_default_user, 
    create_user, list_users, change_role, delete_user, change_user_password,
    get_user_limits, can_user_add_stream, can_user_upload, 
    update_user_limits, get_all_users_with_limits, calculate_user_storage
)

from modules.database import (
    get_video_database as get_video_database_sqlite,
    get_thumbnail_database as get_thumbnail_database_sqlite,
    get_live_streams_data,
    get_looped_videos_data,
    get_bulk_upload_queue_data,
    get_stream_mapping as get_stream_mapping_sqlite,
    add_video_to_db,
    delete_video_from_db,
    add_thumbnail_to_db,
    delete_thumbnail_from_db,
    add_live_stream_to_db,
    delete_live_stream_from_db,
    update_stream_status,
    add_schedule_to_db,
    update_schedule_in_db,
    delete_schedule_from_db,
    add_looped_video_to_db,
    update_looped_video_in_db,
    add_bulk_upload_to_db,
    update_bulk_upload_in_db,
    save_stream_mapping_data,
    delete_stream_mapping_data,
    delete_token_mappings_data,
    get_schedules,
    get_all_schedules,
    init_database
)

import psutil
import platform
from modules.utils import LicenseValidator, check_license, get_hwid, get_system_info
from modules.services import telegram_notifier
from functools import wraps


# Admin-only decorator (checks is_admin instead of role)
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        from modules.database import get_user_by_id
        user_data = get_user_by_id(int(current_user.id))
        if not user_data or not user_data.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if user is demo role
def demo_readonly(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role == 'demo':
            flash('Demo account has read-only access. Cannot perform this action.', 'warning')
            return redirect(request.referrer or url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Constants
EXCEL_FILE = 'live_stream_data.xlsx'
TIMEZONE = 'Asia/Jakarta'
SCOPES = ['https://www.googleapis.com/auth/youtube']
SCHEDULER_STATUS_FILE = 'scheduler_status.json'
AUTO_UPLOAD_SCHEDULER_STATUS_FILE = 'auto_upload_scheduler_status.json'
VIDEO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}
THUMBNAIL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thumbnails')
ALLOWED_THUMBNAIL_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
LIVE_STREAMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'live_streams.json')
TOKENS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tokens')
STREAM_TIMERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stream_timers.json')
RTMP_SERVERS = {
    'youtube': 'rtmp://a.rtmp.youtube.com/live2/',
    'facebook': 'rtmps://live-api-s.facebook.com:443/rtmp/',
    'instagram': 'rtmps://live-upload.instagram.com:443/rtmp/',
    'twitch': 'rtmp://live.twitch.tv/app/',
    'tiktok': 'rtmps://live-push.tiktok.com/live/'
}
# Dictionary to store running ffmpeg processes
live_processes = {}
# Dictionary to store active timers for auto-stop
active_timers = {}

app = Flask(__name__)

# Initialize SQLite database
try:
    init_database()
    print("✅ SQLite database initialized")
except Exception as e:
    print(f"⚠️  Database initialization error: {e}")
app.secret_key = 'your-secret-key-here'  # untuk flash messages

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login terlebih dahulu untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning'

# Initialize default user
initialize_default_user()

# Helper function to get schedules for current user
def get_user_schedules():
    """Get schedules for current user from SQLite"""
    try:
        if current_user.is_authenticated:
            user_id = int(current_user.id)
            return get_schedules(user_id)
        return []
    except Exception as e:
        print(f"Error getting schedules: {e}")
        return []


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# ==== Role helpers ====
# Simplified role system: admin and user only
ROLE_LIMITS = {
    'user': None,  # unlimited (or use user_limits from database)
    'admin': None,  # unlimited
}

def role_max_streams(role):
    """Get max streams for role (deprecated - use user_limits table instead)"""
    role = (role or 'user').lower()
    return ROLE_LIMITS.get(role, None)

def role_can_manage(role):
    """Check if role can manage system (admin only)"""
    return (role or '').lower() == 'admin'

def role_can_add_streams(role):
    """Check if role can add streams (all users can, but limited by user_limits)"""
    # All authenticated users can add streams (limits checked separately via user_limits table)
    return role is not None and role.lower() in ['user', 'admin']

# ==== License System ====
@app.before_request
def check_valid_license():
    """Check license validity before each request"""
    # Skip license check for public pages and static files
    public_endpoints = ['login', 'home', 'register', 'license_page', 'activate_license', 
                       'verify_license_online', 'get_license_info', 'static']
    
    if request.endpoint in public_endpoints:
        return
    
    # Skip if not logged in (will redirect to login)
    if not current_user.is_authenticated:
        return
    
    # Check license validity
    try:
        valid, message = check_license()
        if not valid:
            # Allow access to license page even if invalid
            if request.endpoint == 'license_page':
                return
            flash(f'⚠️ Lisensi: {message}', 'warning')
            return redirect(url_for('license_page'))
    except Exception as e:
        # If license check fails (e.g., file not found), allow access
        # This prevents app from breaking before first license activation
        print(f"License check error: {e}")
        pass

# Ensure video, thumbnail, and tokens folders exist
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(TOKENS_FOLDER, exist_ok=True)

# Helper function to get list of token files
def get_token_files(user_id=None):
    """Get list of token files from tokens folder, filtered by user_id if provided"""
    try:
        # If user_id provided, use per-user folder
        if user_id:
            user_tokens_folder = os.path.join(TOKENS_FOLDER, f'user_{user_id}')
            if not os.path.exists(user_tokens_folder):
                os.makedirs(user_tokens_folder, exist_ok=True)
            tokens = [f for f in os.listdir(user_tokens_folder) if f.endswith('.json')]
        else:
            # Legacy: no user_id, use root tokens folder
            if not os.path.exists(TOKENS_FOLDER):
                os.makedirs(TOKENS_FOLDER, exist_ok=True)
            tokens = [f for f in os.listdir(TOKENS_FOLDER) if f.endswith('.json')]
        return sorted(tokens)
    except Exception as e:
        print(f"Error getting token files: {e}")
        return []

def get_token_path(token_name, user_id=None):
    """Get full path for a token file"""
    if not token_name:
        return None
    # Ensure it has .json extension
    if not token_name.endswith('.json'):
        token_name += '.json'
    
    # If user_id provided, use per-user folder
    if user_id:
        user_tokens_folder = os.path.join(TOKENS_FOLDER, f'user_{user_id}')
        os.makedirs(user_tokens_folder, exist_ok=True)
        return os.path.join(user_tokens_folder, token_name)
    
    # Legacy: root tokens folder
    return os.path.join(TOKENS_FOLDER, token_name)

# Create a static folder link to videos folder for serving videos
app.config['UPLOAD_FOLDER'] = VIDEO_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024  # 2GB max upload (total for all files)

# Video database file
VIDEO_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'video_database.json')
# Thumbnail database file
THUMBNAIL_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thumbnail_database.json')

# Live stream functions
def get_live_streams():
    """Get live streams for current user from SQLite"""
    try:
        return get_live_streams_data()
    except Exception as e:
        print(f"Error getting live streams: {e}")
        return []
    
    try:
        with open(LIVE_STREAMS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_live_streams(streams):
    """DEPRECATED - use update_stream_status or individual functions"""
    pass

def get_stream_timers():
    """Load stream timers from JSON file"""
    if not os.path.exists(STREAM_TIMERS_FILE):
        with open(STREAM_TIMERS_FILE, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(STREAM_TIMERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_stream_timers(timers):
    """Save stream timers to JSON file"""
    with open(STREAM_TIMERS_FILE, 'w') as f:
        json.dump(timers, f, indent=4)

def cancel_stream_timer(stream_id):
    """Cancel active timer for a stream"""
    if stream_id in active_timers:
        timer = active_timers[stream_id]
        timer.cancel()
        del active_timers[stream_id]
        print(f"[TIMER] Cancelled timer for stream {stream_id}")
        
        # Remove from persistent storage
        timers = get_stream_timers()
        timers = [t for t in timers if t['stream_id'] != stream_id]
        save_stream_timers(timers)
        return True
    return False

def get_video_title(filename):
    videos = get_video_database()
    for video in videos:
        if video['filename'] == filename:
            return video['title']
    return filename

def start_ffmpeg_stream(stream):
    """Start an ffmpeg process to stream a video to RTMP server"""
    try:
        video_path = os.path.join(VIDEO_FOLDER, stream['video_file'])
        
        # Verify video file exists
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            return False
        
        # Map database fields to expected fields (backward compatibility)
        # server_type → rtmp_server
        # stream_url → custom_rtmp
        rtmp_server = stream.get('rtmp_server') or stream.get('server_type', 'youtube')
        custom_rtmp = stream.get('custom_rtmp') or stream.get('stream_url', '')
        
        # Get RTMP URL
        if rtmp_server == 'custom':
            rtmp_url = custom_rtmp
        else:
            rtmp_url = RTMP_SERVERS.get(rtmp_server, RTMP_SERVERS['youtube'])
        
        # Build full RTMP URL with stream key
        full_rtmp_url = f"{rtmp_url}{stream['stream_key']}"
        
        # Resolve ffmpeg binary (absolute path for systemd environments)
        ffmpeg_bin = shutil.which('ffmpeg') or '/usr/bin/ffmpeg'
        if not os.path.exists(ffmpeg_bin):
            print("Error: ffmpeg binary not found. Install ffmpeg and ensure it's in PATH or at /usr/bin/ffmpeg")
            return False
        
        # Build ffmpeg command - simplified to match manual command
        cmd = [
            ffmpeg_bin,
            '-re',  # Read input at native frame rate
            '-stream_loop', '-1',  # Loop video infinitely
            '-i', video_path,  # Input file
            '-c', 'copy',  # Copy codec (no re-encoding, more efficient)
        ]
        
        # Do not add duration (-t) to ffmpeg; duration will be enforced by a timer that stops the process.
        
        # Add output format and URL
        cmd.extend([
            '-f', 'flv',  # Output format
            full_rtmp_url  # Output URL
        ])
        
        # Log the command for debugging
        print(f"Starting ffmpeg with command: {' '.join(cmd)}")
        
        # Create log file for ffmpeg output
        log_dir = os.path.join(os.getcwd(), 'ffmpeg_logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{stream['id']}.log")
        
        # Start process with proper detachment for background operation
        with open(log_file, 'w') as log_f:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,  # Prevent stdin issues
                stdout=log_f,  # Write to log file instead of PIPE
                stderr=subprocess.STDOUT,  # Merge stderr to stdout
                start_new_session=True if os.name != 'nt' else False,  # Detach on Unix
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)  # Prevent window on Windows; no-op elsewhere
            )
        
        # Check if process started successfully
        time.sleep(0.5)  # Give process time to start
        if process.poll() is not None:
            # Process terminated immediately
            print(f"ffmpeg failed to start. Check log: {log_file}")
            return False
        
        # Store process
        live_processes[stream['id']] = process
        
        # Update stream status and actual start time
        streams = get_live_streams()
        actual_start_time = datetime.now(pytz.timezone(TIMEZONE))
        for s in streams:
            if s['id'] == stream['id']:
                s['status'] = 'live'
                s['process_pid'] = process.pid
                # Update start_date to actual start time when started manually
                s['start_date'] = actual_start_time.strftime('%Y-%m-%dT%H:%M')
                s['actual_start_time'] = actual_start_time.isoformat()
                break
        save_live_streams(streams)
        
        # Schedule auto-stop based on duration, if specified
        try:
            print(f"[DEBUG] Stream duration setting: '{stream.get('duration')}'")
            if 'duration' in stream and stream['duration'] and int(stream['duration']) > 0:
                duration_seconds = int(stream['duration']) * 60
                stop_time = actual_start_time + timedelta(seconds=duration_seconds)
                print(f"[AUTO-STOP] Will trigger in {duration_seconds} seconds ({stream['duration']} minutes)")
                print(f"[AUTO-STOP] Scheduled stop time: {stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                def _auto_stop_when_due(expected_pid=process.pid, sid=stream['id']):
                    print(f"[AUTO-STOP] Timer triggered! Stream ID={sid}, Expected PID={expected_pid}")
                    try:
                        current_proc = live_processes.get(sid)
                        print(f"[AUTO-STOP] Current process: {current_proc}")
                        
                        if current_proc:
                            print(f"[AUTO-STOP] Process PID: {current_proc.pid}, Poll status: {current_proc.poll()}")
                        
                        if current_proc and current_proc.pid == expected_pid and current_proc.poll() is None:
                            print(f"[AUTO-STOP] Duration reached ({duration_seconds}s). Stopping stream ID={sid} PID={expected_pid}")
                            stop_ffmpeg_stream(sid)
                            print(f"[AUTO-STOP] Stream {sid} stopped successfully")
                            
                            # Remove timer from active_timers and persistent storage
                            if sid in active_timers:
                                del active_timers[sid]
                            timers = get_stream_timers()
                            timers = [t for t in timers if t['stream_id'] != sid]
                            save_stream_timers(timers)
                        else:
                            print(f"[AUTO-STOP] Skipped for stream ID={sid}: process changed or already stopped")
                    except Exception as e:
                        print(f"[AUTO-STOP] Error during auto-stop for stream ID={sid}: {e}")
                        import traceback
                        traceback.print_exc()
                
                t = threading.Timer(duration_seconds, _auto_stop_when_due)
                t.daemon = True
                t.start()
                
                # Store timer in memory and persistent storage
                active_timers[stream['id']] = t
                
                timer_info = {
                    'stream_id': stream['id'],
                    'stream_title': stream.get('title', 'Unknown'),
                    'pid': process.pid,
                    'start_time': actual_start_time.isoformat(),
                    'stop_time': stop_time.isoformat(),
                    'duration_minutes': int(stream['duration']),
                    'created_at': datetime.now(pytz.timezone(TIMEZONE)).isoformat()
                }
                timers = get_stream_timers()
                # Remove any existing timer for this stream
                timers = [t for t in timers if t['stream_id'] != stream['id']]
                timers.append(timer_info)
                save_stream_timers(timers)
                
                print(f"[AUTO-STOP] ✓ Scheduled for stream ID={stream['id']} (PID {process.pid}) in {duration_seconds}s")
                print(f"[AUTO-STOP] ✓ Timer saved to {STREAM_TIMERS_FILE}")
            else:
                print(f"[AUTO-STOP] Not scheduled - duration is empty or 0")
        except Exception as e:
            print(f"[AUTO-STOP] Failed to schedule auto-stop: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"Stream started successfully with PID: {process.pid}")
        
        # Send Telegram notification for stream start
        try:
            stream_title = stream.get('title', 'Unknown')
            scheduled_time = stream.get('start_date', datetime.now().strftime('%Y-%m-%d %H:%M'))
            
            # Get YouTube watch link if available
            rtmp_server = stream.get('rtmp_server', '')
            stream_key = stream.get('stream_key', '')
            broadcast_link = f"https://studio.youtube.com" if rtmp_server == 'youtube' else "Custom RTMP"
            
            # Get user_id from stream owner
            user_id = None
            if stream.get('owner'):
                from modules.auth import get_user_by_username
                user_data = get_user_by_username(stream['owner'])
                if user_data:
                    user_id = user_data['id']
            
            telegram_notifier.notify_stream_starting(stream_title, scheduled_time, broadcast_link, user_id=user_id)
        except Exception as e:
            print(f"[TELEGRAM] Failed to send stream start notification: {e}")
        
        return True
    except Exception as e:
        print(f"Error starting stream: {e}")
        return False

def stop_ffmpeg_stream(stream_id):
    """Stop a running ffmpeg process"""
    print(f"[STOP] stop_ffmpeg_stream called for stream_id: {stream_id}")
    
    # Cancel any active timer for this stream
    cancel_stream_timer(stream_id)
    
    # Try to get PID from live_processes or from live_streams.json
    pid_to_kill = None
    process = None
    
    if stream_id in live_processes:
        process = live_processes[stream_id]
        pid_to_kill = process.pid
        print(f"[STOP] Found process in live_processes, PID: {pid_to_kill}")
    else:
        # Fallback: Get PID from live_streams.json
        print(f"[STOP] Stream not in live_processes, checking live_streams.json...")
        streams = get_live_streams()
        for stream in streams:
            if stream['id'] == stream_id and stream.get('process_pid'):
                pid_to_kill = stream['process_pid']
                print(f"[STOP] Found PID in live_streams.json: {pid_to_kill}")
                break
    
    # Kill the process if PID found
    if pid_to_kill:
        try:
            # Check if process exists using psutil
            if psutil.pid_exists(pid_to_kill):
                proc = psutil.Process(pid_to_kill)
                
                # Verify it's actually an ffmpeg process
                if 'ffmpeg' in proc.name().lower():
                    print(f"[STOP] Killing FFmpeg process PID: {pid_to_kill}")
                    proc.terminate()
                    
                    # Wait up to 5 seconds for graceful termination
                    try:
                        proc.wait(timeout=5)
                        print(f"[STOP] ✓ Process {pid_to_kill} terminated gracefully")
                    except psutil.TimeoutExpired:
                        print(f"[STOP] Process {pid_to_kill} didn't terminate in 5s, forcing kill...")
                        proc.kill()
                        proc.wait(timeout=3)
                        print(f"[STOP] ✓ Process {pid_to_kill} killed forcefully")
                else:
                    print(f"[STOP] ⚠ PID {pid_to_kill} is not an ffmpeg process ({proc.name()})")
            else:
                print(f"[STOP] Process PID {pid_to_kill} no longer exists")
        except psutil.NoSuchProcess:
            print(f"[STOP] Process PID {pid_to_kill} no longer exists")
        except Exception as e:
            print(f"[STOP] Error killing process {pid_to_kill}: {e}")
    
    # Clean up live_processes dict
    if stream_id in live_processes:
        del live_processes[stream_id]
        print(f"[STOP] ✓ Removed stream {stream_id} from live_processes dict")
    
    # Update stream status
    streams = get_live_streams()
    for stream in streams:
        if stream['id'] == stream_id:
            print(f"[STOP] Updating stream status to 'completed'")
            stream['status'] = 'completed'
            stream['process_pid'] = None

            # Update Excel file to increment scheduledStartTime by 1 day
            try:
                df = pd.read_excel(EXCEL_FILE)
                original_start_date_str = stream['start_date']
                original_start_date_dt = datetime.strptime(original_start_date_str, '%Y-%m-%dT%H:%M')

                matching_rows = df[
                    (df['title'] == stream['title']) &
                    (pd.to_datetime(df['scheduledStartTime']).dt.date == original_start_date_dt.date)
                ]

                if not matching_rows.empty:
                    idx_to_update = matching_rows.index[0]
                    current_excel_date = pd.to_datetime(df.loc[idx_to_update, 'scheduledStartTime'])
                    new_excel_date = current_excel_date + timedelta(days=1)
                    df.loc[idx_to_update, 'scheduledStartTime'] = new_excel_date.strftime('%Y-%m-%d %H:%M:%S')
                    df.to_excel(EXCEL_FILE, index=False)
                    logging.info(f"✅ Excel updated for '{stream['title']}': New scheduled date {new_excel_date.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logging.warning(f"⚠️ No matching entry found in Excel for stream '{stream['title']}' with original date {original_start_date_dt.date()}")
            except Exception as excel_err:
                logging.error(f"❌ Error updating Excel file: {excel_err}")

            # NOTE: Jadwal baru untuk repeat_daily sudah dibuat di check_scheduled_streams() saat stream dimulai
            # Tidak perlu buat lagi di sini untuk menghindari duplikasi
            print(f"[STREAM_ENDED] Stream '{stream['title']}' berakhir. Jadwal berikutnya (jika repeat_daily=True) sudah dibuat saat stream dimulai.")
            
            # Send Telegram notification for stream stop
            try:
                stream_title = stream.get('title', 'Unknown')
                duration = stream.get('duration', None)
                duration_text = f"{duration} minutes" if duration else None
                
                # Get user_id from stream owner
                user_id = None
                if stream.get('owner'):
                    from modules.auth import get_user_by_username
                    user_data = get_user_by_username(stream['owner'])
                    if user_data:
                        user_id = user_data['id']
                
                telegram_notifier.notify_stream_ended(stream_title, duration_text, user_id=user_id)
            except Exception as e:
                print(f"[TELEGRAM] Failed to send stream stop notification: {e}")
            
            break
    
    save_live_streams(streams)
    print(f"[STOP] ✓ Stream {stream_id} stop completed successfully")
    return True

def check_scheduled_streams():
    """Check for streams that need to be started based on schedule"""
    streams = get_live_streams()
    now = datetime.now()
    modified = False
    
    for stream in streams:
        # Only start streams that are explicitly scheduled
        if stream['status'] == 'scheduled':
            start_time = datetime.strptime(stream['start_date'], '%Y-%m-%dT%H:%M')
            
            # If it's time to start the stream
            if start_time <= now:
                # Add backward compatibility mapping before starting stream
                if 'server_type' in stream and 'rtmp_server' not in stream:
                    stream['rtmp_server'] = stream['server_type']
                if 'stream_url' in stream and 'custom_rtmp' not in stream:
                    stream['custom_rtmp'] = stream['stream_url']
                
                success = start_ffmpeg_stream(stream)
                
                # Update status to 'live' if stream started successfully
                if success:
                    stream['status'] = 'live'
                    print(f"Stream {stream['title']} started automatically and is now running")
                    # Hapus flash karena berjalan di luar request context
                
                modified = True
                
                # If this is a daily repeating stream, schedule the next occurrence
                # Only add if stream started successfully and it's a repeating stream
                if success and stream.get('repeat_daily', False):
                    # Create a new stream for tomorrow
                    new_stream = stream.copy()
                    new_stream['id'] = str(uuid.uuid4())
                    new_stream['status'] = 'scheduled'
                    
                    # Set start date to tomorrow at the same time
                    next_day = start_time + timedelta(days=1)
                    new_stream['start_date'] = next_day.strftime('%Y-%m-%dT%H:%M')
                    
                    # Preserve duration if it exists
                    if 'duration' in stream:
                        new_stream['duration'] = stream['duration']
                    
                    # Check if a similar stream already exists to prevent duplicates
                    # Check ALL streams with same video_file and start_date regardless of status
                    duplicate_exists = False
                    for existing_stream in streams:
                        if (existing_stream['video_file'] == new_stream['video_file'] and
                            existing_stream['start_date'] == new_stream['start_date']):
                            duplicate_exists = True
                            print(f"[SCHEDULER] Duplicate detected: Stream for {new_stream['start_date']} already exists (ID: {existing_stream['id'][:8]}..., Status: {existing_stream['status']})")
                            break
                    
                    if not duplicate_exists:
                        streams.append(new_stream)
                        modified = True
                        print(f"[SCHEDULER] Created next schedule for {new_stream['title']} on {new_stream['start_date']}")
    
    # Only save if changes were made
    if modified:
        save_live_streams(streams)

# Start a background thread to check for scheduled streams
def run_scheduler():
    while True:
        check_scheduled_streams()
        time.sleep(60)  # Check every minute

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_database():
    """Get videos for current user from SQLite"""
    try:
        return get_video_database_sqlite()
    except Exception as e:
        print(f"Error getting videos: {e}")
        return []
    try:
        with open(VIDEO_DB_FILE, 'r') as f:
            data = json.load(f)
            # Ensure data is a list, not a dict
            if isinstance(data, dict):
                return []
            return data if isinstance(data, list) else []
    except:
        return []

def save_video_database(videos):
    """DEPRECATED - use add_video_to_db or delete_video_from_db instead"""
    # This function is kept for backward compatibility but does nothing
    # All video operations now use individual add/delete functions
    pass

def get_thumbnail_database():
    """Get thumbnails for current user from SQLite"""
    try:
        return get_thumbnail_database_sqlite()
    except Exception as e:
        print(f"Error getting thumbnails: {e}")
        return []
    except:
        return []

def save_thumbnail_database(thumbnails):
    """DEPRECATED - use add_thumbnail_to_db or delete_thumbnail_from_db instead"""
    pass

def allowed_thumbnail_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_THUMBNAIL_EXTENSIONS

def save_scheduler_status(status):
    try:
        with open(SCHEDULER_STATUS_FILE, 'w') as f:
            json.dump({
                'last_run': status.get('last_run', ''),
                'next_check': status.get('next_check', ''),
                'last_status': status.get('last_status', ''),
                'active': status.get('active', False)
            }, f)
    except Exception as e:
        print(f"Error saving scheduler status: {e}")

def get_scheduler_status():
    try:
        with open(SCHEDULER_STATUS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            'last_run': '',
            'next_check': '',
            'last_status': 'Never run',
            'active': False
        }

def save_auto_upload_scheduler_status(status):
    """Save auto upload scheduler status"""
    try:
        with open(AUTO_UPLOAD_SCHEDULER_STATUS_FILE, 'w') as f:
            json.dump({
                'last_run': status.get('last_run', ''),
                'next_check': status.get('next_check', ''),
                'last_status': status.get('last_status', ''),
                'active': status.get('active', False),
                'uploads_processed': status.get('uploads_processed', 0)
            }, f)
    except Exception as e:
        print(f"Error saving auto upload scheduler status: {e}")

def get_auto_upload_scheduler_status():
    """Get auto upload scheduler status"""
    try:
        with open(AUTO_UPLOAD_SCHEDULER_STATUS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            'last_run': '',
            'next_check': '',
            'last_status': 'Never run',
            'active': False,
            'uploads_processed': 0
        }

def get_stream_name(stream_id):
    """Convert stream ID to stream name using the mapping from live.py"""
    if not stream_id:
        return ''

    # Try live.py reverse mapping first (fast when available)
    try:
        from modules.youtube.live import REVERSE_STREAM_MAPPING
        if stream_id in REVERSE_STREAM_MAPPING:
            return REVERSE_STREAM_MAPPING[stream_id]
        # if not found, don't return yet — fall back to saved mappings
    except Exception:
        pass

    # Fallback: try to read our saved stream_mapping from database and find a title
    try:
        mapping = get_stream_mapping()
        for token, streams in mapping.items():
            # streams expected: {streamId: {stream_name: ..., ...}}
            for sid, meta in (streams or {}).items():
                if sid == stream_id:
                    # meta might be a dict with stream_name (new) or title (old)
                    if isinstance(meta, dict):
                        return meta.get('stream_name') or meta.get('title') or meta.get('name') or stream_id
                    # otherwise meta might be a string name
                    return str(meta)
    except Exception:
        pass

    # Last resort: return the provided value unchanged
    return stream_id

def load_schedule_times(user_id=None):
    """Load schedule times - PER USER if user_id provided, else global"""
    if user_id:
        # Load from database for specific user
        try:
            from modules.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT scheduler_times FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()
                if row and row['scheduler_times']:
                    return json.loads(row['scheduler_times'])
        except Exception as e:
            logging.error(f"Error loading schedule times for user {user_id}: {e}")
    
    # Fallback to global config file (legacy)
    try:
        with open('schedule_config.json', 'r') as f:
            config = json.load(f)
            return config.get('schedule_times', [])
    except:
        return []

def save_schedule_times(times, user_id=None):
    """Save schedule times - PER USER if user_id provided, else global"""
    if user_id:
        # Save to database for specific user
        try:
            from modules.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET scheduler_times = ?
                    WHERE id = ?
                ''', (json.dumps(times), user_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving schedule times for user {user_id}: {e}")
            return False
    
    # Fallback to global config file (legacy)
    with open('schedule_config.json', 'w') as f:
        json.dump({'schedule_times': times}, f)

def get_stream_mapping():
    """Get stream mappings for current user from database"""
    from modules.database import get_stream_mappings
    try:
        if current_user.is_authenticated:
            user_id = int(current_user.id)
            return get_stream_mappings(user_id)
        return {}
    except Exception as e:
        print(f"Error getting stream mappings: {e}")
        return {}

@app.route('/edit_schedule/<int:index>', methods=['GET'])
@login_required
def edit_schedule(index):
    """Edit schedule - FROM DATABASE (index is actually schedule_id)"""
    # Restrict demo role from editing schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat mengedit jadwal.', 'error')
        return redirect(url_for('schedules'))
    try:
        user_id = int(current_user.id)
        schedule_id = index  # Using 'index' param for backward compatibility, but it's actually schedule_id
        
        # Get schedule from database
        from modules.database import get_schedule_by_id
        db_schedule = get_schedule_by_id(schedule_id, user_id)
        
        if not db_schedule:
            flash('Schedule not found!', 'error')
            return redirect(url_for('schedules'))
        
        # Convert to format compatible with template
        schedule = {
            'title': db_schedule['title'],
            'description': db_schedule.get('description', ''),
            'scheduledStartTime': db_schedule['scheduled_start_time'],
            'videoFile': db_schedule.get('video_file', ''),
            'thumbnailFile': db_schedule.get('thumbnail', '').replace('thumbnails/', ''),
            'tokenFile': db_schedule.get('token_file', ''),
            'privacyStatus': db_schedule.get('privacy_status', 'unlisted'),
            'streamNameExisting': db_schedule.get('stream_name', ''),
            'streamIdExisting': db_schedule.get('stream_id', ''),
            'autoStart': bool(db_schedule.get('auto_start', 0)),
            'autoStop': bool(db_schedule.get('auto_stop', 0)),
            'madeForKids': bool(db_schedule.get('made_for_kids', 0)),
            'repeat_daily': bool(db_schedule.get('repeat_daily', 0))
        }
        
        # Get user resources
        tokens = get_token_files(user_id)
        stream_mapping = get_stream_mapping()
        thumbnails = get_thumbnail_database()
        
        return render_template('edit_schedule.html', schedule=schedule, index=schedule_id, 
                             tokens=tokens, stream_mapping=stream_mapping, thumbnails=thumbnails)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('schedules'))

@app.route('/update_schedule/<int:index>', methods=['POST'])
@login_required
@demo_readonly
def update_schedule(index):
    """Update schedule in database - PER USER (index is actually schedule_id)"""
    # Restrict demo role from updating schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat mengubah jadwal.', 'error')
        return redirect(url_for('schedules'))
    try:
        user_id = int(current_user.id)
        schedule_id = index  # Using 'index' param for backward compatibility
        data = request.form.to_dict()
        
        # Resolve stream name
        submitted_stream = data.get('streamNameExisting', '')
        resolved_stream = get_stream_name(submitted_stream)
        app.logger.debug(f"update_schedule: submitted stream='{submitted_stream}' resolved='{resolved_stream}'")

        # Fix thumbnail path: add 'thumbnails/' prefix if needed
        thumbnail_file = data.get('thumbnailFile', '').strip()
        if thumbnail_file and not thumbnail_file.startswith('thumbnails/'):
            thumbnail_file = f'thumbnails/{thumbnail_file}'
        
        # Update in database
        from modules.database import update_schedule as db_update_schedule
        updates = {
            'title': data['title'],
            'description': data.get('description', ''),
            'scheduled_start_time': data['scheduledStartTime'],
            'video_file': data.get('videoFile', ''),
            'thumbnail': thumbnail_file,
            'stream_name': resolved_stream,
            'stream_id': data.get('streamIdExisting', ''),
            'token_file': data['tokenFile'],
            'privacy_status': data.get('privacyStatus', 'unlisted'),
            'auto_start': 1 if data.get('autoStart') == 'on' else 0,
            'auto_stop': 1 if data.get('autoStop') == 'on' else 0,
            'made_for_kids': 1 if data.get('madeForKids') == 'on' else 0,
            'repeat_daily': 1 if data.get('repeat_daily') == 'on' else 0
        }
        
        db_update_schedule(schedule_id, user_id, updates)
        flash('Schedule updated successfully!', 'success')
        
    except Exception as e:
        logging.error(f"Error updating schedule: {e}")
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/delete_schedule/<int:index>', methods=['POST'])
@login_required
@demo_readonly
def delete_schedule(index):
    """Delete schedule from database - PER USER (index is actually schedule_id)"""
    # Restrict demo role from deleting schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat menghapus jadwal.', 'error')
        return redirect(url_for('schedules'))
    try:
        user_id = int(current_user.id)
        schedule_id = index  # Using 'index' param for backward compatibility
        
        # Delete from database
        from modules.database import delete_schedule as db_delete_schedule
        if db_delete_schedule(schedule_id, user_id):
            flash('Schedule deleted successfully!', 'success')
        else:
            flash('Schedule not found or access denied!', 'error')
            
    except Exception as e:
        logging.error(f"Error deleting schedule: {e}")
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/stream_keys')
@login_required
def stream_keys():
    # Get available tokens (per-user)
    user_id = int(current_user.id)
    tokens = get_token_files(user_id)
    # Get current stream mapping from database
    from modules.database import get_stream_mappings
    stream_mapping = get_stream_mappings(user_id)
    return render_template('stream_keys.html', tokens=tokens, stream_mapping=stream_mapping)


@app.route('/manage_streams')
@login_required
def manage_streams():
    from modules.database import get_stream_mappings
    user_id = int(current_user.id)
    stream_mapping = get_stream_mappings(user_id)
    return render_template('manage_streams.html', stream_mapping=stream_mapping)


@app.route('/delete_stream_mapping', methods=['POST'])
@login_required
def delete_stream_mapping():
    from modules.database import delete_stream_mapping as db_delete_stream_mapping
    
    user_id = int(current_user.id)
    token_file = request.form.get('token_file')
    stream_id = request.form.get('stream_id')
    try:
        if db_delete_stream_mapping(user_id, token_file, stream_id):
            flash('Stream mapping deleted.', 'success')
        else:
            flash('Stream mapping not found.', 'warning')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_streams'))


@app.route('/delete_token_mapping', methods=['POST'])
@login_required
def delete_token_mapping():
    from modules.database import delete_token_mappings
    
    user_id = int(current_user.id)
    token_file = request.form.get('token_file')
    try:
        if delete_token_mappings(user_id, token_file):
            flash('Token mappings deleted.', 'success')
        else:
            flash('Token not found in mappings.', 'warning')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_streams'))


@app.route('/export_stream_mapping', methods=['POST'])
@login_required
def export_stream_mapping():
    from modules.database import get_stream_mappings
    
    user_id = int(current_user.id)
    try:
        mapping = get_stream_mappings(user_id)
        data = json.dumps(mapping, indent=4)
        return (data, 200, {
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="stream_mapping.json"'
        })
    except Exception as e:
        flash(f'Error exporting mapping: {e}', 'error')
        return redirect(url_for('manage_streams'))

@app.route('/fetch_stream_keys', methods=['POST'])
@login_required
@demo_readonly
def fetch_stream_keys():
    from modules.youtube.kunci import get_stream_keys
    from modules.database import save_stream_mapping
    
    user_id = int(current_user.id)
    token_file = request.form.get('token_file')
    if not token_file:
        flash('Please select a token file', 'error')
        return redirect(url_for('stream_keys'))
    
    try:
        # Get full token path using per-user folder structure
        token_path = get_token_path(token_file, user_id)
        
        if not os.path.exists(token_path):
            flash(f'Token file not found: {token_file}', 'error')
            return redirect(url_for('stream_keys'))
        
        # Get stream keys from YouTube
        stream_keys = get_stream_keys(token_path)
        if stream_keys:
            # Save each stream to database
            saved_count = 0
            for stream_id, stream_data in stream_keys.items():
                # Extract stream key from cdn info
                stream_key = ''
                stream_name = stream_data.get('title', '')
                if 'cdn' in stream_data and 'ingestionInfo' in stream_data['cdn']:
                    stream_key = stream_data['cdn']['ingestionInfo'].get('streamName', '')
                
                # Save to database
                if save_stream_mapping(user_id, token_file, stream_id, {
                    'stream_name': stream_name,
                    'stream_key': stream_key,
                    'metadata': stream_data
                }):
                    saved_count += 1
            
            if saved_count > 0:
                flash(f'Successfully fetched and saved {saved_count} stream key(s)!', 'success')
            else:
                flash('No stream keys were saved', 'warning')
        else:
            flash('No stream keys found in this channel', 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('stream_keys'))

@app.route('/create_new_stream', methods=['POST'])
@login_required
def create_new_stream():
    """Create a new stream key in YouTube Studio"""
    from modules.youtube.kunci import get_youtube_service
    from modules.database import save_stream_mapping
    
    user_id = int(current_user.id)
    stream_title = request.form.get('stream_title', '').strip()
    token_file = request.form.get('token_file')
    
    if not stream_title:
        flash('Stream title is required', 'error')
        return redirect(url_for('stream_keys'))
    
    if not token_file:
        flash('Please select a token file', 'error')
        return redirect(url_for('stream_keys'))
    
    try:
        # Get full token path using per-user folder structure
        token_path = get_token_path(token_file, user_id)
        
        if not os.path.exists(token_path):
            flash(f'Token file not found: {token_file}', 'error')
            return redirect(url_for('stream_keys'))
        
        # Create YouTube service using token
        youtube = get_youtube_service(token_path)
        
        # Create new live stream
        stream_body = {
            'snippet': {'title': stream_title},
            'cdn': {
                'frameRate': 'variable',
                'ingestionType': 'rtmp',
                'resolution': 'variable'
            }
        }
        
        response = youtube.liveStreams().insert(
            part='snippet,cdn',
            body=stream_body
        ).execute()
        
        stream_id = response['id']
        stream_key = response['cdn']['ingestionInfo']['streamName']
        
        # Save to database
        save_stream_mapping(user_id, token_file, stream_id, {
            'stream_name': stream_title,
            'stream_key': stream_key,
            'metadata': response
        })
        
        flash(f'Stream key created successfully! Title: "{stream_title}", Key: {stream_key}', 'success')
        
    except Exception as e:
        flash(f'Error creating stream: {str(e)}', 'error')
    
    return redirect(url_for('stream_keys'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect to home if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = authenticate_user(username, password)
        if user:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect to home if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()
        
        if not username or not password:
            flash('Username dan password wajib diisi', 'error')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Konfirmasi password tidak cocok', 'error')
            return redirect(url_for('register'))
        
        ok, msg = create_user(username, password, role='user')
        if ok:
            flash('Registrasi berhasil, silakan login', 'success')
            return redirect(url_for('login'))
        else:
            flash(msg, 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'success')
    return redirect(url_for('login'))

@app.route('/license', methods=['GET', 'POST'])
@login_required
@require_admin
def license_page():
    """License management page"""
    validator = LicenseValidator()
    system_info = get_system_info()
    license_info = validator.get_license_info()
    
    # Check current license status
    valid, message, days = validator.verify_license()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'activate':
            license_key = request.form.get('license_key', '').strip()
            
            if not license_key:
                flash('Masukkan kode lisensi!', 'error')
            else:
                success, msg = validator.activate_license(license_key)
                if success:
                    flash(msg, 'success')
                    return redirect(url_for('license_page'))
                else:
                    flash(msg, 'error')
        
        elif action == 'verify':
            valid, msg, days = validator.verify_license(force_online=True)
            if valid:
                flash(f'{msg}', 'success')
            else:
                flash(f'{msg}', 'error')
            return redirect(url_for('license_page'))
    
    return render_template('license.html', 
                         system_info=system_info,
                         license_info=license_info,
                         valid=valid,
                         message=message,
                         days_remaining=days)


# Helper function to get user usage for templates
def get_current_user_usage():
    """Get current user's usage stats for display in templates"""
    if not current_user.is_authenticated:
        return None
    
    from modules.auth import get_user_limits
    try:
        user_id = int(current_user.id)
        limits = get_user_limits(user_id)
        return limits
    except:
        return None

# Make it available in all templates
@app.context_processor
def inject_user_usage():
    return dict(user_usage=get_current_user_usage())

@app.route('/')
def home():
    # Show landing page if not authenticated
    if not current_user.is_authenticated:
        return render_template('landing.html')

    # Get schedules data when authenticated (dashboard)
    try:
        df = pd.read_excel(EXCEL_FILE)
        schedules = df.to_dict('records')
    except:
        schedules = []

    # Get tokens (per-user)
    user_id = int(current_user.id)
    tokens = get_token_files(user_id)
    
    return render_template('index.html', schedules=schedules, tokens=tokens)

# API Endpoints for Dashboard
@app.route('/api/system-stats')
@login_required
def api_system_stats():
    """Get real-time system statistics"""
    try:
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory Usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = round(memory.used / (1024**3), 2)  # GB
        memory_total = round(memory.total / (1024**3), 2)  # GB
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = round(disk.used / (1024**3), 2)  # GB
        disk_total = round(disk.total / (1024**3), 2)  # GB
        
        # Network Speed (bytes per second)
        net_io_start = psutil.net_io_counters()
        time.sleep(1)
        net_io_end = psutil.net_io_counters()
        
        download_speed = (net_io_end.bytes_recv - net_io_start.bytes_recv) / 1024  # KB/s
        upload_speed = (net_io_end.bytes_sent - net_io_start.bytes_sent) / 1024  # KB/s
        
        return jsonify({
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count
            },
            'memory': {
                'percent': memory_percent,
                'used': memory_used,
                'total': memory_total
            },
            'disk': {
                'percent': disk_percent,
                'used': disk_used,
                'total': disk_total
            },
            'network': {
                'download': round(download_speed, 2),
                'upload': round(upload_speed, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get schedules data
        try:
            df = pd.read_excel(EXCEL_FILE)
            schedules = df.to_dict('records')
            total_schedules = len(schedules)
            pending_schedules = len([s for s in schedules if not s.get('success', False)])
            completed_schedules = len([s for s in schedules if s.get('success', False)])
        except:
            schedules = []
            total_schedules = 0
            pending_schedules = 0
            completed_schedules = 0
        
        # Get live streams data
        streams = get_live_streams()
        total_streams = len(streams)
        active_streams = len([s for s in streams if s.get('status') == 'live'])
        scheduled_streams = len([s for s in streams if s.get('status') == 'scheduled'])
        completed_streams = len([s for s in streams if s.get('status') == 'completed'])
        
        # Get tokens count (per-user)
        user_id = int(current_user.id)
        tokens = get_token_files(user_id)
        total_tokens = len(tokens)
        
        # Get videos count
        videos = get_video_database()
        total_videos = len(videos)
        
        # Get active FFmpeg processes
        active_processes = len(live_processes)
        
        # Calculate today's streaming duration
        today = datetime.now().date()
        today_streams = [s for s in streams if 'start_date' in s]
        today_duration = 0
        for stream in today_streams:
            try:
                start_date = datetime.strptime(stream['start_date'], '%Y-%m-%dT%H:%M').date()
                if start_date == today and 'duration' in stream:
                    today_duration += int(stream.get('duration', 0))
            except:
                pass
        
        return jsonify({
            'schedules': {
                'total': total_schedules,
                'pending': pending_schedules,
                'completed': completed_schedules
            },
            'streams': {
                'total': total_streams,
                'active': active_streams,
                'scheduled': scheduled_streams,
                'completed': completed_streams
            },
            'tokens': total_tokens,
            'videos': total_videos,
            'active_processes': active_processes,
            'today_duration': today_duration
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule-timeline')
@login_required
def api_schedule_timeline():
    """Get schedule timeline for calendar view"""
    try:
        df = pd.read_excel(EXCEL_FILE)
        schedules = df.to_dict('records')
        
        timeline = []
        for schedule in schedules:
            try:
                scheduled_time = pd.to_datetime(schedule['scheduledStartTime'])
                timeline.append({
                    'title': schedule.get('title', 'No Title'),
                    'date': scheduled_time.strftime('%Y-%m-%d'),
                    'time': scheduled_time.strftime('%H:%M'),
                    'status': 'completed' if schedule.get('success', False) else 'pending',
                    'privacy': schedule.get('privacyStatus', 'unlisted')
                })
            except:
                pass
        
        return jsonify(timeline)
    except:
        return jsonify([])

@app.route('/api/activity-log')
@login_required
def api_activity_log():
    """Get recent activity log"""
    try:
        activities = []
        
        # Get recent streams
        streams = get_live_streams()
        for stream in streams[-10:]:  # Last 10 streams
            status_icon = '🔴' if stream.get('status') == 'live' else '✅' if stream.get('status') == 'completed' else '📅'
            activities.append({
                'icon': status_icon,
                'title': stream.get('title', 'Unknown'),
                'action': 'Streaming' if stream.get('status') == 'live' else 'Completed' if stream.get('status') == 'completed' else 'Scheduled',
                'time': stream.get('start_date', 'Unknown time'),
                'type': stream.get('status', 'unknown')
            })
        
        # Sort by time (most recent first)
        activities.reverse()
        
        return jsonify(activities[:15])  # Return last 15 activities
    except Exception as e:
        return jsonify([])

@app.route('/api/active-timers')
@login_required
def api_active_timers():
    """Get active auto-stop timers"""
    try:
        timers = get_stream_timers()
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        
        active_timer_list = []
        for timer in timers:
            stop_time = datetime.fromisoformat(timer['stop_time'])
            time_remaining = (stop_time - current_time).total_seconds()
            
            # Only include timers that haven't expired yet
            if time_remaining > 0:
                active_timer_list.append({
                    'stream_id': timer['stream_id'],
                    'stream_title': timer['stream_title'],
                    'pid': timer['pid'],
                    'start_time': timer['start_time'],
                    'stop_time': timer['stop_time'],
                    'duration_minutes': timer['duration_minutes'],
                    'time_remaining_seconds': int(time_remaining),
                    'time_remaining_formatted': f"{int(time_remaining // 60)}m {int(time_remaining % 60)}s"
                })
        
        return jsonify(active_timer_list)
    except Exception as e:
        print(f"[API] Error getting active timers: {e}")
        return jsonify([])

@app.route('/video-gallery')
@login_required
def video_gallery():
    videos = get_video_database()
    return render_template('video_gallery.html', videos=videos)

@app.route('/upload-video', methods=['POST'])
@login_required
@demo_readonly
def upload_video():
    # Check storage limit before upload
    from modules.auth import can_user_upload
    
    user_id = int(current_user.id)
    files = request.files.getlist('video_files')
    
    # Calculate total size
    total_size = 0
    for file in files:
        if file and hasattr(file, 'content_length') and file.content_length:
            total_size += file.content_length
    
    total_size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
    
    # Check if user can upload this size
    can_upload, message = can_user_upload(user_id, total_size_mb)
    if not can_upload:
        flash(f'Upload failed: {message}', 'error')
        return redirect(url_for('video_gallery'))
    
    # Continue with original upload logic...
    # Check if multiple files or single file
    files = request.files.getlist('video_files')
    
    # Fallback to old single file upload for compatibility
    if not files or (len(files) == 1 and files[0].filename == ''):
        if 'video_file' in request.files:
            files = [request.files['video_file']]
        else:
            flash('No files selected', 'danger')
            return redirect(url_for('video_gallery'))
    
    if not files or all(f.filename == '' for f in files):
        flash('No files selected', 'danger')
        return redirect(url_for('video_gallery'))
    
    uploaded_count = 0
    failed_count = 0
    from modules.database import add_video_to_db
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            try:
                # Generate unique filename
                original_filename = secure_filename(file.filename)
                file_extension = original_filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                
                # Save the file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Use original filename as title (without extension)
                video_title = original_filename.rsplit('.', 1)[0]
                
                # Generate thumbnail from first frame
                thumbnail_filename = None
                thumbnail_id = None
                try:
                    thumbnail_filename = f"{uuid.uuid4()}.jpg"
                    thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
                    
                    # Use ffmpeg to extract first frame
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-i', file_path,
                        '-ss', '00:00:01',
                        '-vframes', '1',
                        '-q:v', '2',
                        '-y',  # Overwrite
                        thumbnail_path
                    ]
                    result = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=30)
                    
                    # If successful, add to thumbnail database
                    if result.returncode == 0 and os.path.exists(thumbnail_path):
                        from modules.database import add_thumbnail
                        thumbnail_title = f"Auto: {video_title[:50]}"
                        thumbnail_id = str(uuid.uuid4())
                        add_thumbnail(user_id, {
                            'id': thumbnail_id,
                            'filename': thumbnail_filename,
                            'title': thumbnail_title,
                            'original_filename': f"{video_title[:50]}.jpg"
                        })
                        logging.info(f"✓ Auto-generated thumbnail: {thumbnail_filename} for user {user_id}")
                    else:
                        thumbnail_filename = None
                except Exception as e:
                    logging.error(f"Could not generate thumbnail for {original_filename}: {e}")
                    thumbnail_filename = None
                
                # Add to database using proper function
                video_data = {
                    'id': str(uuid.uuid4()),  # Generate unique ID
                    'title': video_title,
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'thumbnail': thumbnail_filename if thumbnail_filename else '',
                    'source': 'local'
                }
                
                add_video_to_db(video_data)  # ✅ Saves to database properly
                
                uploaded_count += 1
                logging.info(f"Successfully uploaded: {original_filename}")
                
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                logging.error(f"Failed to upload {file.filename}: {error_msg}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
        else:
            failed_count += 1
            logging.warning(f"Invalid file type: {file.filename}")
    
    # Always return JSON response (form submission via AJAX)
    if uploaded_count > 0 and failed_count == 0:
        message = f'{uploaded_count} video{"s" if uploaded_count > 1 else ""} uploaded successfully!'
        return jsonify({'success': True, 'message': message, 'uploaded': uploaded_count}), 200
    elif uploaded_count > 0 and failed_count > 0:
        message = f'{uploaded_count} uploaded, {failed_count} failed'
        return jsonify({'success': True, 'message': message, 'uploaded': uploaded_count, 'failed': failed_count}), 200
    else:
        error_msg = 'All uploads failed. Check logs for details.'
        logging.error(f"Upload failed - uploaded: {uploaded_count}, failed: {failed_count}")
        return jsonify({'success': False, 'message': error_msg}), 200  # Changed to 200 to avoid frontend error

@app.route('/import-from-drive', methods=['POST'])
@login_required
def import_from_drive():
    drive_link = request.form.get('drive_link', '')
    video_title = request.form.get('drive_video_title', 'Untitled Video')
    
    if not drive_link:
        flash('No Google Drive link provided', 'danger')
        return redirect(url_for('video_gallery'))
    
    try:
        # Extract file ID from Google Drive link
        file_id = None
        if 'drive.google.com/file/d/' in drive_link:
            file_id = drive_link.split('/file/d/')[1].split('/')[0]
        elif 'drive.google.com/open?id=' in drive_link:
            file_id = drive_link.split('open?id=')[1].split('&')[0]
        
        if not file_id:
            flash('Invalid Google Drive link format', 'danger')
            return redirect(url_for('video_gallery'))
        
        # Create direct download link
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # Download the file
        response = requests.get(download_url, stream=True)
        
        # Check if it's a video file by content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('video/'):
            flash('The file is not a video or is not publicly accessible', 'danger')
            return redirect(url_for('video_gallery'))
        
        # Generate unique filename
        file_extension = 'mp4'  # Default extension
        if 'content-disposition' in response.headers:
            disposition = response.headers['content-disposition']
            if 'filename=' in disposition:
                original_filename = disposition.split('filename=')[1].strip('"\'')
                if '.' in original_filename:
                    file_extension = original_filename.rsplit('.', 1)[1].lower()
        
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Add to database
        from modules.database import add_video_to_db
        video_data = {
            'id': str(uuid.uuid4()),  # Generate unique ID
            'title': video_title,
            'filename': unique_filename,
            'original_filename': f"google_drive_{file_id}.{file_extension}",
            'source': 'google_drive',
            'drive_file_id': file_id
        }
        add_video_to_db(video_data)  # ✅ Saves to database properly
        
        flash('Video imported from Google Drive successfully!', 'success')
    except Exception as e:
        flash(f'Error importing video: {str(e)}', 'danger')
    
    return redirect(url_for('video_gallery'))

@app.route('/delete-video/<video_id>')
@login_required
@demo_readonly
def delete_video(video_id):
    """Delete video - FROM DATABASE"""
    videos = get_video_database()
    
    # Find the video to delete
    video_to_delete = None
    for video in videos:
        if video['id'] == video_id:
            video_to_delete = video
            break
    
    if video_to_delete:
        # Delete the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], video_to_delete['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete thumbnail if exists
        if video_to_delete.get('thumbnail'):
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, video_to_delete['thumbnail'])
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        
        # Remove from database
        from modules.database import delete_video_from_db
        delete_video_from_db(video_id)  # ✅ Deletes from database properly
        
        flash('Video deleted successfully!', 'success')
    else:
        flash('Video not found', 'danger')
    
    return redirect(url_for('video_gallery'))

@app.route('/videos/<filename>')
@login_required
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Thumbnail Routes
@app.route('/thumbnail-gallery')
@login_required
def thumbnail_gallery():
    thumbnails = get_thumbnail_database()
    return render_template('thumbnail_gallery.html', thumbnails=thumbnails)

@app.route('/upload-thumbnail', methods=['POST'])
@login_required
@demo_readonly
def upload_thumbnail():
    if 'thumbnail_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('thumbnail_gallery'))
    
    file = request.files['thumbnail_file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('thumbnail_gallery'))
    
    if file and allowed_thumbnail_file(file.filename):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Save the file
        file_path = os.path.join(THUMBNAIL_FOLDER, unique_filename)
        file.save(file_path)
        
        # Add to database
        thumbnail_title = request.form.get('thumbnail_title', 'Untitled Thumbnail')
        from modules.database import add_thumbnail_to_db
        thumbnail_data = {
            'id': str(uuid.uuid4()),  # Generate unique ID
            'title': thumbnail_title,
            'filename': unique_filename,
            'original_filename': original_filename
        }
        add_thumbnail_to_db(thumbnail_data)  # ✅ Saves to database properly
        
        flash('Thumbnail uploaded successfully!', 'success')
        return redirect(url_for('thumbnail_gallery'))
    
    flash('Invalid file type. Allowed types: ' + ', '.join(ALLOWED_THUMBNAIL_EXTENSIONS), 'danger')
    return redirect(url_for('thumbnail_gallery'))

@app.route('/delete-thumbnail/<thumbnail_id>')
@login_required
@demo_readonly
def delete_thumbnail(thumbnail_id):
    """Delete thumbnail - FROM DATABASE"""
    thumbnails = get_thumbnail_database()
    
    # Find the thumbnail to delete
    thumbnail_to_delete = None
    for thumbnail in thumbnails:
        if thumbnail['id'] == thumbnail_id:
            thumbnail_to_delete = thumbnail
            break
    
    if thumbnail_to_delete:
        # Delete the file
        file_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_to_delete['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from database
        from modules.database import delete_thumbnail_from_db
        delete_thumbnail_from_db(thumbnail_id)  # ✅ Deletes from database properly
        
        flash('Thumbnail deleted successfully!', 'success')
    else:
        flash('Thumbnail not found', 'danger')
    
    return redirect(url_for('thumbnail_gallery'))

@app.route('/thumbnails/<filename>')
@login_required
def serve_thumbnail(filename):
    return send_from_directory(THUMBNAIL_FOLDER, filename)

# Live Stream Routes
@app.route('/live-streams')
@login_required
def live_streams():
    """Display live streams - READ FROM DATABASE"""
    streams = get_live_streams()
    videos = get_video_database()
    stream_mapping = get_stream_mapping()
    
    # Remove duplicates based on id
    unique_streams = []
    stream_ids = set()
    for stream in streams:
        if stream['id'] not in stream_ids:
            stream_ids.add(stream['id'])
            unique_streams.append(stream)
    
    # Sort streams by start date (newest first)
    unique_streams.sort(key=lambda x: datetime.strptime(x['start_date'], '%Y-%m-%dT%H:%M'), reverse=True)
    
    # Add video titles and backward compatibility fields for display
    for stream in unique_streams:
        video_path = os.path.join(VIDEO_FOLDER, stream.get('video_file', ''))
        stream['video_title'] = get_video_title(stream.get('video_file', ''))
        
        # Backward compatibility: map database fields to template fields
        # server_type → rtmp_server (for template display)
        if 'server_type' in stream and 'rtmp_server' not in stream:
            stream['rtmp_server'] = stream['server_type']
        
        # stream_url → custom_rtmp (for template display)
        if 'stream_url' in stream and 'custom_rtmp' not in stream:
            stream['custom_rtmp'] = stream['stream_url']
        
        # Convert repeat_daily to boolean for template
        if 'repeat_daily' in stream:
            stream['repeat_daily'] = bool(stream['repeat_daily'])
    
    return render_template('live_streams.html', streams=unique_streams, videos=videos, rtmp_servers=RTMP_SERVERS, stream_mapping=stream_mapping)

@app.route('/edit-live-stream/<stream_id>', methods=['GET', 'POST'])
@login_required
@demo_readonly
def edit_live_stream(stream_id):
    """Edit live stream - UPDATE DATABASE"""
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role):
        flash('Role Anda tidak diizinkan mengedit jadwal (demo-preview).', 'error')
        return redirect(url_for('live_streams'))
    
    user_id = int(current_user.id)
    from modules.database import get_live_stream_by_id, update_live_stream
    
    # Get stream from database
    stream_to_edit = get_live_stream_by_id(stream_id, user_id)
    
    if not stream_to_edit:
        flash('Jadwal live stream tidak ditemukan')
        return redirect(url_for('live_streams'))
    
    if request.method == 'POST':
        # Get form data
        rtmp_server = request.form.get('rtmp_server')
        custom_rtmp = request.form.get('custom_rtmp', '')
        
        # Prepare updates
        # Map form fields to database fields:
        # rtmp_server → server_type
        # custom_rtmp → stream_url
        updates = {
            'title': request.form['title'],
            'start_date': request.form['start_date'],
            'server_type': rtmp_server,  # rtmp_server → server_type
            'stream_key': request.form['stream_key'],
            'video_file': request.form['video_file'],
            'duration': int(request.form.get('duration', 0)) if request.form.get('duration') else 0,
            'stream_url': custom_rtmp if rtmp_server == 'custom' else '',  # custom_rtmp → stream_url
            'repeat_daily': 1 if 'repeat_daily' in request.form else 0
        }
        
        try:
            update_live_stream(stream_id, user_id, updates)
            logging.info(f"[LIVE STREAM] Updated: {stream_id} by user {current_user.username}")
            flash('Jadwal live stream berhasil diperbarui', 'success')
        except Exception as e:
            logging.error(f"[LIVE STREAM] Error updating stream: {e}")
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('live_streams'))
    
    # GET request - load form
    videos = get_video_database()
    
    # Add backward compatibility fields for template
    # server_type → rtmp_server (for template)
    # stream_url → custom_rtmp (for template)
    stream_to_edit['rtmp_server'] = stream_to_edit.get('server_type', 'youtube')
    stream_to_edit['custom_rtmp'] = stream_to_edit.get('stream_url', '')
    
    return render_template('edit_live_stream.html', stream=stream_to_edit, videos=videos, rtmp_servers=RTMP_SERVERS)

@app.route('/add-live-stream', methods=['POST'])
@login_required
@demo_readonly
def add_live_stream():
    # Check stream limit before adding
    from modules.auth import can_user_add_stream
    
    user_id = int(current_user.id)
    can_add, message = can_user_add_stream(user_id)
    if not can_add:
        flash(f'Cannot add stream: {message}', 'error')
        return redirect(url_for('live_streams'))
    
    # Continue with original logic...
    # Role restriction
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role):
        flash('Role Anda tidak diizinkan membuat live/schedule (demo-preview).', 'error')
        return redirect(url_for('live_streams'))
    # Get form data
    title = request.form.get('title')
    start_date = request.form.get('start_date')
    rtmp_server = request.form.get('rtmp_server')
    stream_key = request.form.get('stream_key')
    video_file = request.form.get('video_file')
    duration = request.form.get('duration')
    repeat_daily = 'repeat_daily' in request.form
    custom_rtmp = request.form.get('custom_rtmp', '')
    
    # Validate inputs
    if not title or not start_date or not rtmp_server or not stream_key or not video_file:
        flash('Semua field harus diisi')
        return redirect(url_for('live_streams'))
    
    # Prepare data for database
    # Map form fields to database fields:
    # rtmp_server → server_type
    # custom_rtmp → stream_url
    from modules.database import add_live_stream_to_db
    
    stream_data = {
        'id': str(uuid.uuid4()),
        'title': title,
        'video_file': video_file,
        'stream_key': stream_key,
        'stream_url': custom_rtmp if rtmp_server == 'custom' else '',
        'server_type': rtmp_server,  # rtmp_server → server_type
        'status': 'scheduled',
        'start_date': start_date,
        'duration': int(duration) if duration else 0,
        'repeat_daily': 1 if repeat_daily else 0
    }
    
    try:
        add_live_stream_to_db(stream_data)
        logging.info(f"[LIVE STREAM] Added: {title} for user {current_user.username}")
        flash('Jadwal live stream berhasil ditambahkan', 'success')
    except Exception as e:
        logging.error(f"[LIVE STREAM] Error adding stream: {e}")
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('live_streams'))

@app.route('/start-live-stream-now/<stream_id>', methods=['GET', 'POST'])
@login_required
@demo_readonly
def start_live_stream_now(stream_id):
    # Role restriction
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role):
        flash('Role Anda tidak diizinkan memulai live (demo-preview).', 'error')
        return redirect(url_for('live_streams'))
    streams = get_live_streams()
    
    for stream in streams:
        if stream['id'] == stream_id:
            # Owner check unless admin
            if stream.get('owner') and stream['owner'] != current_user.username and not role_can_manage(role):
                flash('Tidak dapat memulai live stream milik user lain.', 'error')
                return redirect(url_for('live_streams'))
            if stream['status'] == 'scheduled' or stream['status'] == 'completed':
                # Add backward compatibility mapping before starting stream
                # server_type → rtmp_server, stream_url → custom_rtmp
                if 'server_type' in stream and 'rtmp_server' not in stream:
                    stream['rtmp_server'] = stream['server_type']
                if 'stream_url' in stream and 'custom_rtmp' not in stream:
                    stream['custom_rtmp'] = stream['stream_url']
                
                # Start the stream immediately
                if start_ffmpeg_stream(stream):
                    stream['status'] = 'live'
                    save_live_streams(streams)
                    flash('Live stream dimulai')
                    # Tambahkan log untuk debugging
                    print(f"Live stream berhasil dimulai untuk ID: {stream_id}")
                else:
                    flash('Gagal memulai live stream. Pastikan ffmpeg terinstall dan video tersedia.')
                    print(f"Gagal memulai live stream untuk ID: {stream_id}")
            break
    
    return redirect(url_for('live_streams'))

@app.route('/cancel-live-stream/<stream_id>', methods=['GET', 'POST'])
@login_required
@demo_readonly
def cancel_live_stream(stream_id):
    """Cancel/Delete live stream - USE DATABASE"""
    user_id = int(current_user.id)
    action = request.args.get('action', 'stop')  # Default action is stop
    
    # Get stream from database
    from modules.database import get_live_stream_by_id, delete_live_stream, update_live_stream
    stream = get_live_stream_by_id(stream_id, user_id)
    
    if not stream:
        flash('Live stream tidak ditemukan', 'error')
        return redirect(url_for('live_streams'))
    
    # Check ownership
    role = getattr(current_user, 'role', 'user')
    if stream['user_id'] != user_id and not role_can_manage(role):
        flash('Tidak dapat mengubah stream milik user lain.', 'error')
        return redirect(url_for('live_streams'))
    
    if action == 'delete':
        # Delete from database
        if stream['status'] == 'live':
            stop_ffmpeg_stream(stream_id)
        
        if delete_live_stream(stream_id, user_id):
            flash('Jadwal live stream berhasil dihapus', 'success')
        else:
            flash('Gagal menghapus jadwal live stream', 'error')
    else:  # action == 'stop'
        if stream['status'] == 'live':
            stop_ffmpeg_stream(stream_id)
            # Update status to completed
            update_live_stream(stream_id, user_id, {'status': 'completed'})
            flash('Live stream berhasil dihentikan', 'success')
        else:
            flash('Live stream tidak sedang berjalan', 'warning')
    
    return redirect(url_for('live_streams'))

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    role = getattr(current_user, 'role', 'demo')
    if not role_can_manage(role):
        flash('Akses ditolak: fitur khusus admin.', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role_new = request.form.get('role', 'demo').strip().lower()
            ok, msg = create_user(username, password, role=role_new)
            flash(msg, 'success' if ok else 'error')
        elif action == 'update_role':
            username = request.form.get('username')
            role_new = request.form.get('role', 'demo').strip().lower()
            ok, msg = change_role(username, role_new)
            flash(msg, 'success' if ok else 'error')
        elif action == 'delete':
            username = request.form.get('username', '').strip()
            if username == current_user.username:
                flash('Cannot delete your own account', 'error')
            else:
                ok, msg = delete_user(username)
                flash(msg, 'success' if ok else 'error')
        elif action == 'change_password':
            username = request.form.get('username', '').strip()
            new_password = request.form.get('new_password', '').strip()
            if not new_password:
                flash('Password cannot be empty', 'error')
            elif len(new_password) < 4:
                flash('Password must be at least 4 characters', 'error')
            else:
                ok, msg = change_user_password(username, new_password)
                flash(msg, 'success' if ok else 'error')
        return redirect(url_for('admin_users'))
    users = list_users()
    
    # Get user limits data for the limits tab
    from modules.auth import get_all_users_with_limits
    user_limits = get_all_users_with_limits()
    
    return render_template('admin_users_with_limits.html', users=users, user_limits=user_limits)

# Route sudah didefinisikan sebelumnya

@app.route('/schedules')
@login_required
def schedules():
    """View schedules page - FROM DATABASE (per-user)"""
    try:
        user_id = int(current_user.id)
        
        # Get schedules from database (user-specific)
        from modules.database import get_schedules_by_user
        db_schedules = get_schedules_by_user(user_id)
        
        # Convert to format compatible with templates
        schedules = []
        for schedule in db_schedules:
            # Clean thumbnail path: remove 'thumbnails/' prefix if exists
            thumbnail_raw = schedule.get('thumbnail', '')
            thumbnail_clean = thumbnail_raw.replace('thumbnails/', '') if thumbnail_raw else ''
            
            schedules.append({
                'id': schedule['id'],
                'title': schedule['title'],
                'description': schedule.get('description', ''),
                'scheduledStartTime': schedule['scheduled_start_time'],
                'videoFile': schedule.get('video_file', ''),
                'thumbnail': thumbnail_clean,
                'thumbnailFile': thumbnail_clean,
                'streamNameExisting': schedule.get('stream_name', ''),
                'streamIdExisting': schedule.get('stream_id', ''),
                'tokenFile': schedule.get('token_file', ''),
                'token_file': schedule.get('token_file', ''),
                'privacyStatus': schedule.get('privacy_status', 'unlisted'),
                'autoStart': bool(schedule.get('auto_start', 0)),
                'autoStop': bool(schedule.get('auto_stop', 0)),
                'madeForKids': bool(schedule.get('made_for_kids', 0)),
                'repeat_daily': bool(schedule.get('repeat_daily', 0)),
                'success': bool(schedule.get('success', 0)),
                'broadcastLink': schedule.get('broadcast_link', '')
            })
        
    except Exception as e:
        logging.error(f"Error loading schedules: {e}")
        schedules = []
    
    stream_mapping = get_stream_mapping()
    # Get list of available tokens (per-user)
    user_id = int(current_user.id)
    tokens = get_token_files(user_id)
    # Get thumbnails
    thumbnails = get_thumbnail_database()
    
    # Get scheduler status and config (per-user)
    role = getattr(current_user, 'role', 'user')
    scheduler_status = get_scheduler_status()
    schedule_times = load_schedule_times(user_id=user_id)  # Per-user schedule times
    is_admin = role_can_manage(role)
    
    return render_template('schedules.html', 
                         schedules=schedules, 
                         stream_mapping=stream_mapping, 
                         tokens=tokens, 
                         thumbnails=thumbnails,
                         scheduler_status=scheduler_status,
                         schedule_times=schedule_times,
                         is_admin=is_admin)

@app.route('/add_schedule', methods=['POST'])
@login_required
@demo_readonly
def add_schedule():
    """Add schedule to database - PER USER"""
    # Check stream/schedule limit
    from modules.auth import can_user_add_stream
    
    user_id = int(current_user.id)
    can_add, message = can_user_add_stream(user_id)
    if not can_add:
        flash(f'Cannot add schedule: {message}', 'error')
        return redirect(url_for('schedules'))
    
    # Restrict demo role from adding schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat menambahkan jadwal.', 'error')
        return redirect(url_for('schedules'))
    
    try:
        data = request.form.to_dict()
        
        # Resolve stream name and log for debugging
        submitted_stream = data.get('streamNameExisting', '')
        resolved_stream = get_stream_name(submitted_stream)
        app.logger.debug(f"add_schedule: submitted stream='{submitted_stream}' resolved='{resolved_stream}'")

        # Fix thumbnail path: add 'thumbnails/' prefix if needed
        thumbnail_file = data.get('thumbnailFile', '').strip()
        if thumbnail_file and not thumbnail_file.startswith('thumbnails/'):
            thumbnail_file = f'thumbnails/{thumbnail_file}'
        
        # Insert into database instead of Excel
        from modules.database import add_schedule
        schedule_data = {
            'title': data['title'],
            'description': data.get('description', ''),
            'scheduled_start_time': data['scheduledStartTime'],
            'video_file': data.get('videoFile', ''),
            'thumbnail': thumbnail_file,
            'stream_name': resolved_stream,
            'stream_id': data.get('streamIdExisting', ''),
            'token_file': data['tokenFile'],
            'repeat_daily': 1 if data.get('repeat_daily') == 'on' else 0,
            'privacy_status': data.get('privacyStatus', 'unlisted'),
            'auto_start': 1 if data.get('autoStart') == 'on' else 0,
            'auto_stop': 1 if data.get('autoStop') == 'on' else 0,
            'made_for_kids': 1 if data.get('madeForKids') == 'on' else 0,
            'success': 0
        }
        
        add_schedule(user_id, schedule_data)
        flash('Schedule added successfully!', 'success')
        
    except Exception as e:
        logging.error(f"Error adding schedule: {e}")
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/run_schedule_now/<int:index>', methods=['POST'])
@login_required
@demo_readonly
def run_schedule_now(index):
    """Run a single schedule manually (on-demand execution)"""
    user_id = int(current_user.id)
    try:
        # Read Excel
        df = pd.read_excel(EXCEL_FILE)
        
        # Validate index
        if index >= len(df):
            flash('Schedule not found', 'error')
            return redirect(url_for('schedules'))
        
        row = df.iloc[index]
        
        # Check if already completed
        if row.get('success', False):
            flash('This schedule has already been completed', 'warning')
            return redirect(url_for('schedules'))
        
        # Extract schedule data
        title = row['title']
        description = row['description']
        scheduled_start_time = row['scheduledStartTime']
        privacy_status = row.get('privacyStatus', 'unlisted')
        auto_start = bool(row.get('autoStart', False))
        auto_stop = bool(row.get('autoStop', False))
        made_for_kids = bool(row.get('madeForKids', False))
        token_file = row['tokenFile']
        use_existing_stream = bool(row.get('useExistingStream', False))
        
        # Handle NaN values properly
        stream_name_existing = row.get('streamNameExisting', '')
        stream_name_existing = '' if pd.isna(stream_name_existing) else str(stream_name_existing).strip()
        
        thumbnail_path = row.get('thumbnailFile', '')
        thumbnail_path = '' if pd.isna(thumbnail_path) else str(thumbnail_path).strip()
        
        repeat_daily = bool(row.get('repeat_daily', False))
        
        # Import scheduler functions
        from modules.youtube.live import schedule_live_stream
        from modules.youtube.kunci import get_youtube_service
        
        # Get YouTube service
        youtube = get_youtube_service(token_file)
        
        # Create broadcast on YouTube
        broadcast_id, stream_id = schedule_live_stream(
            youtube, title, description, scheduled_start_time,
            privacy_status, auto_start, auto_stop, made_for_kids,
            use_existing_stream, stream_name_existing, token_file
        )
        
        # Upload thumbnail if exists
        if thumbnail_path:
            # Normalize thumbnail path
            if not thumbnail_path.startswith('thumbnails/'):
                thumbnail_path = f'thumbnails/{thumbnail_path}'
            thumbnail_path = thumbnail_path.lstrip('/')
            
            if os.path.exists(thumbnail_path):
                youtube.thumbnails().set(
                    videoId=broadcast_id,
                    media_body=thumbnail_path
                ).execute()
                logging.info(f"Thumbnail uploaded: {thumbnail_path}")
            else:
                logging.warning(f"Thumbnail not found: {thumbnail_path}")
        
        # Update Excel
        df.at[index, 'success'] = True
        df.at[index, 'streamId'] = str(stream_id)
        broadcast_link = f"https://studio.youtube.com/video/{broadcast_id}/livestreaming"
        df.at[index, 'broadcastLink'] = broadcast_link
        
        # Send Telegram notification
        try:
            # Format time for display
            display_time = scheduled_start_time if isinstance(scheduled_start_time, str) else str(scheduled_start_time)
            logging.info(f"[TELEGRAM] Sending notification for: {title}")
            telegram_notifier.notify_schedule_created(title, display_time, broadcast_link, user_id=user_id)
            logging.info(f"[TELEGRAM] Notification sent successfully")
        except Exception as e:
            logging.error(f"[TELEGRAM] Failed to send notification: {e}", exc_info=True)
        
        # Handle repeat_daily
        if repeat_daily:
            # +1 day for tomorrow, reset success
            from datetime import timedelta
            current_date = pd.to_datetime(df.at[index, 'scheduledStartTime'])
            new_date = current_date + timedelta(days=1)
            df.at[index, 'scheduledStartTime'] = new_date.strftime('%Y-%m-%dT%H:%M')
            df.at[index, 'success'] = False  # Reset for tomorrow
            logging.info(f"[REPEAT DAILY] Rescheduled for {new_date}")
        else:
            logging.info(f"[ONE-TIME] Schedule completed")
        
        df.to_excel(EXCEL_FILE, index=False)
        
        flash(f'✅ Schedule "{title}" has been created successfully!', 'success')
        
    except Exception as e:
        logging.error(f"Error running schedule: {e}")
        flash(f'❌ Error: {str(e)}', 'error')
        
        # Send error notification
        try:
            telegram_notifier.notify_schedule_error(title if 'title' in locals() else 'Unknown', str(e), user_id=user_id)
        except:
            pass
    
    return redirect(url_for('schedules'))

@app.route('/tokens')
@login_required
def tokens():
    # Get tokens for current user only
    user_id = int(current_user.id)
    tokens = get_token_files(user_id)
    return render_template('tokens.html', tokens=tokens)

@app.route('/create_token', methods=['POST'])
@login_required
@demo_readonly
def create_token():
    try:
        from modules.services.client_secret_manager import get_user_client_secret_path
        
        token_name = request.form.get('token_name', 'token.json')
        if not token_name.endswith('.json'):
            token_name += '.json'
        
        # Get user's client_secret path
        user_id = int(current_user.id)
        client_secret_path = get_user_client_secret_path(user_id)
        
        if not client_secret_path or not os.path.exists(client_secret_path):
            flash('Please upload your client_secret.json first in YouTube API Settings', 'error')
            return redirect(url_for('tokens'))
        
        # Generate authorization URL using Flow
        flow = Flow.from_client_secrets_file(
            client_secret_path,
            scopes=SCOPES,
            redirect_uri='http://localhost'
        )
        
        # Generate authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        
        # Redirect to authorization page
        return render_template('token_authorization.html', 
                             auth_url=auth_url, 
                             token_name=token_name)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('tokens'))

@app.route('/complete_token', methods=['POST'])
@login_required
@demo_readonly
def complete_token():
    try:
        token_name = request.form.get('token_name', 'token.json')
        auth_input = request.form.get('auth_code', '').strip()
        
        if not auth_input:
            flash('Kode authorization tidak boleh kosong', 'error')
            return redirect(url_for('tokens'))
        
        # Extract authorization code from input
        # User can paste either:
        # 1. Full URL: http://localhost:5001/?code=4/0AVG7fiR...&scope=...
        # 2. Just the code: 4/0AVG7fiR...
        
        auth_code = auth_input
        
        # Check if input is a URL
        if 'code=' in auth_input:
            # Extract code parameter from URL
            try:
                from urllib.parse import urlparse, parse_qs
                
                # Parse URL
                parsed = urlparse(auth_input)
                params = parse_qs(parsed.query)
                
                if 'code' in params and params['code']:
                    auth_code = params['code'][0]
                    logging.info(f"Extracted authorization code from URL")
                else:
                    flash('Tidak dapat menemukan parameter "code" di URL', 'error')
                    return redirect(url_for('tokens'))
            except Exception as e:
                logging.error(f"Error parsing URL: {e}")
                flash(f'Error parsing URL: {str(e)}', 'error')
                return redirect(url_for('tokens'))
        
        # Get user's client_secret path
        from modules.services.client_secret_manager import get_user_client_secret_path
        user_id = int(current_user.id)
        client_secret_path = get_user_client_secret_path(user_id)
        
        if not client_secret_path or not os.path.exists(client_secret_path):
            flash('Please upload your client_secret.json first in YouTube API Settings', 'error')
            return redirect(url_for('tokens'))
        
        # Create flow again and fetch token
        flow = Flow.from_client_secrets_file(
            client_secret_path,
            scopes=SCOPES,
            redirect_uri='http://localhost'
        )
        
        # Fetch token using the authorization code
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # Save token to tokens folder (per-user)
        token_path = get_token_path(token_name, user_id)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())
        
        flash(f'Token {token_name} berhasil dibuat!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('tokens'))

@app.route('/delete_token', methods=['POST'])
@login_required
@demo_readonly
def delete_token():
    try:
        token_name = request.form.get('token_name')
        if not token_name:
            flash('Token name is required', 'error')
            return redirect(url_for('tokens'))
        
        if not token_name.endswith('.json'):
            token_name += '.json'
        
        # Check if it's a valid token file
        if token_name == 'client_secret.json':
            flash('Cannot delete client_secret.json', 'error')
            return redirect(url_for('tokens'))
        
        # Try to delete the token file from tokens folder (per-user)
        user_id = int(current_user.id)
        token_path = get_token_path(token_name, user_id)
        if os.path.exists(token_path):
            os.remove(token_path)
            
            # Also remove any associated stream mappings
            try:
                mapping = get_stream_mapping()
                if token_name in mapping:
                    del mapping[token_name]
                    with open('stream_mapping.json', 'w') as f:
                        json.dump(mapping, f, indent=4)
            except:
                pass  # Ignore errors with stream mapping cleanup
                
            flash(f'Token {token_name} has been deleted', 'success')
        else:
            flash(f'Token {token_name} not found', 'warning')
            
    except Exception as e:
        flash(f'Error deleting token: {str(e)}', 'error')
    
    return redirect(url_for('tokens'))

def check_and_run_schedules():
    """Check if any schedules should be run now"""
    # import live (now using modules.youtube.live)
    current_time = datetime.now(pytz.timezone(TIMEZONE))
    times = load_schedule_times()
    current_time_str = current_time.strftime('%H:%M')
    
    if current_time_str in times:
        try:
            from modules.youtube import live; live.main()  # Run the scheduler
            status = {
                'last_run': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'next_check': (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'last_status': 'Success',
                'active': True
            }
        except Exception as e:
            status = {
                'last_run': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'next_check': (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'last_status': f'Error: {str(e)}',
                'active': True
            }
    else:
        status = get_scheduler_status()
        status['next_check'] = (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
        status['active'] = True
    
    save_scheduler_status(status)
    return status

def start_scheduler_thread():
    def run_scheduler():
        while True:
            check_and_run_schedules()
            time.sleep(60)  # Wait for 1 minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

# DEPRECATED: Moved to /schedules page (admin section)
# @app.route('/auto_schedule')
# @login_required
# def auto_schedule():
#     schedule_times = load_schedule_times()
#     scheduler_status = get_scheduler_status()
#     return render_template('auto_schedule.html', 
#                          schedule_times=schedule_times,
#                          scheduler_status=scheduler_status)

@app.route('/update_schedule_times', methods=['POST'])
@login_required
def update_schedule_times():
    """Update schedule times - PER USER"""
    user_id = int(current_user.id)
    times = request.form.getlist('times[]')
    
    success = save_schedule_times(times, user_id=user_id)
    
    if success:
        flash('Schedule times updated successfully!', 'success')
    else:
        flash('Failed to update schedule times.', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/run_scheduler', methods=['POST'])
@login_required
def run_scheduler():
    """Run scheduler manually - PER USER"""
    user_id = int(current_user.id)
    try:
        from modules.youtube import live
        live.main()  # Run scheduler directly
        
        # Update status
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        status = {
            'last_run': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'next_check': (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'last_status': 'Success (Manual Run)',
            'active': True
        }
        save_scheduler_status(status)
        
        flash('Scheduler berhasil dijalankan!', 'success')
    except Exception as e:
        status = {
            'last_run': datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S'),
            'last_status': f'Error: {str(e)}',
            'active': True
        }
        save_scheduler_status(status)
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('schedules'))

# ==== License Management Routes ====
# Note: Main license_page route is defined earlier in the file (around line 1032)

@app.route('/license/activate', methods=['POST'])
@login_required
def activate_license():
    """Activate license with key"""
    license_key = request.form.get('license_key', '').strip().upper()
    
    if not license_key:
        flash('Masukkan kode lisensi!', 'error')
        return redirect(url_for('license_page'))
    
    try:
        validator = LicenseValidator()
        success, message = validator.activate_license(license_key)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
    except Exception as e:
        flash(f'Error aktivasi: {str(e)}', 'error')
    
    return redirect(url_for('license_page'))

@app.route('/license/verify', methods=['POST'])
@login_required
def verify_license_online():
    """Force online verification"""
    try:
        validator = LicenseValidator()
        valid, message, days = validator.verify_license(force_online=True)
        
        if valid:
            flash(f'✓ {message}', 'success')
        else:
            flash(f'✗ {message}', 'error')
    except Exception as e:
        flash(f'Error verifikasi: {str(e)}', 'error')
    
    return redirect(url_for('license_page'))

@app.route('/license/info')
@login_required
def get_license_info():
    """Get license info as JSON (for API/AJAX)"""
    try:
        validator = LicenseValidator()
        valid, message, days = validator.verify_license()
        
        return jsonify({
            'valid': valid,
            'message': message,
            'days_remaining': days if valid else 0,
            'license_info': validator.get_license_info(),
            'system_info': get_system_info()
        })
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': str(e),
            'error': True
        }), 500

@app.route('/telegram_settings', methods=['GET', 'POST'])
@login_required
def telegram_settings():
    """Telegram notification settings page - PER USER"""
    user_id = int(current_user.id)
    
    if request.method == 'POST':
        config = {
            'enabled': request.form.get('enabled') == 'on',
            'bot_token': request.form.get('bot_token', '').strip(),
            'chat_id': request.form.get('chat_id', '').strip()
        }
        
        telegram_notifier.save_config(config, user_id=user_id)
        flash('Telegram settings saved successfully!', 'success')
        return redirect(url_for('telegram_settings'))
    
    config = telegram_notifier.load_config(user_id=user_id)
    return render_template('telegram_settings.html', config=config)

@app.route('/telegram_test', methods=['POST'])
@login_required
def telegram_test():
    """Test Telegram bot connection - PER USER"""
    user_id = int(current_user.id)
    success, message = telegram_notifier.test_connection(user_id=user_id)
    return jsonify({'success': success, 'message': message})

# ==== New Features: Video Looping, AI Metadata, Bulk Upload ====

# Constants for new features
LOOPED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos', 'done')
LOOPED_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'looped_videos.json')
BULK_UPLOAD_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bulk_upload_queue.json')
AUTO_UPLOAD_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_upload_config.json')
METADATA_EXCEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metadata_templates.xlsx')

# Ensure folders exist
os.makedirs(LOOPED_FOLDER, exist_ok=True)

def get_looped_videos():
    """Get looped videos for current user from SQLite"""
    try:
        return get_looped_videos_data()
    except Exception as e:
        print(f"Error getting looped videos: {e}")
        return []
    try:
        with open(LOOPED_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_looped_videos(looped_videos):
    """Save looped videos database"""
    with open(LOOPED_DB_FILE, 'w') as f:
        json.dump(looped_videos, f, indent=4)

def get_bulk_upload_queue():
    """Get bulk upload queue for current user from SQLite"""
    try:
        return get_bulk_upload_queue_data()
    except Exception as e:
        print(f"Error getting upload queue: {e}")
        return []
    try:
        with open(BULK_UPLOAD_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_bulk_upload_queue(queue):
    """DEPRECATED - use add_bulk_upload_to_db or update_bulk_upload_in_db instead"""
    pass

def load_gemini_config(user_id=None):
    """Load Gemini API configuration - PER USER"""
    # Per-user configuration from database
    if user_id:
        try:
            from modules.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT gemini_api_key, gemini_model, gemini_custom_prompt 
                    FROM users WHERE id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row and row['gemini_api_key']:
                    return {
                        'api_key': row['gemini_api_key'],
                        'model': row['gemini_model'] or 'gemini-2.0-flash-exp',
                        'custom_prompt': row['gemini_custom_prompt']
                    }
        except Exception as e:
            logging.error(f"Error loading Gemini config for user {user_id}: {e}")
    
    # Fallback to global config file (legacy)
    config_file = 'gemini_config.json'
    if not os.path.exists(config_file):
        return None
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except:
        return None

def get_metadata_from_excel():
    """Load metadata templates from Excel file"""
    if not os.path.exists(METADATA_EXCEL_FILE):
        return []
    
    try:
        import openpyxl
        workbook = openpyxl.load_workbook(METADATA_EXCEL_FILE)
        sheet = workbook.active
        
        metadata_list = []
        # Skip header row, start from row 2
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0]:  # If title exists
                metadata_list.append({
                    'title': str(row[0]) if row[0] else '',
                    'description': str(row[1]) if row[1] else '',
                    'tags': str(row[2]) if row[2] else ''
                })
        
        return metadata_list
    except Exception as e:
        logging.error(f"Error reading Excel metadata: {e}")
        return []

def get_random_metadata(count=1):
    """Get random metadata from Excel file"""
    import random
    
    metadata_list = get_metadata_from_excel()
    if not metadata_list:
        return []
    
    # If requested count is more than available, allow duplicates
    if count <= len(metadata_list):
        return random.sample(metadata_list, count)
    else:
        return random.choices(metadata_list, k=count)

def get_auto_upload_config(user_id=None):
    """Get auto upload scheduler configuration - PER USER"""
    # Per-user configuration from database
    if user_id:
        try:
            from modules.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT auto_upload_enabled, auto_upload_offset_hours, 
                           auto_upload_check_interval 
                    FROM users WHERE id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'enabled': bool(row['auto_upload_enabled']),
                        'upload_offset_hours': row['auto_upload_offset_hours'] or 2,
                        'check_interval_minutes': row['auto_upload_check_interval'] or 30
                    }
        except Exception as e:
            logging.error(f"Error loading auto upload config for user {user_id}: {e}")
    
    # Fallback to global config file (legacy)
    if not os.path.exists(AUTO_UPLOAD_CONFIG_FILE):
        return {'enabled': False, 'upload_offset_hours': 2, 'check_interval_minutes': 30}
    
    try:
        with open(AUTO_UPLOAD_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'enabled': False, 'upload_offset_hours': 2, 'check_interval_minutes': 30}

def save_auto_upload_config(config, user_id=None):
    """Save auto upload scheduler configuration - PER USER"""
    # Per-user configuration to database
    if user_id:
        try:
            from modules.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET auto_upload_enabled = ?,
                        auto_upload_offset_hours = ?,
                        auto_upload_check_interval = ?
                    WHERE id = ?
                ''', (
                    1 if config.get('enabled') else 0,
                    config.get('upload_offset_hours', 2),
                    config.get('check_interval_minutes', 30),
                    user_id
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving auto upload config for user {user_id}: {e}")
            return False
    
    # Fallback to global config file (legacy)
    with open(AUTO_UPLOAD_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    return True

@app.route('/video-looping')
@login_required
def video_looping():
    """Video looping page - bulk loop videos"""
    videos = get_video_database()
    looped_videos = get_looped_videos()
    return render_template('video_looping.html', videos=videos, looped_videos=looped_videos)

@app.route('/start-video-looping', methods=['POST'])
@login_required
@demo_readonly
def start_video_looping():
    """Start looping selected videos"""
    video_ids = request.form.getlist('video_ids[]')
    loop_duration = request.form.get('loop_duration', '60')  # Default 60 minutes
    
    if not video_ids:
        flash('Pilih minimal satu video untuk di-loop', 'error')
        return redirect(url_for('video_looping'))
    
    try:
        loop_duration_minutes = int(loop_duration)
        if loop_duration_minutes <= 0:
            flash('Durasi loop harus lebih dari 0 menit', 'error')
            return redirect(url_for('video_looping'))
    except ValueError:
        flash('Durasi loop tidak valid', 'error')
        return redirect(url_for('video_looping'))
    
    videos = get_video_database()
    looped_videos = get_looped_videos()
    
    for video_id in video_ids:
        video = next((v for v in videos if v['id'] == video_id), None)
        if not video:
            continue
        
        # Create looped video entry
        looped_id = str(uuid.uuid4())
        looped_entry = {
            'id': looped_id,
            'original_video_id': video_id,
            'original_filename': video['filename'],
            'original_title': video['title'],
            'loop_duration_minutes': loop_duration_minutes,
            'status': 'processing',
            'progress': 0,
            'output_filename': None,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        looped_videos.append(looped_entry)
        
        # Start looping process in background thread
        def loop_video_background(entry, original_file, current_user_id):
            try:
                input_path = os.path.join(VIDEO_FOLDER, original_file)
                # Use original filename with loop_ prefix
                original_name = os.path.splitext(original_file)[0]
                output_filename = f"loop_{original_name}.mp4"
                output_path = os.path.join(LOOPED_FOLDER, output_filename)
                
                # Calculate loop duration in seconds
                duration_seconds = loop_duration_minutes * 60
                
                # FFmpeg command to loop video
                cmd = [
                    'ffmpeg',
                    '-stream_loop', '-1',  # Infinite loop
                    '-i', input_path,
                    '-t', str(duration_seconds),  # Duration
                    '-c', 'copy',  # Copy codec (no re-encoding)
                    '-y',  # Overwrite output file
                    output_path
                ]
                
                # Run ffmpeg
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for completion
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    # Success - generate thumbnail and update entry
                    thumbnail_generated = False
                    try:
                        # Generate thumbnail from looped video
                        thumbnail_filename = f"{uuid.uuid4()}.jpg"
                        thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
                        
                        thumb_cmd = [
                            'ffmpeg',
                            '-i', output_path,
                            '-ss', '00:00:01',
                            '-vframes', '1',
                            '-q:v', '2',
                            '-y',
                            thumbnail_path
                        ]
                        thumb_result = subprocess.run(thumb_cmd, capture_output=True, timeout=30)
                        
                        if thumb_result.returncode == 0 and os.path.exists(thumbnail_path):
                            from modules.database import add_thumbnail
                            thumbnail_title = f"Auto: {entry['original_title'][:50]} (Looped)"
                            thumbnail_id = str(uuid.uuid4())
                            add_thumbnail(current_user_id, {
                                'id': thumbnail_id,
                                'filename': thumbnail_filename,
                                'title': thumbnail_title,
                                'original_filename': f"{entry['original_title'][:50]}_looped.jpg"
                            })
                            thumbnail_generated = True
                            entry['thumbnail'] = thumbnail_filename  # Save thumbnail filename
                            logging.info(f"✓ Auto-generated thumbnail for looped video: {thumbnail_filename} user {current_user_id}")
                    except Exception as thumb_err:
                        logging.error(f"Could not generate thumbnail for looped video: {thumb_err}")
                    
                    entry['status'] = 'completed'
                    entry['progress'] = 100
                    entry['output_filename'] = output_filename
                    entry['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if 'thumbnail' not in entry:
                        entry['thumbnail'] = None  # Ensure field exists
                else:
                    # Failed
                    entry['status'] = 'failed'
                    entry['error'] = stderr.decode('utf-8')[:500]
                
                save_looped_videos(looped_videos)
                
                # Also update database
                try:
                    update_looped_video_in_db(entry['id'], {
                        'status': entry['status'],
                        'progress': entry['progress'],
                        'output_filename': entry.get('output_filename'),
                        'completed_at': entry.get('completed_at'),
                        'thumbnail': entry.get('thumbnail')
                    })
                except Exception as db_err:
                    logging.error(f"Failed to update looped video in DB: {db_err}")
                
            except Exception as e:
                entry['status'] = 'failed'
                entry['error'] = str(e)
                save_looped_videos(looped_videos)
                
                # Update database
                try:
                    update_looped_video_in_db(entry['id'], {
                        'status': 'failed',
                        'error': str(e)
                    })
                except Exception as db_err:
                    logging.error(f"Failed to update looped video error in DB: {db_err}")
        
        # Start background thread
        thread = threading.Thread(
            target=loop_video_background,
            args=(looped_entry, video['filename'], user_id)
        )
        thread.daemon = True
        thread.start()
    
    save_looped_videos(looped_videos)
    flash(f'{len(video_ids)} video sedang diproses untuk looping', 'success')
    return redirect(url_for('video_looping'))

@app.route('/api/looping-status')
@login_required
def api_looping_status():
    """Get looping status for all videos"""
    looped_videos = get_looped_videos()
    return jsonify(looped_videos)

@app.route('/serve-looped-video/<filename>')
@login_required
def serve_looped_video(filename):
    """Serve looped video file"""
    return send_from_directory(LOOPED_FOLDER, filename)

@app.route('/delete-looped-video/<video_id>', methods=['POST'])
@login_required
@demo_readonly
def delete_looped_video(video_id):
    """Delete a single looped video"""
    try:
        looped_videos = get_looped_videos()
        
        video_to_delete = next((v for v in looped_videos if v['id'] == video_id), None)
        if not video_to_delete:
            return jsonify({'success': False, 'message': 'Video not found'})
        
        # Delete file if exists
        if video_to_delete.get('output_filename'):
            file_path = os.path.join(LOOPED_FOLDER, video_to_delete['output_filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
    
        # Remove from database
        looped_videos = [v for v in looped_videos if v['id'] != video_id]
        save_looped_videos(looped_videos)
        
        return jsonify({'success': True, 'message': 'Video deleted successfully'})
    except Exception as e:
        logging.error(f"Error deleting looped video: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/bulk-delete-looped-videos', methods=['POST'])
@login_required
@demo_readonly
def bulk_delete_looped_videos():
    """Delete multiple looped videos at once"""
    try:
        data = request.get_json()
        video_ids = data.get('video_ids', [])
        
        if not video_ids:
            return jsonify({'success': False, 'message': 'No videos selected'})
        
        looped_videos = get_looped_videos()
        deleted_count = 0
        
        for video_id in video_ids:
            video_to_delete = next((v for v in looped_videos if v['id'] == video_id), None)
            if video_to_delete:
                # Delete file if exists
                if video_to_delete.get('output_filename'):
                    file_path = os.path.join(LOOPED_FOLDER, video_to_delete['output_filename'])
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            logging.error(f"Error deleting file {file_path}: {e}")
        
        # Remove all selected videos from database
        looped_videos = [v for v in looped_videos if v['id'] not in video_ids]
        save_looped_videos(looped_videos)
        
        return jsonify({
            'success': True, 
            'message': f'{deleted_count} video(s) deleted successfully'
        })
    except Exception as e:
        logging.error(f"Error bulk deleting looped videos: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/gemini-settings', methods=['GET', 'POST'])
@login_required
def gemini_settings():
    """Gemini API settings page - PER USER"""
    user_id = int(current_user.id)
    
    if request.method == 'POST':
        api_key = request.form.get('api_key', '').strip()
        model = request.form.get('model', 'gemini-2.0-flash-exp').strip()
        custom_prompt = request.form.get('custom_prompt', '').strip()
        
        # Save to database
        from modules.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET gemini_api_key = ?,
                    gemini_model = ?,
                    gemini_custom_prompt = ?
                WHERE id = ?
            ''', (api_key, model, custom_prompt or None, user_id))
            conn.commit()
        
        flash('Gemini API settings saved successfully!', 'success')
        return redirect(url_for('gemini_settings'))
    
    config = load_gemini_config(user_id=user_id) or {}
    metadata_count = len(get_metadata_from_excel())
    config['metadata_count'] = metadata_count
    return render_template('gemini_settings.html', config=config)

@app.route('/bulk-scheduling')
@login_required
def bulk_scheduling():
    """Bulk scheduling page with AI metadata generation"""
    # Get looped videos
    looped_videos = get_looped_videos()
    completed_looped = [v for v in looped_videos if v['status'] == 'completed']
    
    # Get regular videos (non-looped)
    regular_videos = get_video_database()
    
    # Get tokens (per-user)
    user_id = int(current_user.id)
    tokens = get_token_files(user_id)
    thumbnails = get_thumbnail_database()
    stream_mapping = get_stream_mapping()
    
    # Check if Gemini API is configured (per-user)
    gemini_config = load_gemini_config(user_id=user_id)
    gemini_configured = gemini_config and gemini_config.get('api_key')
    
    # Check if metadata Excel exists
    metadata_count = len(get_metadata_from_excel())
    
    return render_template('bulk_scheduling.html', 
                         looped_videos=completed_looped,
                         regular_videos=regular_videos,
                         tokens=tokens,
                         thumbnails=thumbnails,
                         stream_mapping=stream_mapping,
                         gemini_configured=gemini_configured,
                         metadata_count=metadata_count)

@app.route('/generate-ai-metadata', methods=['POST'])
@login_required
@demo_readonly
def generate_ai_metadata():
    """Generate metadata using Gemini AI - PER USER"""
    user_id = int(current_user.id)
    video_ids = request.form.getlist('video_ids[]')
    keyword = request.form.get('keyword', '').strip()
    
    if not video_ids:
        return jsonify({'success': False, 'error': 'Pilih minimal satu video'}), 400
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword harus diisi'}), 400
    
    # Load Gemini config (per-user)
    gemini_config = load_gemini_config(user_id=user_id)
    if not gemini_config or not gemini_config.get('api_key'):
        return jsonify({'success': False, 'error': 'Gemini API belum dikonfigurasi'}), 400
    
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=gemini_config['api_key'])
        model_name = gemini_config.get('model', 'gemini-2.5-flash')
        model = genai.GenerativeModel(model_name)
        
        # Get both regular and looped videos
        regular_videos = get_video_database()
        looped_videos = get_looped_videos()
        completed_looped = [v for v in looped_videos if v['status'] == 'completed']
        
        generated_metadata = []
        
        for idx, video_id in enumerate(video_ids, 1):
            # Check if it's a regular or looped video
            video = None
            video_type = 'regular'
            
            # Parse video_id (format: "regular_xxx" or "looped_xxx")
            if video_id.startswith('regular_'):
                actual_id = video_id.replace('regular_', '')
                video = next((v for v in regular_videos if v['id'] == actual_id), None)
                video_type = 'regular'
            elif video_id.startswith('looped_'):
                actual_id = video_id.replace('looped_', '')
                video = next((v for v in completed_looped if v['id'] == actual_id), None)
                video_type = 'looped'
            else:
                # Legacy format without prefix
                video = next((v for v in looped_videos if v['id'] == video_id), None)
                if not video:
                    video = next((v for v in regular_videos if v['id'] == video_id), None)
            
            if not video:
                logging.warning(f"Video not found: {video_id}")
                continue
            
            # Generate prompt for Gemini
            # Get video title (handle both regular and looped videos)
            if video_type == 'looped':
                video_title = video.get('original_title', 'Unknown')
            else:
                video_title = video.get('title', 'Unknown')
            
            # Use custom prompt if available
            custom_prompt = gemini_config.get('custom_prompt')
            
            if custom_prompt:
                # Replace placeholders in custom prompt
                prompt = custom_prompt.replace('{keyword}', keyword)
                prompt = prompt.replace('{index}', str(idx))
                prompt = prompt.replace('{original_title}', video_title)
            else:
                # Default prompt
                prompt = f"""Generate YouTube video metadata for video #{idx} based on the keyword: "{keyword}"

Original video title: {video_title}

Please provide:
1. A catchy YouTube title (max 100 characters)
2. A detailed description (2-3 paragraphs)
3. 10-15 relevant tags (comma separated)

IMPORTANT: Return ONLY a valid JSON object with no additional text, markdown, or explanations.

Format your response exactly like this:
{{
    "title": "video title here",
    "description": "video description here",
    "tags": "tag1, tag2, tag3, ..."
}}
"""
            
            # Generate content
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Log raw response for debugging
            logging.info(f"[GEMINI] Raw response for video {idx}: {response_text[:200]}...")
            
            # Try to parse JSON from response
            # Sometimes Gemini wraps JSON in markdown code blocks
            json_text = response_text
            
            # Remove markdown code blocks if present
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0].strip()
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0].strip()
            
            # Remove any leading/trailing whitespace or special characters
            json_text = json_text.strip()
            
            # Try to find JSON object in response
            if '{' in json_text and '}' in json_text:
                # Extract JSON object
                start_idx = json_text.find('{')
                end_idx = json_text.rfind('}') + 1
                json_text = json_text[start_idx:end_idx]
            
            try:
                metadata = json.loads(json_text)
            except json.JSONDecodeError as je:
                logging.error(f"[GEMINI] JSON parse error for video {idx}: {je}")
                logging.error(f"[GEMINI] Attempted to parse: {json_text}")
                
                # Fallback: create basic metadata
                metadata = {
                    'title': f'{keyword} - Video {idx}',
                    'description': f'Video about {keyword}. Generated content.',
                    'tags': keyword
                }
            
            generated_metadata.append({
                'video_id': video_id,
                'title': metadata.get('title', f'{keyword} - Video {idx}'),
                'description': metadata.get('description', ''),
                'tags': metadata.get('tags', keyword)
            })
        
        return jsonify({'success': True, 'metadata': generated_metadata})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate-random-metadata', methods=['POST'])
@login_required
@demo_readonly
def generate_random_metadata():
    """Generate metadata using random selection from Excel"""
    video_ids = request.form.getlist('video_ids[]')
    
    if not video_ids:
        return jsonify({'success': False, 'error': 'Pilih minimal satu video'}), 400
    
    try:
        # Get random metadata
        random_metadata = get_random_metadata(count=len(video_ids))
        
        if not random_metadata:
            return jsonify({'success': False, 'error': 'File Excel metadata tidak ditemukan atau kosong. Upload file Excel di halaman Gemini Settings.'}), 400
        
        generated_metadata = []
        for idx, video_id in enumerate(video_ids):
            metadata = random_metadata[idx]
            generated_metadata.append({
                'video_id': video_id,
                'title': metadata['title'],
                'description': metadata['description'],
                'tags': metadata['tags']
            })
        
        return jsonify({'success': True, 'metadata': generated_metadata})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload-metadata-excel', methods=['POST'])
@login_required
@demo_readonly
def upload_metadata_excel():
    """Upload Excel file with metadata templates"""
    if 'excel_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('gemini_settings'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('gemini_settings'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('File must be Excel format (.xlsx or .xls)', 'error')
        return redirect(url_for('gemini_settings'))
    
    try:
        # Save the file
        file.save(METADATA_EXCEL_FILE)
        
        # Validate the file
        metadata_list = get_metadata_from_excel()
        
        if not metadata_list:
            os.remove(METADATA_EXCEL_FILE)
            flash('Excel file is empty or invalid format. Please check: Column A=Title, B=Description, C=Tags', 'error')
            return redirect(url_for('gemini_settings'))
        
        flash(f'Excel metadata uploaded successfully! {len(metadata_list)} templates loaded.', 'success')
        return redirect(url_for('gemini_settings'))
        
    except Exception as e:
        flash(f'Error uploading Excel: {str(e)}', 'error')
        return redirect(url_for('gemini_settings'))

@app.route('/save-bulk-upload-queue', methods=['POST'])
@login_required
@demo_readonly
def save_bulk_upload_queue_route():
    """Save videos to upload queue with metadata - PER USER"""
    from modules.database import add_bulk_upload_item, get_looped_videos
    
    user_id = int(current_user.id)
    data = request.get_json()
    
    if not data or not data.get('videos'):
        return jsonify({'success': False, 'error': 'Data tidak valid'}), 400
    
    videos = data['videos']
    start_date_str = data.get('start_date')
    token_file = data.get('token_file')
    stream_id = data.get('stream_id')
    thumbnail_id = data.get('thumbnail_id')
    privacy_status = data.get('privacy_status', 'unlisted')
    
    if not start_date_str or not token_file:
        return jsonify({'success': False, 'error': 'Tanggal awal dan token harus diisi'}), 400
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    except:
        return jsonify({'success': False, 'error': 'Format tanggal tidak valid'}), 400
    
    # Get looped videos database for current user
    looped_videos = get_looped_videos(user_id)
    
    added_count = 0
    for idx, video_data in enumerate(videos):
        video_id = video_data['video_id']
        video = next((v for v in looped_videos if v['id'] == video_id), None)
        if not video or video['status'] != 'completed':
            continue
        
        # Calculate publish date (increment by 1 day for each video)
        publish_date = start_date + timedelta(days=idx)
        
        queue_entry = {
            'id': str(uuid.uuid4()),
            'video_id': video_id,
            'video_path': os.path.join(LOOPED_FOLDER, video['output_filename']),
            'title': video_data['title'],
            'description': video_data['description'],
            'tags': video_data['tags'].split(',') if isinstance(video_data['tags'], str) else video_data['tags'],
            'scheduled_publish_time': publish_date.strftime('%Y-%m-%d %H:%M:%S'),
            'token_file': token_file,
            'stream_id': stream_id,
            'thumbnail_id': thumbnail_id,
            'privacy_status': privacy_status,
            'status': 'queued'
        }
        
        # Add to database
        add_bulk_upload_item(user_id, queue_entry)
        added_count += 1
    
    return jsonify({'success': True, 'message': f'{added_count} video ditambahkan ke antrian upload'})

@app.route('/bulk-upload-queue')
@login_required
def bulk_upload_queue_page():
    """View upload queue - PER USER"""
    from modules.database import get_bulk_upload_queue
    
    user_id = int(current_user.id)
    queue = get_bulk_upload_queue(user_id)
    auto_config = get_auto_upload_config(user_id=user_id)
    scheduler_status = get_auto_upload_scheduler_status()
    return render_template('bulk_upload_queue.html', 
                         queue=queue, 
                         auto_config=auto_config,
                         scheduler_status=scheduler_status)

@app.route('/start-bulk-upload', methods=['POST'])
@login_required
@demo_readonly
def start_bulk_upload():
    """Start uploading all queued videos to YouTube - PER USER"""
    from modules.database import get_bulk_upload_queue
    
    user_id = int(current_user.id)
    queue = get_bulk_upload_queue(user_id)
    queued_items = [item for item in queue if item['status'] == 'queued']
    
    if not queued_items:
        flash('Tidak ada video dalam antrian', 'warning')
        return redirect(url_for('bulk_upload_queue_page'))
    
    # Start upload process in background
    def upload_videos_background():
        from modules.youtube.kunci import get_youtube_service
        from googleapiclient.http import MediaFileUpload
        
        for item in queued_items:
            try:
                # Check video duration first
                video_path = item['video_path']
                
                if not os.path.exists(video_path):
                    item['status'] = 'failed'
                    item['error'] = 'File video tidak ditemukan'
                    save_bulk_upload_queue(queue)
                    continue
                
                # Get video duration using ffprobe
                try:
                    ffprobe_cmd = [
                        'ffprobe',
                        '-v', 'error',
                        '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        video_path
                    ]
                    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
                    duration_seconds = float(result.stdout.strip())
                    duration_minutes = duration_seconds / 60
                    duration_hours = duration_minutes / 60
                    
                    logging.info(f"Video duration: {duration_minutes:.2f} minutes ({duration_hours:.2f} hours)")
                    
                    # YouTube limits:
                    # - Unverified accounts: 15 minutes (900 seconds)
                    # - Verified accounts: 12 hours (43200 seconds)
                    # - For safety, warn at 11.5 hours
                    
                    if duration_seconds > 41400:  # 11.5 hours
                        item['status'] = 'failed'
                        item['error'] = f'Video terlalu panjang ({duration_hours:.2f} jam). YouTube maksimal 12 jam untuk akun terverifikasi.'
                        save_bulk_upload_queue(queue)
                        logging.error(f"Video too long: {duration_hours:.2f} hours")
                        continue
                    
                    if duration_seconds > 900:  # 15 minutes
                        logging.warning(f"Video duration {duration_minutes:.2f} minutes - requires verified YouTube account!")
                        # Continue anyway, let YouTube API handle it
                    
                except Exception as e:
                    logging.warning(f"Could not check video duration: {e}")
                    # Continue anyway if ffprobe fails
                
                # Update status
                item['status'] = 'uploading'
                save_bulk_upload_queue(queue)
                
                # Get YouTube service
                youtube = get_youtube_service(item['token_file'])
                
                # Prepare video metadata
                # Parse scheduled time and convert to UTC
                scheduled_time = datetime.strptime(item['scheduled_publish_time'], '%Y-%m-%d %H:%M:%S')
                
                # Use timezone from app config, convert to UTC
                local_tz = pytz.timezone(TIMEZONE)
                utc_tz = pytz.UTC
                
                # Make scheduled_time timezone aware (local timezone)
                scheduled_time_local = local_tz.localize(scheduled_time)
                # Convert to UTC
                scheduled_time_utc = scheduled_time_local.astimezone(utc_tz)
                
                # Get current time in UTC
                now_utc = datetime.now(utc_tz)
                
                # YouTube API Scheduled Publishing Rules:
                # 1. privacyStatus MUST be "private" for scheduled upload
                # 2. Set publishAt in ISO 8601 format (UTC)
                # 3. Video will automatically become PUBLIC at publishAt time
                # 4. Cannot use "unlisted" for scheduled videos
                
                # Ensure scheduled time is at least 1 hour in the future
                if scheduled_time_utc <= now_utc + timedelta(hours=1):
                    scheduled_time_utc = now_utc + timedelta(hours=2)
                    logging.warning(f"Scheduled time adjusted to {scheduled_time_utc} UTC (minimum 1 hour in future)")
                
                body = {
                    'snippet': {
                        'title': item['title'],
                        'description': item['description'],
                        'tags': item['tags'] if isinstance(item['tags'], list) else item['tags'].split(','),
                        'categoryId': '22'  # People & Blogs
                    },
                    'status': {
                        'privacyStatus': 'private',  # MUST be private for scheduled upload
                        'publishAt': scheduled_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),  # ISO 8601 UTC format
                        'selfDeclaredMadeForKids': False
                    }
                }
                
                logging.info(f"Uploading video: {item['title']}")
                logging.info(f"Privacy: private (will auto-publish to PUBLIC at scheduled time)")
                logging.info(f"Scheduled publish (UTC): {scheduled_time_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                logging.info(f"Scheduled publish (Local): {item['scheduled_publish_time']} {TIMEZONE}")
                
                # If stream_id provided, bind to live stream
                if item.get('stream_id'):
                    body['status']['streamId'] = item['stream_id']
                
                # Upload video
                media = MediaFileUpload(item['video_path'], chunksize=-1, resumable=True)
                request = youtube.videos().insert(
                    part='snippet,status',
                    body=body,
                    media_body=media
                )
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        item['upload_progress'] = int(status.progress() * 100)
                        save_bulk_upload_queue(queue)
                
                video_id = response['id']
                item['youtube_video_id'] = video_id
                
                # Upload thumbnail if specified
                if item.get('thumbnail_id'):
                    thumbnails = get_thumbnail_database()
                    thumbnail = next((t for t in thumbnails if t['id'] == item['thumbnail_id']), None)
                    if thumbnail:
                        thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail['filename'])
                        if os.path.exists(thumbnail_path):
                            youtube.thumbnails().set(
                                videoId=video_id,
                                media_body=thumbnail_path
                            ).execute()
                
                # Update status to completed
                item['status'] = 'completed'
                item['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                item['video_url'] = f'https://studio.youtube.com/video/{video_id}/edit'
                save_bulk_upload_queue(queue)
                
            except Exception as e:
                error_message = str(e)
                item['status'] = 'failed'
                
                # Better error messages for common YouTube API errors
                if 'exceeded the number of videos they may upload' in error_message:
                    item['error'] = '❌ YouTube Daily Quota Exceeded: You have reached the maximum number of uploads per day (default: 6 videos/24h). Wait 24 hours or request quota increase at https://support.google.com/youtube/contact/yt_api_form'
                elif 'uploadLimitExceeded' in error_message:
                    item['error'] = '❌ Video too long for unverified account. Verify your YouTube account at https://www.youtube.com/verify or reduce video length to under 15 minutes.'
                elif 'quotaExceeded' in error_message:
                    item['error'] = '❌ YouTube API Quota Exceeded: Daily API call limit reached. Wait until quota resets (midnight Pacific Time) or request increase.'
                elif 'forbidden' in error_message.lower():
                    item['error'] = '❌ Permission Error: Check your YouTube API credentials and OAuth token. Token may have expired.'
                elif 'invalidVideoMetadata' in error_message:
                    item['error'] = '❌ Invalid Metadata: Check title length (<100 chars), description, and tags format.'
                else:
                    item['error'] = f'❌ Upload Failed: {error_message}'
                
                logging.error(f"Upload failed for {item['title']}: {error_message}")
                save_bulk_upload_queue(queue)
    
    # Start background thread
    thread = threading.Thread(target=upload_videos_background)
    thread.daemon = True
    thread.start()
    
    flash(f'Memulai upload {len(queued_items)} video ke YouTube...', 'success')
    return redirect(url_for('bulk_upload_queue_page'))

@app.route('/api/upload-queue-status')
@login_required
def api_upload_queue_status():
    """Get upload queue status"""
    queue = get_bulk_upload_queue()
    return jsonify(queue)

@app.route('/delete-queue-item/<item_id>', methods=['POST'])
@login_required
@demo_readonly
def delete_queue_item(item_id):
    """Delete item from upload queue - PER USER"""
    from modules.database import delete_bulk_upload_item
    
    user_id = int(current_user.id)
    
    if delete_bulk_upload_item(item_id, user_id):
        flash('Item berhasil dihapus dari antrian', 'success')
    else:
        flash('Item tidak ditemukan', 'error')
    
    return redirect(url_for('bulk_upload_queue_page'))

@app.route('/clear-completed-queue', methods=['POST'])
@login_required
@demo_readonly
def clear_completed_queue():
    """Clear all completed items from queue - PER USER"""
    from modules.database import get_bulk_upload_queue, delete_bulk_upload_item
    
    user_id = int(current_user.id)
    queue = get_bulk_upload_queue(user_id)
    
    deleted_count = 0
    for item in queue:
        if item['status'] == 'completed':
            if delete_bulk_upload_item(item['id'], user_id):
                deleted_count += 1
    
    flash(f'{deleted_count} item berhasil dihapus', 'success')
    return redirect(url_for('bulk_upload_queue_page'))

@app.route('/requeue-items', methods=['POST'])
@login_required
@demo_readonly
def requeue_items():
    """Re-queue selected items (duplicate them with queued status)"""
    data = request.get_json()
    item_ids = data.get('item_ids', [])
    
    if not item_ids:
        return jsonify({'success': False, 'error': 'No items selected'}), 400
    
    try:
        queue = get_bulk_upload_queue()
        requeued_count = 0
        
        for item_id in item_ids:
            # Find the item
            original_item = next((item for item in queue if item['id'] == item_id), None)
            if not original_item:
                continue
            
            # Only allow requeue for completed/failed items
            if original_item['status'] not in ['completed', 'failed']:
                continue
            
            # Create a duplicate with new ID and queued status
            new_item = {
                'id': str(uuid.uuid4()),
                'video_id': original_item['video_id'],
                'video_path': original_item['video_path'],
                'title': original_item['title'],
                'description': original_item['description'],
                'tags': original_item['tags'],
                'scheduled_publish_time': original_item['scheduled_publish_time'],
                'token_file': original_item['token_file'],
                'stream_id': original_item.get('stream_id'),
                'thumbnail_id': original_item.get('thumbnail_id'),
                'privacy_status': original_item.get('privacy_status', 'unlisted'),
                'status': 'queued',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            queue.append(new_item)
            requeued_count += 1
        
        save_bulk_upload_queue(queue)
        
        return jsonify({
            'success': True, 
            'message': f'{requeued_count} item(s) added back to queue'
        })
        
    except Exception as e:
        logging.error(f"Error requeueing items: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/toggle-auto-upload', methods=['POST'])
@login_required
def toggle_auto_upload():
    """Toggle auto upload scheduler - PER USER"""
    try:
        user_id = int(current_user.id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        config = get_auto_upload_config(user_id=user_id)
        config['enabled'] = data.get('enabled', False)
        
        if 'upload_offset_hours' in data:
            config['upload_offset_hours'] = int(data['upload_offset_hours'])
        if 'check_interval_minutes' in data:
            config['check_interval_minutes'] = int(data['check_interval_minutes'])
        
        save_auto_upload_config(config, user_id=user_id)
        
        status = 'enabled' if config['enabled'] else 'disabled'
        return jsonify({
            'success': True, 
            'message': f'Auto upload scheduler {status}',
            'config': config
        })
    except Exception as e:
        logging.error(f"Error toggling auto upload: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Auto Upload Scheduler Background Thread
def auto_upload_scheduler():
    """Background thread that automatically uploads videos based on schedule - PER USER"""
    while True:
        try:
            from modules.database import get_all_users, get_bulk_upload_queue, update_bulk_upload_item
            
            # Update status: Running
            current_time = datetime.now(pytz.timezone(TIMEZONE))
            scheduler_status = {
                'last_run': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'active': True,
                'last_status': 'Checking...',
                'uploads_processed': 0
            }
            save_auto_upload_scheduler_status(scheduler_status)
            
            # Get all users
            users = get_all_users()
            
            if not users:
                logging.info("[AUTO-UPLOAD] No users found, sleeping for 5 minutes...")
                scheduler_status['last_status'] = 'No users found'
                scheduler_status['next_check'] = (current_time + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
                save_auto_upload_scheduler_status(scheduler_status)
                time.sleep(300)
                continue
            
            any_uploads_pending = False
            min_check_interval = 30  # Default 30 minutes
            uploads_processed = 0
            
            # Loop through each user and check their queue
            for user in users:
                user_id = user['id']
                username = user.get('username', 'unknown')
                
                # Get user's auto upload config
                config = get_auto_upload_config(user_id=user_id)
                
                if not config.get('enabled', False):
                    continue
                
                # Update minimum check interval based on user configs
                user_interval = config.get('check_interval_minutes', 30)
                if user_interval < min_check_interval:
                    min_check_interval = user_interval
                
                # Get user's upload queue
                queue = get_bulk_upload_queue(user_id)
                queued_items = [item for item in queue if item['status'] == 'queued']
                
                if not queued_items:
                    continue
                
                any_uploads_pending = True
            
                # Check which videos should be uploaded now
                now = datetime.now(pytz.timezone(TIMEZONE))
                upload_offset = timedelta(hours=config.get('upload_offset_hours', 2))
                
                for item in queued_items:
                    try:
                        # Parse scheduled publish time
                        scheduled_time = datetime.strptime(item['scheduled_publish_time'], '%Y-%m-%d %H:%M:%S')
                        scheduled_time = pytz.timezone(TIMEZONE).localize(scheduled_time)
                        
                        # Calculate when to upload (X hours before publish time)
                        upload_time = scheduled_time - upload_offset
                        
                        # If upload time has arrived, upload now
                        if now >= upload_time and item['status'] == 'queued':
                            logging.info(f"[AUTO-UPLOAD][{username}] Starting auto upload for: {item['title']}")
                            logging.info(f"[AUTO-UPLOAD][{username}] Scheduled publish: {item['scheduled_publish_time']}")
                            
                            # Upload the video (reuse existing upload logic)
                            from modules.youtube.kunci import get_youtube_service
                            from googleapiclient.http import MediaFileUpload
                            
                            # Mark as uploading
                            update_bulk_upload_item(item['id'], user_id, {'status': 'uploading'})
                        
                            # Get token path for per-user tokens
                            token_path = get_token_path(item['token_file'], user_id)
                            
                            # Get YouTube service
                            youtube = get_youtube_service(token_path)
                            
                            # Prepare metadata (same as manual upload)
                            scheduled_time_dt = datetime.strptime(item['scheduled_publish_time'], '%Y-%m-%d %H:%M:%S')
                            local_tz = pytz.timezone(TIMEZONE)
                            utc_tz = pytz.UTC
                            scheduled_time_local = local_tz.localize(scheduled_time_dt)
                            scheduled_time_utc = scheduled_time_local.astimezone(utc_tz)
                            
                            # Ensure at least 1 hour in future
                            now_utc = datetime.now(utc_tz)
                            if scheduled_time_utc <= now_utc + timedelta(hours=1):
                                scheduled_time_utc = now_utc + timedelta(hours=2)
                            
                            body = {
                                'snippet': {
                                    'title': item['title'],
                                    'description': item['description'],
                                    'tags': item['tags'] if isinstance(item['tags'], list) else item['tags'].split(','),
                                    'categoryId': '22'
                                },
                                'status': {
                                    'privacyStatus': 'private',
                                    'publishAt': scheduled_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                    'selfDeclaredMadeForKids': False
                                }
                            }
                            
                            if item.get('stream_id'):
                                body['status']['streamId'] = item['stream_id']
                            
                            # Upload video
                            media = MediaFileUpload(item['video_path'], chunksize=-1, resumable=True)
                            request = youtube.videos().insert(
                                part='snippet,status',
                                body=body,
                                media_body=media
                            )
                            
                            response = None
                            while response is None:
                                status, response = request.next_chunk()
                                if status:
                                    progress = int(status.progress() * 100)
                                    update_bulk_upload_item(item['id'], user_id, {'progress': progress})
                            
                            video_id = response['id']
                        
                            # Upload thumbnail if specified
                            if item.get('thumbnail_id'):
                                from modules.database import get_thumbnails
                                thumbnails = get_thumbnails(user_id)
                                thumbnail = next((t for t in thumbnails if t['id'] == item['thumbnail_id']), None)
                                if thumbnail:
                                    thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail['filename'])
                                    if os.path.exists(thumbnail_path):
                                        youtube.thumbnails().set(
                                            videoId=video_id,
                                            media_body=thumbnail_path
                                        ).execute()
                            
                            # Mark as completed
                            video_url = f'https://studio.youtube.com/video/{video_id}/edit'
                            update_bulk_upload_item(item['id'], user_id, {
                                'status': 'completed',
                                'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'youtube_video_id': video_id
                            })
                            
                            logging.info(f"[AUTO-UPLOAD][{username}] ✓ Successfully uploaded: {item['title']}")
                            logging.info(f"[AUTO-UPLOAD][{username}] YouTube Video ID: {video_id}")
                            uploads_processed += 1
                            
                    except Exception as e:
                        logging.error(f"[AUTO-UPLOAD][{username}] Error uploading {item.get('title', 'Unknown')}: {e}")
                        update_bulk_upload_item(item['id'], user_id, {
                            'status': 'failed',
                            'error_message': str(e)
                        })
            
            # Update status before sleep
            next_check_time = datetime.now(pytz.timezone(TIMEZONE)) + timedelta(minutes=min_check_interval)
            scheduler_status['next_check'] = next_check_time.strftime('%Y-%m-%d %H:%M:%S')
            scheduler_status['uploads_processed'] = uploads_processed
            
            if uploads_processed > 0:
                scheduler_status['last_status'] = f'Success - {uploads_processed} video(s) uploaded'
            elif any_uploads_pending:
                scheduler_status['last_status'] = 'Success - No videos ready to upload yet'
            else:
                scheduler_status['last_status'] = 'Success - Queue empty'
            
            save_auto_upload_scheduler_status(scheduler_status)
            
            # Sleep before next check
            if not any_uploads_pending:
                logging.info(f"[AUTO-UPLOAD] No pending uploads. Sleeping for {min_check_interval} minutes...")
            else:
                logging.info(f"[AUTO-UPLOAD] Sleeping for {min_check_interval} minutes...")
            
            time.sleep(min_check_interval * 60)
            
        except Exception as e:
            logging.error(f"[AUTO-UPLOAD] Scheduler error: {e}")
            
            # Update status with error
            error_time = datetime.now(pytz.timezone(TIMEZONE))
            scheduler_status = {
                'last_run': error_time.strftime('%Y-%m-%d %H:%M:%S'),
                'next_check': (error_time + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'last_status': f'Error: {str(e)}',
                'active': True,
                'uploads_processed': 0
            }
            save_auto_upload_scheduler_status(scheduler_status)
            
            time.sleep(60)  # Sleep 1 minute on error


# ===== ADMIN USER LIMITS MANAGEMENT =====

# User limits routes removed - now integrated in admin_users page

@app.route('/admin/users/update_limits', methods=['POST'])
@login_required
@require_admin
def admin_update_limits():
    """Update user limits"""
    user_id = int(request.form.get('user_id'))
    max_streams = int(request.form.get('max_streams', 0))
    max_storage_mb = int(request.form.get('max_storage_mb', 0))
    
    success = update_user_limits(user_id, max_streams, max_storage_mb)
    
    if success:
        flash(f'User limits updated successfully!', 'success')
    else:
        flash('Failed to update limits (cannot modify admin users)', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/reset_usage', methods=['POST'])
@login_required
@require_admin
def admin_reset_usage():
    """Reset user usage (delete all data)"""
    user_id = int(request.form.get('user_id'))
    
    try:
        from modules.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if admin
            cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row and row['is_admin']:
                return jsonify({'success': False, 'message': 'Cannot reset admin user'})
            
            # Get files to delete
            cursor.execute('SELECT filename FROM videos WHERE user_id = ?', (user_id,))
            videos = cursor.fetchall()
            
            cursor.execute('SELECT filename FROM thumbnails WHERE user_id = ?', (user_id,))
            thumbnails = cursor.fetchall()
            
            cursor.execute('SELECT output_filename FROM looped_videos WHERE user_id = ? AND status = "completed"', (user_id,))
            looped = cursor.fetchall()
            
            # Delete files
            for row in videos:
                filepath = os.path.join(VIDEO_FOLDER, row['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            for row in thumbnails:
                filepath = os.path.join(THUMBNAIL_FOLDER, row['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            looped_folder = os.path.join(VIDEO_FOLDER, 'done')
            for row in looped:
                if row['output_filename']:
                    filepath = os.path.join(looped_folder, row['output_filename'])
                    if os.path.exists(filepath):
                        os.remove(filepath)
            
            # Delete database records
            cursor.execute('DELETE FROM videos WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM thumbnails WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM looped_videos WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM bulk_upload_queue WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM live_streams WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM schedules WHERE user_id = ?', (user_id,))
            
            return jsonify({'success': True, 'message': 'User data reset successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})



# ===== CLIENT SECRET MANAGEMENT (PER-USER) =====

@app.route('/settings/youtube-api')
@login_required
def client_secret_settings():
    """YouTube API settings page"""
    from modules.services.client_secret_manager import get_client_secret_info, list_user_tokens
    
    user_id = int(current_user.id)
    client_info = get_client_secret_info(user_id)
    tokens = list_user_tokens(user_id)
    
    return render_template('client_secret_settings.html', 
                         client_info=client_info,
                         tokens=tokens)

@app.route('/settings/youtube-api/upload', methods=['POST'])
@login_required
def upload_client_secret():
    """Upload client_secret.json for current user"""
    from modules.services.client_secret_manager import set_user_client_secret
    
    if 'client_secret' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('client_secret_settings'))
    
    file = request.files['client_secret']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('client_secret_settings'))
    
    if not file.filename.endswith('.json'):
        flash('File must be a JSON file', 'error')
        return redirect(url_for('client_secret_settings'))
    
    user_id = int(current_user.id)
    success, message, filepath = set_user_client_secret(user_id, file.read(), file.filename)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('client_secret_settings'))

@app.route('/settings/youtube-api/delete', methods=['POST'])
@login_required
def delete_client_secret():
    """Delete client_secret for current user"""
    from modules.services.client_secret_manager import delete_user_client_secret
    
    user_id = int(current_user.id)
    success, message = delete_user_client_secret(user_id)
    
    return jsonify({'success': success, 'message': message})


if __name__ == '__main__':
    # Disable debug mode for production
    app.debug = False
    
    # Enable logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize scheduler
    start_scheduler_thread()
    
    # Start auto upload scheduler thread
    auto_scheduler_thread = threading.Thread(target=auto_upload_scheduler, daemon=True)
    auto_scheduler_thread.start()
    logging.info("[AUTO-UPLOAD] Auto upload scheduler thread started")
    
    # Start daily license check thread
    def daily_license_check():
        """Background thread to check license validity daily"""
        import time
        
        while True:
            try:
                # Sleep for 24 hours
                time.sleep(24 * 60 * 60)
                
                logging.info("[LICENSE] Running daily license verification...")
                validator = LicenseValidator()
                valid, message, days = validator.verify_license(force_online=True)
                
                if valid:
                    logging.info(f"[LICENSE] ✓ License valid: {days} days remaining")
                else:
                    logging.warning(f"[LICENSE] ✗ License invalid: {message}")
                    
            except Exception as e:
                logging.error(f"[LICENSE] Daily check error: {e}")
    
    license_thread = threading.Thread(target=daily_license_check, daemon=True)
    license_thread.start()
    logging.info("[LICENSE] Daily license check thread started")

    # Start Flask with debug mode to show detailed errors
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

