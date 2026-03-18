# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from datetime import datetime

from flask import jsonify, request, session

from app.extensions import limiter
from app.http.common import is_platform_admin, json_dict, parse_version
from app.models import get_db, get_maintenance_status, get_user_by_id, log_access
from app.models import review_user_approval

from config import (
    DESKTOP_CLIENT_ARTIFACT_SHA256,
    DESKTOP_CLIENT_ARTIFACT_SIGNATURE,
    DESKTOP_CLIENT_CANARY_ARTIFACT_SHA256,
    DESKTOP_CLIENT_CANARY_ARTIFACT_SIGNATURE,
    DESKTOP_CLIENT_CANARY_DOWNLOAD_URL,
    DESKTOP_CLIENT_CANARY_LATEST_VERSION,
    DESKTOP_CLIENT_CANARY_MIN_VERSION,
    DESKTOP_CLIENT_CANARY_RELEASE_NOTES_URL,
    DESKTOP_CLIENT_CANARY_SIGNATURE_ALG,
    DESKTOP_CLIENT_CHANNEL_DEFAULT,
    DESKTOP_CLIENT_DOWNLOAD_URL,
    DESKTOP_CLIENT_LATEST_VERSION,
    DESKTOP_CLIENT_MIN_VERSION,
    DESKTOP_CLIENT_RELEASE_NOTES_URL,
    DESKTOP_CLIENT_SIGNATURE_ALG,
    DESKTOP_ONLY_MODE,
    REQUIRE_SIGNED_UPDATES_IN_PROD,
)


def _route_compat_value(name: str, default):
    try:
        import app.routes as routes

        return getattr(routes, name, default)
    except Exception:
        return default


