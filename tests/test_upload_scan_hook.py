# -*- coding: utf-8 -*-

import io


def _register_and_login(client, username: str):
    r = client.post(
        '/api/register',
        json={'username': username, 'password': 'Password123!', 'nickname': username},
    )
    assert r.status_code == 200
    login = client.post('/api/login', json={'username': username, 'password': 'Password123!'})
    assert login.status_code == 200


def _create_room(client) -> int:
    created = client.post('/api/rooms', json={'members': []})
    assert created.status_code == 200
    return int(created.json['room_id'])


def _png_bytes() -> bytes:
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 48


def test_upload_scan_unknown_provider_blocks(client):
    _register_and_login(client, 'scan_block')
    room_id = _create_room(client)
    client.application.config['UPLOAD_SCAN_ENABLED'] = True
    client.application.config['UPLOAD_SCAN_PROVIDER'] = 'unknown'

    response = client.post(
        '/api/upload',
        data={'room_id': str(room_id), 'file': (io.BytesIO(b'hello'), 'scan.txt')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 400


def test_upload_scan_noop_allows(client):
    _register_and_login(client, 'scan_allow')
    room_id = _create_room(client)
    client.application.config['UPLOAD_SCAN_ENABLED'] = True
    client.application.config['UPLOAD_SCAN_PROVIDER'] = 'noop'

    response = client.post(
        '/api/upload',
        data={'room_id': str(room_id), 'file': (io.BytesIO(b'hello'), 'scan-ok.txt')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 200
    assert response.json.get('upload_token')


def test_profile_upload_scan_unknown_provider_blocks(client):
    _register_and_login(client, 'scan_profile_block')
    client.application.config['UPLOAD_SCAN_ENABLED'] = True
    client.application.config['UPLOAD_SCAN_PROVIDER'] = 'unknown'

    response = client.post(
        '/api/profile/image',
        data={'file': (io.BytesIO(_png_bytes()), 'avatar.png')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 400
