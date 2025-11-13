"""
SQLite Database Manager for JadwalStream
Provides database models and helper functions with per-user data isolation
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional, Any

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jadwalstream.db')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database with all required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'demo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT,
                thumbnail TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'local',
                drive_file_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id)')
        
        # Thumbnails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS thumbnails (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_thumbnails_user_id ON thumbnails(user_id)')
        
        # Live Streams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_streams (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                video_file TEXT NOT NULL,
                stream_id TEXT,
                stream_key TEXT,
                stream_url TEXT,
                server_type TEXT DEFAULT 'youtube',
                status TEXT DEFAULT 'scheduled',
                process_pid INTEGER,
                start_date TEXT,
                end_date TEXT,
                duration INTEGER,
                auto_stop_enabled INTEGER DEFAULT 0,
                auto_stop_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_live_streams_user_id ON live_streams(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_live_streams_status ON live_streams(status)')
        
        # Schedules table (migrated from Excel)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedules_time ON schedules(scheduled_start_time)')
        
        # Looped Videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS looped_videos (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                original_video_id TEXT NOT NULL,
                original_filename TEXT,
                original_title TEXT,
                loop_duration_minutes INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                output_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_looped_videos_user_id ON looped_videos(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_looped_videos_status ON looped_videos(status)')
        
        # Bulk Upload Queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bulk_upload_queue (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                video_id TEXT NOT NULL,
                video_path TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                scheduled_publish_time TIMESTAMP,
                token_file TEXT,
                stream_id TEXT,
                thumbnail_id TEXT,
                privacy_status TEXT DEFAULT 'private',
                status TEXT DEFAULT 'queued',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_at TIMESTAMP,
                youtube_video_id TEXT,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bulk_upload_user_id ON bulk_upload_queue(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bulk_upload_status ON bulk_upload_queue(status)')
        
        # Stream Mappings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stream_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_file TEXT NOT NULL,
                stream_id TEXT NOT NULL,
                stream_name TEXT,
                stream_key TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, token_file, stream_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stream_mappings_user_id ON stream_mappings(user_id)')
        
        # Stream Timers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stream_timers (
                stream_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                timer_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stream_timers_user_id ON stream_timers(user_id)')
        
        conn.commit()

# ============= USER FUNCTIONS =============

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_user(username: str, password_hash: str, role: str = 'demo') -> int:
    """Create new user and return user ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            (username, password_hash, role)
        )
        return cursor.lastrowid

def update_user_role(username: str, role: str) -> bool:
    """Update user role"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE username = ?', (role, username))
        return cursor.rowcount > 0

def update_user_password(username: str, password_hash: str) -> bool:
    """Update user password"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, username))
        return cursor.rowcount > 0

def delete_user(username: str) -> bool:
    """Delete user and all associated data (CASCADE)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        return cursor.rowcount > 0

def list_all_users() -> List[Dict]:
    """List all users"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

# ============= VIDEO FUNCTIONS =============

