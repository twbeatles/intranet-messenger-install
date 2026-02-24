# -*- coding: utf-8 -*-

import io


def _register(client, username: str, password: str = 'Password123!'):
    return client.post(
        '/api/register',
        json={'username': username, 'password': password, 'nickname': username},
    )


def _login(client, username: str, password: str = 'Password123!'):
    return client.post('/api/login', json={'username': username, 'password': password})


def test_upload_response_includes_file_type_and_upload_token(client):
    _register(client, 'upload_contract_u1')
    _register(client, 'upload_contract_u2')

    assert _login(client, 'upload_contract_u1').status_code == 200

    users = client.get('/api/users').json
    u2 = next(u for u in users if u['username'] == 'upload_contract_u2')

    created = client.post('/api/rooms', json={'members': [u2['id']]})
    assert created.status_code == 200
    room_id = created.json['room_id']

    file_content = io.BytesIO(b'hello contract')
    response = client.post(
        '/api/upload',
        data={'room_id': str(room_id), 'file': (file_content, 'contract.txt')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 200
    payload = response.json
    assert payload['success'] is True
    assert payload.get('upload_token')
    assert payload.get('file_type') == 'file'

