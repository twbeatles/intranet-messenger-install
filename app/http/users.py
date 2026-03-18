# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import uuid
from datetime import datetime

from flask import jsonify, request, session

from app.http.common import emit_profile_updated_event, json_dict
from app.models import change_password, delete_user, get_user_by_id, safe_file_delete, update_user_profile as model_update_user_profile
from app.security.upload_scanner import scan_saved_file, scan_upload_stream
from app.utils import sanitize_input, validate_file_header, validate_password

from config import UPLOAD_FOLDER


def _update_user_profile_impl():
    try:
        import app.routes as routes

        return getattr(routes, "update_user_profile", model_update_user_profile)
    except Exception:
        return model_update_user_profile


def register_user_routes(app) -> None:
    @app.route("/api/profile")
    def get_profile():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        user = get_user_by_id(session["user_id"])
        if user:
            return jsonify(user)
        return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

    @app.route("/api/profile", methods=["PUT"])
    def update_profile():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        data = json_dict()
        nickname = sanitize_input(data.get("nickname", ""), max_length=20)
        status_message = sanitize_input(data.get("status_message", ""), max_length=100)
        if nickname and len(nickname) < 2:
            return jsonify({"error": "닉네임은 2자 이상이어야 합니다."}), 400

        success = _update_user_profile_impl()(
            session["user_id"],
            nickname=nickname if nickname else None,
            status_message=status_message if status_message else None,
        )
        if success:
            if nickname:
                session["nickname"] = nickname
            emit_profile_updated_event(int(session["user_id"]))
            return jsonify({"success": True})
        return jsonify({"error": "프로필 업데이트에 실패했습니다."}), 500

    @app.route("/api/profile/image", methods=["POST"])
    def upload_profile_image():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        upload_folder = str(app.config.get("UPLOAD_FOLDER", UPLOAD_FOLDER) or UPLOAD_FOLDER)

        if "file" not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400
        file = request.files["file"]
        raw_filename = str(file.filename or "")
        if raw_filename == "":
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400

        allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
        ext = raw_filename.rsplit(".", 1)[-1].lower() if "." in raw_filename else ""
        if ext not in allowed_extensions:
            return jsonify({"error": "이미지 파일만 업로드 가능합니다."}), 400
        if not validate_file_header(file):
            return jsonify({"error": "유효하지 않은 이미지 파일입니다."}), 400

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > 5 * 1024 * 1024:
            return jsonify({"error": "파일 크기는 5MB 이하여야 합니다."}), 400

        ok, reason = scan_upload_stream(
            file,
            filename=str(file.filename or ""),
            content_type=str(getattr(file, "content_type", "") or ""),
        )
        if not ok:
            return jsonify({"error": reason or "업로드 스캔 정책에 의해 차단되었습니다."}), 400
        file.seek(0)

        profile_folder = os.path.join(upload_folder, "profiles")
        os.makedirs(profile_folder, exist_ok=True)

        user = get_user_by_id(session["user_id"])
        old_profile_image = str((user or {}).get("profile_image") or "").strip()
        filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = os.path.join(profile_folder, filename)
        file.save(file_path)
        ok, reason = scan_saved_file(
            file_path,
            filename=str(file.filename or ""),
            content_type=str(getattr(file, "content_type", "") or ""),
        )
        if not ok:
            safe_file_delete(file_path)
            return jsonify({"error": reason or "업로드 파일 보안 검증에 실패했습니다."}), 400

        profile_image = f"profiles/{filename}"
        try:
            success = _update_user_profile_impl()(session["user_id"], profile_image=profile_image)
            if success:
                if old_profile_image:
                    try:
                        old_image_path = os.path.join(upload_folder, old_profile_image)
                        safe_file_delete(old_image_path)
                    except Exception:
                        pass
                emit_profile_updated_event(int(session["user_id"]))
                return jsonify({"success": True, "profile_image": profile_image})
            safe_file_delete(file_path)
            return jsonify({"error": "프로필 이미지 데이터베이스 업데이트 실패"}), 500
        except Exception:
            safe_file_delete(file_path)
            return jsonify({"error": "프로필 처리 중 오류가 발생했습니다."}), 500

    @app.route("/api/profile/image", methods=["DELETE"])
    def delete_profile_image():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        user = get_user_by_id(session["user_id"])
        upload_folder = app.config.get("UPLOAD_FOLDER", UPLOAD_FOLDER)
        if user and user.get("profile_image"):
            try:
                old_image_path = os.path.join(upload_folder, user["profile_image"])
                safe_file_delete(old_image_path)
            except Exception:
                pass

        success = _update_user_profile_impl()(session["user_id"], profile_image="")
        if success:
            emit_profile_updated_event(int(session["user_id"]))
            return jsonify({"success": True})
        return jsonify({"error": "프로필 이미지 삭제에 실패했습니다."}), 500

    @app.route("/api/me/password", methods=["PUT"])
    def update_password():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        data = json_dict()
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        if not current_password or not new_password:
            return jsonify({"error": "입력값이 부족합니다."}), 400

        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        success, error, new_session_token = change_password(session["user_id"], current_password, new_password)
        if success:
            if new_session_token:
                session["session_token"] = new_session_token
            return jsonify({"success": True, "message": "비밀번호가 변경되었습니다. 다른 기기에서의 세션은 로그아웃됩니다."})
        return jsonify({"error": error}), 400

    @app.route("/api/me", methods=["DELETE"])
    def delete_account():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        data = json_dict()
        password = data.get("password")
        if not password:
            return jsonify({"error": "비밀번호를 입력해주세요."}), 400

        success, error = delete_user(session["user_id"], password)
        if success:
            session.clear()
            return jsonify({"success": True})
        return jsonify({"error": error}), 400
