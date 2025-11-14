"""
YouTube API Integration Module
"""

from .kunci import (
    get_youtube_service,
    get_stream_keys,
    save_stream_mapping,
    load_stream_mapping
)

from .jadwal import (
    get_user_token_path,
    process_schedule,
    run_scheduler,
    schedule_jobs,
    main as jadwal_main
)

from .live import (
    load_stream_mapping as live_load_stream_mapping,
    get_youtube_service as live_get_youtube_service,
    get_stream_id_from_name,
    schedule_live_stream,
    main as live_main
)

# Import REVERSE_STREAM_MAPPING separately to handle potential import issues
try:
    from .live import REVERSE_STREAM_MAPPING
except ImportError:
    REVERSE_STREAM_MAPPING = {}

__all__ = [
    'get_youtube_service',
    'get_stream_keys',
    'save_stream_mapping',
    'load_stream_mapping',
    'get_user_token_path',
    'process_schedule',
    'run_scheduler',
    'schedule_jobs',
    'jadwal_main',
    'live_load_stream_mapping',
    'live_get_youtube_service',
    'get_stream_id_from_name',
    'schedule_live_stream',
    'live_main',
    'REVERSE_STREAM_MAPPING'
]
