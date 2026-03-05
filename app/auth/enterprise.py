# -*- coding: utf-8 -*-
"""
Enterprise authentication provider registry.

Current built-in providers:
- mock: static username/password mapping for integration testing
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


EnterpriseAuthResult = dict[str, Any]
EnterpriseProvider = Callable[[str, str, Mapping[str, Any]], EnterpriseAuthResult]


def _normalize_mock_users(raw: Any) -> dict[str, str]:
    if isinstance(raw, dict):
        normalized: dict[str, str] = {}
        for key, value in raw.items():
            username = str(key or '').strip()
            if not username:
                continue
            normalized[username] = str(value or '')
        return normalized

    # Optional shorthand: "alice:pass,bob:pass2"
    if isinstance(raw, str):
        normalized = {}
        chunks = [c.strip() for c in raw.split(',') if c.strip()]
        for chunk in chunks:
            if ':' not in chunk:
                continue
            username, password = chunk.split(':', 1)
            username = username.strip()
            if not username:
                continue
            normalized[username] = password.strip()
        return normalized

    return {}


def _auth_mock(username: str, password: str, config: Mapping[str, Any]) -> EnterpriseAuthResult:
    users = _normalize_mock_users(config.get('ENTERPRISE_MOCK_USERS'))
    if not users:
        return {
            'ok': False,
            'status_code': 500,
            'error': 'mock 엔터프라이즈 사용자 구성이 없습니다.',
        }

    expected = users.get(username)
    if expected is None or expected != password:
        return {
            'ok': False,
            'status_code': 401,
            'error': '엔터프라이즈 인증에 실패했습니다.',
        }

    return {
        'ok': True,
        'status_code': 200,
        'identity': {
            'username': username,
        },
    }


_PROVIDERS: dict[str, EnterpriseProvider] = {
    'mock': _auth_mock,
}


def authenticate_enterprise(
    provider: str,
    username: str,
    password: str,
    *,
    config: Mapping[str, Any],
) -> EnterpriseAuthResult:
    normalized_provider = str(provider or '').strip().lower()
    if not normalized_provider:
        return {
            'ok': False,
            'status_code': 400,
            'error': '엔터프라이즈 인증 제공자가 구성되지 않았습니다.',
        }

    provider_fn = _PROVIDERS.get(normalized_provider)
    if provider_fn is None:
        return {
            'ok': False,
            'status_code': 501,
            'error': f'지원하지 않는 엔터프라이즈 인증 제공자입니다: {normalized_provider}',
        }

    return provider_fn(username, password, config)
