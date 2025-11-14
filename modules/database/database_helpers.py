"""
Database Helper Functions
Wrapper functions untuk backward compatibility dengan app.py yang existing
Provides same interface as JSON-based functions but uses SQLite backend
"""

import json
from typing import List, Dict, Optional
from flask_login import current_user
from modules.database.database import (
    get_videos, get_video_by_id, add_video, delete_video,
    get_thumbnails, get_thumbnail_by_id, add_thumbnail, delete_thumbnail,
    get_live_streams, get_live_stream_by_id, add_live_stream, update_live_stream, delete_live_stream,
    get_schedules, add_schedule, update_schedule, delete_schedule,
    get_looped_videos, add_looped_video, update_looped_video, delete_looped_video,
    get_bulk_upload_queue, add_bulk_upload_item, update_bulk_upload_item, delete_bulk_upload_item,
    get_stream_mappings, save_stream_mapping, delete_stream_mapping, delete_token_mappings,
    get_stream_timer, save_stream_timer, delete_stream_timer
)

def get_current_user_id():
    """Get current authenticated user ID"""
    try:
        # Check if current_user exists and is authenticated
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            try:
                return int(current_user.id)
            except (ValueError, AttributeError, TypeError):
                # Fallback to user ID 1 if something goes wrong
                return 1
    except (RuntimeError, AttributeError):
        # No user context (e.g., during app initialization or background tasks)
        pass
    
    # Default to user ID 1 if no user is authenticated
    # This is safe for background tasks that don't have user context
    return 1

# ============= VIDEO DATABASE FUNCTIONS =============

def get_video_database() -> List[Dict]:
    """Get all videos for current user (compatible with old JSON format)"""
    user_id = get_current_user_id()
    videos = get_videos(user_id)
    # Convert date_added from timestamp to string if needed
    for video in videos:
        if 'date_added' not in video or not video['date_added']:
            video['date_added'] = ''
    return videos

def save_video_database(videos: List[Dict]):
    """
    Save videos (DEPRECATED - use add_video or delete_video instead)
    This function is kept for backward compatibility but does nothing
    as we now use individual insert/update/delete operations
    """
    # This is now handled by individual add_video/delete_video calls in the actual routes
    # Keeping this function to avoid breaking existing code that calls it
    pass

# ============= THUMBNAIL DATABASE FUNCTIONS =============

def get_thumbnail_database() -> List[Dict]:
    """Get all thumbnails for current user"""
    user_id = get_current_user_id()
    return get_thumbnails(user_id)

def save_thumbnail_database(thumbnails: List[Dict]):
    """DEPRECATED - use add_thumbnail or delete_thumbnail instead"""
    pass

# ============= LIVE STREAM FUNCTIONS =============

def get_live_streams_data() -> List[Dict]:
    """Get all live streams for current user"""
    user_id = get_current_user_id()
    streams = get_live_streams(user_id)
    # Convert database format to expected format
    for stream in streams:
        # Convert integer boolean fields to Python bools if needed
        if 'auto_stop_enabled' in stream:
            stream['auto_stop_enabled'] = bool(stream['auto_stop_enabled'])
    return streams

def save_live_streams(streams: List[Dict]):
    """
    Save live streams (DEPRECATED)
    For updates, use update_live_stream() instead
    """
    pass

def update_stream_status(stream_id: str, status: str, **kwargs):
    """Update live stream status and other fields"""
    user_id = get_current_user_id()
    updates = {'status': status}
    updates.update(kwargs)
    return update_live_stream(stream_id, user_id, updates)

# ============= STREAM MAPPING FUNCTIONS =============

def get_stream_mapping() -> Dict:
    """Get stream mappings for current user"""
    user_id = get_current_user_id()
    return get_stream_mappings(user_id)

def save_stream_mapping_data(token_file: str, stream_id: str, stream_data: Dict) -> bool:
    """Save stream mapping for current user"""
    user_id = get_current_user_id()
    return save_stream_mapping(user_id, token_file, stream_id, stream_data)

def delete_stream_mapping_data(token_file: str, stream_id: str) -> bool:
    """Delete stream mapping"""
    user_id = get_current_user_id()
    return delete_stream_mapping(user_id, token_file, stream_id)

def delete_token_mappings_data(token_file: str) -> bool:
    """Delete all mappings for a token"""
    user_id = get_current_user_id()
    return delete_token_mappings(user_id, token_file)

# ============= LOOPED VIDEO FUNCTIONS =============

def get_looped_videos_data() -> List[Dict]:
    """Get all looped videos for current user"""
    user_id = get_current_user_id()
    return get_looped_videos(user_id)

def save_looped_videos(looped_videos: List[Dict]):
    """DEPRECATED - use add_looped_video or update_looped_video instead"""
    pass

# ============= BULK UPLOAD QUEUE FUNCTIONS =============

