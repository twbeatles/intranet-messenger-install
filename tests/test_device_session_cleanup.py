# -*- coding: utf-8 -*-

from app.auth_tokens import cleanup_stale_device_sessions
from app.models.base import get_db


def _register_and_login_device(client, username: str) -> dict:
    client.post(
        '/api/register',
        json={
            'username': username,
            'password': 'Password123!',
            'nickname': username,
        },
    )
    response = client.post(
        '/api/device-sessions',
        json={
            'username': username,
            'password': 'Password123!',
            'device_name': f'{username}-device',
            'remember': True,
        },
    )
    assert response.status_code == 200
    return response.json


def test_cleanup_stale_device_sessions_removes_old_revoked(client):
    payload = _register_and_login_device(client, 'cleanup_revoked')
    session_id = int(payload['device_session_id'])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE device_sessions
        SET revoked_at = '2000-01-01 00:00:00',
            expires_at = '2000-01-01 00:00:00'
        WHERE id = ?
        ''',
        (session_id,),
    )
    conn.commit()

    removed = cleanup_stale_device_sessions(revoked_grace_days=1, max_inactive_days=365)
    assert removed >= 1

    listing = client.get('/api/device-sessions')
    assert listing.status_code == 200
    assert listing.json.get('sessions') == []


def test_cleanup_stale_device_sessions_removes_long_inactive(client):
    payload = _register_and_login_device(client, 'cleanup_inactive')
    session_id = int(payload['device_session_id'])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE device_sessions
        SET last_used_at = '2000-01-01 00:00:00',
            expires_at = '2099-01-01 00:00:00',
            revoked_at = NULL
        WHERE id = ?
        ''',
        (session_id,),
    )
    conn.commit()

    removed = cleanup_stale_device_sessions(revoked_grace_days=365, max_inactive_days=1)
    assert removed >= 1

    listing = client.get('/api/device-sessions')
    assert listing.status_code == 200
    assert listing.json.get('sessions') == []
