# -*- coding: utf-8 -*-
"""
사내 메신저 v4.36 설정 파일
"""

import os
import sys
from typing import cast

# ============================================================================
# 경로 설정 (PyInstaller 호환)
# ============================================================================
# BUNDLE_DIR: 번들된 리소스 위치 (static, templates, app, gui 등)
# BASE_DIR: 실행 파일 위치 (데이터베이스, 업로드, 로그 등 사용자 데이터)

if getattr(sys, 'frozen', False):
    # PyInstaller로 패키징된 경우
    BUNDLE_DIR = cast(str, getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
    BASE_DIR = os.path.dirname(sys.executable)  # 실행 파일 위치 (DB, 로그 등)
else:
    # 개발 환경
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = BUNDLE_DIR

# 데이터베이스 (사용자 데이터 - BASE_DIR)
DATABASE_PATH = os.path.join(BASE_DIR, 'messenger.db')

# 업로드 (사용자 데이터 - BASE_DIR)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'ico', 'svg', 'heic', 'heif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip', 'rar', '7z'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# SSL 인증서 (사용자 데이터 - BASE_DIR)
SSL_DIR = os.path.join(BASE_DIR, 'certs')
SSL_CERT_PATH = os.path.join(SSL_DIR, 'cert.pem')
SSL_KEY_PATH = os.path.join(SSL_DIR, 'key.pem')

# 리소스 폴더 (번들 리소스 - BUNDLE_DIR)
STATIC_FOLDER = os.path.join(BUNDLE_DIR, 'static')
TEMPLATE_FOLDER = os.path.join(BUNDLE_DIR, 'templates')

# ============================================================================
# 서버 설정
# ============================================================================
APP_ENV = (os.environ.get('MESSENGER_ENV') or os.environ.get('FLASK_ENV') or 'dev').strip().lower()
_USE_HTTPS_ENV = (os.environ.get('USE_HTTPS') or '').strip().lower()
if _USE_HTTPS_ENV in ('1', 'true', 'yes', 'on'):
    USE_HTTPS = True
elif _USE_HTTPS_ENV in ('0', 'false', 'no', 'off'):
    USE_HTTPS = False
else:
    USE_HTTPS = APP_ENV in ('prod', 'production')

DEFAULT_PORT = 5000
CONTROL_PORT = 5001  # GUI-서버 제어 API 포트
SESSION_TIMEOUT_HOURS = 72  # 3일
PASSWORD_SALT = "messenger_secure_salt_2024"
DEVICE_SESSION_TTL_DAYS = 30
DEVICE_SESSION_SHORT_TTL_DAYS = 1

# Desktop migration/cutover policy
DESKTOP_ONLY_MODE = False
DESKTOP_CLIENT_MIN_VERSION = "1.0.0"
DESKTOP_CLIENT_LATEST_VERSION = "1.0.0"
DESKTOP_CLIENT_DOWNLOAD_URL = ""
DESKTOP_CLIENT_RELEASE_NOTES_URL = ""
DESKTOP_CLIENT_ARTIFACT_SHA256 = ""
DESKTOP_CLIENT_ARTIFACT_SIGNATURE = ""
DESKTOP_CLIENT_SIGNATURE_ALG = "rsa-sha256"
DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM = ""
DESKTOP_CLIENT_CHANNEL_DEFAULT = "stable"  # stable | canary
DESKTOP_CLIENT_CANARY_MIN_VERSION = "1.0.0"
DESKTOP_CLIENT_CANARY_LATEST_VERSION = "1.0.0"
DESKTOP_CLIENT_CANARY_DOWNLOAD_URL = ""
DESKTOP_CLIENT_CANARY_RELEASE_NOTES_URL = ""
DESKTOP_CLIENT_CANARY_ARTIFACT_SHA256 = ""
DESKTOP_CLIENT_CANARY_ARTIFACT_SIGNATURE = ""
DESKTOP_CLIENT_CANARY_SIGNATURE_ALG = "rsa-sha256"
DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM = ""

# Policy switches (default: preserve current behavior)
ENFORCE_HTTPS = False
ALLOW_SELF_REGISTER = True
MAINTENANCE_INTERVAL_MINUTES = 30
REQUIRE_MESSAGE_ENCRYPTION = False
REQUIRE_SIGNED_UPDATES_IN_PROD = True
RATE_LIMIT_STORAGE_URI = "memory://"
RATE_LIMIT_KEY_MODE = "ip"  # ip | user_ip
SESSION_TOKEN_FAIL_OPEN = True
UPLOAD_SCAN_ENABLED = False
UPLOAD_SCAN_PROVIDER = "noop"
UPLOAD_SCAN_FAIL_OPEN = False
UPLOAD_SCAN_HTTP_URL = ""
UPLOAD_SCAN_HTTP_TIMEOUT_SECONDS = 10.0
UPLOAD_SCAN_HTTP_VERIFY_TLS = True
UPLOAD_SCAN_HTTP_HEADERS = {}
UPLOAD_SCAN_CLAMD_HOST = ""
UPLOAD_SCAN_CLAMD_PORT = 3310
UPLOAD_SCAN_CLAMD_TIMEOUT_SECONDS = 10.0
ENTERPRISE_AUTH_ENABLED = False
ENTERPRISE_AUTH_PROVIDER = ""
ENTERPRISE_MOCK_USERS = {}  # {"username": "password"}
ENTERPRISE_HTTP_URL = ""
ENTERPRISE_HTTP_TIMEOUT_SECONDS = 5.0
ENTERPRISE_HTTP_VERIFY_TLS = True
ENTERPRISE_HTTP_HEADERS = {}
ENTERPRISE_HTTP_USERNAME_FIELD = "username"
ENTERPRISE_HTTP_PASSWORD_FIELD = "password"
ENTERPRISE_HTTP_IDENTITY_FIELD = "identity"
ENTERPRISE_LDAP_URL = ""
ENTERPRISE_LDAP_BASE_DN = ""
ENTERPRISE_LDAP_USER_DN_TEMPLATE = ""
ENTERPRISE_LDAP_USER_FILTER = "(sAMAccountName={username})"
ENTERPRISE_LDAP_BIND_DN = ""
ENTERPRISE_LDAP_BIND_PASSWORD = ""
ENTERPRISE_LDAP_TIMEOUT_SECONDS = 5.0

# Socket.IO CORS
# None이면 Flask-SocketIO 기본 정책(동일 출처)을 따릅니다.
# 필요 시 예: ['http://127.0.0.1:5000', 'http://localhost:5000']
SOCKETIO_CORS_ALLOWED_ORIGINS = None

# ============================================================================
# 동시 접속 및 성능 설정
# ============================================================================
# 비동기 모드: 'gevent' (권장, 고성능), 'eventlet', 'threading' (기본, 제한적)
# gevent를 사용하려면: pip install gevent gevent-websocket
# eventlet을 사용하려면: pip install eventlet
# ASYNC_MODE = 'gevent'  # 수십~수백 명 동시 접속 지원
# ASYNC_MODE = 'gevent'  # 수십~수백 명 동시 접속 지원
ASYNC_MODE = 'gevent'  # 수십~수백 명 동시 접속 지원 (권장)

# Socket.IO 설정
PING_TIMEOUT = 120  # 클라이언트 연결 타임아웃 (초)
PING_INTERVAL = 25  # 핑 간격 (초)
MAX_HTTP_BUFFER_SIZE = 10 * 1024 * 1024  # 10MB (메시지 버퍼 크기)

# 동시 연결 제한 (0 = 무제한)
MAX_CONNECTIONS = 0

# 메시지 큐 설정 (대규모 배포 시 Redis 사용 권장)
# MESSAGE_QUEUE = 'redis://localhost:6379'  # Redis 사용 시 주석 해제
MESSAGE_QUEUE = None  # 단일 서버 모드

# ============================================================================
# 앱 정보
# ============================================================================
APP_NAME = "사내 메신저 서버"
VERSION = "4.36"

