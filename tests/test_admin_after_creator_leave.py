# -*- coding: utf-8 -*-

from __future__ import annotations


def _register(client, username: str, password: str = 'Password123!') -> None:
    response = client.post(
        '/api/register',
        json={
            'username': username,
            'password': password,
            'nickname': username,
        },
    )
    assert response.status_code == 200


def _login(client, username: str, password: str = 'Password123!') -> None:
    response = client.post('/api/login', json={'username': username, 'password': password})
    assert response.status_code == 200


def test_creator_loses_admin_control_after_leaving_room(client):
    _register(client, 'creator_guard')
    _register(client, 'member_guard_a')
    _register(client, 'member_guard_b')

    _login(client, 'creator_guard')
    users = client.get('/api/users').json
    user_a = next(u for u in users if u['username'] == 'member_guard_a')
    user_b = next(u for u in users if u['username'] == 'member_guard_b')

    created = client.post(
        '/api/rooms',
        json={'name': 'Creator Leave Guard', 'members': [user_a['id'], user_b['id']]},
    )
    assert created.status_code == 200
    room_id = int(created.json['room_id'])

    left = client.post(f'/api/rooms/{room_id}/leave')
    assert left.status_code == 200

    kick_attempt = client.delete(f'/api/rooms/{room_id}/members/{user_b["id"]}')
    assert kick_attempt.status_code == 403

    set_admin_attempt = client.post(
        f'/api/rooms/{room_id}/admins',
        json={'user_id': user_b['id'], 'is_admin': False},
    )
    assert set_admin_attempt.status_code == 403


def test_created_by_is_reassigned_to_remaining_member_after_creator_leave(client):
    _register(client, 'creator_reassign')
    _register(client, 'member_reassign_a')
    _register(client, 'member_reassign_b')

    _login(client, 'creator_reassign')
    users = client.get('/api/users').json
    user_a = next(u for u in users if u['username'] == 'member_reassign_a')
    user_b = next(u for u in users if u['username'] == 'member_reassign_b')

    created = client.post(
        '/api/rooms',
        json={'name': 'Creator Reassign', 'members': [user_a['id'], user_b['id']]},
    )
    assert created.status_code == 200
    room_id = int(created.json['room_id'])

    left = client.post(f'/api/rooms/{room_id}/leave')
    assert left.status_code == 200

    # login as the lowest remaining user_id (member_reassign_a) and verify admin ownership
    client.post('/api/logout')
    _login(client, 'member_reassign_a')
    admin_check = client.get(f'/api/rooms/{room_id}/admin-check')
    assert admin_check.status_code == 200
    assert bool(admin_check.json.get('is_admin')) is True
