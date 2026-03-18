# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from config import (
    ALLOW_SELF_REGISTER,
    APP_ENV,
    ENTERPRISE_AUTH_ENABLED,
    ENTERPRISE_AUTH_PROVIDER,
    ENTERPRISE_MOCK_USERS,
    ENFORCE_HTTPS,
    RATE_LIMIT_KEY_MODE,
    RATE_LIMIT_STORAGE_URI,
    REQUIRE_MESSAGE_ENCRYPTION,
    REQUIRE_SIGNED_UPDATES_IN_PROD,
    SESSION_TOKEN_FAIL_OPEN,
    UPLOAD_FOLDER,
    UPLOAD_SCAN_ENABLED,
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
        "enterprise_auth_enabled": bool(ENTERPRISE_AUTH_ENABLED),
        "enterprise_auth_provider": ENTERPRISE_AUTH_PROVIDER,
        "enterprise_mock_users": ENTERPRISE_MOCK_USERS,
        "require_message_encryption": bool(REQUIRE_MESSAGE_ENCRYPTION),
        "require_signed_updates_in_prod": bool(REQUIRE_SIGNED_UPDATES_IN_PROD),
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
    app.config["ENTERPRISE_AUTH_ENABLED"] = runtime["enterprise_auth_enabled"]
    app.config["ENTERPRISE_AUTH_PROVIDER"] = runtime["enterprise_auth_provider"]
    if isinstance(runtime["enterprise_mock_users"], dict):
        app.config["ENTERPRISE_MOCK_USERS"] = dict(runtime["enterprise_mock_users"])
    else:
        app.config["ENTERPRISE_MOCK_USERS"] = runtime["enterprise_mock_users"]
    app.config["REQUIRE_MESSAGE_ENCRYPTION"] = runtime["require_message_encryption"]
    app.config["REQUIRE_SIGNED_UPDATES_IN_PROD"] = runtime["require_signed_updates_in_prod"]

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

