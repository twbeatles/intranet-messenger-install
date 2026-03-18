# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from datetime import datetime

from flask import request, session


def install_session_guard(app, *, logger, session_guard_stats: dict) -> None:
    @app.before_request
    def validate_session_token_guard():
        user_id = session.get("user_id")
        if not user_id:
            return None
        path = request.path or ""
        if path.startswith("/static/"):
            return None

        def is_sensitive_guard_request() -> bool:
            method = str(request.method or "GET").upper()
            if path.startswith("/uploads/"):
                return True
            if path.startswith("/api/upload"):
                return True
            if path in ("/api/profile", "/api/profile/image", "/api/me/password"):
                return True
            if method in ("POST", "PUT", "PATCH", "DELETE") and path.startswith("/api/"):
                return True
            return False

        try:
            from app.models import get_user_session_token

            current_token = get_user_session_token(int(user_id))
            if not current_token:
                return None
            if session.get("session_token") == current_token:
                return None
        except Exception as exc:
            if is_sensitive_guard_request():
                session_guard_stats["fail_closed_count"] = int(session_guard_stats.get("fail_closed_count") or 0) + 1
                session_guard_stats["last_fail_closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.error(f"Session token guard fail-closed(sensitive): {exc}")
                session.clear()
                return (
                    json.dumps(
                        {"error": "세션 검증 시스템 오류입니다. 잠시 후 다시 시도해주세요."},
                        ensure_ascii=False,
                    ),
                    503,
                    {"Content-Type": "application/json; charset=utf-8"},
                )
            if bool(app.config.get("SESSION_TOKEN_FAIL_OPEN", True)):
                session_guard_stats["fail_open_count"] = int(session_guard_stats.get("fail_open_count") or 0) + 1
                session_guard_stats["last_fail_open_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.warning(f"Session token guard fail-open: {exc}")
                return None
            session_guard_stats["fail_closed_count"] = int(session_guard_stats.get("fail_closed_count") or 0) + 1
            session_guard_stats["last_fail_closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"Session token guard fail-closed: {exc}")
            session.clear()
            return (
                json.dumps(
                    {"error": "세션 검증 시스템 오류입니다. 잠시 후 다시 시도해주세요."},
                    ensure_ascii=False,
                ),
                503,
                {"Content-Type": "application/json; charset=utf-8"},
            )

        session.clear()
        return (
            json.dumps({"error": "세션이 만료되었습니다. 다시 로그인해주세요."}, ensure_ascii=False),
            401,
            {"Content-Type": "application/json; charset=utf-8"},
        )

