# -*- coding: utf-8 -*-

from __future__ import annotations

import os

SESSION_STORE_DIRNAME = ".session_store"
LEGACY_SESSION_STORE_DIRNAME = "flask_session"


def _normalize_dir(path: str) -> str:
    return os.path.realpath(os.path.abspath(str(path or "")))


def get_base_dir() -> str:
    try:
        from config import BASE_DIR

        return _normalize_dir(BASE_DIR)
    except Exception:
        return _normalize_dir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_session_store_dir(*, base_dir: str | None = None) -> str:
    root = _normalize_dir(base_dir or get_base_dir())
    return os.path.join(root, SESSION_STORE_DIRNAME)


def get_legacy_session_store_dir(*, base_dir: str | None = None) -> str:
    root = _normalize_dir(base_dir or get_base_dir())
    return os.path.join(root, LEGACY_SESSION_STORE_DIRNAME)


def get_upload_root() -> str:
    fallback = os.path.join(get_base_dir(), "uploads")
    candidates: list[str] = []

    try:
        from flask import current_app

        folder = str(current_app.config.get("UPLOAD_FOLDER") or "").strip()
        if folder:
            candidates.append(folder)
    except Exception:
        pass

    try:
        import config  # type: ignore

        folder = str(getattr(config, "UPLOAD_FOLDER", "") or "").strip()
        if folder:
            candidates.append(folder)
    except Exception:
        pass

    candidates.append(fallback)

    normalized: list[str] = []
    seen: set[str] = set()
    for folder in candidates:
        real_folder = _normalize_dir(folder)
        if real_folder in seen:
            continue
        seen.add(real_folder)
        normalized.append(real_folder)

    for folder in normalized:
        if os.path.isdir(folder):
            return folder
    return normalized[0] if normalized else _normalize_dir(fallback)


def normalize_upload_relpath(path: str) -> str:
    return str(path or "").replace("\\", "/").strip("/")


def resolve_upload_path(path: str) -> str:
    return os.path.join(get_upload_root(), normalize_upload_relpath(path))
