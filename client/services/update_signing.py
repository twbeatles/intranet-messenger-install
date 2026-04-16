# -*- coding: utf-8 -*-
"""
Helpers for verifying signed desktop update metadata.
"""

from __future__ import annotations

import base64
import binascii
import json
from functools import lru_cache
from typing import Any, Mapping, Protocol, cast


SUPPORTED_SIGNATURE_ALGS = {"rsa-sha256", "sha256"}


class _VerifyingPublicKey(Protocol):
    def verify(self, signature: bytes, data: bytes, padding: Any, algorithm: Any) -> None:
        ...


def build_signed_manifest(payload: Mapping[str, Any]) -> dict[str, str]:
    return {
        "artifact_sha256": str(payload.get("artifact_sha256") or "").strip(),
        "channel": str(payload.get("channel") or "stable").strip().lower() or "stable",
        "download_url": str(payload.get("download_url") or "").strip(),
        "latest_version": str(payload.get("latest_version") or "").strip(),
        "minimum_version": str(payload.get("minimum_version") or "").strip(),
        "release_notes_url": str(payload.get("release_notes_url") or "").strip(),
    }


def build_signed_manifest_bytes(payload: Mapping[str, Any]) -> bytes:
    manifest = build_signed_manifest(payload)
    return json.dumps(
        manifest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _get_signing_public_key_pem(channel: str) -> str:
    try:
        import config as runtime_config
    except Exception:
        return ""

    stable_pem = str(getattr(runtime_config, "DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM", "") or "").strip()
    canary_pem = str(getattr(runtime_config, "DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM", "") or "").strip()
    if channel == "canary":
        return canary_pem or stable_pem
    return stable_pem


@lru_cache(maxsize=4)
def _load_public_key(public_key_pem: str):
    from cryptography.hazmat.primitives import serialization

    return serialization.load_pem_public_key(public_key_pem.encode("utf-8"))


def verify_signed_update_payload(payload: Mapping[str, Any]) -> tuple[bool, str]:
    signature_alg = str(payload.get("signature_alg") or "").strip().lower()
    if signature_alg not in SUPPORTED_SIGNATURE_ALGS:
        return False, f"unsupported signature_alg: {signature_alg or 'missing'}"

    channel = str(payload.get("channel") or "stable").strip().lower() or "stable"
    public_key_pem = _get_signing_public_key_pem(channel)
    if not public_key_pem:
        return False, "signing public key is not configured"

    signature_b64 = str(payload.get("artifact_signature") or "").strip()
    if not signature_b64:
        return False, "artifact_signature is missing"

    try:
        signature = base64.b64decode(signature_b64, validate=True)
    except (ValueError, binascii.Error):
        return False, "artifact_signature is not valid base64"

    try:
        public_key = cast(_VerifyingPublicKey, _load_public_key(public_key_pem))
    except Exception as exc:
        return False, f"signing public key is invalid: {exc}"

    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        public_key.verify(
            signature,
            build_signed_manifest_bytes(payload),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except Exception:
        return False, "artifact signature verification failed"

    return True, ""
