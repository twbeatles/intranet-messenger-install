# -*- coding: utf-8 -*-
"""
Device session token management for desktop clients.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.models.base import get_db


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _fmt_ts(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def issue_device_session(
    user_id: int,
    device_name: str,
    ip: str = '',
    user_agent: str = '',
    ttl_days: int = 30,
    remember: bool = True,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Issue a new device token and store only its hash."""
    conn = get_db()
    cursor = conn.cursor()

    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    now = _now_utc()
    expires_at = now + timedelta(days=max(1, int(ttl_days)))
    normalized_device_id = (device_id or uuid.uuid4().hex).strip()[:64]
    normalized_name = (device_name or 'Desktop').strip()[:120]

    cursor.execute(
        '''
        INSERT INTO device_sessions (
            user_id, device_id, token_hash, device_name, created_at,
            last_used_at, expires_at, revoked_at, ip, user_agent, remember, ttl_days
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
        ''',
        (
            user_id,
            normalized_device_id,
            token_hash,
            normalized_name,
            _fmt_ts(now),
            _fmt_ts(now),
            _fmt_ts(expires_at),
            (ip or '')[:64],
            (user_agent or '')[:500],
            1 if remember else 0,
            max(1, int(ttl_days)),
        ),
    )
    session_id = cursor.lastrowid
    conn.commit()

    return {
        'device_token': raw_token,
        'session_id': session_id,
        'device_id': normalized_device_id,
        'expires_at': _fmt_ts(expires_at),
        'remember': bool(remember),
        'ttl_days': max(1, int(ttl_days)),
    }


def get_device_session_by_token(token: str) -> dict[str, Any] | None:
    """Resolve token to an active, non-expired session row."""
    if not token:
        return None

    conn = get_db()
    cursor = conn.cursor()
    now = _fmt_ts(_now_utc())
    cursor.execute(
        '''
        SELECT *
        FROM device_sessions
        WHERE token_hash = ?
          AND revoked_at IS NULL
          AND expires_at > ?
        LIMIT 1
        ''',
        (_hash_token(token), now),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def touch_device_session(session_id: int, ip: str = '', user_agent: str = '') -> None:
    """Update last-used metadata."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE device_sessions
        SET last_used_at = ?, ip = ?, user_agent = ?
        WHERE id = ?
        ''',
        (_fmt_ts(_now_utc()), (ip or '')[:64], (user_agent or '')[:500], session_id),
    )
    conn.commit()


def revoke_device_session_by_token(token: str) -> bool:
    """Revoke the active device session by raw token."""
    if not token:
        return False

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE device_sessions
        SET revoked_at = ?
        WHERE token_hash = ?
          AND revoked_at IS NULL
        ''',
        (_fmt_ts(_now_utc()), _hash_token(token)),
    )
    conn.commit()
    return cursor.rowcount > 0


def revoke_device_session_by_id(user_id: int, session_id: int) -> bool:
    """Revoke a specific device session owned by user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE device_sessions
        SET revoked_at = ?
        WHERE id = ?
          AND user_id = ?
          AND revoked_at IS NULL
        ''',
        (_fmt_ts(_now_utc()), session_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def rotate_device_session_token(
    token: str,
    ip: str = '',
    user_agent: str = '',
    ttl_days: int = 30,
) -> dict[str, Any] | None:
    """Rotate token: revoke old one immediately and issue a new one."""
    current = get_device_session_by_token(token)
    if not current:
        return None

    # Revoke old token first.
    if not revoke_device_session_by_token(token):
        return None

    issued = issue_device_session(
        user_id=current['user_id'],
        device_name=current.get('device_name') or 'Desktop',
        ip=ip,
        user_agent=user_agent,
        ttl_days=int(current.get('ttl_days') or ttl_days or 30),
        remember=bool(current.get('remember', 1)),
        device_id=current.get('device_id'),
    )
    return {
        **issued,
        'user_id': current['user_id'],
    }


def list_active_device_sessions(user_id: int) -> list[dict[str, Any]]:
    """List non-revoked sessions for the user, including expired status."""
    conn = get_db()
    cursor = conn.cursor()
    now = _fmt_ts(_now_utc())
    cursor.execute(
        '''
        SELECT id, user_id, device_id, device_name, created_at, last_used_at,
               expires_at, ip, user_agent, remember, ttl_days,
               CASE WHEN expires_at <= ? THEN 1 ELSE 0 END AS is_expired
        FROM device_sessions
        WHERE user_id = ?
          AND revoked_at IS NULL
        ORDER BY last_used_at DESC, id DESC
        ''',
        (now, user_id),
    )
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


def cleanup_stale_device_sessions(
    *,
    revoked_grace_days: int = 30,
    max_inactive_days: int = 90,
) -> int:
    """
    Purge long-retained device sessions to keep table size bounded.

    Removal targets:
    - revoked sessions older than revoked_grace_days
    - expired sessions
    - very old inactive sessions (last_used_at older than max_inactive_days)
    """
    conn = get_db()
    cursor = conn.cursor()
    now = _now_utc()
    revoked_cutoff = now - timedelta(days=max(1, int(revoked_grace_days)))
    inactive_cutoff = now - timedelta(days=max(1, int(max_inactive_days)))
    cursor.execute(
        '''
        DELETE FROM device_sessions
        WHERE (revoked_at IS NOT NULL AND revoked_at < ?)
           OR (expires_at <= ?)
           OR (last_used_at < ?)
        ''',
        (
            _fmt_ts(revoked_cutoff),
            _fmt_ts(now),
            _fmt_ts(inactive_cutoff),
        ),
    )
    removed = int(cursor.rowcount or 0)
    conn.commit()
    return removed
