# -*- coding: utf-8 -*-
"""
Catalog loader for desktop i18n resources.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


SUPPORTED = ('ko', 'en')
DEFAULT = 'ko'


def normalize_locale(value: str | None) -> str:
    raw = (value or '').strip().lower()
    if raw.startswith('en'):
        return 'en'
    if raw.startswith('ko'):
        return 'ko'
    return DEFAULT


def to_display_locale(value: str) -> str:
    return 'en-US' if normalize_locale(value) == 'en' else 'ko-KR'


def _i18n_root() -> Path:
    return Path(__file__).resolve().parents[2] / 'i18n'


@lru_cache(maxsize=32)
def load_catalog(domain: str, locale_code: str) -> dict[str, str]:
    locale_norm = normalize_locale(locale_code)
    path = _i18n_root() / locale_norm / f'{domain}.json'
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}
