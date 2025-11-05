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
from user_auth import User, get_user_by_id, authenticate_user, initialize_default_user, create_user, list_users, change_role, delete_user, change_user_password
import psutil
import platform
from license_validator import LicenseValidator, check_license
from hwid import get_hwid, get_system_info
import telegram_notifier
from functools import wraps

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
app.secret_key = 'your-secret-key-here'  # untuk flash messages

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login terlebih dahulu untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning'

# Initialize default user
initialize_default_user()

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# ==== Role helpers ====
ROLE_LIMITS = {
    'demo': 0,
    'silver': 3,
    'gold': 10,
    'platinum': 20,
    'admin': None,  # unlimited
}

def role_max_streams(role):
    role = (role or 'demo').lower()
    return ROLE_LIMITS.get(role, 0)

def role_can_manage(role):
    return (role or '').lower() == 'admin'

def role_can_add_streams(role):
    if role is None:
        return False
    role = role.lower()
    return role in ['silver', 'gold', 'platinum', 'admin']

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
def get_token_files():
    """Get list of token files from tokens folder, excluding client_secret.json"""
    try:
        if not os.path.exists(TOKENS_FOLDER):
            os.makedirs(TOKENS_FOLDER, exist_ok=True)
        tokens = [f for f in os.listdir(TOKENS_FOLDER) if f.endswith('.json')]
        return sorted(tokens)
    except Exception as e:
        print(f"Error getting token files: {e}")
        return []

def get_token_path(token_name):
    """Get full path for a token file"""
    if not token_name:
        return None
    # Ensure it has .json extension
    if not token_name.endswith('.json'):
        token_name += '.json'
    return os.path.join(TOKENS_FOLDER, token_name)

# Create a static folder link to videos folder for serving videos
app.config['UPLOAD_FOLDER'] = VIDEO_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload

# Video database file
VIDEO_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'video_database.json')
# Thumbnail database file
THUMBNAIL_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thumbnail_database.json')