def get_videos(user_id: int) -> List[Dict]:
    """Get all videos for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM videos WHERE user_id = ? ORDER BY date_added DESC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_video_by_id(video_id: str, user_id: int) -> Optional[Dict]:
    """Get video by ID (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM videos WHERE id = ? AND user_id = ?', (video_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_video(user_id: int, video_data: Dict) -> str:
    """Add new video"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO videos (id, user_id, title, filename, original_filename, thumbnail, source, drive_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_data['id'],
            user_id,
            video_data['title'],
            video_data['filename'],
            video_data.get('original_filename', ''),
            video_data.get('thumbnail', ''),
            video_data.get('source', 'local'),
            video_data.get('drive_file_id', '')
        ))
        return video_data['id']

def delete_video(video_id: str, user_id: int) -> bool:
    """Delete video (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM videos WHERE id = ? AND user_id = ?', (video_id, user_id))
        return cursor.rowcount > 0

# ============= THUMBNAIL FUNCTIONS =============

def get_thumbnails(user_id: int) -> List[Dict]:
    """Get all thumbnails for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM thumbnails WHERE user_id = ? ORDER BY date_added DESC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_thumbnail_by_id(thumbnail_id: str, user_id: int) -> Optional[Dict]:
    """Get thumbnail by ID (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM thumbnails WHERE id = ? AND user_id = ?', (thumbnail_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_thumbnail(user_id: int, thumbnail_data: Dict) -> str:
    """Add new thumbnail"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO thumbnails (id, user_id, title, filename, original_filename)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            thumbnail_data['id'],
            user_id,
            thumbnail_data['title'],
            thumbnail_data['filename'],
            thumbnail_data.get('original_filename', '')
        ))
        return thumbnail_data['id']

def delete_thumbnail(thumbnail_id: str, user_id: int) -> bool:
    """Delete thumbnail (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM thumbnails WHERE id = ? AND user_id = ?', (thumbnail_id, user_id))
        return cursor.rowcount > 0

# ============= LIVE STREAM FUNCTIONS =============

def get_live_streams(user_id: int) -> List[Dict]:
    """Get all live streams for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM live_streams WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_live_stream_by_id(stream_id: str, user_id: int) -> Optional[Dict]:
    """Get live stream by ID (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM live_streams WHERE id = ? AND user_id = ?', (stream_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_live_stream(user_id: int, stream_data: Dict) -> str:
    """Add new live stream"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO live_streams (
                id, user_id, title, video_file, stream_id, stream_key, stream_url,
                server_type, status, process_pid, start_date, end_date, duration,
                auto_stop_enabled, auto_stop_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stream_data['id'],
            user_id,
            stream_data['title'],
            stream_data['video_file'],
            stream_data.get('stream_id', ''),
            stream_data.get('stream_key', ''),
            stream_data.get('stream_url', ''),
            stream_data.get('server_type', 'youtube'),
            stream_data.get('status', 'scheduled'),
            stream_data.get('process_pid'),
            stream_data.get('start_date', ''),
            stream_data.get('end_date', ''),
            stream_data.get('duration', 0),
            stream_data.get('auto_stop_enabled', 0),
            stream_data.get('auto_stop_minutes', 0)
        ))
        return stream_data['id']

def update_live_stream(stream_id: str, user_id: int, updates: Dict) -> bool:
    """Update live stream fields"""
    if not updates:
        return False
    
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [stream_id, user_id]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE live_streams SET {set_clause} WHERE id = ? AND user_id = ?',
            values
        )
        return cursor.rowcount > 0

def delete_live_stream(stream_id: str, user_id: int) -> bool:
    """Delete live stream (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM live_streams WHERE id = ? AND user_id = ?', (stream_id, user_id))
        return cursor.rowcount > 0

# ============= SCHEDULE FUNCTIONS =============

def get_schedules(user_id: int) -> List[Dict]:
    """Get all schedules for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedules WHERE user_id = ? ORDER BY scheduled_start_time ASC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_schedules() -> List[Dict]:
    """Get all schedules (for scheduler background task)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedules ORDER BY scheduled_start_time ASC')
        return [dict(row) for row in cursor.fetchall()]

def get_schedule_by_id(schedule_id: int, user_id: int) -> Optional[Dict]:
    """Get schedule by ID (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedules WHERE id = ? AND user_id = ?', (schedule_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_schedule(user_id: int, schedule_data: Dict) -> int:
    """Add new schedule"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedules (
                user_id, title, description, scheduled_start_time, video_file,
                thumbnail, stream_name, stream_id, token_file, repeat_daily, 
                privacy_status, auto_start, auto_stop, made_for_kids, success, broadcast_link
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            schedule_data['title'],
            schedule_data.get('description', ''),
            schedule_data['scheduled_start_time'],
            schedule_data.get('video_file', ''),
            schedule_data.get('thumbnail', ''),
            schedule_data.get('stream_name', ''),
            schedule_data.get('stream_id', ''),
            schedule_data.get('token_file', ''),
            schedule_data.get('repeat_daily', 0),
            schedule_data.get('privacy_status', 'unlisted'),
            schedule_data.get('auto_start', 0),
            schedule_data.get('auto_stop', 0),
            schedule_data.get('made_for_kids', 0),
            schedule_data.get('success', 0),
            schedule_data.get('broadcast_link', '')
        ))
        return cursor.lastrowid

def update_schedule(schedule_id: int, user_id: int, updates: Dict) -> bool:
    """Update schedule fields"""
    if not updates:
        return False
    
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [schedule_id, user_id]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE schedules SET {set_clause} WHERE id = ? AND user_id = ?',
            values
        )
        return cursor.rowcount > 0

def delete_schedule(schedule_id: int, user_id: int) -> bool:
    """Delete schedule (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM schedules WHERE id = ? AND user_id = ?', (schedule_id, user_id))
        return cursor.rowcount > 0

# Alias functions for easier migration from documentation
def get_schedules_by_user(user_id: int) -> List[Dict]:
    """Alias for get_schedules - for documentation compatibility"""
    return get_schedules(user_id)

def get_all_pending_schedules() -> List[Dict]:
    """Get all pending schedules (success=0) across all users"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedules WHERE success = 0 ORDER BY scheduled_start_time ASC')
        return [dict(row) for row in cursor.fetchall()]

def add_schedule_to_db(schedule_data: Dict) -> int:
    """Alias for add_schedule - for documentation compatibility"""
    user_id = schedule_data.pop('user_id')
    return add_schedule(user_id, schedule_data)

def update_schedule_status(schedule_id: int, success: bool = True, broadcast_id: str = None, broadcast_link: str = None) -> bool:
    """Update schedule status after processing"""
    updates = {'success': 1 if success else 0}
    if broadcast_link:
        updates['broadcast_link'] = broadcast_link
    if broadcast_id:
        # Store broadcast_id in description or add new column if needed
        updates['broadcast_link'] = f"https://studio.youtube.com/video/{broadcast_id}/livestreaming"
    
    # Find schedule to get user_id (needed for isolation)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM schedules WHERE id = ?', (schedule_id,))
        row = cursor.fetchone()
        if not row:
            return False
        user_id = row['user_id']
    
    return update_schedule(schedule_id, user_id, updates)

def get_all_users() -> List[Dict]:
    """Alias for list_all_users - for documentation compatibility"""
    return list_all_users()

# ============= LOOPED VIDEO FUNCTIONS =============

def get_looped_videos(user_id: int) -> List[Dict]:
    """Get all looped videos for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM looped_videos WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def add_looped_video(user_id: int, looped_data: Dict) -> str:
    """Add new looped video"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO looped_videos (
                id, user_id, original_video_id, original_filename, original_title,
                loop_duration_minutes, status, progress, output_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            looped_data['id'],
            user_id,
            looped_data['original_video_id'],
            looped_data.get('original_filename', ''),
            looped_data.get('original_title', ''),
            looped_data['loop_duration_minutes'],
            looped_data.get('status', 'pending'),
            looped_data.get('progress', 0),
            looped_data.get('output_filename', '')
        ))
        return looped_data['id']

def update_looped_video(looped_id: str, user_id: int, updates: Dict) -> bool:
    """Update looped video fields"""
    if not updates:
        return False
    
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [looped_id, user_id]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE looped_videos SET {set_clause} WHERE id = ? AND user_id = ?',
            values
        )
        return cursor.rowcount > 0

