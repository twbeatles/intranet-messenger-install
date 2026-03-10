# -*- coding: utf-8 -*-
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)

class _CompressExtension(Protocol):
    def init_app(self, app: Any) -> object:
        ...


class _FallbackCompress:
    """
    Fallback no-op compression extension.
    Keeps app bootable when optional compression backend deps are missing.
    """

    def init_app(self, app: Any) -> None:
        app.logger.warning("flask_compress unavailable; response compression disabled")
        logger.warning("flask_compress unavailable; response compression disabled")
        return None


try:
    from flask_compress import Compress as _RuntimeCompress
except Exception:
    compress: _CompressExtension = _FallbackCompress()
else:
    compress = _RuntimeCompress()


def _rate_limit_key():
    """
    Compute limiter key dynamically so mode can be switched by config.
    Supported modes:
    - ip:      request remote address
    - user_ip: "<user_id>:<ip>" for authenticated sessions
    """
    ip = get_remote_address() or "unknown"
    try:
        from flask import current_app, session

        mode = str(current_app.config.get("RATE_LIMIT_KEY_MODE", "ip") or "ip").strip().lower()
        if mode == "user_ip":
            user_id = session.get("user_id")
            if user_id:
                return f"{int(user_id)}:{ip}"
        return ip
    except Exception:
        return ip


# [v4.3] 보안 확장 인스턴스
limiter = Limiter(key_func=_rate_limit_key, storage_uri="memory://")
csrf = CSRFProtect()

# [v4.4] 성능 최적화 확장
