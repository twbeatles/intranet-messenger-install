# -*- coding: utf-8 -*-
"""
Shared i18n helpers for API/socket/server GUI.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any


SUPPORTED_LOCALES = ('ko', 'en')
DEFAULT_LOCALE = 'ko'
DEFAULT_DISPLAY_LOCALE = 'ko-KR'


def normalize_locale(raw: str | None) -> str:
    value = (raw or '').strip().lower()
    if not value:
        return DEFAULT_LOCALE
    if value.startswith('ko'):
        return 'ko'
    if value.startswith('en'):
        return 'en'
    return DEFAULT_LOCALE


def to_display_locale(locale_code: str) -> str:
    return 'en-US' if normalize_locale(locale_code) == 'en' else 'ko-KR'


def _i18n_root() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'i18n')


@lru_cache(maxsize=32)
def load_catalog(locale_code: str, domain: str) -> dict[str, str]:
    locale_norm = normalize_locale(locale_code)
    path = os.path.join(_i18n_root(), locale_norm, f'{domain}.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return {}
    return {}


def translate(key: str, locale_code: str, domain: str, fallback: str = '', **kwargs: Any) -> str:
    locale_norm = normalize_locale(locale_code)
    catalog = load_catalog(locale_norm, domain)
    text = catalog.get(key)
    if text is None and locale_norm != DEFAULT_LOCALE:
        text = load_catalog(DEFAULT_LOCALE, domain).get(key)
    if text is None:
        text = fallback or key
    try:
        return text.format(**kwargs) if kwargs else text
    except Exception:
        return text


def _locale_from_accept_language(header_value: str | None) -> str:
    header = (header_value or '').strip()
    if not header:
        return DEFAULT_LOCALE
    parts = [p.strip() for p in header.split(',') if p.strip()]
    for part in parts:
        lang = part.split(';', 1)[0].strip()
        norm = normalize_locale(lang)
        if norm in SUPPORTED_LOCALES:
            return norm
    return DEFAULT_LOCALE


def resolve_locale(req=None, sess=None, manual_value: str | None = None) -> str:
    if manual_value:
        return normalize_locale(manual_value)

    # 1) session preference
    try:
        if sess and isinstance(sess, dict):
            pref = sess.get('locale')
            if pref:
                return normalize_locale(pref)
    except Exception:
        pass

    # 2) X-App-Language
    try:
        if req is not None:
            header_lang = req.headers.get('X-App-Language')
            if header_lang:
                return normalize_locale(header_lang)
    except Exception:
        pass

    # 3) Accept-Language
    try:
        if req is not None:
            return _locale_from_accept_language(req.headers.get('Accept-Language'))
    except Exception:
        pass

    return DEFAULT_LOCALE


def resolve_socket_locale(req=None) -> str:
    try:
        if req is not None:
            query_lang = req.args.get('lang') if hasattr(req, 'args') else None
            if query_lang:
                return normalize_locale(query_lang)
            header_lang = req.headers.get('X-App-Language') if hasattr(req, 'headers') else None
            if header_lang:
                return normalize_locale(header_lang)
            return _locale_from_accept_language(req.headers.get('Accept-Language'))
    except Exception:
        pass
    return DEFAULT_LOCALE
