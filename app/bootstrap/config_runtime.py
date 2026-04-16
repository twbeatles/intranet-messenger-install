# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from config import (
    ALLOW_SELF_REGISTER,
    APP_ENV,
    DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM,
    DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM,
    ENTERPRISE_AUTH_ENABLED,
    ENTERPRISE_AUTH_PROVIDER,
    ENTERPRISE_HTTP_HEADERS,
    ENTERPRISE_HTTP_IDENTITY_FIELD,
    ENTERPRISE_HTTP_PASSWORD_FIELD,
    ENTERPRISE_HTTP_TIMEOUT_SECONDS,
    ENTERPRISE_HTTP_URL,
    ENTERPRISE_HTTP_USERNAME_FIELD,
    ENTERPRISE_HTTP_VERIFY_TLS,
    ENTERPRISE_LDAP_BASE_DN,
    ENTERPRISE_LDAP_BIND_DN,
    ENTERPRISE_LDAP_BIND_PASSWORD,
    ENTERPRISE_LDAP_TIMEOUT_SECONDS,
    ENTERPRISE_LDAP_URL,
    ENTERPRISE_LDAP_USER_DN_TEMPLATE,
    ENTERPRISE_LDAP_USER_FILTER,
    ENTERPRISE_MOCK_USERS,
    ENFORCE_HTTPS,
    RATE_LIMIT_KEY_MODE,
    RATE_LIMIT_STORAGE_URI,
    REQUIRE_MESSAGE_ENCRYPTION,
    REQUIRE_SIGNED_UPDATES_IN_PROD,
    SESSION_TOKEN_FAIL_OPEN,
    UPLOAD_FOLDER,
    UPLOAD_SCAN_ENABLED,
    UPLOAD_SCAN_FAIL_OPEN,
    UPLOAD_SCAN_HTTP_HEADERS,
    UPLOAD_SCAN_HTTP_TIMEOUT_SECONDS,
    UPLOAD_SCAN_HTTP_URL,
    UPLOAD_SCAN_HTTP_VERIFY_TLS,
    UPLOAD_SCAN_CLAMD_HOST,
    UPLOAD_SCAN_CLAMD_PORT,
    UPLOAD_SCAN_CLAMD_TIMEOUT_SECONDS,
    UPLOAD_SCAN_PROVIDER,
)


