# -*- coding: utf-8 -*-
"""
Socket.IO compatibility shim.
"""

from app.models import is_room_member
from app.realtime.registry import register_socket_events
from app.realtime.state import (
    cleanup_old_cache,
    force_remove_user_from_room,
    get_user_room_id_set,
    get_user_room_ids,
    invalidate_user_cache,
    user_has_room_access,
)

__all__ = [
    "cleanup_old_cache",
    "force_remove_user_from_room",
    "get_user_room_id_set",
    "get_user_room_ids",
    "invalidate_user_cache",
    "is_room_member",
    "register_socket_events",
    "user_has_room_access",
]
