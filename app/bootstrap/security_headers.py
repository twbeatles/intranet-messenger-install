# -*- coding: utf-8 -*-

from __future__ import annotations

import json

from flask import request, session

from app.api_response import enrich_error_payload_if_needed
from app.i18n import resolve_locale


def install_security_headers(app) -> None:
    @app.after_request
    def add_security_headers(response):
        content_type = response.headers.get("Content-Type", "")
        if response.status_code >= 400 and "application/json" in content_type:
            try:
                payload = response.get_json(silent=True)
                if isinstance(payload, dict):
                    locale_code = resolve_locale(req=request, sess=session)
                    updated = enrich_error_payload_if_needed(payload, locale_code)
                    response.set_data(json.dumps(updated, ensure_ascii=False).encode("utf-8"))
            except Exception:
                pass

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' ws: wss:;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
