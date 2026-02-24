# -*- coding: utf-8 -*-
"""
E2E crypto compatibility helpers.

Supports:
- v2: PBKDF2-SHA256 + AES-CBC + HMAC-SHA256
- v1: OpenSSL/CryptoJS salted format (U2FsdGVkX...)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256


class CryptoError(RuntimeError):
    pass


def _pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _pkcs7_unpad(data: bytes, block_size: int = 16) -> bytes:
    if not data or len(data) % block_size != 0:
        raise CryptoError('invalid padded block length')
    pad_len = data[-1]
    if pad_len < 1 or pad_len > block_size:
        raise CryptoError('invalid padding value')
    if data[-pad_len:] != bytes([pad_len] * pad_len):
        raise CryptoError('invalid padding bytes')
    return data[:-pad_len]


@dataclass(frozen=True)
class V2Keys:
    enc_key: bytes
    mac_key: bytes


def derive_v2_keys(passphrase: str, salt: bytes, iterations: int = 10000) -> V2Keys:
    if not isinstance(passphrase, str) or not passphrase:
        raise CryptoError('passphrase is required')
    if len(salt) != 16:
        raise CryptoError('salt must be 16 bytes')

    derived = PBKDF2(
        password=passphrase.encode('utf-8'),
        salt=salt,
        dkLen=64,
        count=iterations,
        hmac_hash_module=SHA256,
    )
    return V2Keys(enc_key=derived[:32], mac_key=derived[32:])


def encrypt_v2(plaintext: str, passphrase: str) -> str:
    if plaintext is None:
        plaintext = ''
    salt = os.urandom(16)
    iv = os.urandom(16)
    keys = derive_v2_keys(passphrase, salt)
    cipher = AES.new(keys.enc_key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(_pkcs7_pad(plaintext.encode('utf-8')))

    mac_data = salt + iv + ciphertext
    mac = hmac.new(keys.mac_key, mac_data, hashlib.sha256).digest()

    return 'v2:{salt}:{iv}:{ct}:{mac}'.format(
        salt=base64.b64encode(salt).decode('ascii'),
        iv=base64.b64encode(iv).decode('ascii'),
        ct=base64.b64encode(ciphertext).decode('ascii'),
        mac=base64.b64encode(mac).decode('ascii'),
    )


def decrypt_v2(payload: str, passphrase: str) -> str:
    try:
        _, salt_b64, iv_b64, ct_b64, mac_b64 = payload.split(':', 4)
    except ValueError as exc:
        raise CryptoError('invalid v2 payload format') from exc

    salt = base64.b64decode(salt_b64)
    iv = base64.b64decode(iv_b64)
    ciphertext = base64.b64decode(ct_b64)
    mac = base64.b64decode(mac_b64)

    keys = derive_v2_keys(passphrase, salt)
    expected = hmac.new(keys.mac_key, salt + iv + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, mac):
        raise CryptoError('v2 hmac verification failed')

    cipher = AES.new(keys.enc_key, AES.MODE_CBC, iv)
    plaintext = _pkcs7_unpad(cipher.decrypt(ciphertext))
    return plaintext.decode('utf-8')


def _evp_bytes_to_key(password: bytes, salt: bytes, key_len: int = 32, iv_len: int = 16) -> tuple[bytes, bytes]:
    """OpenSSL EVP_BytesToKey (MD5, 1 iteration)."""
    d = b''
    result = b''
    while len(result) < (key_len + iv_len):
        d = hashlib.md5(d + password + salt).digest()
        result += d
    return result[:key_len], result[key_len:key_len + iv_len]


def encrypt_v1_compat(plaintext: str, passphrase: str) -> str:
    """Produce OpenSSL-compatible salted payload for tests/compat."""
    if plaintext is None:
        plaintext = ''
    salt = os.urandom(8)
    key, iv = _evp_bytes_to_key(passphrase.encode('utf-8'), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(_pkcs7_pad(plaintext.encode('utf-8')))
    data = b'Salted__' + salt + ciphertext
    return base64.b64encode(data).decode('ascii')


def decrypt_v1_compat(ciphertext_b64: str, passphrase: str) -> str:
    raw = base64.b64decode(ciphertext_b64)
    if not raw.startswith(b'Salted__') or len(raw) < 16:
        raise CryptoError('invalid v1 payload')
    salt = raw[8:16]
    ciphertext = raw[16:]
    key, iv = _evp_bytes_to_key(passphrase.encode('utf-8'), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return _pkcs7_unpad(cipher.decrypt(ciphertext)).decode('utf-8')


def encrypt_message(plaintext: str, room_key: str) -> str:
    return encrypt_v2(plaintext, room_key)


def decrypt_message(ciphertext: str, room_key: str) -> str:
    if not isinstance(ciphertext, str) or not ciphertext:
        return ''
    if ciphertext.startswith('v2:'):
        return decrypt_v2(ciphertext, room_key)
    if ciphertext.startswith('U2FsdGVkX'):
        return decrypt_v1_compat(ciphertext, room_key)
    return ciphertext

