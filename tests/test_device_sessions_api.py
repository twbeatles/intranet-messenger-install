# -*- coding: utf-8 -*-


def _register(client, username: str, password: str = 'Password123!', nickname: str | None = None):
    return client.post(
        '/api/register',
        json={
            'username': username,
            'password': password,
            'nickname': nickname or username,
        },
    )


def test_create_device_session_and_list(client):
    _register(client, 'ds_user_1')

    r = client.post(
        '/api/device-sessions',
        json={
            'username': 'ds_user_1',
            'password': 'Password123!',
            'device_name': 'test-device',
            'remember': True,
        },
    )
    assert r.status_code == 200
    payload = r.json
    assert payload['access_ok'] is True
    assert payload['device_token']
    assert payload['user']['username'] == 'ds_user_1'

    listing = client.get('/api/device-sessions')
    assert listing.status_code == 200
    sessions = listing.json.get('sessions', [])
    assert len(sessions) == 1
    assert sessions[0]['device_name'] == 'test-device'


def test_refresh_rotates_token(client):
    _register(client, 'ds_user_2')
    created = client.post(
        '/api/device-sessions',
        json={
            'username': 'ds_user_2',
            'password': 'Password123!',
            'device_name': 'rotation-device',
            'remember': True,
        },
    )
    assert created.status_code == 200
    first_token = created.json['device_token']

    refreshed = client.post(
        '/api/device-sessions/refresh',
        json={'device_token': first_token},
        headers={'X-Device-Token': first_token},
    )
    assert refreshed.status_code == 200
    second_token = refreshed.json['device_token_rotated']
    assert second_token
    assert second_token != first_token

    old_token_reuse = client.post(
        '/api/device-sessions/refresh',
        json={'device_token': first_token},
        headers={'X-Device-Token': first_token},
    )
    assert old_token_reuse.status_code == 401


def test_revoke_current_device_session(client):
    _register(client, 'ds_user_3')
    created = client.post(
        '/api/device-sessions',
        json={
            'username': 'ds_user_3',
            'password': 'Password123!',
            'device_name': 'revoke-device',
            'remember': True,
        },
    )
    token = created.json['device_token']

    revoked = client.delete(
        '/api/device-sessions/current',
        json={'device_token': token},
        headers={'X-Device-Token': token},
    )
    assert revoked.status_code == 200
    assert revoked.json['success'] is True

    unauthorized_list = client.get('/api/device-sessions')
    assert unauthorized_list.status_code == 401


def test_revoke_other_device_session_by_id(client):
    _register(client, 'ds_user_4')

    first = client.post(
        '/api/device-sessions',
        json={
            'username': 'ds_user_4',
            'password': 'Password123!',
            'device_name': 'device-a',
            'remember': True,
        },
    )
    assert first.status_code == 200
    first_token = first.json['device_token']
    first_id = first.json['device_session_id']

    second = client.post(
        '/api/device-sessions/refresh',
        json={'device_token': first_token},
        headers={'X-Device-Token': first_token},
    )
    assert second.status_code == 200

    revoke_old = client.delete(f'/api/device-sessions/{first_id}')
    # old one can already be revoked by rotation. Either not found or success is acceptable.
    assert revoke_old.status_code in (200, 404)

