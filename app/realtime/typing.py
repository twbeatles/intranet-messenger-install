# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import time

from flask import session

from app.models import get_user_by_id
from app.realtime.emitter import socket_emit
from app.realtime.state import (
    TYPING_RATE_LIMIT,
    typing_last_emit,
    typing_rate_lock,
    user_has_room_access,
)

logger = logging.getLogger(__name__)


def register_typing_handlers(socketio) -> None:
    @socketio.on("typing")
    def handle_typing(data):
        try:
            if "user_id" not in session:
                return

            room_id = data.get("room_id")
            if not room_id:
                return
            try:
                room_id = int(room_id)
            except (TypeError, ValueError):
                return
            if room_id <= 0:
                return

            user_id = session["user_id"]
            if not user_has_room_access(user_id, room_id):
                return

            current_time = time.time()
            rate_key = (user_id, room_id)
            with typing_rate_lock:
                last_emit = typing_last_emit.get(rate_key, 0)
                if current_time - last_emit < TYPING_RATE_LIMIT:
                    return
                typing_last_emit[rate_key] = current_time
                if len(typing_last_emit) > 1000:
                    expired = [key for key, value in typing_last_emit.items() if current_time - value > 300]
                    for key in expired:
                        del typing_last_emit[key]

            is_typing = data.get("is_typing", False)
            nickname = session.get("nickname", "")
            if not nickname:
                user = get_user_by_id(user_id)
                nickname = user.get("nickname", "사용자") if user else "사용자"

            socket_emit(
                "user_typing",
                {"room_id": room_id, "user_id": user_id, "nickname": nickname, "is_typing": is_typing},
                room=f"room_{room_id}",
                include_self=False,
            )
        except Exception as exc:
            logger.error(f"Typing event error: {exc}")
