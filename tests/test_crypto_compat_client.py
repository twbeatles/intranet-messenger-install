# -*- coding: utf-8 -*-

from client.services.crypto_compat import (
    decrypt_message,
    decrypt_v1_compat,
    decrypt_v2,
    encrypt_message,
    encrypt_v1_compat,
    encrypt_v2,
)


def test_v2_roundtrip():
    key = 'room-secret-key'
    plaintext = 'hello v2 message'
    payload = encrypt_v2(plaintext, key)
    assert payload.startswith('v2:')
    decoded = decrypt_v2(payload, key)
    assert decoded == plaintext


def test_v1_roundtrip():
    key = 'legacy-key'
    plaintext = 'hello v1 message'
    payload = encrypt_v1_compat(plaintext, key)
    assert payload.startswith('U2FsdGVkX')
    decoded = decrypt_v1_compat(payload, key)
    assert decoded == plaintext


def test_decrypt_message_auto_detect():
    key = 'detect-key'
    plain = 'direct text'
    assert decrypt_message(plain, key) == plain

    v1 = encrypt_v1_compat('legacy', key)
    assert decrypt_message(v1, key) == 'legacy'

    v2 = encrypt_message('modern', key)
    assert decrypt_message(v2, key) == 'modern'