def delete_looped_video(looped_id: str, user_id: int) -> bool:
    """Delete looped video (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM looped_videos WHERE id = ? AND user_id = ?', (looped_id, user_id))
        return cursor.rowcount > 0

# ============= BULK UPLOAD QUEUE FUNCTIONS =============

def get_bulk_upload_queue(user_id: int) -> List[Dict]:
    """Get all bulk upload queue items for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bulk_upload_queue WHERE user_id = ? ORDER BY scheduled_publish_time ASC', (user_id,))
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            # Parse tags from JSON string
            if data.get('tags'):
                try:
                    data['tags'] = json.loads(data['tags'])
                except:
                    data['tags'] = []
            results.append(data)
        return results

def add_bulk_upload_item(user_id: int, upload_data: Dict) -> str:
    """Add new bulk upload item"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Convert tags list to JSON string
        tags_json = json.dumps(upload_data.get('tags', []))
        
        cursor.execute('''
            INSERT INTO bulk_upload_queue (
                id, user_id, video_id, video_path, title, description, tags,
                scheduled_publish_time, token_file, stream_id, thumbnail_id,
                privacy_status, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            upload_data['id'],
            user_id,
            upload_data['video_id'],
            upload_data['video_path'],
            upload_data['title'],
            upload_data.get('description', ''),
            tags_json,
            upload_data.get('scheduled_publish_time', ''),
            upload_data.get('token_file', ''),
            upload_data.get('stream_id', ''),
            upload_data.get('thumbnail_id', ''),
            upload_data.get('privacy_status', 'private'),
            upload_data.get('status', 'queued')
        ))
        return upload_data['id']

def update_bulk_upload_item(upload_id: str, user_id: int, updates: Dict) -> bool:
    """Update bulk upload item fields"""
    if not updates:
        return False
    
    # Handle tags conversion to JSON if present
    if 'tags' in updates and isinstance(updates['tags'], list):
        updates['tags'] = json.dumps(updates['tags'])
    
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [upload_id, user_id]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE bulk_upload_queue SET {set_clause} WHERE id = ? AND user_id = ?',
            values
        )
        return cursor.rowcount > 0

def delete_bulk_upload_item(upload_id: str, user_id: int) -> bool:
    """Delete bulk upload item (with user isolation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bulk_upload_queue WHERE id = ? AND user_id = ?', (upload_id, user_id))
        return cursor.rowcount > 0

# ============= STREAM MAPPING FUNCTIONS =============

def get_stream_mappings(user_id: int, token_file: Optional[str] = None) -> Dict:
    """Get stream mappings for a user, optionally filtered by token_file"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if token_file:
            cursor.execute(
                'SELECT * FROM stream_mappings WHERE user_id = ? AND token_file = ?',
                (user_id, token_file)
            )
        else:
            cursor.execute('SELECT * FROM stream_mappings WHERE user_id = ?', (user_id,))
        
        # Build nested dict structure: {token_file: {stream_id: {metadata}}}
        mappings = {}
        for row in cursor.fetchall():
            data = dict(row)
            token = data['token_file']
            stream_id = data['stream_id']
            
            if token not in mappings:
                mappings[token] = {}
            
            mappings[token][stream_id] = {
                'stream_name': data.get('stream_name', ''),
                'stream_key': data.get('stream_key', ''),
                'metadata': json.loads(data['metadata']) if data.get('metadata') else {}
            }
        
        return mappings

def save_stream_mapping(user_id: int, token_file: str, stream_id: str, stream_data: Dict) -> bool:
    """Save or update stream mapping"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        metadata_json = json.dumps(stream_data.get('metadata', {}))
        
        cursor.execute('''
            INSERT INTO stream_mappings (user_id, token_file, stream_id, stream_name, stream_key, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, token_file, stream_id) 
            DO UPDATE SET stream_name = ?, stream_key = ?, metadata = ?
        ''', (
            user_id, token_file, stream_id,
            stream_data.get('stream_name', ''),
            stream_data.get('stream_key', ''),
            metadata_json,
            stream_data.get('stream_name', ''),
            stream_data.get('stream_key', ''),
            metadata_json
        ))
        return True

def delete_stream_mapping(user_id: int, token_file: str, stream_id: str) -> bool:
    """Delete specific stream mapping"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM stream_mappings WHERE user_id = ? AND token_file = ? AND stream_id = ?',
            (user_id, token_file, stream_id)
        )
        return cursor.rowcount > 0

def delete_token_mappings(user_id: int, token_file: str) -> bool:
    """Delete all mappings for a token"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM stream_mappings WHERE user_id = ? AND token_file = ?',
            (user_id, token_file)
        )
        return cursor.rowcount > 0

