# -*- coding: utf-8 -*-

from __future__ import annotations

from client.app_controller import MessengerAppController


def test_verify_update_metadata_requires_signature_when_flagged():
    ok, reason = MessengerAppController._verify_update_metadata({'signature_required': True})
    assert ok is False
    assert 'required' in reason


def test_unsigned_update_gate_blocks_when_required_and_not_verified():
    blocked, reason = MessengerAppController._should_block_unsigned_update(
        {
            'signature_required': True,
            'artifact_verified': False,
            'artifact_verification_reason': 'artifact_signature is missing',
        }
    )
    assert blocked is True
    assert 'missing' in reason


def test_unsigned_update_gate_allows_when_signature_not_required():
    blocked, reason = MessengerAppController._should_block_unsigned_update(
        {
            'signature_required': False,
            'artifact_verified': False,
        }
    )
    assert blocked is False
    assert reason == ''
