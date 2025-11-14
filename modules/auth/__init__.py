"""
Authentication & User Management Module
"""

from .user_auth import (
    User,
    get_user_by_id,
    get_user_by_username,
    authenticate_user,
    initialize_default_user,
    create_user,
    list_users,
    change_role,
    delete_user,
    change_user_password
)

from .user_limits import (
    get_user_limits,
    calculate_user_storage,
    can_user_add_stream,
    can_user_upload,
    update_user_limits,
    get_all_users_with_limits
)

__all__ = [
    'User',
    'get_user_by_id',
    'get_user_by_username',
    'authenticate_user',
    'initialize_default_user',
    'create_user',
    'list_users',
    'change_role',
    'delete_user',
    'change_user_password',
    'get_user_limits',
    'calculate_user_storage',
    'can_user_add_stream',
    'can_user_upload',
    'update_user_limits',
    'get_all_users_with_limits'
]
