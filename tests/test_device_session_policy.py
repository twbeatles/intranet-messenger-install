# -*- coding: utf-8 -*-

from datetime import datetime

from config import DEVICE_SESSION_SHORT_TTL_DAYS, DEVICE_SESSION_TTL_DAYS


def _register(client, username: str):
    response = client.post(
        '/api/register',
        json={
            'username': username,
            'password': 'Password123!',
            'nickname': username,
        },
    )
    assert response.status_code == 200


def test_device_session_refresh_preserves_short_ttl_policy(client):
    _register(client, 'ttl_short_user')

    created = client.post(
        '/api/device-sessions',
        json={
            'username': 'ttl_short_user',
            'password': 'Password123!',
            'device_name': 'short-device',
            'remember': False,
        },
    )
    assert created.status_code == 200
    assert created.json.get('remember') is False
    token = created.json['device_token']

    refreshed = client.post(
        '/api/device-sessions/refresh',
        json={'device_token': token},
        headers={'X-Device-Token': token},
    )
    assert refreshed.status_code == 200
    assert refreshed.json.get('remember') is False

    listed = client.get('/api/device-sessions')
    assert listed.status_code == 200
    sessions = listed.json.get('sessions') or []
    assert len(sessions) == 1
    assert int(sessions[0].get('ttl_days') or 0) == int(DEVICE_SESSION_SHORT_TTL_DAYS)
    assert bool(sessions[0].get('remember')) is False


def test_device_session_refresh_preserves_long_ttl_policy(client):
    _register(client, 'ttl_long_user')

    created = client.post(
        '/api/device-sessions',
        json={
            'username': 'ttl_long_user',
            'password': 'Password123!',
            'device_name': 'long-device',
            'remember': True,
        },
    )
    assert created.status_code == 200
    assert created.json.get('remember') is True
    token = created.json['device_token']

    refreshed = client.post(
        '/api/device-sessions/refresh',
        json={'device_token': token},
        headers={'X-Device-Token': token},
    )
    assert refreshed.status_code == 200
    assert refreshed.json.get('remember') is True

    listed = client.get('/api/device-sessions')
    assert listed.status_code == 200
    sessions = listed.json.get('sessions') or []
    assert len(sessions) == 1
    assert int(sessions[0].get('ttl_days') or 0) == int(DEVICE_SESSION_TTL_DAYS)
    assert bool(sessions[0].get('remember')) is True

    expires_at = datetime.strptime(str(sessions[0]['expires_at']), '%Y-%m-%d %H:%M:%S')
    assert expires_at > datetime.now()
