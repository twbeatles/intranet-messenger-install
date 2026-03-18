# -*- coding: utf-8 -*-

from __future__ import annotations

import logging

from flask import jsonify, request, session

from app.auth_tokens import (
    get_device_session_by_token,
    issue_device_session,
    list_active_device_sessions,
    revoke_device_session_by_id,
    revoke_device_session_by_token,
    rotate_device_session_token,
    touch_device_session,
)
from app.extensions import csrf, limiter
from app.http.common import approval_gate_for_user, begin_user_session, extract_device_token, json_dict
from app.models import (
    authenticate_user,
    create_user,
    get_user_by_id,
    get_user_by_username,
    log_access,
    request_user_approval,
    review_user_approval,
)
from app.utils import validate_password, validate_username

from config import (
    ALLOW_SELF_REGISTER,
    DEVICE_SESSION_SHORT_TTL_DAYS,
    DEVICE_SESSION_TTL_DAYS,
    ENTERPRISE_AUTH_ENABLED,
    ENTERPRISE_AUTH_PROVIDER,
)

logger = logging.getLogger(__name__)


def register_auth_routes(app) -> None:
    @app.route("/api/register", methods=["POST"])
    @csrf.exempt
    @limiter.limit("5 per minute")
    def register():
        data = json_dict()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        nickname = data.get("nickname", "").strip() or username

        if not username or not password:
            return jsonify({"error": "아이디와 비밀번호를 입력해주세요."}), 400
        if not validate_username(username):
            return jsonify({"error": "아이디는 3-20자 영문, 숫자, 밑줄만 사용 가능합니다."}), 400
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        allow_self_register = bool(app.config.get("ALLOW_SELF_REGISTER", ALLOW_SELF_REGISTER))
        if not allow_self_register:
            user_id = create_user(username, password, nickname)
            if not user_id:
                return jsonify({"error": "이미 존재하는 아이디입니다."}), 400
            if not request_user_approval(int(user_id), reason="self-register-disabled"):
                return jsonify({"error": "승인 요청 생성에 실패했습니다."}), 500
            log_access(user_id, "register_pending_approval", request.remote_addr, request.user_agent.string)
            return jsonify({"success": True, "pending_approval": True, "user_id": user_id}), 202

        user_id = create_user(username, password, nickname)
        if user_id:
            log_access(user_id, "register", request.remote_addr, request.user_agent.string)
            return jsonify({"success": True, "user_id": user_id})
        return jsonify({"error": "이미 존재하는 아이디입니다."}), 400

    @app.route("/api/login", methods=["POST"])
    @csrf.exempt
    @limiter.limit("10 per minute")
    def login():
        data = json_dict()
        user = authenticate_user(data.get("username", ""), data.get("password", ""))
        if user:
            blocked = approval_gate_for_user(user)
            if blocked:
                return blocked
            new_csrf_token = begin_user_session(user)
            log_access(user["id"], "login", request.remote_addr, request.user_agent.string)
            return jsonify({"success": True, "user": user, "csrf_token": new_csrf_token})
        return jsonify({"error": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401

    @app.route("/api/device-sessions", methods=["POST"])
    @csrf.exempt
    @limiter.limit("10 per minute")
    def create_device_session_route():
        data = json_dict()
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        raw_remember = data.get("remember", True)
        device_name = (data.get("device_name") or "Desktop Client").strip()

        if not username or not password:
            return jsonify({"error": "아이디와 비밀번호를 입력해주세요."}), 400
        if not isinstance(raw_remember, bool):
            return jsonify({"error": "remember는 boolean 값이어야 합니다."}), 400
        remember = raw_remember

        user = authenticate_user(username, password)
        if not user:
            return jsonify({"error": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401
        blocked = approval_gate_for_user(user)
        if blocked:
            return blocked

        ttl_days = DEVICE_SESSION_TTL_DAYS if remember else DEVICE_SESSION_SHORT_TTL_DAYS
        issued = issue_device_session(
            user_id=user["id"],
            device_name=device_name,
            ip=request.remote_addr or "",
            user_agent=request.user_agent.string or "",
            ttl_days=ttl_days,
            remember=remember,
        )
        csrf_token = begin_user_session(user)
        session["device_session_id"] = issued["session_id"]
        session["device_id"] = issued["device_id"]
        session["remember_device"] = bool(issued.get("remember", remember))
        log_access(user["id"], "login_device", request.remote_addr, request.user_agent.string)
        return jsonify(
            {
                "access_ok": True,
                "device_token": issued["device_token"],
                "expires_at": issued["expires_at"],
                "user": user,
                "csrf_token": csrf_token,
                "device_session_id": issued["session_id"],
                "remember": bool(issued.get("remember", remember)),
            }
        )

    @app.route("/api/device-sessions/refresh", methods=["POST"])
    @csrf.exempt
    @limiter.limit("30 per minute")
    def refresh_device_session_route():
        token = extract_device_token()
        if not token:
            return jsonify({"error": "device_token이 필요합니다."}), 400

        rotated = rotate_device_session_token(
            token=token,
            ip=request.remote_addr or "",
            user_agent=request.user_agent.string or "",
            ttl_days=DEVICE_SESSION_TTL_DAYS,
        )
        if not rotated:
            return jsonify({"error": "유효하지 않거나 만료된 토큰입니다."}), 401

        user = get_user_by_id(rotated["user_id"])
        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), 401

        csrf_token = begin_user_session(user)
        session["device_session_id"] = rotated["session_id"]
        session["device_id"] = rotated["device_id"]
        session["remember_device"] = bool(rotated.get("remember", True))
        touch_device_session(
            session_id=rotated["session_id"],
            ip=request.remote_addr or "",
            user_agent=request.user_agent.string or "",
        )
        log_access(user["id"], "refresh_device_session", request.remote_addr, request.user_agent.string)
        return jsonify(
            {
                "access_ok": True,
                "device_token_rotated": rotated["device_token"],
                "expires_at": rotated["expires_at"],
                "user": user,
                "csrf_token": csrf_token,
                "device_session_id": rotated["session_id"],
                "remember": bool(rotated.get("remember", True)),
            }
        )

    @app.route("/api/device-sessions/current", methods=["DELETE"])
    @csrf.exempt
    def revoke_current_device_session_route():
        token = extract_device_token()
        revoked = False
        user_id = session.get("user_id")

        if token:
            active = get_device_session_by_token(token)
            if active:
                user_id = active.get("user_id", user_id)
            revoked = revoke_device_session_by_token(token)
        elif user_id and session.get("device_session_id"):
            revoked = revoke_device_session_by_id(user_id, int(session["device_session_id"]))

        if user_id:
            log_access(user_id, "logout_device", request.remote_addr, request.user_agent.string)
        session.clear()
        return jsonify({"success": True, "revoked": bool(revoked)})

    @app.route("/api/device-sessions")
    def list_device_sessions_route():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        include_expired = str(request.args.get("include_expired", "")).lower() in ("1", "true", "yes")
        sessions = list_active_device_sessions(session["user_id"], include_expired=include_expired)
        current_session_id = int(session.get("device_session_id") or 0)
        for row in sessions:
            row["is_current"] = row.get("id") == current_session_id
        return jsonify({"sessions": sessions})

    @app.route("/api/device-sessions/<int:device_session_id>", methods=["DELETE"])
    def revoke_device_session_route(device_session_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        revoked = revoke_device_session_by_id(session["user_id"], device_session_id)
        if not revoked:
            return jsonify({"error": "세션을 찾을 수 없습니다."}), 404
        if int(session.get("device_session_id") or 0) == device_session_id:
            session.clear()
            return jsonify({"success": True, "current_revoked": True})
        return jsonify({"success": True, "current_revoked": False})

    @app.route("/api/auth/enterprise-login", methods=["POST"])
    @csrf.exempt
    @limiter.limit("20 per minute")
    def enterprise_login():
        if not bool(app.config.get("ENTERPRISE_AUTH_ENABLED", ENTERPRISE_AUTH_ENABLED)):
            return jsonify({"error": "엔터프라이즈 인증이 비활성화되어 있습니다."}), 501
        provider = str(app.config.get("ENTERPRISE_AUTH_PROVIDER", ENTERPRISE_AUTH_PROVIDER) or "").strip().lower()
        if not provider:
            return jsonify({"error": "엔터프라이즈 인증 제공자가 구성되지 않았습니다."}), 400

        data = json_dict()
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")
        if not username or not password:
            return jsonify({"error": "아이디와 비밀번호를 입력해주세요."}), 400

        from app.auth.enterprise import authenticate_enterprise

        auth_result = authenticate_enterprise(
            provider=provider,
            username=username,
            password=password,
            config=app.config,
        )
        if not isinstance(auth_result, dict):
            auth_result = {}
        if not bool(auth_result.get("ok")):
            return jsonify({"error": str(auth_result.get("error") or "엔터프라이즈 인증에 실패했습니다.")}), int(
                auth_result.get("status_code") or 401
            )

        identity_value = auth_result.get("identity")
        identity = identity_value if isinstance(identity_value, dict) else {}
        local_username = str(identity.get("username") or username).strip()
        user = get_user_by_username(local_username)
        if not user:
            return jsonify({"error": "로컬 계정이 존재하지 않습니다."}), 404

        blocked = approval_gate_for_user(user)
        if blocked:
            return blocked

        new_csrf_token = begin_user_session(user)
        log_access(user["id"], f"login_enterprise_{provider}", request.remote_addr, request.user_agent.string)
        return jsonify({"success": True, "provider": provider, "user": user, "csrf_token": new_csrf_token})

    @app.route("/api/logout", methods=["POST"])
    @csrf.exempt
    def logout():
        if "user_id" in session:
            log_access(session["user_id"], "logout", request.remote_addr, request.user_agent.string)
        if session.get("user_id") and session.get("device_session_id"):
            revoke_device_session_by_id(int(session["user_id"]), int(session["device_session_id"]))
        else:
            token = extract_device_token()
            if token:
                revoke_device_session_by_token(token)
        session.clear()
        return jsonify({"success": True})
