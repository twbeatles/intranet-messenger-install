# -*- coding: utf-8 -*-

from __future__ import annotations

import base64

import config
from client.controllers.update_policy import verify_update_metadata
from client.services.update_signing import build_signed_manifest_bytes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def _build_payload() -> dict[str, object]:
    return {
        "channel": "stable",
        "minimum_version": "1.0.0",
        "latest_version": "2.0.0",
        "download_url": "https://example.invalid/download",
        "release_notes_url": "https://example.invalid/release-notes",
        "artifact_sha256": "ab" * 32,
        "signature_required": True,
    }


def _sign_payload(payload: dict[str, object], private_key) -> dict[str, object]:
    signed = dict(payload)
    signature = private_key.sign(
        build_signed_manifest_bytes(signed),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    signed["artifact_signature"] = base64.b64encode(signature).decode("ascii")
    signed["signature_alg"] = "rsa-sha256"
    return signed


def test_verify_update_metadata_accepts_valid_signature(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    monkeypatch.setattr(config, "DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM", public_pem, raising=False)
    monkeypatch.setattr(config, "DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM", "", raising=False)

    ok, reason = verify_update_metadata(_sign_payload(_build_payload(), private_key))
    assert ok is True
    assert reason == ""


def test_verify_update_metadata_rejects_tampered_payload(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    monkeypatch.setattr(config, "DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM", public_pem, raising=False)
    monkeypatch.setattr(config, "DESKTOP_CLIENT_CANARY_SIGNING_PUBLIC_KEY_PEM", "", raising=False)

    payload = _sign_payload(_build_payload(), private_key)
    payload["latest_version"] = "2.0.1"
    ok, reason = verify_update_metadata(payload)
    assert ok is False
    assert "failed" in reason
