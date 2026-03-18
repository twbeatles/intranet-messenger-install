# -*- coding: utf-8 -*-

from __future__ import annotations

import logging

from flask import session

from app.models import get_room_admins, is_room_admin
from app.realtime.emitter import emit_error_i18n, socket_emit

logger = logging.getLogger(__name__)


def register_admin_handlers(socketio) -> None:
    @socketio.on("room_name_updated")
    def handle_room_name_updated(data):
        try:
            if "user_id" not in session:
                return
            logger.warning(f"Ignored client-originated room_name_updated: user={session.get('user_id')}")
            emit_error_i18n("잘못된 요청입니다.")
        except Exception as exc:
            logger.error(f"Room name update broadcast error: {exc}")

    @socketio.on("room_members_updated")
    def handle_room_members_updated(data):
        try:
            if "user_id" not in session:
                return
            logger.warning(f"Ignored client-originated room_members_updated: user={session.get('user_id')}")
            emit_error_i18n("잘못된 요청입니다.")
        except Exception as exc:
            logger.error(f"Room members update broadcast error: {exc}")

    @socketio.on("profile_updated")
    def handle_profile_updated(data):
        try:
            if "user_id" in session:
                logger.warning(f"Ignored client-originated profile_updated: user={session.get('user_id')}")
                emit_error_i18n("잘못된 요청입니다.")
        except Exception as exc:
            logger.error(f"Profile update broadcast error: {exc}")

    @socketio.on("admin_updated")
    def handle_admin_updated(data):
        try:
            room_id = data.get("room_id")
            target_user_id = data.get("user_id")
            if room_id and target_user_id is not None and "user_id" in session:
                if not is_room_admin(room_id, session["user_id"]):
                    emit_error_i18n("관리자만 권한을 변경할 수 있습니다.")
                    return
                admins = get_room_admins(int(room_id))
                admin_ids = {
                    int(admin.get("id") or 0)
                    for admin in admins
                    if int(admin.get("id") or 0) > 0
                }
                socket_emit(
                    "admin_updated",
                    {"room_id": room_id, "user_id": target_user_id, "is_admin": int(target_user_id) in admin_ids},
                    room=f"room_{room_id}",
                )
        except Exception as exc:
            logger.error(f"Admin update broadcast error: {exc}")