# Live stream functions
def get_live_streams():
    if not os.path.exists(LIVE_STREAMS_FILE):
        with open(LIVE_STREAMS_FILE, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(LIVE_STREAMS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_live_streams(streams):
    with open(LIVE_STREAMS_FILE, 'w') as f:
        json.dump(streams, f, indent=4)

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
        
        # Get RTMP URL
        if stream['rtmp_server'] == 'custom':
            rtmp_url = stream['custom_rtmp']
        else:
            rtmp_url = RTMP_SERVERS.get(stream['rtmp_server'], RTMP_SERVERS['youtube'])
        
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
            
            telegram_notifier.notify_stream_starting(stream_title, scheduled_time, broadcast_link)
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
                telegram_notifier.notify_stream_ended(stream_title, duration_text)
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
                    duplicate_exists = False
                    for existing_stream in streams:
                        if (existing_stream['video_file'] == new_stream['video_file'] and
                            existing_stream['start_date'] == new_stream['start_date'] and
                            existing_stream['status'] == 'scheduled'):
                            duplicate_exists = True
                            break
                    
                    if not duplicate_exists:
                        streams.append(new_stream)
                        modified = True
    
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
    if not os.path.exists(VIDEO_DB_FILE):
        return []
    try:
        with open(VIDEO_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_video_database(videos):
    with open(VIDEO_DB_FILE, 'w') as f:
        json.dump(videos, f, indent=4)

def get_thumbnail_database():
    if not os.path.exists(THUMBNAIL_DB_FILE):
        return []
    try:
        with open(THUMBNAIL_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_thumbnail_database(thumbnails):
    with open(THUMBNAIL_DB_FILE, 'w') as f:
        json.dump(thumbnails, f, indent=4)

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

def get_stream_name(stream_id):
    """Convert stream ID to stream name using the mapping from live.py"""
    if not stream_id:
        return ''

    # Try live.py reverse mapping first (fast when available)
    try:
        from live import REVERSE_STREAM_MAPPING
        if stream_id in REVERSE_STREAM_MAPPING:
            return REVERSE_STREAM_MAPPING[stream_id]
        # if not found, don't return yet — fall back to saved mappings
    except Exception:
        pass

    # Fallback: try to read our saved stream_mapping.json and find a title
    try:
        mapping = get_stream_mapping()
        for token, streams in mapping.items():
            # streams expected: {streamId: {title: ..., ...}}
            for sid, meta in (streams or {}).items():
                if sid == stream_id:
                    # meta might be a dict with a title
                    if isinstance(meta, dict):
                        return meta.get('title') or meta.get('name') or stream_id
                    # otherwise meta might be a string name
                    return str(meta)
    except Exception:
        pass

    # Last resort: return the provided value unchanged
    return stream_id

def load_schedule_times():
    try:
        with open('schedule_config.json', 'r') as f:
            config = json.load(f)
            return config.get('schedule_times', ["00:35", "00:37", "00:39"])
    except:
        return ["00:35", "00:37", "00:39"]

def save_schedule_times(times):
    with open('schedule_config.json', 'w') as f:
        json.dump({'schedule_times': times}, f)

def get_stream_mapping():
    try:
        with open('stream_mapping.json', 'r') as f:
            return json.load(f)
    except:
        return {}

@app.route('/edit_schedule/<int:index>', methods=['GET'])
@login_required
def edit_schedule(index):
    # Restrict demo role from editing schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat mengedit jadwal.', 'error')
        return redirect(url_for('schedules'))
    try:
        # Read the Excel file
        if not os.path.exists(EXCEL_FILE):
            flash('Schedule file not found!', 'error')
            return redirect(url_for('schedules'))
        df = pd.read_excel(EXCEL_FILE)
        schedule = df.iloc[index].to_dict()
        
        # Clean up NaN values
        for key, value in schedule.items():
            if pd.isna(value):
                schedule[key] = ''
        
        # Handle the datetime conversion
        try:
            # Try to parse the datetime from the Excel value
            dt = pd.to_datetime(schedule['scheduledStartTime'])
            # Format it for the datetime-local input
            schedule['scheduledStartTime'] = dt.strftime('%Y-%m-%dT%H:%M')
        except:
            # If parsing fails, try to use the value as-is if it's properly formatted
            current_value = str(schedule.get('scheduledStartTime', ''))
            if 'T' in current_value:  # Check if it's already in the correct format
                schedule['scheduledStartTime'] = current_value
            else:
                schedule['scheduledStartTime'] = ''  # Set empty if invalid
        
        # Normalize thumbnail path - remove 'thumbnails/' prefix for comparison
        if schedule.get('thumbnailFile'):
            schedule['thumbnailFile'] = schedule['thumbnailFile'].replace('thumbnails/', '')
        
        # Ensure boolean fields are actual booleans
        for bool_field in ['autoStart', 'autoStop', 'madeForKids', 'useExistingStream', 'repeat_daily']:
            if bool_field in schedule:
                schedule[bool_field] = bool(schedule[bool_field])
        
        tokens = get_token_files()
        stream_mapping = get_stream_mapping()
        thumbnails = get_thumbnail_database()
        return render_template('edit_schedule.html', schedule=schedule, index=index, 
                             tokens=tokens, stream_mapping=stream_mapping, thumbnails=thumbnails)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('schedules'))

@app.route('/update_schedule/<int:index>', methods=['POST'])
@login_required
@demo_readonly
def update_schedule(index):
    # Restrict demo role from updating schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat mengubah jadwal.', 'error')
        return redirect(url_for('schedules'))
    try:
        data = request.form.to_dict()
        if not os.path.exists(EXCEL_FILE):
            flash('Schedule file not found!', 'error')
            return redirect(url_for('schedules'))
        df = pd.read_excel(EXCEL_FILE)
        
        # Resolve stream name and log for debugging
        submitted_stream = data.get('streamNameExisting', '')
        resolved_stream = get_stream_name(submitted_stream)
        app.logger.debug(f"update_schedule: submitted stream='{submitted_stream}' resolved='{resolved_stream}'")

        # Fix thumbnail path: add 'thumbnails/' prefix if needed
        thumbnail_file = data.get('thumbnailFile', '').strip()
        if thumbnail_file and not thumbnail_file.startswith('thumbnails/'):
            thumbnail_file = f'thumbnails/{thumbnail_file}'
        
        # Update the row
        df.loc[index, 'title'] = data['title']
        df.loc[index, 'description'] = data['description']
        df.loc[index, 'scheduledStartTime'] = data['scheduledStartTime']
        df.loc[index, 'privacyStatus'] = data.get('privacyStatus', 'unlisted')
        df.loc[index, 'autoStart'] = data.get('autoStart') == 'on'
        df.loc[index, 'autoStop'] = data.get('autoStop') == 'on'
        df.loc[index, 'madeForKids'] = data.get('madeForKids') == 'on'
        df.loc[index, 'tokenFile'] = data['tokenFile']
        df.loc[index, 'useExistingStream'] = data.get('useExistingStream') == 'on'
        df.loc[index, 'streamNameExisting'] = resolved_stream
        df.loc[index, 'thumbnailFile'] = thumbnail_file
        df.loc[index, 'repeat_daily'] = data.get('repeat_daily') == 'on'
        
        # Save the changes
        df.to_excel(EXCEL_FILE, index=False)
        flash('Schedule updated successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/delete_schedule/<int:index>', methods=['POST'])
@login_required
@demo_readonly
def delete_schedule(index):
    # Restrict demo role from deleting schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat menghapus jadwal.', 'error')
        return redirect(url_for('schedules'))
    try:
        if not os.path.exists(EXCEL_FILE):
            flash('Schedule file not found!', 'error')
            return redirect(url_for('schedules'))
        df = pd.read_excel(EXCEL_FILE)
        df = df.drop(index)
        df.to_excel(EXCEL_FILE, index=False)
        flash('Schedule deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/stream_keys')
@login_required
def stream_keys():
    # Get available tokens
    tokens = get_token_files()
    # Get current stream mapping
    stream_mapping = get_stream_mapping()
    return render_template('stream_keys.html', tokens=tokens, stream_mapping=stream_mapping)


@app.route('/manage_streams')
@login_required
def manage_streams():
    from kunci import load_stream_mapping
    stream_mapping = load_stream_mapping()
    return render_template('manage_streams.html', stream_mapping=stream_mapping)


@app.route('/delete_stream_mapping', methods=['POST'])
@login_required
def delete_stream_mapping():
    token_file = request.form.get('token_file')
    stream_id = request.form.get('stream_id')
    try:
        mapping = get_stream_mapping()
        if token_file in mapping and stream_id in mapping[token_file]:
            del mapping[token_file][stream_id]
            # if token has no more streams, keep empty dict or remove key
            if not mapping[token_file]:
                mapping.pop(token_file, None)
            with open('stream_mapping.json', 'w') as f:
                json.dump(mapping, f, indent=4)
            flash('Stream mapping deleted.', 'success')
        else:
            flash('Stream mapping not found.', 'warning')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_streams'))


@app.route('/delete_token_mapping', methods=['POST'])
@login_required
def delete_token_mapping():
    token_file = request.form.get('token_file')
    try:
        mapping = get_stream_mapping()
        if token_file in mapping:
            mapping.pop(token_file, None)
            with open('stream_mapping.json', 'w') as f:
                json.dump(mapping, f, indent=4)
            flash('Token mappings deleted.', 'success')
        else:
            flash('Token not found in mappings.', 'warning')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_streams'))


@app.route('/export_stream_mapping', methods=['POST'])
@login_required
def export_stream_mapping():
    try:
        mapping = get_stream_mapping()
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
    from kunci import get_stream_keys, save_stream_mapping
    token_file = request.form.get('token_file')
    if not token_file:
        flash('Please select a token file', 'error')
        return redirect(url_for('stream_keys'))
    
    try:
        # Get stream keys from YouTube
        stream_keys = get_stream_keys(token_file)
        if stream_keys:
            # Save to stream_mapping.json under the token filename (merge existing)
            if save_stream_mapping(stream_keys, token_file):
                flash('Stream keys fetched and saved successfully!', 'success')
            else:
                flash('Error saving stream keys', 'error')
        else:
            flash('No stream keys found', 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('stream_keys'))

@app.route('/create_new_stream', methods=['POST'])
@login_required
def create_new_stream():
    """Create a new stream key in YouTube Studio"""
    stream_title = request.form.get('stream_title', '').strip()
    token_file = request.form.get('token_file')
    
    if not stream_title:
        flash('Stream title is required', 'error')
        return redirect(url_for('stream_keys'))
    
    if not token_file:
        flash('Please select a token file', 'error')
        return redirect(url_for('stream_keys'))
    
    try:
        # Import YouTube service
        from kunci import get_youtube_service
        
        # Create YouTube service using token
        youtube = get_youtube_service(token_file)
        
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
        stream_name = response['cdn']['ingestionInfo']['streamName']
        
        # Save to stream_mapping.json
        import json
        mapping = {}
        if os.path.exists('stream_mapping.json'):
            with open('stream_mapping.json', 'r') as f:
                mapping = json.load(f)
        
        if token_file not in mapping:
            mapping[token_file] = {}
        
        mapping[token_file][stream_id] = {
            'title': stream_title,
            'cdn': response['cdn']
        }
        
        with open('stream_mapping.json', 'w') as f:
            json.dump(mapping, f, indent=2)
        
        flash(f'Stream key created successfully! Title: "{stream_title}", Key: {stream_name}', 'success')
        
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
        
        ok, msg = create_user(username, password, role='demo')
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

    # Get tokens
    tokens = get_token_files()
    
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
        
        # Get tokens count
        tokens = get_token_files()
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
    if 'video_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('video_gallery'))
    
    file = request.files['video_file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('video_gallery'))
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Generate thumbnail from first frame
        thumbnail_filename = None
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
                thumbnail_path
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, timeout=30)
        except Exception as e:
            print(f"Could not generate thumbnail: {e}")
            thumbnail_filename = None
        
        # Add to database
        video_title = request.form.get('video_title', 'Untitled Video')
        videos = get_video_database()
        videos.append({
            'id': str(uuid.uuid4()),
            'title': video_title,
            'filename': unique_filename,
            'original_filename': original_filename,
            'thumbnail': thumbnail_filename,
            'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'local'
        })
        save_video_database(videos)
        
        flash('Video uploaded successfully!', 'success')
        return redirect(url_for('video_gallery'))
    
    flash('Invalid file type. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS), 'danger')
    return redirect(url_for('video_gallery'))

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
        videos = get_video_database()
        videos.append({
            'id': str(uuid.uuid4()),
            'title': video_title,
            'filename': unique_filename,
            'original_filename': f"google_drive_{file_id}.{file_extension}",
            'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'google_drive',
            'drive_file_id': file_id
        })
        save_video_database(videos)
        
        flash('Video imported from Google Drive successfully!', 'success')
    except Exception as e:
        flash(f'Error importing video: {str(e)}', 'danger')
    
    return redirect(url_for('video_gallery'))

@app.route('/delete-video/<video_id>')
@login_required
@demo_readonly
def delete_video(video_id):
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
        
        # Remove from database
        videos = [v for v in videos if v['id'] != video_id]
        save_video_database(videos)
        
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
        thumbnails = get_thumbnail_database()
        thumbnails.append({
            'id': str(uuid.uuid4()),
            'title': thumbnail_title,
            'filename': unique_filename,
            'original_filename': original_filename,
            'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_thumbnail_database(thumbnails)
        
        flash('Thumbnail uploaded successfully!', 'success')
        return redirect(url_for('thumbnail_gallery'))
    
    flash('Invalid file type. Allowed types: ' + ', '.join(ALLOWED_THUMBNAIL_EXTENSIONS), 'danger')
    return redirect(url_for('thumbnail_gallery'))

@app.route('/delete-thumbnail/<thumbnail_id>')
@login_required
@demo_readonly
def delete_thumbnail(thumbnail_id):
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
        thumbnails = [t for t in thumbnails if t['id'] != thumbnail_id]
        save_thumbnail_database(thumbnails)
        
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
    
    # Add video titles to streams for display
    for stream in unique_streams:
        video_path = os.path.join(VIDEO_FOLDER, stream['video_file'])
        stream['video_title'] = get_video_title(stream['video_file'])
    
    print(f"Total streams to display: {len(unique_streams)}")
    return render_template('live_streams.html', streams=unique_streams, videos=videos, rtmp_servers=RTMP_SERVERS, stream_mapping=stream_mapping)

@app.route('/edit-live-stream/<stream_id>', methods=['GET', 'POST'])
@login_required
@demo_readonly
def edit_live_stream(stream_id):
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role):
        flash('Role Anda tidak diizinkan mengedit jadwal (demo-preview).', 'error')
        return redirect(url_for('live_streams'))
    streams = get_live_streams()
    videos = get_video_database()
    
    # Find the stream to edit
    stream_to_edit = None
    for stream in streams:
        if stream['id'] == stream_id:
            stream_to_edit = stream
            break
    
    if not stream_to_edit:
        flash('Jadwal live stream tidak ditemukan')
        return redirect(url_for('live_streams'))
    
    if request.method == 'POST':
        if stream_to_edit.get('owner') and stream_to_edit['owner'] != current_user.username and not role_can_manage(role):
            flash('Tidak dapat mengedit stream milik user lain.', 'error')
            return redirect(url_for('live_streams'))
        # Update stream data
        stream_to_edit['title'] = request.form['title']
        stream_to_edit['start_date'] = request.form['start_date']
        stream_to_edit['rtmp_server'] = request.form['rtmp_server']
        stream_to_edit['stream_key'] = request.form['stream_key']
        stream_to_edit['duration'] = request.form.get('duration')
        
        # Handle custom RTMP
        if stream_to_edit['rtmp_server'] == 'custom':
            stream_to_edit['custom_rtmp'] = request.form['custom_rtmp']
        
        # Find video title
        video_file = request.form['video_file']
        stream_to_edit['video_file'] = video_file
        stream_to_edit['video_title'] = get_video_title(video_file)
        
        # Handle repeat daily option
        stream_to_edit['repeat_daily'] = 'repeat_daily' in request.form
        
        # Save changes
        save_live_streams(streams)
        flash('Jadwal live stream berhasil diperbarui')
        return redirect(url_for('live_streams'))
    
    return render_template('edit_live_stream.html', stream=stream_to_edit, videos=videos, rtmp_servers=RTMP_SERVERS)

@app.route('/add-live-stream', methods=['POST'])
@login_required
@demo_readonly
def add_live_stream():
    # Role restriction
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role):
        flash('Role Anda tidak diizinkan membuat live/schedule (demo-preview).', 'error')
        return redirect(url_for('live_streams'))
    title = request.form.get('title')
    start_date = request.form.get('start_date')
    rtmp_server = request.form.get('rtmp_server')
    stream_key = request.form.get('stream_key')
    video_file = request.form.get('video_file')
    duration = request.form.get('duration')
    repeat_daily = 'repeat_daily' in request.form
    custom_rtmp = request.form.get('custom_rtmp', '')
    
    # Debug print
    print(f"Form data: title={title}, start_date={start_date}, rtmp_server={rtmp_server}, stream_key={stream_key}, video_file={video_file}, duration={duration}, repeat_daily={repeat_daily}")
    
    # Validate inputs
    if not title or not start_date or not rtmp_server or not stream_key or not video_file:
        flash('Semua field harus diisi')
        return redirect(url_for('live_streams'))
    
    # Create new stream
    new_stream = {
        'id': str(uuid.uuid4()),
        'title': title,
        'start_date': start_date,
        'rtmp_server': rtmp_server,
        'stream_key': stream_key,
        'video_file': video_file,
        'duration': duration,
        'repeat_daily': repeat_daily,
        'custom_rtmp': custom_rtmp if rtmp_server == 'custom' else '',
        'status': 'scheduled',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'owner': current_user.username
    }
    
    # Add to streams with role limit check
    streams = get_live_streams()
    # Count user's active streams (scheduled or live)
    user_active = sum(1 for s in streams if s.get('owner') == current_user.username and s.get('status') in ['scheduled', 'live'])
    max_allowed = role_max_streams(role)
    if max_allowed is not None and user_active >= max_allowed:
        flash(f'Melebihi batas video aktif untuk role {role} (maks {max_allowed}).', 'error')
        return redirect(url_for('live_streams'))
    streams.append(new_stream)
    save_live_streams(streams)
    
    # Debug print
    print(f"Saved stream: {new_stream}")
    print(f"Total streams: {len(streams)}")
    
    flash('Jadwal live stream berhasil ditambahkan')
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
    streams = get_live_streams()
    action = request.args.get('action', 'stop')  # Default action is stop
    
    for i, stream in enumerate(streams):
        if stream['id'] == stream_id:
            role = getattr(current_user, 'role', 'demo')
            if stream.get('owner') and stream['owner'] != current_user.username and not role_can_manage(role):
                flash('Tidak dapat mengubah stream milik user lain.', 'error')
                return redirect(url_for('live_streams'))
            if action == 'delete':
                # Hapus jadwal
                if stream['status'] == 'live':
                    # Stop the stream if it's running
                    stop_ffmpeg_stream(stream_id)
                
                # Remove from list
                streams.pop(i)
                save_live_streams(streams)
                flash('Jadwal live stream berhasil dihapus')
            else:  # action == 'stop'
                if stream['status'] == 'live':
                    # Stop the stream if it's running
                    stop_ffmpeg_stream(stream_id)
                    # Update status to completed but keep the schedule
                    stream['status'] = 'completed'
                    save_live_streams(streams)
                    
                    # Update Excel file to increment scheduledStartTime by 1 day
                    try:
                        df = pd.read_excel(EXCEL_FILE)
                        # Assuming 'title' is a unique identifier or you have another way to match
                        # For now, let's match by title and the original start date to be safe
                        original_start_date_str = stream['start_date'] # Format YYYY-MM-DDTHH:MM
                        original_start_date_dt = datetime.strptime(original_start_date_str, '%Y-%m-%dT%H:%M')
                    
                        # Find the row in Excel that matches the stream title and a close scheduled start time
                        # We'll compare dates only for finding the row to avoid issues with slight time differences
                        matching_rows = df[
                            (df['title'] == stream['title']) &
                            (pd.to_datetime(df['scheduledStartTime']).dt.date == original_start_date_dt.date)
                        ]
                    
                        if not matching_rows.empty:
                            # Take the first match if multiple are found (should ideally be unique)
                            idx_to_update = matching_rows.index[0]
                            
                            # Increment date by 1 day
                            current_excel_date = pd.to_datetime(df.loc[idx_to_update, 'scheduledStartTime'])
                            new_excel_date = current_excel_date + timedelta(days=1)
                            df.loc[idx_to_update, 'scheduledStartTime'] = new_excel_date.strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Save the updated Excel file
                            df.to_excel(EXCEL_FILE, index=False)
                            logging.info(f"✅ Excel updated for '{stream['title']}': New scheduled date {new_excel_date.strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            logging.warning(f"⚠️ No matching entry found in Excel for stream '{stream['title']}' with original date {original_start_date_dt.date()}")
                    except Exception as excel_err:
                        logging.error(f"❌ Error updating Excel file: {excel_err}")

                    # NOTE: Repeat daily logic is handled in stop_ffmpeg_stream() function
                    # to avoid duplicate schedules (called from both auto-stop and manual stop)
                    flash('Live stream berhasil dihentikan')
                    break
            save_live_streams(streams)
            break
    
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
    return render_template('admin_users_cyber.html', users=users)

# Route sudah didefinisikan sebelumnya

@app.route('/schedules')
@login_required
def schedules():
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            schedules = df.to_dict('records')
            # Clean up NaN values to avoid template errors
            for schedule in schedules:
                for key, value in schedule.items():
                    if pd.isna(value):
                        schedule[key] = ''
        else:
            # Create empty Excel file with proper columns
            df = pd.DataFrame(columns=['title', 'scheduledStartTime', 'videoFile', 'thumbnail', 'streamNameExisting', 'streamIdExisting', 'token_file', 'repeat_daily'])
            df.to_excel(EXCEL_FILE, index=False)
            schedules = []
    except Exception as e:
        logging.error(f"Error loading schedules: {e}")
        schedules = []
    stream_mapping = get_stream_mapping()
    # Get list of available tokens
    tokens = get_token_files()
    # Get thumbnails
    thumbnails = get_thumbnail_database()
    return render_template('schedules.html', schedules=schedules, stream_mapping=stream_mapping, tokens=tokens, thumbnails=thumbnails)

@app.route('/add_schedule', methods=['POST'])
@login_required
@demo_readonly
def add_schedule():
    # Restrict demo role from adding schedules
    role = getattr(current_user, 'role', 'demo')
    if not role_can_add_streams(role) and not role_can_manage(role):
        flash('Akses ditolak: role demo tidak dapat menambahkan jadwal.', 'error')
        return redirect(url_for('schedules'))
    try:
        data = request.form.to_dict()
        df = pd.read_excel(EXCEL_FILE) if os.path.exists(EXCEL_FILE) else pd.DataFrame()
        
        # Resolve stream name and log for debugging
        submitted_stream = data.get('streamNameExisting', '')
        resolved_stream = get_stream_name(submitted_stream)
        app.logger.debug(f"add_schedule: submitted stream='{submitted_stream}' resolved='{resolved_stream}'")

        # Fix thumbnail path: add 'thumbnails/' prefix if needed
        thumbnail_file = data.get('thumbnailFile', '').strip()
        if thumbnail_file and not thumbnail_file.startswith('thumbnails/'):
            thumbnail_file = f'thumbnails/{thumbnail_file}'
        
        new_row = {
            'title': data['title'],
            'description': data['description'],
            'scheduledStartTime': data['scheduledStartTime'],
            'privacyStatus': data.get('privacyStatus', 'unlisted'),
            'autoStart': data.get('autoStart') == 'on',
            'autoStop': data.get('autoStop') == 'on',
            'madeForKids': data.get('madeForKids') == 'on',
            'tokenFile': data['tokenFile'],
            'useExistingStream': data.get('useExistingStream') == 'on',
            'streamNameExisting': resolved_stream,
            'thumbnailFile': thumbnail_file,
            'repeat_daily': data.get('repeat_daily') == 'on',
            'success': False,
            'streamId': '',
            'broadcastLink': '',
            'streamIdExisting': ''
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)
        flash('Schedule added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('schedules'))

@app.route('/run_schedule_now/<int:index>', methods=['POST'])
@login_required
@demo_readonly
def run_schedule_now(index):
    """Run a single schedule manually (on-demand execution)"""
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
        from live import schedule_live_stream
        from kunci import get_youtube_service
        
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
            telegram_notifier.notify_schedule_created(title, display_time, broadcast_link)
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
            telegram_notifier.notify_schedule_error(title if 'title' in locals() else 'Unknown', str(e))
        except:
            pass
    
    return redirect(url_for('schedules'))

@app.route('/tokens')
@login_required
def tokens():
    tokens = get_token_files()
    return render_template('tokens.html', tokens=tokens)

@app.route('/create_token', methods=['POST'])
@login_required
@demo_readonly
def create_token():
    try:
        token_name = request.form.get('token_name', 'token.json')
        if not token_name.endswith('.json'):
            token_name += '.json'
        
        # Generate authorization URL using Flow
        flow = Flow.from_client_secrets_file(
            'client_secret.json',
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
        auth_code = request.form.get('auth_code', '').strip()
        
        if not auth_code:
            flash('Kode authorization tidak boleh kosong', 'error')
            return redirect(url_for('tokens'))
        
        # Create flow again and fetch token
        flow = Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=SCOPES,
            redirect_uri='http://localhost'
        )
        
        # Fetch token using the authorization code
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # Save token to tokens folder
        token_path = get_token_path(token_name)
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
        
        # Try to delete the token file from tokens folder
        token_path = get_token_path(token_name)
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
    import live
    current_time = datetime.now(pytz.timezone(TIMEZONE))
    times = load_schedule_times()
    current_time_str = current_time.strftime('%H:%M')
    
    if current_time_str in times:
        try:
            live.main()  # Run the scheduler
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

@app.route('/auto_schedule')
@login_required
def auto_schedule():
    schedule_times = load_schedule_times()
    scheduler_status = get_scheduler_status()
    return render_template('auto_schedule.html', 
                         schedule_times=schedule_times,
                         scheduler_status=scheduler_status)

@app.route('/update_schedule_times', methods=['POST'])
@login_required
def update_schedule_times():
    # Restrict to admin only
    role = getattr(current_user, 'role', 'demo')
    if not role_can_manage(role):
        flash('Akses ditolak: hanya admin yang dapat mengubah Auto Schedule.', 'error')
        return redirect(url_for('auto_schedule'))
    times = request.form.getlist('times[]')
    save_schedule_times(times)
    flash('Jadwal auto-scheduling berhasil diupdate!', 'success')
    return redirect(url_for('auto_schedule'))

@app.route('/run_scheduler', methods=['POST'])
@login_required
def run_scheduler():
    # Restrict to admin only
    role = getattr(current_user, 'role', 'demo')
    if not role_can_manage(role):
        flash('Akses ditolak: hanya admin yang dapat menjalankan scheduler.', 'error')
        return redirect(url_for('auto_schedule'))
    try:
        import live
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
    return redirect(url_for('auto_schedule'))

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
    """Telegram notification settings page"""
    # Check if user has permission
    role = getattr(current_user, 'role', 'demo')
    if not role_can_manage(role):
        flash('Access denied: Only admin can manage Telegram settings.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        config = {
            'enabled': request.form.get('enabled') == 'on',
            'bot_token': request.form.get('bot_token', '').strip(),
            'chat_id': request.form.get('chat_id', '').strip()
        }
        
        telegram_notifier.save_config(config)
        flash('Telegram settings saved successfully!', 'success')
        return redirect(url_for('telegram_settings'))
    
    config = telegram_notifier.load_config()
    return render_template('telegram_settings.html', config=config)

@app.route('/telegram_test', methods=['POST'])
@login_required
def telegram_test():
    """Test Telegram bot connection"""
    role = getattr(current_user, 'role', 'demo')
    if not role_can_manage(role):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    success, message = telegram_notifier.test_connection()
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

    # Start Flask in production mode
    app.run(debug=False, use_reloader=False, host='0.0.0.0')

