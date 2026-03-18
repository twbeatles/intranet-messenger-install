# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import time
import traceback

from flask import current_app, session

from app.models import (
    create_file_message_with_record,
    create_message,
    delete_message,
    edit_message,
    get_message_by_client_msg_id,
    get_message_reactions,
    get_message_room_id,
    get_pinned_messages,
    get_poll,
    is_room_member,
    update_last_read,
)
from app.realtime.emitter import emit_error_i18n, socket_emit
from app.realtime.state import user_has_room_access
from app.upload_tokens import consume_upload_token, get_upload_token_failure_reason

try:
    from config import REQUIRE_MESSAGE_ENCRYPTION
except ImportError:
    REQUIRE_MESSAGE_ENCRYPTION = False

logger = logging.getLogger(__name__)


def register_message_handlers(socketio) -> None:
    @socketio.on("send_message")
    def handle_send_message(data):
        try:
            if not isinstance(data, dict):
                data = {}
            if "user_id" not in session:
                emit_error_i18n("로그인이 필요합니다.")
                return {"ok": False, "error": "로그인이 필요합니다."}

            room_id = data.get("room_id")
            if not isinstance(room_id, int) or room_id <= 0:
                emit_error_i18n("잘못된 대화방 ID입니다.")
                return {"ok": False, "error": "잘못된 대화방 ID입니다."}

            content = data.get("content", "")
            content = content.strip() if isinstance(content, str) else ""
            message_type = data.get("type", "text")
            if message_type == "system":
                emit_error_i18n("잘못된 요청입니다.")
                return {"ok": False, "error": "잘못된 요청입니다."}
            if message_type not in {"text", "file", "image"}:
                message_type = "text"

            file_path = None
            file_name = None
            file_size = None
            reply_to = data.get("reply_to")
            if reply_to is not None and not isinstance(reply_to, int):
                reply_to = None
            if isinstance(reply_to, int) and reply_to <= 0:
                reply_to = None
            encrypted = bool(data.get("encrypted", True))
            client_msg_id = data.get("client_msg_id")
            client_msg_id = client_msg_id if isinstance(client_msg_id, str) else ""
            client_msg_id = client_msg_id.strip()[:64]

            if message_type == "text":
                enforce_encryption = bool(current_app.config.get("REQUIRE_MESSAGE_ENCRYPTION", REQUIRE_MESSAGE_ENCRYPTION))
                if enforce_encryption and not encrypted:
                    emit_error_i18n("암호화되지 않은 텍스트 메시지는 허용되지 않습니다.")
                    return {"ok": False, "error": "암호화되지 않은 텍스트 메시지는 허용되지 않습니다."}
                if encrypted and len(content) > 200000:
                    emit_error_i18n("잘못된 요청입니다.")
                    return {"ok": False, "error": "잘못된 요청입니다."}
                if not encrypted and len(content) > 10000:
                    emit_error_i18n("잘못된 요청입니다.")
                    return {"ok": False, "error": "잘못된 요청입니다."}

            if not user_has_room_access(session["user_id"], room_id):
                emit_error_i18n("대화방 접근 권한이 없습니다.")
                return {"ok": False, "error": "대화방 접근 권한이 없습니다."}

            if reply_to is not None:
                reply_room_id = get_message_room_id(reply_to)
                if reply_room_id is None or int(reply_room_id) != int(room_id):
                    emit_error_i18n("잘못된 요청입니다.")
                    return {"ok": False, "error": "잘못된 요청입니다."}

            if client_msg_id:
                existing_message = get_message_by_client_msg_id(room_id, session["user_id"], client_msg_id)
                if existing_message:
                    return {"ok": True, "message_id": int(existing_message.get("id") or 0)}

            if message_type in ("file", "image"):
                token = data.get("upload_token")
                if not isinstance(token, str) or not token:
                    emit_error_i18n("업로드 토큰이 필요합니다.")
                    return {"ok": False, "error": "업로드 토큰이 필요합니다."}
                reason = get_upload_token_failure_reason(
                    token=token,
                    user_id=session["user_id"],
                    room_id=room_id,
                    expected_type=message_type,
                )
                if reason:
                    emit_error_i18n(str(reason))
                    return {"ok": False, "error": str(reason)}

                token_data = consume_upload_token(
                    token=token,
                    user_id=session["user_id"],
                    room_id=room_id,
                    expected_type=message_type,
                )
                if not token_data:
                    emit_error_i18n("업로드 토큰이 이미 사용되었거나 만료되었습니다.")
                    return {"ok": False, "error": "업로드 토큰이 이미 사용되었거나 만료되었습니다."}

                file_path = token_data.get("file_path")
                file_name = token_data.get("file_name")
                file_size = token_data.get("file_size")
                encrypted = False
                content = file_name or content

            if not content and not file_path:
                return {"ok": False, "error": "잘못된 요청입니다."}

            if message_type in ("file", "image") and file_path:
                normalized_file_size = None
                try:
                    if file_size is not None:
                        normalized_file_size = int(file_size)
                except (TypeError, ValueError):
                    normalized_file_size = None
                message = create_file_message_with_record(
                    room_id=int(room_id),
                    sender_id=int(session["user_id"]),
                    content=content,
                    message_type=message_type,
                    file_path=str(file_path),
                    file_name=str(file_name or ""),
                    file_size=normalized_file_size,
                    reply_to=reply_to,
                    client_msg_id=client_msg_id or None,
                )
            else:
                message = create_message(
                    room_id,
                    session["user_id"],
                    content,
                    message_type,
                    file_path,
                    file_name,
                    reply_to,
                    encrypted,
                    client_msg_id=client_msg_id or None,
                )

            if message:
                created = bool(message.pop("__created", True))
                message_id = int(message.get("id") or 0)
                if not created:
                    return {"ok": True, "message_id": message_id}
                if client_msg_id:
                    message["client_msg_id"] = client_msg_id
                message["unread_count"] = 0
                socket_emit("new_message", message, room=f"room_{room_id}")
                logger.debug(f"Message sent: room={room_id}, user={session['user_id']}, type={message_type}")
                return {"ok": True, "message_id": message_id}

            logger.warning(f"Message creation failed: room={room_id}, user={session['user_id']}")
            emit_error_i18n("메시지 저장에 실패했습니다.")
            return {"ok": False, "error": "메시지 저장에 실패했습니다."}
        except Exception as exc:
            logger.error(f"Send message error: {exc}\n{traceback.format_exc()}")
            emit_error_i18n("메시지 전송에 실패했습니다.")
            return {"ok": False, "error": "메시지 전송에 실패했습니다."}

    @socketio.on("message_read")
    def handle_message_read(data):
        try:
            if "user_id" not in session:
                return

            room_id = data.get("room_id")
            message_id = data.get("message_id")
            try:
                normalized_room_id = int(room_id)
                normalized_message_id = int(message_id)
            except (TypeError, ValueError):
                return
            if normalized_room_id <= 0 or normalized_message_id <= 0:
                return
            if not is_room_member(normalized_room_id, session["user_id"]):
                return

            message_room_id = get_message_room_id(normalized_message_id)
            if message_room_id is None or int(message_room_id) != normalized_room_id:
                emit_error_i18n("잘못된 요청입니다.")
                return

            update_last_read(normalized_room_id, session["user_id"], normalized_message_id)
            socket_emit(
                "read_updated",
                {"room_id": normalized_room_id, "user_id": session["user_id"], "message_id": normalized_message_id},
                room=f"room_{normalized_room_id}",
            )
        except Exception as exc:
            logger.error(f"Message read error: {exc}")

    @socketio.on("edit_message")
    def handle_edit_message(data):
        try:
            if "user_id" not in session:
                return

            message_id = data.get("message_id")
            encrypted = data.get("encrypted", True)
            content = data.get("content", "")
            content = content.strip() if isinstance(content, str) else ""

            if encrypted and len(content) > 200000:
                emit_error_i18n("잘못된 요청입니다.")
                return
            if not encrypted and len(content) > 10000:
                emit_error_i18n("잘못된 요청입니다.")
                return
            if not message_id or not content:
                emit_error_i18n("잘못된 요청입니다.")
                return

            success, error_msg, room_id = edit_message(message_id, session["user_id"], content)
            if success:
                socket_emit(
                    "message_edited",
                    {"room_id": room_id, "message_id": message_id, "content": content, "encrypted": encrypted},
                    room=f"room_{room_id}",
                )
            else:
                emit_error_i18n(str(error_msg))
        except Exception as exc:
            logger.error(f"Edit message error: {exc}")
            emit_error_i18n("메시지 수정에 실패했습니다.")

    @socketio.on("delete_message")
    def handle_delete_message(data):
        try:
            if "user_id" not in session:
                return

            message_id = data.get("message_id")
            if not message_id:
                emit_error_i18n("잘못된 요청입니다.")
                return

            success, result = delete_message(message_id, session["user_id"])
            if success:
                room_id = result
                socket_emit("message_deleted", {"room_id": room_id, "message_id": message_id}, room=f"room_{room_id}")
            else:
                emit_error_i18n(str(result))
        except Exception as exc:
            logger.error(f"Delete message error: {exc}")
            emit_error_i18n("메시지 삭제에 실패했습니다.")

    @socketio.on("reaction_updated")
    def handle_reaction_updated(data):
        try:
            room_id = data.get("room_id")
            message_id = data.get("message_id")
            if "user_id" not in session:
                emit_error_i18n("로그인이 필요합니다.")
                return
            if not room_id or not message_id:
                emit_error_i18n("잘못된 요청입니다.")
                return
            if not is_room_member(room_id, session["user_id"]):
                emit_error_i18n("대화방 멤버만 리액션을 추가할 수 있습니다.")
                return
            message_room_id = get_message_room_id(int(message_id))
            if message_room_id != int(room_id):
                emit_error_i18n("잘못된 요청입니다.")
                return

            reactions = get_message_reactions(int(message_id))
            socket_emit("reaction_updated", {"room_id": room_id, "message_id": message_id, "reactions": reactions}, room=f"room_{room_id}")
        except Exception as exc:
            logger.error(f"Reaction update broadcast error: {exc}")

    @socketio.on("poll_updated")
    def handle_poll_updated(data):
        try:
            room_id = data.get("room_id")
            poll_payload = data.get("poll") if isinstance(data.get("poll"), dict) else {}
            poll_id = data.get("poll_id") or poll_payload.get("id")
            if "user_id" not in session:
                emit_error_i18n("로그인이 필요합니다.")
                return
            if not room_id or not poll_id:
                emit_error_i18n("잘못된 요청입니다.")
                return
            if not is_room_member(room_id, session["user_id"]):
                emit_error_i18n("대화방 멤버만 투표를 업데이트할 수 있습니다.")
                return

            poll = get_poll(int(poll_id))
            if not poll or int(poll.get("room_id") or 0) != int(room_id):
                emit_error_i18n("잘못된 요청입니다.")
                return

            socket_emit("poll_updated", {"room_id": room_id, "poll": poll}, room=f"room_{room_id}")
        except Exception as exc:
            logger.error(f"Poll update broadcast error: {exc}")

    @socketio.on("poll_created")
    def handle_poll_created(data):
        try:
            room_id = data.get("room_id")
            poll_payload = data.get("poll") if isinstance(data.get("poll"), dict) else {}
            poll_id = data.get("poll_id") or poll_payload.get("id")
            if "user_id" not in session:
                emit_error_i18n("로그인이 필요합니다.")
                return
            if not room_id or not poll_id:
                emit_error_i18n("잘못된 요청입니다.")
                return
            if not is_room_member(room_id, session["user_id"]):
                emit_error_i18n("대화방 멤버만 투표를 생성할 수 있습니다.")
                return

            poll = get_poll(int(poll_id))
            if not poll or int(poll.get("room_id") or 0) != int(room_id):
                emit_error_i18n("잘못된 요청입니다.")
                return

            socket_emit("poll_created", {"room_id": room_id, "poll": poll}, room=f"room_{room_id}")
        except Exception as exc:
            logger.error(f"Poll created broadcast error: {exc}")

    @socketio.on("pin_updated")
    def handle_pin_updated(data):
        try:
            room_id = data.get("room_id")
            if room_id and "user_id" in session:
                if not is_room_member(room_id, session["user_id"]):
                    emit_error_i18n("대화방 멤버만 공지를 수정할 수 있습니다.")
                    return

                nickname = session.get("nickname", "사용자")
                content = f"{nickname}님이 공지사항을 업데이트했습니다."
                sys_msg = create_message(room_id, session["user_id"], content, "system")
                if sys_msg:
                    socket_emit("new_message", sys_msg, room=f"room_{room_id}")

                pins = get_pinned_messages(int(room_id))
                socket_emit("pin_updated", {"room_id": room_id, "pins": pins}, room=f"room_{room_id}")
        except Exception as exc:
            logger.error(f"Pin update broadcast error: {exc}")
