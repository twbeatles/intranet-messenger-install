# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import uuid
from datetime import datetime

from flask import jsonify, request, send_from_directory, session
from werkzeug.utils import secure_filename

from app.http.common import json_dict
from app.models import delete_room_file, get_db, get_room_files, is_room_admin, is_room_member, safe_file_delete
from app.security.upload_scanner import scan_saved_file, scan_upload_stream
from app.upload_tokens import issue_upload_token
from app.utils import allowed_file, validate_file_header

from config import UPLOAD_FOLDER


def register_upload_routes(app) -> None:
    @app.route("/api/upload", methods=["POST"])
    def upload_file():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        upload_folder = str(app.config.get("UPLOAD_FOLDER", UPLOAD_FOLDER) or UPLOAD_FOLDER)

        room_id = request.form.get("room_id", type=int)
        if not room_id:
            return jsonify({"error": "room_id가 필요합니다."}), 400
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        max_size = 16 * 1024 * 1024
        if request.content_length and request.content_length > max_size:
            return jsonify({"error": "파일 크기는 16MB 이하여야 합니다."}), 413
        if "file" not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400

        file = request.files["file"]
        raw_filename = str(file.filename or "")
        if raw_filename == "":
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400

        if file and allowed_file(raw_filename):
            if not validate_file_header(file):
                return jsonify({"error": "파일 내용이 확장자와 일치하지 않습니다."}), 400

            ok, reason = scan_upload_stream(
                file,
                filename=str(file.filename or ""),
                content_type=str(getattr(file, "content_type", "") or ""),
            )
            if not ok:
                return jsonify({"error": reason or "업로드 스캔 정책에 의해 차단되었습니다."}), 400

            filename = secure_filename(raw_filename)
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            ok, reason = scan_saved_file(
                file_path,
                filename=filename,
                content_type=str(getattr(file, "content_type", "") or ""),
            )
            if not ok:
                safe_file_delete(file_path)
                return jsonify({"error": reason or "업로드 파일 보안 검증에 실패했습니다."}), 400

            file_size = os.path.getsize(file_path)
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            file_type = "image" if ext in {"png", "jpg", "jpeg", "gif", "webp", "bmp", "ico"} else "file"
            upload_token = issue_upload_token(
                user_id=session["user_id"],
                room_id=room_id,
                file_path=unique_filename,
                file_name=filename,
                file_type=file_type,
                file_size=file_size,
            )
            if not upload_token:
                safe_file_delete(file_path)
                return jsonify({"error": "업로드 토큰 발급에 실패했습니다."}), 500
            return jsonify(
                {
                    "success": True,
                    "file_path": unique_filename,
                    "file_name": filename,
                    "file_type": file_type,
                    "upload_token": upload_token,
                }
            )

        return jsonify({"error": "허용되지 않는 파일 형식입니다."}), 400

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        upload_folder = str(app.config.get("UPLOAD_FOLDER", UPLOAD_FOLDER) or UPLOAD_FOLDER)

        safe_filename = secure_filename(os.path.basename(filename))
        is_profile = False
        if "/" in filename:
            subdir = os.path.dirname(filename)
            if subdir not in ["profiles"]:
                return jsonify({"error": "접근 권한이 없습니다."}), 403
            safe_path = os.path.join(subdir, safe_filename)
            is_profile = subdir == "profiles"
        else:
            safe_path = safe_filename

        full_path = os.path.realpath(os.path.join(upload_folder, safe_path))
        if not full_path.startswith(os.path.realpath(upload_folder)):
            return jsonify({"error": "잘못된 요청입니다."}), 400
        if not os.path.isfile(full_path):
            return jsonify({"error": "파일을 찾을 수 없습니다."}), 404

        download_name = safe_filename
        if not is_profile:
            try:
                conn = get_db()
                cursor = conn.cursor()
                lookup_path = safe_path.replace("\\", "/")
                cursor.execute(
                    "SELECT room_id, file_name FROM room_files WHERE file_path = ? ORDER BY id DESC LIMIT 1",
                    (lookup_path,),
                )
                row = cursor.fetchone()
            except Exception:
                row = None

            if not row:
                return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
            room_id = row["room_id"]
            download_name = row["file_name"] or download_name
            if not is_room_member(room_id, session["user_id"]):
                return jsonify({"error": "접근 권한이 없습니다."}), 403

        ext = os.path.splitext(safe_filename)[1].lower().lstrip(".")
        inline_exts = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "ico"}
        as_attachment = (not is_profile) and (ext not in inline_exts)
        response = send_from_directory(
            os.path.dirname(full_path),
            os.path.basename(full_path),
            as_attachment=as_attachment,
            download_name=download_name if as_attachment else None,
        )
        response.headers["Cache-Control"] = "private, max-age=3600" if is_profile else "private, no-store"
        response.headers["Vary"] = "Accept-Encoding"
        if not as_attachment and ext in inline_exts:
            response.headers["Content-Disposition"] = "inline"
        return response

    @app.route("/api/rooms/<int:room_id>/files")
    def get_files(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403
        file_type = request.args.get("type")
        return jsonify(get_room_files(room_id, file_type))

    @app.route("/api/rooms/<int:room_id>/files/<int:file_id>", methods=["DELETE"])
    def delete_file_route(room_id, file_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403
        is_admin = is_room_admin(room_id, session["user_id"])
        success, _file_path = delete_room_file(file_id, session["user_id"], room_id=room_id, is_admin=is_admin)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "파일 삭제 권한이 없습니다."}), 403