def get_bulk_upload_queue_data() -> List[Dict]:
    """Get bulk upload queue for current user"""
    user_id = get_current_user_id()
    return get_bulk_upload_queue(user_id)

def save_bulk_upload_queue(queue: List[Dict]):
    """DEPRECATED - use add_bulk_upload_item or update_bulk_upload_item instead"""
    pass

# ============= STREAM TIMER FUNCTIONS =============

def get_stream_timers() -> Dict:
    """
    Get all stream timers for current user
    Returns dict format: {stream_id: timer_data}
    """
    user_id = get_current_user_id()
    # Note: This would require getting all streams first, then their timers
    # For now, return empty dict as timers are accessed individually
    return {}

def get_stream_timer_data(stream_id: str) -> Optional[Dict]:
    """Get stream timer for specific stream"""
    user_id = get_current_user_id()
    return get_stream_timer(stream_id, user_id)

def save_stream_timer_data(stream_id: str, timer_data: Dict) -> bool:
    """Save stream timer"""
    user_id = get_current_user_id()
    return save_stream_timer(stream_id, user_id, timer_data)

def delete_stream_timer_data(stream_id: str) -> bool:
    """Delete stream timer"""
    user_id = get_current_user_id()
    return delete_stream_timer(stream_id, user_id)

# ============= BACKWARD COMPATIBILITY HELPERS =============

def add_video_to_db(video_data: Dict) -> str:
    """Add video for current user"""
    user_id = get_current_user_id()
    return add_video(user_id, video_data)

def delete_video_from_db(video_id: str) -> bool:
    """Delete video for current user"""
    user_id = get_current_user_id()
    return delete_video(video_id, user_id)

def add_thumbnail_to_db(thumbnail_data: Dict) -> str:
    """Add thumbnail for current user"""
    user_id = get_current_user_id()
    return add_thumbnail(user_id, thumbnail_data)

def delete_thumbnail_from_db(thumbnail_id: str) -> bool:
    """Delete thumbnail for current user"""
    user_id = get_current_user_id()
    return delete_thumbnail(thumbnail_id, user_id)

def add_live_stream_to_db(stream_data: Dict) -> str:
    """Add live stream for current user"""
    user_id = get_current_user_id()
    return add_live_stream(user_id, stream_data)

def delete_live_stream_from_db(stream_id: str) -> bool:
    """Delete live stream for current user"""
    user_id = get_current_user_id()
    return delete_live_stream(stream_id, user_id)

def add_schedule_to_db(schedule_data: Dict) -> int:
    """Add schedule for current user"""
    user_id = get_current_user_id()
    return add_schedule(user_id, schedule_data)

def update_schedule_in_db(schedule_id: int, updates: Dict) -> bool:
    """Update schedule for current user"""
    user_id = get_current_user_id()
    return update_schedule(schedule_id, user_id, updates)

def delete_schedule_from_db(schedule_id: int) -> bool:
    """Delete schedule for current user"""
    user_id = get_current_user_id()
    return delete_schedule(schedule_id, user_id)

def add_looped_video_to_db(looped_data: Dict) -> str:
    """Add looped video for current user"""
    user_id = get_current_user_id()
    return add_looped_video(user_id, looped_data)

def update_looped_video_in_db(looped_id: str, updates: Dict) -> bool:
    """Update looped video for current user"""
    user_id = get_current_user_id()
    return update_looped_video(looped_id, user_id, updates)

def delete_looped_video_from_db(looped_id: str) -> bool:
    """Delete looped video for current user"""
    user_id = get_current_user_id()
    return delete_looped_video(looped_id, user_id)

def add_bulk_upload_to_db(upload_data: Dict) -> str:
    """Add bulk upload item for current user"""
    user_id = get_current_user_id()
    return add_bulk_upload_item(user_id, upload_data)

def update_bulk_upload_in_db(upload_id: str, updates: Dict) -> bool:
    """Update bulk upload item for current user"""
    user_id = get_current_user_id()
    return update_bulk_upload_item(upload_id, user_id, updates)

def delete_bulk_upload_from_db(upload_id: str) -> bool:
    """Delete bulk upload item for current user"""
    user_id = get_current_user_id()
    return delete_bulk_upload_item(upload_id, user_id)

# ============= UTILITY FUNCTIONS =============

def get_user_stats(user_id: int = None) -> Dict:
    """Get statistics for a user"""
    if user_id is None:
        user_id = get_current_user_id()
    
    return {
        'videos': len(get_videos(user_id)),
        'thumbnails': len(get_thumbnails(user_id)),
        'live_streams': len(get_live_streams(user_id)),
        'schedules': len(get_schedules(user_id)),
        'looped_videos': len(get_looped_videos(user_id)),
        'upload_queue': len(get_bulk_upload_queue(user_id))
    }
