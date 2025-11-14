"""
External Services Integration Module
"""

from .telegram_notifier import (
    get_db_connection,
    load_config,
    save_config,
    is_enabled,
    send_message,
    notify_schedule_created,
    notify_stream_starting,
    notify_stream_ended,
    test_connection
)

from .client_secret_manager import (
    get_user_client_secret_path,
    set_user_client_secret,
    has_client_secret,
    get_client_secret_info,
    delete_user_client_secret,
    list_user_tokens
)

__all__ = [
    'get_db_connection',
    'load_config',
    'save_config',
    'is_enabled',
    'send_message',
    'notify_schedule_created',
    'notify_stream_starting',
    'notify_stream_ended',

    'test_connection',
    'get_user_client_secret_path',
    'set_user_client_secret',
    'has_client_secret',
    'get_client_secret_info',
    'delete_user_client_secret',
    'list_user_tokens'
]
