# 📚 JadwalStream - Codebase Guide & Architecture

> **Panduan lengkap untuk memahami struktur kode, arsitektur, dan cara kerja JadwalStream**  
> Dibuat: 21 November 2025  
> Versi: 1.0

---

## 📋 Daftar Isi

1. [Overview Aplikasi](#overview-aplikasi)
2. [Arsitektur Sistem](#arsitektur-sistem)
3. [Struktur Folder](#struktur-folder)
4. [Database Schema](#database-schema)
5. [Modul-Modul Utama](#modul-modul-utama)
6. [Flow Diagram](#flow-diagram)
7. [API Routes](#api-routes)
8. [Fitur-Fitur Utama](#fitur-fitur-utama)
9. [Panduan Update Fitur](#panduan-update-fitur)

---

## 🎯 Overview Aplikasi

**JadwalStream** adalah platform automation untuk mengelola livestream dan upload video YouTube dengan fitur:

### Fitur Utama
- 🎥 **Live Streaming**: Multi-platform RTMP (YouTube, Facebook, Instagram, Twitch, TikTok)
- 📤 **Bulk Upload**: Upload banyak video sekaligus dengan AI metadata generator
- 🔄 **Video Looping**: Loop video pendek menjadi video panjang
- 🤖 **AI Integration**: Gemini AI untuk generate metadata (title, description, tags)
- 👥 **Multi-User System**: Isolasi data per user dengan role-based access
- 📱 **Telegram Notifications**: Notifikasi real-time dengan bahasa gaul Indonesia
- 🔐 **License System**: Hardware-locked license dengan Google Apps Script backend
- ⏰ **Auto Scheduler**: Jadwal otomatis untuk streaming dan upload

### Tech Stack
- **Backend**: Flask (Python 3.10+)
- **Database**: SQLite dengan row-level user isolation
- **Frontend**: Jinja2 templates, TailwindCSS, Alpine.js
- **Video Processing**: FFmpeg
- **APIs**: YouTube Data API v3, Google Gemini AI
- **Authentication**: Flask-Login dengan OAuth 2.0

---

## 🏗️ Arsitektur Sistem

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application                        │
│                        (app.py)                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Auth       │  │   Database   │  │   Services   │      │
│  │   Module     │  │   Module     │  │   Module     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   YouTube    │  │   Utils      │  │   Telegram   │      │
│  │   Module     │  │   Module     │  │   Notifier   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │         SQLite Database               │
        │       (jadwalstream.db)               │
        │                                       │
        │  • users                              │
        │  • videos                             │
        │  • thumbnails                         │
        │  • live_streams                       │
        │  • schedules                          │
        │  • looped_videos                      │
        │  • bulk_upload_queue                  │
        │  • stream_mappings                    │
        └───────────────────────────────────────┘
```

### Request Flow

```
User Request
    │
    ▼
Flask Route (@app.route)
    │
    ▼
Authentication Check (@login_required)
    │
    ▼
License Validation (@app.before_request)
    │
    ▼
Permission Check (role/limits)
    │
    ▼
Business Logic
    │
    ├─► Database Operations (modules/database)
    ├─► YouTube API (modules/youtube)
    ├─► FFmpeg Processing
    └─► Telegram Notifications
    │
    ▼
Response (HTML/JSON)
```

---

## 📁 Struktur Folder

```
jadwalstream/
│
├── app.py                          # Main Flask application (4702 lines)
├── requirements.txt                # Python dependencies
├── install.sh                      # Auto installer script
├── README.md                       # User documentation
├── guide.md                        # This file (developer guide)
│
├── modules/                        # Modular code organization
│   ├── __init__.py
│   │
│   ├── auth/                       # Authentication & Authorization
│   │   ├── __init__.py
│   │   ├── user_auth.py           # User login, registration, password
│   │   └── user_limits.py         # Per-user limits (streams, storage)
│   │
│   ├── database/                   # Database operations
│   │   ├── __init__.py
│   │   ├── database.py            # Main DB functions (954 lines)
│   │   └── database_helpers.py    # Helper functions
│   │
│   ├── services/                   # External services
│   │   ├── __init__.py
│   │   ├── telegram_notifier.py   # Telegram bot integration (375 lines)
│   │   └── client_secret_manager.py # Per-user OAuth credentials
│   │
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── license_validator.py   # License system (240 lines)
│   │   └── hwid.py                # Hardware ID generation
│   │
│   └── youtube/                    # YouTube API integration
│       ├── __init__.py
│       ├── jadwal.py              # Scheduler for auto-upload (285 lines)
│       ├── kunci.py               # Stream keys management
│       └── live.py                # Live broadcast creation (296 lines)
│
├── templates/                      # Jinja2 HTML templates (27 files)
├── static/css/                     # CSS files
├── videos/                         # User uploaded videos (gitignored)
├── thumbnails/                     # User uploaded thumbnails (gitignored)
├── tokens/                         # OAuth tokens per user (gitignored)
├── ffmpeg_logs/                    # FFmpeg process logs (gitignored)
└── jadwalstream.db                 # SQLite database (gitignored)
```

---

## 🗄️ Database Schema

### Tabel Utama

#### 1. **users** - User accounts
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    is_admin INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'approved',  -- pending/approved/rejected
    
    -- Limits
    max_streams INTEGER,
    max_storage_mb INTEGER,
    
    -- Expiry
    expiry_days INTEGER,
    expiry_date TIMESTAMP,
    account_status TEXT DEFAULT 'active',  -- active/expired
    
    -- Contact
    whatsapp TEXT,
    profile_picture TEXT,
    
    -- Per-user configs
    scheduler_times TEXT,  -- JSON array
    telegram_bot_token TEXT,
    telegram_chat_id TEXT,
    telegram_enabled INTEGER DEFAULT 0,
    gemini_api_key TEXT,
    gemini_model TEXT,
    gemini_custom_prompt TEXT,
    auto_upload_enabled INTEGER DEFAULT 0,
    auto_upload_offset_hours INTEGER DEFAULT 2,
    auto_upload_check_interval INTEGER DEFAULT 30,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. **videos** - User uploaded videos
```sql
CREATE TABLE videos (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT,
    thumbnail TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT DEFAULT 'local',  -- 'local' or 'google_drive'
    drive_file_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_videos_user_id ON videos(user_id);
```

#### 3. **thumbnails** - User uploaded thumbnails
```sql
CREATE TABLE thumbnails (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 4. **live_streams** - RTMP streaming sessions
```sql
CREATE TABLE live_streams (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    video_file TEXT NOT NULL,
    stream_id TEXT,
    stream_key TEXT,
    stream_url TEXT,  -- Custom RTMP URL
    server_type TEXT DEFAULT 'youtube',  -- youtube/facebook/twitch/custom
    status TEXT DEFAULT 'scheduled',  -- scheduled/live/completed
    process_pid INTEGER,  -- FFmpeg process ID
    start_date TEXT,
    end_date TEXT,
    duration INTEGER,  -- in minutes
    auto_stop_enabled INTEGER DEFAULT 0,
    auto_stop_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 5. **schedules** - YouTube broadcast schedules
```sql
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    scheduled_start_time TIMESTAMP NOT NULL,
    video_file TEXT NOT NULL,
    thumbnail TEXT,
    stream_name TEXT,
    stream_id TEXT,
    token_file TEXT,
    repeat_daily INTEGER DEFAULT 0,
    success INTEGER DEFAULT 0,
    broadcast_link TEXT,
    privacy_status TEXT DEFAULT 'unlisted',
    auto_start INTEGER DEFAULT 0,
    auto_stop INTEGER DEFAULT 0,
    made_for_kids INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 6. **looped_videos** - Video looping queue
```sql
CREATE TABLE looped_videos (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    original_video_id TEXT NOT NULL,
    original_filename TEXT,
    original_title TEXT,
    loop_duration_minutes INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending/processing/completed/failed
    progress INTEGER DEFAULT 0,
    output_filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 7. **bulk_upload_queue** - Video upload queue
```sql
CREATE TABLE bulk_upload_queue (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    video_id TEXT NOT NULL,
    video_path TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT,  -- JSON array stored as TEXT
    scheduled_publish_time TIMESTAMP,
    token_file TEXT,
    stream_id TEXT,
    thumbnail_id TEXT,
    privacy_status TEXT DEFAULT 'private',
    status TEXT DEFAULT 'queued',  -- queued/uploading/completed/failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP,
    youtube_video_id TEXT,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 8. **stream_mappings** - YouTube stream keys mapping
```sql
CREATE TABLE stream_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_file TEXT NOT NULL,
    stream_id TEXT NOT NULL,
    stream_name TEXT,
    stream_key TEXT,
    metadata TEXT,  -- JSON stored as TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, token_file, stream_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 🧩 Modul-Modul Utama

### 1. **modules/auth/** - Authentication & Authorization

#### `user_auth.py` (200 lines)
**Fungsi utama:**
- `User` class: Flask-Login user model
- `get_user_by_username()`: Load user dari database
- `get_user_by_id()`: Load user by ID
- `create_user()`: Buat user baru
- `authenticate_user()`: Validasi login
- `change_password()`: Ubah password
- `approve_user()` / `reject_user()`: Admin approval
- `initialize_default_user()`: Create default admin

**Contoh penggunaan:**
```python
# Login flow
user = authenticate_user(username, password)
if user:
    login_user(user)
    return redirect(url_for('home'))
```

#### `user_limits.py` (256 lines)
**Fungsi utama:**
- `get_user_limits(user_id)`: Get user limits & usage
- `can_user_add_stream(user_id)`: Check if user can add more streams
- `can_user_upload(user_id, file_size_mb)`: Check storage limit
- `calculate_user_storage(user_id)`: Calculate total storage used
- `update_user_limits(user_id, max_streams, max_storage_mb)`: Admin update limits

**Contoh penggunaan:**
```python
# Check before adding stream
can_add, message = can_user_add_stream(user_id)
if not can_add:
    flash(f'Cannot add stream: {message}', 'error')
    return redirect(url_for('live_streams'))

# Check before upload
can_upload, message = can_user_upload(user_id, file_size_mb)
if not can_upload:
    flash(f'Upload failed: {message}', 'error')
```

---

### 2. **modules/database/** - Database Operations

#### `database.py` (954 lines)
**Core functions:**

**User Management:**
```python
get_user_by_username(username)
get_user_by_id(user_id)
create_user(username, password_hash, role, status, expiry_days, whatsapp)
update_user_role(username, role)
delete_user(username)
check_user_expiry(user_id)  # Check if account expired
```

**Video Management:**
```python
get_videos(user_id)  # Get user's videos
add_video(user_id, video_data)
delete_video(video_id, user_id)
```

**Live Stream Management:**
```python
get_live_streams(user_id)
add_live_stream(user_id, stream_data)
update_live_stream(stream_id, user_id, updates)
delete_live_stream(stream_id, user_id)
```

**Schedule Management:**
```python
get_schedules(user_id)  # Per-user schedules
get_all_schedules()  # All users (for scheduler)
add_schedule(user_id, schedule_data)
update_schedule(schedule_id, user_id, updates)
delete_schedule(schedule_id, user_id)
```

**Bulk Upload Queue:**
```python
get_bulk_upload_queue(user_id)
add_bulk_upload_item(user_id, upload_data)
update_bulk_upload_item(upload_id, user_id, updates)
```

**Database Context Manager:**
```python
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# Usage:
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None
```

---

### 3. **modules/youtube/** - YouTube API Integration

#### `live.py` (296 lines)
**Fungsi utama:**
- `schedule_live_stream()`: Create YouTube broadcast
- `get_stream_id_from_name()`: Resolve stream name to ID
- `load_stream_mapping()`: Load stream keys mapping

**Flow create broadcast:**
```python
def schedule_live_stream(youtube, title, description, scheduled_start_time,
                         privacy_status, auto_start, auto_stop, made_for_kids,
                         use_existing_stream, streamNameExisting, token_file):
    
    # 1. Get or create stream
    if use_existing_stream:
        stream_id = get_stream_id_from_name(streamNameExisting, token_file)
    else:
        stream_response = youtube.liveStreams().insert(
            part='snippet,cdn',
            body={
                'snippet': {'title': f"Stream Key for: {title}"},
                'cdn': {'frameRate': 'variable', 'ingestionType': 'rtmp'}
            }
        ).execute()
        stream_id = stream_response['id']
    
    # 2. Create broadcast
    broadcast_response = youtube.liveBroadcasts().insert(
        part='snippet,status,contentDetails',
        body={
            'snippet': {
                'title': title,
                'description': description,
                'scheduledStartTime': scheduled_start_time
            },
            'status': {'privacyStatus': privacy_status},
            'contentDetails': {
                'enableAutoStart': auto_start,
                'enableAutoStop': auto_stop
            }
        }
    ).execute()
    broadcast_id = broadcast_response['id']
    
    # 3. Bind broadcast to stream
    youtube.liveBroadcasts().bind(
        part='id,contentDetails',
        id=broadcast_id,
        streamId=stream_id
    ).execute()
    
    return broadcast_id, stream_id
```

#### `jadwal.py` (285 lines)
**Auto-scheduler untuk YouTube broadcasts**

**Fungsi utama:**
- `process_schedule(schedule)`: Process single schedule
- `run_scheduler()`: Main scheduler loop
- `schedule_jobs()`: Setup cron-like schedule

**Flow:**
```python
def run_scheduler():
    # 1. Get all pending schedules from database
    pending_schedules = get_all_pending_schedules()
    
    # 2. Process each schedule
    for schedule in pending_schedules:
        user_id = schedule['user_id']
        token_path = get_user_token_path(user_id, schedule['token_file'])
        
        # 3. Authenticate with YouTube
        youtube = get_youtube_service(token_path)
        
        # 4. Create broadcast
        broadcast_id, stream_id = schedule_live_stream(...)
        
        # 5. Upload thumbnail (if exists)
        if thumbnail:
            youtube.thumbnails().set(videoId=broadcast_id, ...)
        
        # 6. Update database
        update_schedule_status(schedule_id, success=True, ...)
        
        # 7. Send Telegram notification
        telegram_notifier.notify_schedule_created(...)
        
        # 8. Handle repeat_daily
        if repeat_daily:
            # Create next day schedule
            add_schedule(user_id, new_schedule_data)
```

---

### 4. **modules/services/** - External Services

#### `telegram_notifier.py` (375 lines)
**Per-user Telegram bot integration**

**Fungsi utama:**
```python
load_config(user_id)  # Load user's Telegram config from DB
save_config(config, user_id)  # Save to DB
send_message(message, user_id)  # Send message to user's bot
notify_schedule_created(title, scheduled_time, broadcast_link, user_id)
notify_stream_starting(title, scheduled_time, broadcast_link, user_id)
notify_stream_ended(title, duration, user_id)
notify_upload_success(title, youtube_video_id, scheduled_time, user_id)
notify_upload_failed(title, error_message, user_id)
test_connection(user_id)  # Test bot connection
```

**Message format (Indonesian slang):**
```python
message = f"""
🎬 <b>Jadwal Live Udah Jadi Bos!</b> 🔥

📺 <b>Judul:</b> {title}
🕐 <b>Jam Tayang:</b> {scheduled_time}
🔗 <b>Link:</b> <a href="{broadcast_link}">Buka Studio</a>

✅ Siap-siap go live nih! Mantap! 🚀
"""
send_message(message, parse_mode='HTML', user_id=user_id)
```

**Config storage:**
```sql
-- Stored in users table
telegram_bot_token TEXT,
telegram_chat_id TEXT,
telegram_enabled INTEGER DEFAULT 0
```

---

### 5. **modules/utils/** - Utility Functions

#### `license_validator.py` (240 lines)
**Hardware-locked license system**

**Fungsi:**
```python
class LicenseValidator:
    def activate_license(license_key)  # Activate with key
    def verify_license()  # Check validity (online/offline)
    def get_license_info()  # Get current license data
```

**Flow:**
```python
# 1. Get hardware ID
hwid = get_hwid()  # SHA256 hash of MAC + hostname

# 2. Activate license
validator = LicenseValidator()
success, message = validator.activate_license(license_key)

# 3. Verify (with cache fallback)
valid, message, days = validator.verify_license()

# Cache structure (license_cache.json):
{
    "license_key": "XXXX-XXXX-XXXX-XXXX",
    "hwid": "abc123...",
    "status": "active",
    "expiry_date": "2025-12-31",
    "last_verified": "2025-11-21 10:00:00"
}
```

---

## 🔄 Flow Diagram

### 1. Live Streaming Flow

```
User uploads video
    │
    ▼
Create live stream
├─ Select video
├─ Set RTMP server (YouTube/Facebook/etc)
├─ Enter stream key
├─ Set duration (optional)
└─ Schedule start time
    │
    ▼
Save to database (status='scheduled')
    │
    ▼
Scheduler checks (every 60 seconds)
    │
    ▼
Start time reached?
    │ Yes
    ▼
Start FFmpeg process
├─ ffmpeg -re -i video.mp4
├─ -stream_loop -1
├─ -c copy
└─ -f flv rtmp://server/key
    │
    ▼
Update status='live'
Store process PID
    │
    ▼
Set auto-stop timer (if duration set)
    │
    ▼ (after duration)
Stop FFmpeg (kill PID)
    │
    ▼
Update status='completed'
    │
    ▼
Send Telegram notification
```

### 2. Bulk Upload with AI Metadata Flow

```
User selects multiple videos
    │
    ▼
Choose metadata generation method
├─ AI (Gemini)
└─ Random (from Excel)
    │
    ▼
Generate metadata for each video
├─ Title
├─ Description
└─ Tags
    │
    ▼
User reviews & edits metadata
    │
    ▼
Set upload schedule
├─ Start date/time
├─ Token file
├─ Stream ID (optional)
└─ Thumbnail (optional)
    │
    ▼
Add to bulk_upload_queue
(status='queued')
    │
    ▼
Auto-upload scheduler checks
(every N minutes)
    │
    ▼
Upload time reached?
    │ Yes
    ▼
Upload to YouTube
├─ Create video with metadata
├─ Set scheduled publish time
├─ Upload thumbnail
└─ Bind to stream (if specified)
    │
    ▼
Update status='completed'
Store youtube_video_id
    │
    ▼
Send Telegram notification
```

### 3. Video Looping Flow

```
User selects video(s)
    │
    ▼
Set loop duration (minutes)
    │
    ▼
Add to looped_videos table
(status='pending')
    │
    ▼
Background thread starts
    │
    ▼
Calculate loop count
loop_count = (duration * 60) / video_duration
    │
    ▼
Run FFmpeg loop command
ffmpeg -stream_loop N -i input.mp4
  -c copy output.mp4
    │
    ▼
Update progress (0-100%)
    │
    ▼
Save to videos/done/
    │
    ▼
Update status='completed'
Store output_filename
    │
    ▼
Video ready for bulk upload
```

---

## 🛣️ API Routes

### Authentication Routes

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/login` | GET, POST | Public | Login page |
| `/register` | GET, POST | Public | Registration page |
| `/logout` | GET | Required | Logout user |

### Dashboard & Profile

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/` | GET | Required | Dashboard/Landing |
| `/profile` | GET | Required | User profile page |
| `/api/system-stats` | GET | Required | Real-time system stats |
| `/api/dashboard-stats` | GET | Required | Dashboard statistics |

### Video Management

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/video-gallery` | GET | Required | Video gallery page |
| `/upload-video` | POST | Required | Upload video files |
| `/delete-video/<video_id>` | GET | Required | Delete video |
| `/videos/<filename>` | GET | Required | Serve video file |
| `/import-from-drive` | POST | Required | Import from Google Drive |

### Thumbnail Management

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/thumbnail-gallery` | GET | Required | Thumbnail gallery |
| `/upload-thumbnail` | POST | Required | Upload thumbnail |
| `/delete-thumbnail/<id>` | GET | Required | Delete thumbnail |
| `/thumbnails/<filename>` | GET | Required | Serve thumbnail file |

### Live Streaming

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/live-streams` | GET | Required | Live streams page |
| `/add-live-stream` | POST | Required | Create new stream |
| `/edit-live-stream/<id>` | GET, POST | Required | Edit stream |
| `/delete-live-stream/<id>` | POST | Required | Delete stream |
| `/start-stream/<id>` | POST | Required | Start streaming |
| `/stop-stream/<id>` | POST | Required | Stop streaming |
| `/api/active-timers` | GET | Required | Get active auto-stop timers |

### Schedule Management

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/schedules` | GET | Required | Schedules page |
| `/add_schedule` | POST | Required | Add new schedule |
| `/edit_schedule/<id>` | GET | Required | Edit schedule form |
| `/update_schedule/<id>` | POST | Required | Update schedule |
| `/delete_schedule/<id>` | POST | Required | Delete schedule |
| `/run_schedule_now/<id>` | POST | Required | Run schedule manually |
| `/update_schedule_times` | POST | Required | Update auto-scheduler times |

### YouTube API & Tokens

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/tokens` | GET | Required | OAuth tokens page |
| `/create_token` | POST | Required | Start OAuth flow |
| `/complete_token` | POST | Required | Complete OAuth |
| `/delete_token` | POST | Required | Delete token |
| `/stream_keys` | GET | Required | Stream keys page |
| `/fetch_stream_keys` | POST | Required | Fetch from YouTube |
| `/create_new_stream` | POST | Required | Create new stream key |
| `/manage_streams` | GET | Required | Manage stream mappings |
| `/delete_stream_mapping` | POST | Required | Delete mapping |
| `/settings/youtube-api` | GET | Required | Client secret settings |
| `/settings/youtube-api/upload` | POST | Required | Upload client_secret |

### Video Looping

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/video-looping` | GET | Required | Video looping page |
| `/start-video-looping` | POST | Required | Start looping videos |
| `/api/looping-status` | GET | Required | Get looping status |
| `/serve-looped-video/<filename>` | GET | Required | Serve looped video |
| `/delete-looped-video/<id>` | POST | Required | Delete looped video |
| `/bulk-delete-looped-videos` | POST | Required | Bulk delete |

### Bulk Upload & AI

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/bulk-scheduling` | GET | Required | Bulk scheduling page |
| `/generate-ai-metadata` | POST | Required | Generate with Gemini AI |
| `/generate-random-metadata` | POST | Required | Random from Excel |
| `/save-bulk-upload-queue` | POST | Required | Save to queue |
| `/bulk-upload-queue` | GET | Required | Upload queue page |
| `/start-bulk-upload` | POST | Required | Start uploading |
| `/api/upload-queue-status` | GET | Required | Get queue status |
| `/edit-queue-item/<id>` | POST | Required | Edit queue item |
| `/delete-queue-item/<id>` | POST | Required | Delete queue item |
| `/gemini-settings` | GET, POST | Required | Gemini API settings |
| `/upload-metadata-excel` | POST | Required | Upload metadata Excel |

### Settings

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/telegram_settings` | GET, POST | Required | Telegram bot config |
| `/telegram_test` | POST | Required | Test Telegram connection |
| `/license` | GET, POST | Admin | License management |
| `/license/activate` | POST | Admin | Activate license |
| `/license/verify` | POST | Admin | Verify license online |

### Admin Routes

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/admin/users` | GET, POST | Admin | User management |
| `/admin/users/update_limits` | POST | Admin | Update user limits |
| `/admin/users/reset_usage` | POST | Admin | Reset user data |

---

## 🔧 Panduan Update Fitur

### Menambah Fitur Baru

#### 1. **Menambah Tabel Database Baru**

```python
# Di modules/database/database.py - function init_database()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS new_feature (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_new_feature_user_id ON new_feature(user_id)')
```

#### 2. **Menambah CRUD Functions**

```python
# Di modules/database/database.py

def get_new_features(user_id: int) -> List[Dict]:
    """Get all features for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM new_feature WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def add_new_feature(user_id: int, feature_data: Dict) -> str:
    """Add new feature"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO new_feature (id, user_id, name, data)
            VALUES (?, ?, ?, ?)
        ''', (
            feature_data['id'],
            user_id,
            feature_data['name'],
            feature_data.get('data', '')
        ))
        return feature_data['id']

def delete_new_feature(feature_id: str, user_id: int) -> bool:
    """Delete feature (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM new_feature WHERE id = ? AND user_id = ?', (feature_id, user_id))
        return cursor.rowcount > 0
```

#### 3. **Menambah Route di app.py**

```python
@app.route('/new-feature')
@login_required
def new_feature_page():
    """New feature page"""
    from modules.database import get_new_features
    
    user_id = int(current_user.id)
    features = get_new_features(user_id)
    
    return render_template('new_feature.html', features=features)

@app.route('/add-new-feature', methods=['POST'])
@login_required
@demo_readonly
def add_new_feature_route():
    """Add new feature"""
    from modules.database import add_new_feature
    
    user_id = int(current_user.id)
    
    # Check user limits if needed
    from modules.auth import can_user_add_stream
    can_add, message = can_user_add_stream(user_id)
    if not can_add:
        flash(f'Cannot add: {message}', 'error')
        return redirect(url_for('new_feature_page'))
    
    # Get form data
    name = request.form.get('name')
    data = request.form.get('data')
    
    # Validate
    if not name:
        flash('Name is required', 'error')
        return redirect(url_for('new_feature_page'))
    
    # Add to database
    feature_data = {
        'id': str(uuid.uuid4()),
        'name': name,
        'data': data
    }
    
    add_new_feature(user_id, feature_data)
    flash('Feature added successfully!', 'success')
    
    return redirect(url_for('new_feature_page'))
```

#### 4. **Membuat Template HTML**

```html
<!-- templates/new_feature.html -->
{% extends "base.html" %}

{% block title %}New Feature{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-6">New Feature</h1>
    
    <!-- Add Form -->
    <form method="POST" action="{{ url_for('add_new_feature_route') }}" class="mb-8">
        <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Name</label>
            <input type="text" name="name" required 
                   class="w-full px-4 py-2 border rounded-lg">
        </div>
        
        <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Data</label>
            <textarea name="data" rows="4" 
                      class="w-full px-4 py-2 border rounded-lg"></textarea>
        </div>
        
        <button type="submit" class="bg-blue-500 text-white px-6 py-2 rounded-lg">
            Add Feature
        </button>
    </form>
    
    <!-- List Features -->
    <div class="grid gap-4">
        {% for feature in features %}
        <div class="border rounded-lg p-4">
            <h3 class="font-bold">{{ feature.name }}</h3>
            <p class="text-gray-600">{{ feature.data }}</p>
            <small class="text-gray-400">{{ feature.created_at }}</small>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

---

### Menambah Per-User Configuration

#### 1. **Tambah Kolom di Tabel users**

```python
# Di modules/database/database.py - function migrate_database()

users_columns_to_add = {
    'new_config_field': 'TEXT',
    'new_config_enabled': 'INTEGER DEFAULT 0'
}

for column_name, column_def in users_columns_to_add.items():
    if column_name not in existing_columns:
        try:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
            print(f"✅ Added column '{column_name}' to users table")
        except Exception as e:
            print(f"⚠️  Could not add column '{column_name}': {e}")
```

#### 2. **Buat Helper Functions**

```python
# Di modules/services/ atau app.py

def load_new_config(user_id=None):
    """Load new config for user"""
    if user_id:
        try:
            from modules.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT new_config_field, new_config_enabled 
                    FROM users WHERE id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'field': row['new_config_field'] or '',
                        'enabled': bool(row['new_config_enabled'])
                    }
        except Exception as e:
            logging.error(f"Error loading config for user {user_id}: {e}")
    
    return {'field': '', 'enabled': False}

def save_new_config(config, user_id=None):
    """Save new config for user"""
    if user_id:
        try:
            from modules.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET new_config_field = ?,
                        new_config_enabled = ?
                    WHERE id = ?
                ''', (
                    config.get('field', ''),
                    1 if config.get('enabled') else 0,
                    user_id
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving config for user {user_id}: {e}")
            return False
    
    return False
```

---

### Menambah Background Task

#### 1. **Buat Function Background Task**

```python
# Di app.py

def background_task_worker():
    """Background task that runs periodically"""
    while True:
        try:
            logging.info("[TASK] Running background task...")
            
            # Get all users
            from modules.database import get_all_users
            users = get_all_users()
            
            for user in users:
                user_id = user['id']
                
                # Check if user has feature enabled
                config = load_new_config(user_id)
                if not config['enabled']:
                    continue
                
                # Do something for this user
                logging.info(f"[TASK] Processing for user {user_id}")
                # ... your logic here ...
            
            logging.info("[TASK] Background task completed")
            
        except Exception as e:
            logging.error(f"[TASK] Error: {e}")
        
        # Sleep for N minutes
        time.sleep(30 * 60)  # 30 minutes
```

#### 2. **Start Thread di Main**

```python
# Di app.py - if __name__ == '__main__':

# Start background task thread
task_thread = threading.Thread(target=background_task_worker, daemon=True)
task_thread.start()
logging.info("[TASK] Background task thread started")
```

---

### Menambah External API Integration

#### 1. **Buat Module Baru**

```python
# modules/services/new_api.py

import requests
import logging

class NewAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.example.com"
    
    def call_api(self, endpoint, data=None):
        """Call API endpoint"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            if data:
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"API Error: {response.status_code}"
        
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except Exception as e:
            return False, str(e)
    
    def process_data(self, data):
        """Process data with API"""
        success, result = self.call_api('process', data)
        return success, result
```

#### 2. **Gunakan di Route**

```python
@app.route('/process-with-api', methods=['POST'])
@login_required
def process_with_api():
    """Process data with external API"""
    from modules.services.new_api import NewAPIClient
    
    user_id = int(current_user.id)
    
    # Get user's API key from config
    config = load_new_config(user_id)
    api_key = config.get('api_key')
    
    if not api_key:
        return jsonify({'success': False, 'error': 'API key not configured'}), 400
    
    # Get data from request
    data = request.get_json()
    
    # Call API
    client = NewAPIClient(api_key)
    success, result = client.process_data(data)
    
    if success:
        return jsonify({'success': True, 'result': result})
    else:
        return jsonify({'success': False, 'error': result}), 500
```

---

### Best Practices

#### 1. **Selalu Gunakan User Isolation**
```python
# ✅ BENAR - dengan user_id
def get_data(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM table WHERE user_id = ?', (user_id,))
        return cursor.fetchall()

# ❌ SALAH - tanpa user_id
def get_data():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM table')  # Ambil semua user!
        return cursor.fetchall()
```

#### 2. **Check Limits Sebelum Action**
```python
# Check stream limit
can_add, message = can_user_add_stream(user_id)
if not can_add:
    flash(f'Cannot add: {message}', 'error')
    return redirect(...)

# Check storage limit
can_upload, message = can_user_upload(user_id, file_size_mb)
if not can_upload:
    flash(f'Upload failed: {message}', 'error')
    return redirect(...)
```

#### 3. **Gunakan Decorators**
```python
@app.route('/admin-only')
@login_required
@require_admin
def admin_only_page():
    # Only admin can access
    pass

@app.route('/add-something', methods=['POST'])
@login_required
@demo_readonly
def add_something():
    # Demo users cannot modify
    pass
```

#### 4. **Error Handling**
```python
try:
    # Your code here
    result = do_something()
    flash('Success!', 'success')
except Exception as e:
    logging.error(f"Error: {e}")
    flash(f'Error: {str(e)}', 'error')
    return redirect(...)
```

#### 5. **Logging**
```python
import logging

logging.info(f"[FEATURE] User {user_id} started process")
logging.warning(f"[FEATURE] Warning: {message}")
logging.error(f"[FEATURE] Error: {error}")
```

---

## 📝 Update Log

Untuk melacak perubahan fitur, update file `progress.md`:

```markdown
## 2025-11-21
- ✅ Created comprehensive guide.md
- ✅ Documented all modules and flows
- ✅ Added update guidelines

## 2025-11-20
- ✅ Added new feature X
- ✅ Fixed bug in Y
- 🔄 In progress: Feature Z
```

---

## 🎓 Kesimpulan

**JadwalStream** adalah aplikasi multi-user yang kompleks dengan:
- **Isolasi data per user** di semua tabel
- **Role-based access control** (admin vs user)
- **Per-user limits** (streams, storage, expiry)
- **Multi-platform streaming** (RTMP)
- **AI integration** (Gemini)
- **Background tasks** (scheduler, auto-upload)
- **External services** (Telegram, YouTube API)

### Key Points untuk Update Fitur:
1. **Selalu gunakan `user_id`** untuk isolasi data
2. **Check limits** sebelum action (streams, storage)
3. **Gunakan decorators** untuk auth & permissions
4. **Error handling** yang baik dengan logging
5. **Background threads** untuk long-running tasks
6. **Database migrations** untuk schema changes

### Struktur Kode:
- `app.py`: Main Flask app dengan routes
- `modules/database/`: Database operations
- `modules/auth/`: Authentication & limits
- `modules/youtube/`: YouTube API integration
- `modules/services/`: External services (Telegram, etc)
- `modules/utils/`: Utilities (license, hwid)

---

**Happy Coding! 🚀**
