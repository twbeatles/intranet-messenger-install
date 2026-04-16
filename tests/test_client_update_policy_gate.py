# -*- coding: utf-8 -*-

from __future__ import annotations

from client.controllers.update_policy import should_block_unsigned_update, verify_update_metadata


def test_verify_update_metadata_requires_signature_when_flagged():
    ok, reason = verify_update_metadata({"signature_required": True})
    assert ok is False
    assert "required" in reason


def test_unsigned_update_gate_blocks_when_required_and_not_verified():
    blocked, reason = should_block_unsigned_update(
        {
            "signature_required": True,
            "artifact_verified": False,
            "artifact_verification_reason": "artifact_signature is missing",
        }
    )
    assert blocked is True
    assert "missing" in reason


def test_unsigned_update_gate_allows_when_signature_not_required():
    blocked, reason = should_block_unsigned_update(
        {
            "signature_required": False,
            "artifact_verified": False,
        }
    )
    assert blocked is False
    assert reason == ""