def load_runtime_config() -> dict[str, Any]:
    runtime = {
        "upload_folder": UPLOAD_FOLDER,
        "rate_limit_storage_uri": RATE_LIMIT_STORAGE_URI,
        "rate_limit_key_mode": RATE_LIMIT_KEY_MODE,
        "app_env": str(APP_ENV or "dev").strip().lower(),
        "session_token_fail_open": bool(SESSION_TOKEN_FAIL_OPEN),
        "enforce_https": bool(ENFORCE_HTTPS),
        "allow_self_register": bool(ALLOW_SELF_REGISTER),
        "upload_scan_enabled": bool(UPLOAD_SCAN_ENABLED),
        "upload_scan_provider": UPLOAD_SCAN_PROVIDER,
        "upload_scan_fail_open": bool(UPLOAD_SCAN_FAIL_OPEN),
        "upload_scan_http_url": str(UPLOAD_SCAN_HTTP_URL or ""),
        "upload_scan_http_timeout_seconds": float(UPLOAD_SCAN_HTTP_TIMEOUT_SECONDS or 10.0),
        "upload_scan_http_verify_tls": bool(UPLOAD_SCAN_HTTP_VERIFY_TLS),
        "upload_scan_http_headers": UPLOAD_SCAN_HTTP_HEADERS,
        "upload_scan_clamd_host": str(UPLOAD_SCAN_CLAMD_HOST or ""),
        "upload_scan_clamd_port": int(UPLOAD_SCAN_CLAMD_PORT or 3310),
        "upload_scan_clamd_timeout_seconds": float(UPLOAD_SCAN_CLAMD_TIMEOUT_SECONDS or 10.0),
        "enterprise_auth_enabled": bool(ENTERPRISE_AUTH_ENABLED),
        "enterprise_auth_provider": ENTERPRISE_AUTH_PROVIDER,
        "enterprise_mock_users": ENTERPRISE_MOCK_USERS,
        "enterprise_http_url": str(ENTERPRISE_HTTP_URL or ""),
        "enterprise_http_timeout_seconds": float(ENTERPRISE_HTTP_TIMEOUT_SECONDS or 5.0),
        "enterprise_http_verify_tls": bool(ENTERPRISE_HTTP_VERIFY_TLS),
        "enterprise_http_headers": ENTERPRISE_HTTP_HEADERS,
        "enterprise_http_username_field": str(ENTERPRISE_HTTP_USERNAME_FIELD or "username"),
        "enterprise_http_password_field": str(ENTERPRISE_HTTP_PASSWORD_FIELD or "password"),
        "enterprise_http_identity_field": str(ENTERPRISE_HTTP_IDENTITY_FIELD or "identity"),
        "enterprise_ldap_url": str(ENTERPRISE_LDAP_URL or ""),
        "enterprise_ldap_base_dn": str(ENTERPRISE_LDAP_BASE_DN or ""),
        "enterprise_ldap_user_dn_template": str(ENTERPRISE_LDAP_USER_DN_TEMPLATE or ""),
        "enterprise_ldap_user_filter": str(ENTERPRISE_LDAP_USER_FILTER or "(sAMAccountName={username})"),
        "enterprise_ldap_bind_dn": str(ENTERPRISE_LDAP_BIND_DN or ""),
        "enterprise_ldap_bind_password": str(ENTERPRISE_LDAP_BIND_PASSWORD or ""),
        "enterprise_ldap_timeout_seconds": float(ENTERPRISE_LDAP_TIMEOUT_SECONDS or 5.0),
        "require_message_encryption": bool(REQUIRE_MESSAGE_ENCRYPTION),
        "require_signed_updates_in_prod": bool(REQUIRE_SIGNED_UPDATES_IN_PROD),
        "desktop_client_signing_public_key_pem": str(DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM or ""),
        "desktop_client_canary_signing_public_key_pem": str(DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM or ""),
    }
    try:
        import config as runtime_config  # type: ignore

        runtime["app_env"] = str(getattr(runtime_config, "APP_ENV", runtime["app_env"]) or runtime["app_env"]).strip().lower()
        runtime["upload_folder"] = str(
            getattr(runtime_config, "UPLOAD_FOLDER", runtime["upload_folder"]) or runtime["upload_folder"]
        )
        runtime["rate_limit_storage_uri"] = str(
            getattr(runtime_config, "RATE_LIMIT_STORAGE_URI", runtime["rate_limit_storage_uri"])
            or runtime["rate_limit_storage_uri"]
        )
        runtime["rate_limit_key_mode"] = str(
            getattr(runtime_config, "RATE_LIMIT_KEY_MODE", runtime["rate_limit_key_mode"])
            or runtime["rate_limit_key_mode"]
        )
        runtime["session_token_fail_open"] = bool(
            getattr(runtime_config, "SESSION_TOKEN_FAIL_OPEN", runtime["session_token_fail_open"])
        )
        runtime["enforce_https"] = bool(
            getattr(runtime_config, "ENFORCE_HTTPS", runtime["enforce_https"])
        )
        runtime["allow_self_register"] = bool(
            getattr(runtime_config, "ALLOW_SELF_REGISTER", runtime["allow_self_register"])
        )
        runtime["upload_scan_enabled"] = bool(
            getattr(runtime_config, "UPLOAD_SCAN_ENABLED", runtime["upload_scan_enabled"])
        )
        runtime["upload_scan_provider"] = str(
            getattr(runtime_config, "UPLOAD_SCAN_PROVIDER", runtime["upload_scan_provider"])
            or runtime["upload_scan_provider"]
        )
        runtime["upload_scan_fail_open"] = bool(
            getattr(runtime_config, "UPLOAD_SCAN_FAIL_OPEN", runtime["upload_scan_fail_open"])
        )
        runtime["upload_scan_http_url"] = str(
            getattr(runtime_config, "UPLOAD_SCAN_HTTP_URL", runtime["upload_scan_http_url"])
            or runtime["upload_scan_http_url"]
        )
        runtime["upload_scan_http_timeout_seconds"] = float(
            getattr(
                runtime_config,
                "UPLOAD_SCAN_HTTP_TIMEOUT_SECONDS",
                runtime["upload_scan_http_timeout_seconds"],
            )
            or runtime["upload_scan_http_timeout_seconds"]
        )
        runtime["upload_scan_http_verify_tls"] = bool(
            getattr(runtime_config, "UPLOAD_SCAN_HTTP_VERIFY_TLS", runtime["upload_scan_http_verify_tls"])
        )
        runtime["upload_scan_http_headers"] = getattr(
            runtime_config,
            "UPLOAD_SCAN_HTTP_HEADERS",
            runtime["upload_scan_http_headers"],
        )
        runtime["upload_scan_clamd_host"] = str(
            getattr(runtime_config, "UPLOAD_SCAN_CLAMD_HOST", runtime["upload_scan_clamd_host"])
            or runtime["upload_scan_clamd_host"]
        )
        runtime["upload_scan_clamd_port"] = int(
            getattr(runtime_config, "UPLOAD_SCAN_CLAMD_PORT", runtime["upload_scan_clamd_port"])
            or runtime["upload_scan_clamd_port"]
        )
        runtime["upload_scan_clamd_timeout_seconds"] = float(
            getattr(
                runtime_config,
                "UPLOAD_SCAN_CLAMD_TIMEOUT_SECONDS",
                runtime["upload_scan_clamd_timeout_seconds"],
            )
            or runtime["upload_scan_clamd_timeout_seconds"]
        )
        runtime["enterprise_auth_enabled"] = bool(
            getattr(runtime_config, "ENTERPRISE_AUTH_ENABLED", runtime["enterprise_auth_enabled"])
        )
        runtime["enterprise_auth_provider"] = str(
            getattr(runtime_config, "ENTERPRISE_AUTH_PROVIDER", runtime["enterprise_auth_provider"])
            or runtime["enterprise_auth_provider"]
        )
        runtime["enterprise_mock_users"] = getattr(
            runtime_config,
            "ENTERPRISE_MOCK_USERS",
            runtime["enterprise_mock_users"],
        )
        runtime["enterprise_http_url"] = str(
            getattr(runtime_config, "ENTERPRISE_HTTP_URL", runtime["enterprise_http_url"])
            or runtime["enterprise_http_url"]
        )
        runtime["enterprise_http_timeout_seconds"] = float(
            getattr(
                runtime_config,
                "ENTERPRISE_HTTP_TIMEOUT_SECONDS",
                runtime["enterprise_http_timeout_seconds"],
            )
            or runtime["enterprise_http_timeout_seconds"]
        )
        runtime["enterprise_http_verify_tls"] = bool(
            getattr(runtime_config, "ENTERPRISE_HTTP_VERIFY_TLS", runtime["enterprise_http_verify_tls"])
        )
        runtime["enterprise_http_headers"] = getattr(
            runtime_config,
            "ENTERPRISE_HTTP_HEADERS",
            runtime["enterprise_http_headers"],
        )
        runtime["enterprise_http_username_field"] = str(
            getattr(runtime_config, "ENTERPRISE_HTTP_USERNAME_FIELD", runtime["enterprise_http_username_field"])
            or runtime["enterprise_http_username_field"]
        )
        runtime["enterprise_http_password_field"] = str(
            getattr(runtime_config, "ENTERPRISE_HTTP_PASSWORD_FIELD", runtime["enterprise_http_password_field"])
            or runtime["enterprise_http_password_field"]
        )
        runtime["enterprise_http_identity_field"] = str(
            getattr(runtime_config, "ENTERPRISE_HTTP_IDENTITY_FIELD", runtime["enterprise_http_identity_field"])
            or runtime["enterprise_http_identity_field"]
        )
        runtime["enterprise_ldap_url"] = str(
            getattr(runtime_config, "ENTERPRISE_LDAP_URL", runtime["enterprise_ldap_url"])
            or runtime["enterprise_ldap_url"]
        )
        runtime["enterprise_ldap_base_dn"] = str(
            getattr(runtime_config, "ENTERPRISE_LDAP_BASE_DN", runtime["enterprise_ldap_base_dn"])
            or runtime["enterprise_ldap_base_dn"]
        )
        runtime["enterprise_ldap_user_dn_template"] = str(
            getattr(
                runtime_config,
                "ENTERPRISE_LDAP_USER_DN_TEMPLATE",
                runtime["enterprise_ldap_user_dn_template"],
            )
            or runtime["enterprise_ldap_user_dn_template"]
        )
        runtime["enterprise_ldap_user_filter"] = str(
            getattr(runtime_config, "ENTERPRISE_LDAP_USER_FILTER", runtime["enterprise_ldap_user_filter"])
            or runtime["enterprise_ldap_user_filter"]
        )
        runtime["enterprise_ldap_bind_dn"] = str(
            getattr(runtime_config, "ENTERPRISE_LDAP_BIND_DN", runtime["enterprise_ldap_bind_dn"])
            or runtime["enterprise_ldap_bind_dn"]
        )
        runtime["enterprise_ldap_bind_password"] = str(
            getattr(runtime_config, "ENTERPRISE_LDAP_BIND_PASSWORD", runtime["enterprise_ldap_bind_password"])
            or runtime["enterprise_ldap_bind_password"]
        )
        runtime["enterprise_ldap_timeout_seconds"] = float(
            getattr(
                runtime_config,
                "ENTERPRISE_LDAP_TIMEOUT_SECONDS",
                runtime["enterprise_ldap_timeout_seconds"],
            )
            or runtime["enterprise_ldap_timeout_seconds"]
        )
        runtime["require_message_encryption"] = bool(
            getattr(runtime_config, "REQUIRE_MESSAGE_ENCRYPTION", runtime["require_message_encryption"])
        )
        runtime["require_signed_updates_in_prod"] = bool(
            getattr(
                runtime_config,
                "REQUIRE_SIGNED_UPDATES_IN_PROD",
                runtime["require_signed_updates_in_prod"],
            )
        )
        runtime["desktop_client_signing_public_key_pem"] = str(
            getattr(
                runtime_config,
                "DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM",
                runtime["desktop_client_signing_public_key_pem"],
            )
            or runtime["desktop_client_signing_public_key_pem"]
        )
        runtime["desktop_client_canary_signing_public_key_pem"] = str(
            getattr(
                runtime_config,
                "DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM",
                runtime["desktop_client_canary_signing_public_key_pem"],
            )
            or runtime["desktop_client_canary_signing_public_key_pem"]
        )
    except Exception:
        pass
    return runtime


