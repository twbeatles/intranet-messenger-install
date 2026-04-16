# -*- coding: utf-8 -*-
"""
Upload scanning provider abstraction.
"""

from __future__ import annotations

import base64
import logging
import socket
import struct
from typing import Any


logger = logging.getLogger(__name__)


class UploadScanError(RuntimeError):
    pass


def _noop_scan(*args, **kwargs) -> tuple[bool, str]:
    return True, ""


def _get_config(name: str, default: Any = None) -> Any:
    try:
        from flask import current_app

        return current_app.config.get(name, default)
    except Exception:
        return default


def _provider_name() -> str:
    return str(_get_config("UPLOAD_SCAN_PROVIDER", "noop") or "noop").strip().lower()


def _is_enabled() -> bool:
    return bool(_get_config("UPLOAD_SCAN_ENABLED", False))


def _is_fail_open_enabled() -> bool:
    return bool(_get_config("UPLOAD_SCAN_FAIL_OPEN", False))


def _normalize_headers(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        header_name = str(key or "").strip()
        if not header_name:
            continue
        normalized[header_name] = str(value or "")
    return normalized


def _scanner_unavailable(message: str, *, exc: Exception | None = None) -> tuple[bool, str]:
    if exc is None:
        logger.warning(message)
    else:
        logger.warning("%s: %s", message, exc)
    if _is_fail_open_enabled():
        return True, ""
    return False, message


def _read_stream_bytes(file_obj) -> bytes:
    position = None
    try:
        position = file_obj.tell()
    except Exception:
        position = None

    try:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        data = file_obj.read()
        if isinstance(data, str):
            return data.encode("utf-8")
        return bytes(data or b"")
    finally:
        if position is not None and hasattr(file_obj, "seek"):
            try:
                file_obj.seek(position)
            except Exception:
                pass


def _read_saved_file(full_path: str) -> bytes:
    with open(full_path, "rb") as handle:
        return handle.read()


def _http_json_scan(payload_bytes: bytes, *, filename: str, content_type: str) -> tuple[bool, str]:
    url = str(_get_config("UPLOAD_SCAN_HTTP_URL", "") or "").strip()
    if not url:
        raise UploadScanError("UPLOAD_SCAN_HTTP_URL is not configured")

    headers = _normalize_headers(_get_config("UPLOAD_SCAN_HTTP_HEADERS", {}))
    timeout = float(_get_config("UPLOAD_SCAN_HTTP_TIMEOUT_SECONDS", 10.0) or 10.0)
    verify_tls = bool(_get_config("UPLOAD_SCAN_HTTP_VERIFY_TLS", True))

    import httpx

    response = httpx.post(
        url,
        json={
            "filename": filename,
            "content_type": content_type,
            "content_b64": base64.b64encode(payload_bytes).decode("ascii"),
            "size_bytes": len(payload_bytes),
        },
        headers=headers,
        timeout=timeout,
        verify=verify_tls,
    )
    try:
        data = response.json()
    except Exception:
        data = {}

    verdict = str(data.get("verdict") or "").strip().lower() if isinstance(data, dict) else ""
    reason = ""
    if isinstance(data, dict):
        reason = str(data.get("reason") or data.get("error") or data.get("message") or "").strip()

    if verdict in {"clean", "allow", "allowed", "ok", "passed"}:
        return True, ""
    if verdict in {"blocked", "deny", "denied", "infected", "malicious"}:
        return False, reason or f"upload rejected by scanner: {verdict}"
    if isinstance(data, dict):
        for truthy_key in ("clean", "ok", "allowed", "passed"):
            if truthy_key in data:
                if bool(data.get(truthy_key)):
                    return True, ""
                return False, reason or "upload rejected by scanner"

    if response.is_success:
        return False, reason or "upload rejected by scanner"
    raise UploadScanError(reason or f"upload scanner HTTP backend returned {response.status_code}")


def _clamd_scan(payload_bytes: bytes) -> tuple[bool, str]:
    host = str(_get_config("UPLOAD_SCAN_CLAMD_HOST", "") or "").strip()
    if not host:
        raise UploadScanError("UPLOAD_SCAN_CLAMD_HOST is not configured")

    port = int(_get_config("UPLOAD_SCAN_CLAMD_PORT", 3310) or 3310)
    timeout = float(_get_config("UPLOAD_SCAN_CLAMD_TIMEOUT_SECONDS", 10.0) or 10.0)

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(b"zINSTREAM\0")
            view = memoryview(payload_bytes)
            chunk_size = 65536
            for offset in range(0, len(view), chunk_size):
                chunk = view[offset : offset + chunk_size]
                sock.sendall(struct.pack("!I", len(chunk)))
                sock.sendall(chunk)
            sock.sendall(struct.pack("!I", 0))

            response_chunks: list[bytes] = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_chunks.append(chunk)
                if b"\n" in chunk:
                    break
    except OSError as exc:
        raise UploadScanError(f"clamd scan failed: {exc}") from exc

    raw_response = b"".join(response_chunks).decode("utf-8", errors="replace").strip()
    if raw_response.endswith("OK"):
        return True, ""
    if "FOUND" in raw_response:
        return False, raw_response
    if "ERROR" in raw_response:
        raise UploadScanError(raw_response)
    return False, raw_response or "upload rejected by clamd"


def _dispatch_scan(provider: str, payload_bytes: bytes, *, filename: str, content_type: str) -> tuple[bool, str]:
    if provider == "noop":
        return _noop_scan(payload_bytes, filename=filename, content_type=content_type)
    if provider == "http_json":
        return _http_json_scan(payload_bytes, filename=filename, content_type=content_type)
    if provider == "clamd":
        return _clamd_scan(payload_bytes)
    raise UploadScanError(f"unknown upload scan provider: {provider}")


def scan_upload_stream(file_obj, *, filename: str = "", content_type: str = "") -> tuple[bool, str]:
    """
    Pre-save scanner hook.
    Returns (ok, reason).
    """
    if not _is_enabled():
        return True, ""

    provider = _provider_name()
    try:
        return _dispatch_scan(
            provider,
            _read_stream_bytes(file_obj),
            filename=filename,
            content_type=content_type,
        )
    except UploadScanError as exc:
        return _scanner_unavailable(str(exc), exc=exc)
    except Exception as exc:
        return _scanner_unavailable("upload scanner failed", exc=exc)


def scan_saved_file(full_path: str, *, filename: str = "", content_type: str = "") -> tuple[bool, str]:
    """
    Post-save scanner hook.
    Returns (ok, reason).
    """
    if not _is_enabled():
        return True, ""

    provider = _provider_name()
    try:
        return _dispatch_scan(
            provider,
            _read_saved_file(full_path),
            filename=filename,
            content_type=content_type,
        )
    except UploadScanError as exc:
        return _scanner_unavailable(str(exc), exc=exc)
    except Exception as exc:
        return _scanner_unavailable("upload scanner failed", exc=exc)
