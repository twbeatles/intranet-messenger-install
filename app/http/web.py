# -*- coding: utf-8 -*-

from __future__ import annotations

from flask import jsonify, render_template, request, send_from_directory, session

from app.extensions import csrf
from app.http.common import json_dict
from app.i18n import load_catalog, resolve_locale, to_display_locale
from app.models import get_user_by_id

from config import (
    DESKTOP_CLIENT_DOWNLOAD_URL,
    DESKTOP_CLIENT_LATEST_VERSION,
    DESKTOP_CLIENT_MIN_VERSION,
    DESKTOP_CLIENT_RELEASE_NOTES_URL,
    DESKTOP_ONLY_MODE,
)


def register_web_routes(app) -> None:
    @app.route("/")
    def index():
        if DESKTOP_ONLY_MODE:
            download = DESKTOP_CLIENT_DOWNLOAD_URL or "관리자에게 데스크톱 설치 파일을 요청하세요."
            notes = DESKTOP_CLIENT_RELEASE_NOTES_URL or "-"
            html = f"""
            <!DOCTYPE html>
            <html lang="ko">
            <head><meta charset="UTF-8"><title>Desktop Only</title></head>
            <body style="font-family:Segoe UI,sans-serif;padding:36px;background:#0f172a;color:#e2e8f0;">
              <h1>사내 메신저 데스크톱 전용 모드</h1>
              <p>웹 접속은 비활성화되었습니다. 설치형 클라이언트를 사용해주세요.</p>
              <ul>
                <li>최소 버전: {DESKTOP_CLIENT_MIN_VERSION}</li>
                <li>최신 버전: {DESKTOP_CLIENT_LATEST_VERSION}</li>
                <li>다운로드: {download}</li>
                <li>릴리즈 노트: {notes}</li>
              </ul>
            </body>
            </html>
            """
            return html, 200, {"Content-Type": "text/html; charset=utf-8"}
        return render_template("index.html")

    @app.route("/api/me")
    def get_current_user():
        if "user_id" in session:
            user = get_user_by_id(session["user_id"])
            if user:
                return jsonify({"logged_in": True, "user": user})
        return jsonify({"logged_in": False})

    @app.route("/api/i18n/<domain>")
    @csrf.exempt
    def get_i18n_catalog(domain: str):
        allowed_domains = {"server", "client", "web", "server_gui"}
        if domain not in allowed_domains:
            return jsonify({"error": "지원하지 않는 i18n 도메인입니다."}), 404

        requested = request.args.get("lang") or request.headers.get("X-App-Language")
        locale_code = resolve_locale(req=request, sess=session, manual_value=requested)
        catalog = load_catalog(locale_code, domain)
        return jsonify(
            {
                "domain": domain,
                "locale": to_display_locale(locale_code),
                "catalog": catalog,
            }
        )

    @app.route("/sw.js")
    def service_worker():
        return send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")
