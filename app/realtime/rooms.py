# -*- coding: utf-8 -*-

from __future__ import annotations

import logging

from flask import session
from flask_socketio import emit, join_room, leave_room

from app.realtime.emitter import emit_error_i18n
from app.realtime.state import get_user_room_id_set, invalidate_user_cache, user_has_room_access

logger = logging.getLogger(__name__)


def register_room_handlers(socketio) -> None:
    @socketio.on("subscribe_rooms")
    def handle_subscribe_rooms(data):
        try:
            if "user_id" not in session:
                return

            room_ids = data.get("room_ids") if isinstance(data, dict) else None
            if not isinstance(room_ids, list):
                return
            room_ids = [room_id for room_id in room_ids if isinstance(room_id, int) and room_id > 0]
            if not room_ids:
                return

            user_id = session["user_id"]
            allowed = get_user_room_id_set(user_id)
            for room_id in room_ids:
                if room_id in allowed or user_has_room_access(user_id, room_id):
                    join_room(f"room_{room_id}")
        except Exception as exc:
            logger.error(f"Subscribe rooms error: {exc}")

    @socketio.on("join_room")
    def handle_join_room(data):
        try:
            room_id = data.get("room_id") if isinstance(data, dict) else None
            if room_id and "user_id" in session:
                try:
                    normalized_room_id = int(room_id)
                except (TypeError, ValueError):
                    normalized_room_id = 0
                if normalized_room_id <= 0:
                    emit_error_i18n("잘못된 대화방 ID입니다.")
                    return
                if user_has_room_access(session["user_id"], normalized_room_id):
                    join_room(f"room_{normalized_room_id}")
                    emit("joined_room", {"room_id": normalized_room_id})
                else:
                    emit_error_i18n("대화방 접근 권한이 없습니다.")
        except Exception as exc:
            logger.error(f"Join room error: {exc}")

    @socketio.on("leave_room")
    def handle_leave_room(data):
        try:
            room_id = data.get("room_id")
            if room_id:
                leave_room(f"room_{room_id}")
                if "user_id" in session:
                    invalidate_user_cache(session["user_id"])
        except Exception as exc:
            logger.error(f"Leave room error: {exc}")
