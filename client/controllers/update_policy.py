# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any


def verify_update_metadata(payload: dict[str, Any]) -> tuple[bool, str]:
    sha = str(payload.get("artifact_sha256") or "").strip()
    sig = str(payload.get("artifact_signature") or "").strip()
    alg = str(payload.get("signature_alg") or "").strip()
    signature_required = bool(payload.get("signature_required", False))
    if not sha and not sig:
        if signature_required:
            return False, "signed update metadata is required"
        return True, ""
    if not sha:
        return False, "artifact_sha256 is missing"
    if not sig:
        return False, "artifact_signature is missing"
    if not alg:
        return False, "signature_alg is missing"
    return True, ""


def should_block_unsigned_update(info: dict[str, Any]) -> tuple[bool, str]:
    if not bool(info.get("signature_required", False)):
        return False, ""
    if bool(info.get("artifact_verified", False)):
        return False, ""
    reason = str(info.get("artifact_verification_reason") or "signed update metadata verification failed")
    return True, reason
