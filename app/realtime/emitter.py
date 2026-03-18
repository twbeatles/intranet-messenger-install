# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, cast

from flask import request
from flask_socketio import emit

from app.api_response import build_socket_error_payload
from app.i18n import resolve_socket_locale


def request_sid() -> str | None:
    sid = getattr(cast(Any, request), "sid", None)
    return sid if isinstance(sid, str) and sid else None


def socket_emit(
    event: str,
    payload: dict[str, Any],
    *,
    room: str | None = None,
    include_self: bool | None = None,
) -> None:
    kwargs: dict[str, Any] = {}
    if room is not None:
        kwargs["room"] = room
    if include_self is not None:
        kwargs["include_self"] = include_self
    cast(Any, emit)(event, payload, **kwargs)


def emit_error_i18n(message_ko: str, *, code: str | None = None, key: str | None = None) -> None:
    locale_code = resolve_socket_locale(request)
    payload = build_socket_error_payload(
        message_ko,
        locale_code=locale_code,
        explicit_code=code,
        explicit_key=key,
    )
    emit("error", payload)
