# -*- coding: utf-8 -*-


def _register(client, username: str, nickname: str):
    response = client.post(
        '/api/register',
        json={
            'username': username,
            'password': 'Password123!',
            'nickname': nickname,
        },
    )
    assert response.status_code == 200


def test_admin_update_requires_boolean_is_admin(client):
    _register(client, 'admin_bool_owner', 'Owner')
    _register(client, 'admin_bool_target', 'Target')

    login = client.post('/api/login', json={'username': 'admin_bool_owner', 'password': 'Password123!'})
    assert login.status_code == 200

    users = client.get('/api/users')
    assert users.status_code == 200
    target = next((u for u in (users.json or []) if u.get('username') == 'admin_bool_target'), None)
    assert target is not None
    target_id = int(target['id'])

    created = client.post('/api/rooms', json={'name': 'Admin Bool Room', 'members': [target_id]})
    assert created.status_code == 200
    room_id = int(created.json['room_id'])

    promote = client.post(
        f'/api/rooms/{room_id}/admins',
        json={
            'user_id': target_id,
            'is_admin': True,
        },
    )
    assert promote.status_code == 200

    invalid_demote = client.post(
        f'/api/rooms/{room_id}/admins',
        json={
            'user_id': target_id,
            'is_admin': 'false',
        },
    )
    assert invalid_demote.status_code == 400
    assert 'boolean' in str(invalid_demote.json.get('error') or '').lower()

    admins = client.get(f'/api/rooms/{room_id}/admins')
    assert admins.status_code == 200
    target_admin = next((a for a in (admins.json or []) if int(a.get('id') or 0) == target_id), None)
    assert target_admin is not None
    assert str(target_admin.get('role') or '') == 'admin'
