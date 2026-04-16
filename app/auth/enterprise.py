# -*- coding: utf-8 -*-
"""
Enterprise authentication provider registry.

Built-in providers:
- mock: static username/password mapping for integration testing
- http_json: POST credentials to an HTTP JSON backend
- ldap: bind against an LDAP directory
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any


logger = logging.getLogger(__name__)

EnterpriseAuthResult = dict[str, Any]
EnterpriseProvider = Callable[[str, str, Mapping[str, Any]], EnterpriseAuthResult]


def _error(status_code: int, message: str) -> EnterpriseAuthResult:
    return {
        "ok": False,
        "status_code": int(status_code),
        "error": str(message or "enterprise authentication failed"),
    }


def _success(username: str) -> EnterpriseAuthResult:
    return {
        "ok": True,
        "status_code": 200,
        "identity": {
            "username": username,
        },
    }


def _normalize_mock_users(raw: Any) -> dict[str, str]:
    if isinstance(raw, dict):
        normalized: dict[str, str] = {}
        for key, value in raw.items():
            normalized[str(key or "").strip()] = str(value or "")
        return {key: value for key, value in normalized.items() if key}

    if isinstance(raw, str):
        normalized: dict[str, str] = {}
        chunks = [chunk.strip() for chunk in raw.split(",") if chunk.strip()]
        for chunk in chunks:
            if ":" not in chunk:
                continue
            username, expected_password = chunk.split(":", 1)
            username = username.strip()
            if username:
                normalized[username] = expected_password.strip()
        return normalized

    return {}


def _normalize_headers(raw: Any) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        header_name = str(key or "").strip()
        if not header_name:
            continue
        normalized[header_name] = str(value or "")
    return normalized


def _extract_identity_username(payload: Any, *, username: str, identity_field: str) -> str:
    if isinstance(payload, Mapping):
        identity = payload.get("identity")
        if isinstance(identity, Mapping):
            nested_username = str(identity.get("username") or identity.get(identity_field) or "").strip()
            if nested_username:
                return nested_username
        field_username = str(payload.get(identity_field) or payload.get("username") or "").strip()
        if field_username:
            return field_username
    return username


def _auth_mock(username: str, password: str, config: Mapping[str, Any]) -> EnterpriseAuthResult:
    users = _normalize_mock_users(config.get("ENTERPRISE_MOCK_USERS"))
    if not users:
        return _error(500, "mock enterprise users are not configured")

    expected = users.get(username)
    if expected is None or expected != password:
        return _error(401, "enterprise authentication failed")

    return _success(username)


def _auth_http_json(username: str, password: str, config: Mapping[str, Any]) -> EnterpriseAuthResult:
    url = str(config.get("ENTERPRISE_HTTP_URL") or "").strip()
    if not url:
        return _error(500, "ENTERPRISE_HTTP_URL is not configured")

    username_field = str(config.get("ENTERPRISE_HTTP_USERNAME_FIELD") or "username").strip() or "username"
    password_field = str(config.get("ENTERPRISE_HTTP_PASSWORD_FIELD") or "password").strip() or "password"
    identity_field = str(config.get("ENTERPRISE_HTTP_IDENTITY_FIELD") or "identity").strip() or "identity"
    headers = _normalize_headers(config.get("ENTERPRISE_HTTP_HEADERS"))
    timeout = float(config.get("ENTERPRISE_HTTP_TIMEOUT_SECONDS") or 5.0)
    verify_tls = bool(config.get("ENTERPRISE_HTTP_VERIFY_TLS", True))

    try:
        import httpx

        response = httpx.post(
            url,
            json={
                username_field: username,
                password_field: password,
            },
            headers=headers,
            timeout=timeout,
            verify=verify_tls,
        )
    except Exception as exc:
        logger.warning("Enterprise HTTP backend request failed: %s", exc)
        return _error(502, f"enterprise backend request failed: {exc}")

    try:
        payload = response.json()
    except Exception:
        payload = {}

    authenticated = response.is_success
    if isinstance(payload, Mapping):
        if "ok" in payload:
            authenticated = bool(payload.get("ok"))
        if "authenticated" in payload:
            authenticated = bool(payload.get("authenticated"))

    if not authenticated:
        status_code = int(response.status_code or 401)
        if status_code < 400:
            status_code = 401
        message = ""
        if isinstance(payload, Mapping):
            message = str(payload.get("error") or payload.get("message") or "").strip()
        return _error(status_code, message or "enterprise authentication failed")

    return _success(_extract_identity_username(payload, username=username, identity_field=identity_field))


def _auth_ldap(username: str, password: str, config: Mapping[str, Any]) -> EnterpriseAuthResult:
    url = str(config.get("ENTERPRISE_LDAP_URL") or "").strip()
    if not url:
        return _error(500, "ENTERPRISE_LDAP_URL is not configured")

    try:
        from ldap3 import Connection, Server, SUBTREE
        from ldap3.utils.conv import escape_filter_chars
    except Exception:
        return _error(500, "ldap3 is required for the ldap enterprise auth provider")

    base_dn = str(config.get("ENTERPRISE_LDAP_BASE_DN") or "").strip()
    user_dn_template = str(config.get("ENTERPRISE_LDAP_USER_DN_TEMPLATE") or "").strip()
    user_filter_template = (
        str(config.get("ENTERPRISE_LDAP_USER_FILTER") or "(sAMAccountName={username})").strip()
        or "(sAMAccountName={username})"
    )
    bind_dn = str(config.get("ENTERPRISE_LDAP_BIND_DN") or "").strip()
    bind_password = str(config.get("ENTERPRISE_LDAP_BIND_PASSWORD") or "")
    timeout = float(config.get("ENTERPRISE_LDAP_TIMEOUT_SECONDS") or 5.0)

    server = Server(url, connect_timeout=timeout)
    search_conn = None
    user_conn = None

    try:
        user_dn = user_dn_template.format(username=username, identity=username) if user_dn_template else ""
        if not user_dn:
            if not base_dn:
                return _error(500, "ENTERPRISE_LDAP_BASE_DN is not configured")
            escaped_username = escape_filter_chars(username)
            user_filter = user_filter_template.format(username=escaped_username, identity=escaped_username)
            search_conn = Connection(
                server,
                user=bind_dn or None,
                password=bind_password or None,
                receive_timeout=timeout,
                auto_bind=False,
            )
            if not search_conn.bind():
                return _error(502, str(search_conn.result.get("message") or "LDAP search bind failed"))
            if not search_conn.search(base_dn, user_filter, search_scope=SUBTREE, attributes=["dn"]):
                return _error(404, "enterprise directory user was not found")
            if len(search_conn.entries) != 1:
                return _error(404, "enterprise directory user lookup was ambiguous")
            user_dn = str(search_conn.entries[0].entry_dn)

        user_conn = Connection(
            server,
            user=user_dn,
            password=password,
            receive_timeout=timeout,
            auto_bind=False,
        )
        if not user_conn.bind():
            return _error(401, str(user_conn.result.get("message") or "enterprise authentication failed"))

        return _success(username)
    except Exception as exc:
        logger.warning("Enterprise LDAP backend failed: %s", exc)
        return _error(502, f"enterprise ldap backend failed: {exc}")
    finally:
        if user_conn is not None:
            try:
                user_conn.unbind()
            except Exception:
                pass
        if search_conn is not None:
            try:
                search_conn.unbind()
            except Exception:
                pass


_PROVIDERS: dict[str, EnterpriseProvider] = {
    "http_json": _auth_http_json,
    "ldap": _auth_ldap,
    "mock": _auth_mock,
}


def authenticate_enterprise(
    provider: str,
    username: str,
    password: str,
    *,
    config: Mapping[str, Any],
) -> EnterpriseAuthResult:
    normalized_provider = str(provider or "").strip().lower()
    if not normalized_provider:
        return _error(400, "enterprise auth provider is not configured")

    provider_fn = _PROVIDERS.get(normalized_provider)
    if provider_fn is None:
        return _error(501, f"unsupported enterprise auth provider: {normalized_provider}")

    return provider_fn(username, password, config)
