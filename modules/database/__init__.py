"""
Database Management Module
"""

from .database import (
    init_database, get_db_connection, get_database_stats,
    
    # User functions
    create_user, get_user_by_username, get_user_by_id, update_user_password, get_all_users,
    
    # Video functions
    add_video, get_videos, get_video_by_id, delete_video,
    get_looped_videos, add_looped_video, update_looped_video, delete_looped_video,
    
    # Thumbnail functions
    add_thumbnail, get_thumbnails, get_thumbnail_by_id, delete_thumbnail,
    update_thumbnail_tags, get_thumbnails_by_tag, get_all_thumbnail_tags, get_random_thumbnail_by_tag,
    
    # Live stream functions
    add_live_stream, get_live_streams, get_live_stream_by_id, update_live_stream, delete_live_stream,
    
    # Schedule functions
    add_schedule, get_schedules, get_all_schedules, get_schedules_by_user,
    get_schedule_by_id, update_schedule, delete_schedule,
    
    # Stream timer functions
    get_stream_timer, save_stream_timer, delete_stream_timer,
    
    # Stream mapping functions
    get_stream_mappings, save_stream_mapping, delete_stream_mapping, delete_token_mappings,
    
    # Bulk upload queue functions
    add_bulk_upload_item, get_bulk_upload_queue, update_bulk_upload_item, delete_bulk_upload_item,
    
    # Facebook pages functions
    get_facebook_pages, get_facebook_page, add_facebook_page, delete_facebook_page, update_facebook_page_token,
    
    # Playlist cache functions
    save_playlist_cache, get_playlist_cache, get_all_playlist_cache, delete_playlist_cache_item, clear_playlist_cache,
    
    # Custom prompts functions
    get_custom_prompts, add_custom_prompt, update_custom_prompt, delete_custom_prompt, get_default_custom_prompt
)

from .database_helpers import (
    get_current_user_id,
    get_video_database,
    get_thumbnail_database,
    get_live_streams_data,
    get_looped_videos_data,
    get_bulk_upload_queue_data,
    get_stream_mapping,
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
    delete_token_mappings_data
)

__all__ = [
    'get_db_connection',
    'init_database',
    'get_user_by_username',
    'get_user_by_id',
    'create_user',
    'get_schedules',
    'get_all_schedules',
    'get_schedules_by_user',
    'get_schedule_by_id',
    'add_schedule',
    'update_schedule',
    'delete_schedule',
    'get_stream_mappings',
    'save_stream_mapping',
    'delete_stream_mapping',
    'delete_token_mappings',
    'get_bulk_upload_queue',
    'add_bulk_upload_item',
    'delete_bulk_upload_item',
    'update_bulk_upload_item',
    'get_all_users',
    'add_thumbnail',
    'add_video',
    'get_videos',
    'get_looped_videos',
    'add_looped_video',
    'update_looped_video',
    'delete_looped_video',
    'get_live_stream_by_id',
    'delete_live_stream',
    'update_live_stream',
    'update_thumbnail_tags',
    'get_thumbnails_by_tag',
    'get_random_thumbnail_by_tag',
    'get_all_thumbnail_tags',
    'save_playlist_cache',
    'get_playlist_cache',
    'get_all_playlist_cache',
    'delete_playlist_cache_item',
    'clear_playlist_cache',
    'get_current_user_id',
    'get_video_database',
    'get_thumbnail_database',
    'get_live_streams_data',
    'get_looped_videos_data',
    'get_bulk_upload_queue_data',
    'get_stream_mapping',
    'add_video_to_db',
    'delete_video_from_db',
    'add_thumbnail_to_db',
    'delete_thumbnail_from_db',
    'add_live_stream_to_db',
    'delete_live_stream_from_db',
    'update_stream_status',
    'add_schedule_to_db',
    'update_schedule_in_db',
    'delete_schedule_from_db',
    'add_looped_video_to_db',
    'update_looped_video_in_db',
    'add_bulk_upload_to_db',
    'update_bulk_upload_in_db',
    'save_stream_mapping_data',
    'delete_stream_mapping_data',
    'delete_token_mappings_data',
    'get_facebook_pages',
    'get_facebook_page',
    'add_facebook_page',
    'delete_facebook_page',
    'update_facebook_page_token'
]
