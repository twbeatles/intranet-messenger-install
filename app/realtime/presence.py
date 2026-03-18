# -*- coding: utf-8 -*-

from __future__ import annotations

import logging

from flask import session
from flask_socketio import join_room

from app.models import get_user_session_token, update_user_status
from app.realtime.emitter import request_sid, socket_emit
from app.realtime.state import (
    cleanup_old_cache,
    get_user_room_ids,
    online_users,
    online_users_lock,
    server_stats,
    stats_lock,
    typing_last_emit,
    typing_rate_lock,
    user_cache,
    user_sids,
)

logger = logging.getLogger(__name__)


def register_presence_handlers(socketio) -> None:
    @socketio.on("connect")
    def handle_connect():
        if "user_id" not in session:
            return False

        user_id = session["user_id"]
        sid = request_sid()
        if sid is None:
            return False
        current_token = get_user_session_token(user_id)
        if current_token and session.get("session_token") != current_token:
            return False

        with online_users_lock:
            online_users[sid] = user_id
            if user_id not in user_sids:
                user_sids[user_id] = []
            user_sids[user_id].append(sid)
            was_offline = len(user_sids[user_id]) == 1

        try:
            join_room(f"user_{int(user_id)}")
        except Exception:
            pass

        room_ids = get_user_room_ids(user_id)
        for room_id in room_ids:
            try:
                join_room(f"room_{room_id}")
            except Exception:
                pass

        if was_offline:
            update_user_status(user_id, "online")
            for room_id in room_ids:
                socket_emit("user_status", {"user_id": user_id, "status": "online"}, room=f"room_{room_id}")

        with stats_lock:
            server_stats["total_connections"] += 1
            server_stats["active_connections"] += 1
            should_cleanup = server_stats["total_connections"] % 100 == 0

        if should_cleanup:
            cleanup_old_cache()

    @socketio.on("disconnect")
    def handle_disconnect():
        user_id = None
        still_online = False
        room_ids: list[int] = []
        sid = request_sid()
        if sid is None:
            return

        with online_users_lock:
            user_id = online_users.pop(sid, None)
            if user_id and user_id in user_sids:
                if sid in user_sids[user_id]:
                    user_sids[user_id].remove(sid)
                still_online = len(user_sids[user_id]) > 0
                if not still_online:
                    del user_sids[user_id]
                    if user_id in user_cache:
                        room_ids = user_cache[user_id].get("rooms", []).copy()

        if user_id and not still_online:
            update_user_status(user_id, "offline")
            if not room_ids:
                room_ids = get_user_room_ids(user_id)
            try:
                for room_id in room_ids:
                    socket_emit("user_status", {"user_id": user_id, "status": "offline"}, room=f"room_{room_id}")
            except Exception as exc:
                logger.error(f"Disconnect broadcast error: {exc}")

            with typing_rate_lock:
                keys_to_remove = [key for key in typing_last_emit if key[0] == user_id]
                for key in keys_to_remove:
                    del typing_last_emit[key]

        with stats_lock:
            server_stats["active_connections"] = max(0, server_stats["active_connections"] - 1)
