# -*- coding: utf-8 -*-
"""
사내 메신저 v4.1 앱 패키지
Flask 앱 팩토리 패턴
"""

from __future__ import annotations

import os
import secrets
import sys
from datetime import timedelta

_IS_TESTING_PROCESS = bool(os.environ.get("PYTEST_CURRENT_TEST")) or ("pytest" in sys.modules)
_SKIP_GEVENT = os.environ.get("SKIP_GEVENT_PATCH", "0") == "1" or _IS_TESTING_PROCESS
_GEVENT_AVAILABLE = False
_GEVENT_ALREADY_PATCHED = False

try:
    from gevent import monkey

    _GEVENT_ALREADY_PATCHED = monkey.is_module_patched("socket")
    if _GEVENT_ALREADY_PATCHED:
        _GEVENT_AVAILABLE = True
except ImportError:
    pass

if not _SKIP_GEVENT and not _GEVENT_ALREADY_PATCHED:
    try:
        from gevent import monkey

        monkey.patch_all()
        _GEVENT_AVAILABLE = True
    except ImportError:
        _GEVENT_AVAILABLE = False

from flask import Flask
from flask_session import Session

from app.bootstrap.config_runtime import apply_runtime_config, load_runtime_config
from app.bootstrap.logging_setup import configure_logging
from app.bootstrap.security_headers import install_security_headers
from app.bootstrap.session_guard import install_session_guard
from app.bootstrap.socketio_factory import create_socketio
from app.extensions import compress, csrf, limiter

try:
    from cachelib.file import FileSystemCache
except Exception:  # pragma: no cover
    FileSystemCache = None

try:
    from config import (
        APP_NAME,
        BASE_DIR,
        ENFORCE_HTTPS,
        MAX_CONTENT_LENGTH,
        SESSION_TIMEOUT_HOURS,
        STATIC_FOLDER,
        TEMPLATE_FOLDER,
        UPLOAD_FOLDER,
        USE_HTTPS,
        VERSION,
    )
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import (
        APP_NAME,
        BASE_DIR,
        ENFORCE_HTTPS,
        MAX_CONTENT_LENGTH,
        SESSION_TIMEOUT_HOURS,
        STATIC_FOLDER,
        TEMPLATE_FOLDER,
        UPLOAD_FOLDER,
        USE_HTTPS,
        VERSION,
    )

logger = configure_logging(BASE_DIR)
socketio = None
session_guard_stats = {
    "fail_open_count": 0,
    "last_fail_open_at": None,
    "fail_closed_count": 0,
    "last_fail_closed_at": None,
}


def get_session_guard_stats() -> dict:
    return {
        "fail_open_count": int(session_guard_stats.get("fail_open_count") or 0),
        "last_fail_open_at": session_guard_stats.get("last_fail_open_at"),
        "fail_closed_count": int(session_guard_stats.get("fail_closed_count") or 0),
        "last_fail_closed_at": session_guard_stats.get("last_fail_closed_at"),
    }


def _load_or_create_secret(file_path: str, byte_length: int) -> str:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    new_value = secrets.token_hex(byte_length)
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(new_value)
    return new_value


def create_app():
    global socketio

    runtime = load_runtime_config()

    static_folder = STATIC_FOLDER
    template_folder = TEMPLATE_FOLDER
    os.makedirs(static_folder, exist_ok=True)
    os.makedirs(template_folder, exist_ok=True)
    os.makedirs(str(runtime["upload_folder"]), exist_ok=True)
    os.makedirs(os.path.join(str(runtime["upload_folder"]), "profiles"), exist_ok=True)

    app = Flask(
        __name__,
        static_folder=static_folder,
        static_url_path="/static",
        template_folder=template_folder,
    )

    app.config["SECRET_KEY"] = _load_or_create_secret(os.path.join(BASE_DIR, ".secret_key"), 32)
    app.config["PASSWORD_SALT"] = _load_or_create_secret(os.path.join(BASE_DIR, ".security_salt"), 16)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["SESSION_COOKIE_SECURE"] = USE_HTTPS
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=SESSION_TIMEOUT_HOURS)
    apply_runtime_config(app, runtime, logger)

    session_dir = os.path.join(BASE_DIR, "flask_session")
    os.makedirs(session_dir, exist_ok=True)
    app.config["SESSION_TYPE"] = "cachelib"
    app.config["SESSION_PERMANENT"] = True
    if FileSystemCache is not None:
        app.config["SESSION_CACHELIB"] = FileSystemCache(cache_dir=session_dir, threshold=5000, default_timeout=0)
    else:  # pragma: no cover
        app.config["SESSION_TYPE"] = "filesystem"
        app.config["SESSION_FILE_DIR"] = session_dir
    Session(app)

    socketio = create_socketio(app, gevent_available=_GEVENT_AVAILABLE, logger=logger)

    from app.http.registry import register_routes
    from app.models import close_thread_db, init_db
    from app.realtime.registry import register_socket_events

    register_routes(app)
    try:
        limiter._storage_uri = runtime["rate_limit_storage_uri"]  # type: ignore[attr-defined]
    except Exception:
        pass
    limiter.init_app(app)
    csrf.init_app(app)
    compress.init_app(app)
    register_socket_events(socketio)
    init_db()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        close_thread_db()

    install_session_guard(app, logger=logger, session_guard_stats=session_guard_stats)
    install_security_headers(app)

    logger.info(f"{APP_NAME} v{VERSION} 앱 초기화 완료")
    return app, socketio