# ============= STREAM TIMER FUNCTIONS =============

def get_stream_timer(stream_id: str, user_id: int) -> Optional[Dict]:
    """Get stream timer data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT timer_data FROM stream_timers WHERE stream_id = ? AND user_id = ?', (stream_id, user_id))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row['timer_data'])
            except:
                return None
        return None

def save_stream_timer(stream_id: str, user_id: int, timer_data: Dict) -> bool:
    """Save or update stream timer"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        timer_json = json.dumps(timer_data)
        cursor.execute('''
            INSERT INTO stream_timers (stream_id, user_id, timer_data)
            VALUES (?, ?, ?)
            ON CONFLICT(stream_id)
            DO UPDATE SET timer_data = ?, user_id = ?
        ''', (stream_id, user_id, timer_json, timer_json, user_id))
        return True

def delete_stream_timer(stream_id: str, user_id: int) -> bool:
    """Delete stream timer"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM stream_timers WHERE stream_id = ? AND user_id = ?', (stream_id, user_id))
        return cursor.rowcount > 0

# ============= DATABASE MAINTENANCE =============

def backup_database(backup_path: str) -> bool:
    """Create a backup of the database"""
    import shutil
    try:
        shutil.copy2(DB_FILE, backup_path)
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def get_database_stats() -> Dict:
    """Get database statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        stats = {}
        
        tables = ['users', 'videos', 'thumbnails', 'live_streams', 'schedules', 
                  'looped_videos', 'bulk_upload_queue', 'stream_mappings', 'stream_timers']
        
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
            stats[table] = cursor.fetchone()['count']
        
        # Database file size
        if os.path.exists(DB_FILE):
            stats['db_size_mb'] = round(os.path.getsize(DB_FILE) / (1024 * 1024), 2)
        
        return stats

if __name__ == '__main__':
    # Initialize database when run directly
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
    print(f"Database file: {DB_FILE}")