def register_system_routes(app) -> None:
    @app.route("/api/admin/users/approve", methods=["POST"])
    def admin_approve_user():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_platform_admin():
            return jsonify({"error": "관리자 권한이 필요합니다."}), 403

        data = json_dict()
        target_user_id = data.get("user_id")
        action = str(data.get("action") or "").strip().lower()
        reason = str(data.get("reason") or "").strip()

        if target_user_id is None:
            return jsonify({"error": "유효한 사용자 ID가 필요합니다."}), 400
        try:
            target_user_id = int(target_user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "유효한 사용자 ID가 필요합니다."}), 400
        if target_user_id <= 0:
            return jsonify({"error": "유효한 사용자 ID가 필요합니다."}), 400
        if action not in ("approve", "reject"):
            return jsonify({"error": "action은 approve/reject만 허용됩니다."}), 400
        if not get_user_by_id(target_user_id):
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

        if not review_user_approval(
            user_id=target_user_id,
            status=action,
            reviewed_by=int(session["user_id"]),
            reason=reason,
        ):
            return jsonify({"error": "승인 상태 변경에 실패했습니다."}), 500

        log_access(int(session["user_id"]), f"approve_user_{action}", request.remote_addr, request.user_agent.string)
        return jsonify({"success": True, "user_id": target_user_id, "status": "approved" if action == "approve" else "rejected"})

    @app.route("/api/security/audit")
    def security_audit_route():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        from app.auth_tokens import list_active_device_sessions

        user_id = int(session["user_id"])
        limit = request.args.get("limit", type=int) or 50
        limit = min(max(limit, 1), 200)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, action, ip_address, user_agent, created_at
            FROM access_logs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        logs = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT action, COUNT(*) AS count
            FROM access_logs
            WHERE user_id = ?
              AND created_at >= datetime('now', '-30 days')
            GROUP BY action
            ORDER BY count DESC
            """,
            (user_id,),
        )
        action_counts = {row["action"]: int(row["count"]) for row in cursor.fetchall()}

        sessions = list_active_device_sessions(user_id)
        revoked_recent = 0
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM device_sessions
            WHERE user_id = ?
              AND revoked_at IS NOT NULL
              AND revoked_at >= datetime('now', '-30 days')
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            revoked_recent = int(row["count"] or 0)

        return jsonify(
            {
                "user_id": user_id,
                "window_days": 30,
                "actions": action_counts,
                "recent_access_logs": logs,
                "active_device_sessions": sessions,
                "revoked_device_sessions_recent": revoked_recent,
            }
        )

    @app.route("/api/system/health")
    def system_health():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        db_ok = True
        db_error = ""
        try:
            conn = get_db()
            conn.execute("SELECT 1")
        except Exception as exc:
            db_ok = False
            db_error = str(exc)

        try:
            from app import get_session_guard_stats

            guard_stats = get_session_guard_stats()
        except Exception:
            guard_stats = {
                "fail_open_count": 0,
                "last_fail_open_at": None,
                "fail_closed_count": 0,
                "last_fail_closed_at": None,
            }

        tls_effective = (os.environ.get("MESSENGER_TLS_EFFECTIVE") or "").strip() == "1"
        if not tls_effective:
            tls_effective = bool(request.is_secure)
        app_env = str(app.config.get("APP_ENV") or "dev").strip().lower()
        require_signed_updates_in_prod = bool(
            app.config.get("REQUIRE_SIGNED_UPDATES_IN_PROD", REQUIRE_SIGNED_UPDATES_IN_PROD)
        )
        signature_required_now = require_signed_updates_in_prod and app_env in ("prod", "production")
        hardening_warnings = [str(value) for value in (app.config.get("HARDENING_WARNINGS") or []) if str(value).strip()]

        payload = {
            "status": "ok" if db_ok else "degraded",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tls": {
                "configured": bool(app.config.get("SESSION_COOKIE_SECURE", False)),
                "effective": bool(tls_effective),
                "enforce_https": bool(app.config.get("ENFORCE_HTTPS", False)),
            },
            "db": {"ok": bool(db_ok)},
            "session_guard": {
                "fail_open_enabled": bool(app.config.get("SESSION_TOKEN_FAIL_OPEN", True)),
                "fail_open_count": int(guard_stats.get("fail_open_count") or 0),
                "last_fail_open_at": guard_stats.get("last_fail_open_at"),
                "fail_closed_count": int(guard_stats.get("fail_closed_count") or 0),
                "last_fail_closed_at": guard_stats.get("last_fail_closed_at"),
            },
            "maintenance": get_maintenance_status(),
            "rate_limit": {
                "storage_uri": str(app.config.get("RATE_LIMIT_STORAGE_URI", "memory://")),
                "key_mode": str(app.config.get("RATE_LIMIT_KEY_MODE", "ip")),
            },
            "hardening": {
                "environment": app_env,
                "warning_count": len(hardening_warnings),
                "warnings": hardening_warnings,
                "require_signed_updates_in_prod": require_signed_updates_in_prod,
                "signature_required_now": signature_required_now,
            },
        }
        if db_error:
            payload["db"]["error"] = db_error
        return jsonify(payload), (200 if db_ok else 503)

    @app.route("/api/client/update")
    def client_update_check():
        client_version = (request.args.get("client_version") or "").strip()
        channel_default = _route_compat_value("DESKTOP_CLIENT_CHANNEL_DEFAULT", DESKTOP_CLIENT_CHANNEL_DEFAULT)
        channel = (request.args.get("channel") or channel_default or "stable").strip().lower()
        if channel not in ("stable", "canary"):
            channel = "stable"

        if channel == "canary":
            minimum_version = _route_compat_value("DESKTOP_CLIENT_CANARY_MIN_VERSION", DESKTOP_CLIENT_CANARY_MIN_VERSION) or _route_compat_value("DESKTOP_CLIENT_MIN_VERSION", DESKTOP_CLIENT_MIN_VERSION)
            latest_version = _route_compat_value("DESKTOP_CLIENT_CANARY_LATEST_VERSION", DESKTOP_CLIENT_CANARY_LATEST_VERSION) or _route_compat_value("DESKTOP_CLIENT_LATEST_VERSION", DESKTOP_CLIENT_LATEST_VERSION)
            download_url = _route_compat_value("DESKTOP_CLIENT_CANARY_DOWNLOAD_URL", DESKTOP_CLIENT_CANARY_DOWNLOAD_URL) or _route_compat_value("DESKTOP_CLIENT_DOWNLOAD_URL", DESKTOP_CLIENT_DOWNLOAD_URL)
            release_notes_url = _route_compat_value("DESKTOP_CLIENT_CANARY_RELEASE_NOTES_URL", DESKTOP_CLIENT_CANARY_RELEASE_NOTES_URL) or _route_compat_value("DESKTOP_CLIENT_RELEASE_NOTES_URL", DESKTOP_CLIENT_RELEASE_NOTES_URL)
            artifact_sha256 = _route_compat_value("DESKTOP_CLIENT_CANARY_ARTIFACT_SHA256", DESKTOP_CLIENT_CANARY_ARTIFACT_SHA256) or _route_compat_value("DESKTOP_CLIENT_ARTIFACT_SHA256", DESKTOP_CLIENT_ARTIFACT_SHA256)
            artifact_signature = _route_compat_value("DESKTOP_CLIENT_CANARY_ARTIFACT_SIGNATURE", DESKTOP_CLIENT_CANARY_ARTIFACT_SIGNATURE) or _route_compat_value("DESKTOP_CLIENT_ARTIFACT_SIGNATURE", DESKTOP_CLIENT_ARTIFACT_SIGNATURE)
            signature_alg = _route_compat_value("DESKTOP_CLIENT_CANARY_SIGNATURE_ALG", DESKTOP_CLIENT_CANARY_SIGNATURE_ALG) or _route_compat_value("DESKTOP_CLIENT_SIGNATURE_ALG", DESKTOP_CLIENT_SIGNATURE_ALG)
        else:
            minimum_version = _route_compat_value("DESKTOP_CLIENT_MIN_VERSION", DESKTOP_CLIENT_MIN_VERSION)
            latest_version = _route_compat_value("DESKTOP_CLIENT_LATEST_VERSION", DESKTOP_CLIENT_LATEST_VERSION)
            download_url = _route_compat_value("DESKTOP_CLIENT_DOWNLOAD_URL", DESKTOP_CLIENT_DOWNLOAD_URL)
            release_notes_url = _route_compat_value("DESKTOP_CLIENT_RELEASE_NOTES_URL", DESKTOP_CLIENT_RELEASE_NOTES_URL)
            artifact_sha256 = _route_compat_value("DESKTOP_CLIENT_ARTIFACT_SHA256", DESKTOP_CLIENT_ARTIFACT_SHA256)
            artifact_signature = _route_compat_value("DESKTOP_CLIENT_ARTIFACT_SIGNATURE", DESKTOP_CLIENT_ARTIFACT_SIGNATURE)
            signature_alg = _route_compat_value("DESKTOP_CLIENT_SIGNATURE_ALG", DESKTOP_CLIENT_SIGNATURE_ALG)

        current = parse_version(client_version) if client_version else (0, 0, 0)
        minimum = parse_version(minimum_version)
        latest = parse_version(latest_version)
        app_env = str(app.config.get("APP_ENV") or "dev").strip().lower()
        signature_required = bool(
            app.config.get("REQUIRE_SIGNED_UPDATES_IN_PROD", REQUIRE_SIGNED_UPDATES_IN_PROD)
        ) and app_env in ("prod", "production")

        response_payload = {
            "channel": channel,
            "desktop_only_mode": bool(_route_compat_value("DESKTOP_ONLY_MODE", DESKTOP_ONLY_MODE)),
            "minimum_version": minimum_version,
            "latest_version": latest_version,
            "download_url": download_url,
            "release_notes_url": release_notes_url,
            "client_version": client_version or None,
            "update_available": current < latest,
            "force_update": current < minimum,
            "signature_required": signature_required,
        }
        if artifact_sha256:
            response_payload["artifact_sha256"] = artifact_sha256
        if artifact_signature:
            response_payload["artifact_signature"] = artifact_signature
        if signature_alg:
            response_payload["signature_alg"] = signature_alg
        return jsonify(response_payload)
