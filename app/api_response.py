# -*- coding: utf-8 -*-
"""
API/socket response helpers for backward-compatible i18n metadata.
"""

from __future__ import annotations

from typing import Any

from app.error_codes import ERROR_MESSAGE_MAP, GENERIC_ERROR_SPEC, ErrorSpec
from app.i18n import to_display_locale, translate


def resolve_error_spec(canonical_ko_error: str) -> ErrorSpec:
    return ERROR_MESSAGE_MAP.get(canonical_ko_error, GENERIC_ERROR_SPEC)


def build_error_payload(
    canonical_ko_error: str,
    *,
    locale_code: str,
    domain: str = 'server',
    explicit_code: str | None = None,
    explicit_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    spec = resolve_error_spec(canonical_ko_error)
    code = explicit_code or spec.code
    key = explicit_key or spec.i18n_key
    localized = translate(key, locale_code, domain, fallback=canonical_ko_error, **kwargs)
    return {
        'error': canonical_ko_error,
        'error_code': code,
        'error_localized': localized,
        'locale': to_display_locale(locale_code),
    }


def build_socket_error_payload(
    canonical_ko_message: str,
    *,
    locale_code: str,
    explicit_code: str | None = None,
    explicit_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    spec = resolve_error_spec(canonical_ko_message)
    code = explicit_code or spec.code
    key = explicit_key or spec.i18n_key
    localized = translate(key, locale_code, 'server', fallback=canonical_ko_message, **kwargs)
    return {
        'message': canonical_ko_message,
        'message_code': code,
        'message_localized': localized,
        'locale': to_display_locale(locale_code),
    }


def enrich_error_payload_if_needed(data: dict[str, Any], locale_code: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        return data
    if 'error' not in data:
        return data
    if 'error_code' in data and 'error_localized' in data:
        if 'locale' not in data:
            data['locale'] = to_display_locale(locale_code)
        return data
    canonical = str(data.get('error') or '')
    payload = build_error_payload(canonical, locale_code=locale_code)
    data.setdefault('error_code', payload['error_code'])
    data.setdefault('error_localized', payload['error_localized'])
    data.setdefault('locale', payload['locale'])
    return data