def apply_runtime_config(app, runtime: dict[str, Any], logger) -> None:
    app.config["UPLOAD_FOLDER"] = runtime["upload_folder"]
    app.config["RATELIMIT_STORAGE_URI"] = runtime["rate_limit_storage_uri"]
    app.config["RATE_LIMIT_STORAGE_URI"] = runtime["rate_limit_storage_uri"]
    app.config["RATE_LIMIT_KEY_MODE"] = runtime["rate_limit_key_mode"]
    app.config["APP_ENV"] = runtime["app_env"]
    app.config["SESSION_TOKEN_FAIL_OPEN"] = runtime["session_token_fail_open"]
    app.config["ENFORCE_HTTPS"] = runtime["enforce_https"]
    app.config["ALLOW_SELF_REGISTER"] = runtime["allow_self_register"]
    app.config["UPLOAD_SCAN_ENABLED"] = runtime["upload_scan_enabled"]
    app.config["UPLOAD_SCAN_PROVIDER"] = runtime["upload_scan_provider"]
    app.config["UPLOAD_SCAN_FAIL_OPEN"] = runtime["upload_scan_fail_open"]
    app.config["UPLOAD_SCAN_HTTP_URL"] = runtime["upload_scan_http_url"]
    app.config["UPLOAD_SCAN_HTTP_TIMEOUT_SECONDS"] = runtime["upload_scan_http_timeout_seconds"]
    app.config["UPLOAD_SCAN_HTTP_VERIFY_TLS"] = runtime["upload_scan_http_verify_tls"]
    app.config["UPLOAD_SCAN_HTTP_HEADERS"] = runtime["upload_scan_http_headers"]
    app.config["UPLOAD_SCAN_CLAMD_HOST"] = runtime["upload_scan_clamd_host"]
    app.config["UPLOAD_SCAN_CLAMD_PORT"] = runtime["upload_scan_clamd_port"]
    app.config["UPLOAD_SCAN_CLAMD_TIMEOUT_SECONDS"] = runtime["upload_scan_clamd_timeout_seconds"]
    app.config["ENTERPRISE_AUTH_ENABLED"] = runtime["enterprise_auth_enabled"]
    app.config["ENTERPRISE_AUTH_PROVIDER"] = runtime["enterprise_auth_provider"]
    if isinstance(runtime["enterprise_mock_users"], dict):
        app.config["ENTERPRISE_MOCK_USERS"] = dict(runtime["enterprise_mock_users"])
    else:
        app.config["ENTERPRISE_MOCK_USERS"] = runtime["enterprise_mock_users"]
    app.config["ENTERPRISE_HTTP_URL"] = runtime["enterprise_http_url"]
    app.config["ENTERPRISE_HTTP_TIMEOUT_SECONDS"] = runtime["enterprise_http_timeout_seconds"]
    app.config["ENTERPRISE_HTTP_VERIFY_TLS"] = runtime["enterprise_http_verify_tls"]
    app.config["ENTERPRISE_HTTP_HEADERS"] = runtime["enterprise_http_headers"]
    app.config["ENTERPRISE_HTTP_USERNAME_FIELD"] = runtime["enterprise_http_username_field"]
    app.config["ENTERPRISE_HTTP_PASSWORD_FIELD"] = runtime["enterprise_http_password_field"]
    app.config["ENTERPRISE_HTTP_IDENTITY_FIELD"] = runtime["enterprise_http_identity_field"]
    app.config["ENTERPRISE_LDAP_URL"] = runtime["enterprise_ldap_url"]
    app.config["ENTERPRISE_LDAP_BASE_DN"] = runtime["enterprise_ldap_base_dn"]
    app.config["ENTERPRISE_LDAP_USER_DN_TEMPLATE"] = runtime["enterprise_ldap_user_dn_template"]
    app.config["ENTERPRISE_LDAP_USER_FILTER"] = runtime["enterprise_ldap_user_filter"]
    app.config["ENTERPRISE_LDAP_BIND_DN"] = runtime["enterprise_ldap_bind_dn"]
    app.config["ENTERPRISE_LDAP_BIND_PASSWORD"] = runtime["enterprise_ldap_bind_password"]
    app.config["ENTERPRISE_LDAP_TIMEOUT_SECONDS"] = runtime["enterprise_ldap_timeout_seconds"]
    app.config["REQUIRE_MESSAGE_ENCRYPTION"] = runtime["require_message_encryption"]
    app.config["REQUIRE_SIGNED_UPDATES_IN_PROD"] = runtime["require_signed_updates_in_prod"]
    app.config["DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM"] = runtime["desktop_client_signing_public_key_pem"]
    app.config["DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM"] = runtime["desktop_client_canary_signing_public_key_pem"]

    app_env = str(runtime["app_env"] or "dev").strip().lower()
    hardening_warnings: list[str] = []
    if app_env in ("prod", "production"):
        if not runtime["enforce_https"]:
            hardening_warnings.append("ENFORCE_HTTPS=False")
        if not runtime["require_message_encryption"]:
            hardening_warnings.append("REQUIRE_MESSAGE_ENCRYPTION=False")
        if runtime["session_token_fail_open"]:
            hardening_warnings.append("SESSION_TOKEN_FAIL_OPEN=True")
        if not runtime["upload_scan_enabled"]:
            hardening_warnings.append("UPLOAD_SCAN_ENABLED=False")
        if not runtime["require_signed_updates_in_prod"]:
            hardening_warnings.append("REQUIRE_SIGNED_UPDATES_IN_PROD=False")
    app.config["HARDENING_WARNINGS"] = hardening_warnings
    if hardening_warnings:
        for warning in hardening_warnings:
            logger.warning(f"[hardening:{app_env}] {warning}")

