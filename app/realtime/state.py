# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import time
from threading import Lock

from app.models import get_user_rooms, is_room_member, server_stats

logger = logging.getLogger(__name__)

online_users: dict[str, int] = {}
user_sids: dict[int, list[str]] = {}
online_users_lock = Lock()
stats_lock = Lock()

user_cache: dict[int, dict] = {}
cache_lock = Lock()
MAX_CACHE_SIZE = 1000
CACHE_TTL = 300

typing_last_emit: dict[tuple[int, int], float] = {}
typing_rate_lock = Lock()
TYPING_RATE_LIMIT = 1.0

_socketio_instance = None


def _socket_compat_attr(name: str, fallback):
    try:
        import app.sockets as sockets

        return getattr(sockets, name, fallback)
    except Exception:
        return fallback


def set_socketio_instance(socketio) -> None:
    global _socketio_instance
    _socketio_instance = socketio


def get_socketio_instance():
    return _socketio_instance


def cleanup_old_cache():
    current_time = time.time()
    expired_keys: list[int] = []

    with cache_lock:
        for user_id, data in user_cache.items():
            if current_time - data.get("updated", 0) > 600:
                expired_keys.append(user_id)
        for key in expired_keys:
            del user_cache[key]
        if len(user_cache) > MAX_CACHE_SIZE:
            sorted_items = sorted(user_cache.items(), key=lambda item: item[1].get("updated", 0))
            to_remove = len(user_cache) - MAX_CACHE_SIZE
            for index in range(to_remove):
                del user_cache[sorted_items[index][0]]

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


def get_user_room_ids(user_id):
    with cache_lock:
        cached = user_cache.get(user_id)
        if cached and (time.time() - cached.get("updated", 0)) < CACHE_TTL:
            if "room_set" not in cached:
                cached["room_set"] = set(cached.get("rooms") or [])
            return cached.get("rooms", [])

    try:
        rooms = get_user_rooms(user_id)
        room_ids = [room["id"] for room in rooms]
        with cache_lock:
            if len(user_cache) > MAX_CACHE_SIZE // 2:
                cleanup_old_cache()
            if user_id not in user_cache:
                user_cache[user_id] = {}
            user_cache[user_id]["rooms"] = room_ids
            user_cache[user_id]["room_set"] = set(room_ids)
            user_cache[user_id]["updated"] = time.time()
        return room_ids
    except Exception as exc:
        logger.error(f"Get user rooms error: {exc}")
        return []


def invalidate_user_cache(user_id):
    with cache_lock:
        if user_id in user_cache:
            del user_cache[user_id]


def get_user_room_id_set(user_id: int) -> set[int]:
    with cache_lock:
        cached = user_cache.get(user_id)
        if cached and (time.time() - cached.get("updated", 0)) < CACHE_TTL:
            room_set = cached.get("room_set")
            if isinstance(room_set, set):
                return set(room_set)
            rebuilt = set(cached.get("rooms") or [])
            cached["room_set"] = rebuilt
            return set(rebuilt)
    return set(get_user_room_ids(user_id))


def user_has_room_access(user_id: int, room_id: int) -> bool:
    try:
        normalized_user_id = int(user_id)
        normalized_room_id = int(room_id)
    except (TypeError, ValueError):
        return False
    if normalized_user_id <= 0 or normalized_room_id <= 0:
        return False

    get_room_id_set = _socket_compat_attr("get_user_room_id_set", get_user_room_id_set)
    room_member_check = _socket_compat_attr("is_room_member", is_room_member)
    invalidate_cache = _socket_compat_attr("invalidate_user_cache", invalidate_user_cache)

    allowed_room_ids = get_room_id_set(normalized_user_id)
    if normalized_room_id in allowed_room_ids:
        return True
    if not room_member_check(normalized_room_id, normalized_user_id):
        return False

    invalidate_cache(normalized_user_id)
    refreshed = get_room_id_set(normalized_user_id)
    return normalized_room_id in refreshed


def force_remove_user_from_room(user_id: int, room_id: int) -> int:
    try:
        normalized_user_id = int(user_id)
        normalized_room_id = int(room_id)
    except (TypeError, ValueError):
        return 0
    if normalized_user_id <= 0 or normalized_room_id <= 0:
        return 0

    socketio_instance = get_socketio_instance()
    if socketio_instance is None:
        return 0

    with online_users_lock:
        sid_list = list(user_sids.get(normalized_user_id, []))
    if not sid_list:
        invalidate_user_cache(normalized_user_id)
        return 0

    room_name = f"room_{normalized_room_id}"
    removed = 0
    for sid in sid_list:
        try:
            socketio_instance.server.leave_room(  # type: ignore[attr-defined]
                sid=sid,
                room=room_name,
                namespace="/",
            )
            removed += 1
        except TypeError:
            try:
                socketio_instance.server.leave_room(sid, room_name)  # type: ignore[attr-defined]
                removed += 1
            except Exception:
                pass
        except Exception:
            pass

    invalidate_user_cache(normalized_user_id)
    return removed
