# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, cast

from flask import jsonify, request, session

from app.models import get_user_by_id, get_user_session_token, is_platform_admin_user


def socketio_emit(
    socketio_instance: Any,
    event: str,
    payload: dict[str, Any],
    *,
    room: str | None = None,
    broadcast: bool = False,
    include_self: bool | None = None,
) -> None:
    kwargs: dict[str, Any] = {}
    if room is not None:
        kwargs["room"] = room
    if broadcast:
        kwargs["broadcast"] = True
    if include_self is not None:
        kwargs["include_self"] = include_self
    cast(Any, socketio_instance).emit(event, payload, **kwargs)


def parse_version(version: str) -> tuple[int, int, int]:
    parts = (version or "0.0.0").strip().split(".")
    normalized: list[int] = []
    for index in range(3):
        try:
            normalized.append(int(parts[index]))
        except Exception:
            normalized.append(0)
    return tuple(normalized)  # type: ignore[return-value]


def normalize_date_bounds(
    date_from_raw: str | None,
    date_to_raw: str | None,
) -> tuple[str | None, str | None]:
    from_dt = None
    to_dt = None

    if date_from_raw is not None and str(date_from_raw).strip():
        if not isinstance(date_from_raw, str):
            raise ValueError("date_from는 YYYY-MM-DD 형식 문자열이어야 합니다.")
        normalized = date_from_raw.strip()
        try:
            from_dt = datetime.strptime(normalized, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("date_from 형식이 올바르지 않습니다. YYYY-MM-DD를 사용하세요.") from exc

    if date_to_raw is not None and str(date_to_raw).strip():
        if not isinstance(date_to_raw, str):
            raise ValueError("date_to는 YYYY-MM-DD 형식 문자열이어야 합니다.")
        normalized = date_to_raw.strip()
        try:
            to_dt = datetime.strptime(normalized, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("date_to 형식이 올바르지 않습니다. YYYY-MM-DD를 사용하세요.") from exc

    if from_dt and to_dt and from_dt > to_dt:
        raise ValueError("date_from은 date_to보다 이후일 수 없습니다.")

    normalized_from = from_dt.strftime("%Y-%m-%d 00:00:00") if from_dt else None
    normalized_to = (
        (to_dt + timedelta(hours=23, minutes=59, seconds=59)).strftime("%Y-%m-%d %H:%M:%S")
        if to_dt
        else None
    )
    return normalized_from, normalized_to


def emit_profile_updated_event(user_id: int) -> None:
    try:
        from app import socketio as socketio_instance
    except Exception:
        return
    if socketio_instance is None:
        return

    user = get_user_by_id(int(user_id)) or {}
    payload = {
        "user_id": int(user_id),
        "nickname": str(user.get("nickname") or ""),
        "profile_image": str(user.get("profile_image") or ""),
    }
    try:
        socketio_emit(
            socketio_instance,
            "user_profile_updated",
            payload,
            broadcast=True,
            include_self=False,
        )
    except TypeError:
        socketio_instance.emit("user_profile_updated", payload)
    except Exception:
        return


def emit_socket_event(
    event: str,
    payload: dict[str, Any] | None = None,
    *,
    room_id: int | None = None,
    user_ids: list[int] | None = None,
    broadcast: bool = False,
) -> None:
    try:
        from app import socketio as socketio_instance
    except Exception:
        return

    if socketio_instance is None:
        return

    emitted = False
    body = payload or {}
    if room_id is not None:
        socketio_emit(socketio_instance, event, body, room=f"room_{int(room_id)}")
        emitted = True

    if user_ids:
        seen_user_ids: set[int] = set()
        for user_id in user_ids:
            try:
                normalized = int(user_id)
            except (TypeError, ValueError):
                continue
            if normalized <= 0 or normalized in seen_user_ids:
                continue
            seen_user_ids.add(normalized)
            socketio_emit(socketio_instance, event, body, room=f"user_{normalized}")
            emitted = True

    if not emitted and broadcast:
        socketio_instance.emit(event, body)


def force_unsubscribe_user_from_room(user_id: int, room_id: int) -> int:
    try:
        from app.sockets import force_remove_user_from_room

        return int(force_remove_user_from_room(int(user_id), int(room_id)) or 0)
    except Exception:
        return 0


def begin_user_session(user: dict[str, Any]) -> str:
    from flask_wtf.csrf import generate_csrf

    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["nickname"] = user.get("nickname", user["username"])
    token = get_user_session_token(user["id"])
    if token:
        session["session_token"] = token
    return generate_csrf()


def json_dict() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def extract_device_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    header_token = request.headers.get("X-Device-Token", "").strip()
    if header_token:
        return header_token

    payload = json_dict()
    token = payload.get("device_token", "")
    return token.strip() if isinstance(token, str) else ""


def approval_gate_for_user(user: dict[str, Any]):
    from app.models import get_user_approval_status

    user_id = int(user.get("id") or 0)
    if user_id <= 0:
        return None
    status = get_user_approval_status(user_id)
    if status == "pending":
        return jsonify({"error": "계정 승인 대기 중입니다."}), 403
    if status == "rejected":
        return jsonify({"error": "승인이 거부된 계정입니다."}), 403
    return None


def is_platform_admin() -> bool:
    try:
        return bool(is_platform_admin_user(int(session.get("user_id") or 0)))
    except Exception:
        return False


def parse_optional_positive_int(data: dict[str, Any], name: str) -> int | None:
    value = data.get(name)
    if value is None or value == "":
        return None
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}는 정수여야 합니다.") from exc
    if normalized <= 0:
        raise ValueError(f"{name}는 1 이상의 정수여야 합니다.")
    return normalized
