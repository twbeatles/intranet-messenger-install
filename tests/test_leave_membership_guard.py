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


def test_leave_requires_membership_and_emits_nothing_for_non_member(app):
    from app import socketio

    owner_client = app.test_client()
    outsider_client = app.test_client()

    _register(owner_client, 'leave_owner')
    _register(owner_client, 'leave_peer')
    _register(owner_client, 'leave_outsider')

    _login(owner_client, 'leave_owner')
    users = owner_client.get('/api/users').json
    peer = next(u for u in users if u['username'] == 'leave_peer')
    room = owner_client.post('/api/rooms', json={'name': 'Leave Guard', 'members': [peer['id']]})
    assert room.status_code == 200
    room_id = int(room.json['room_id'])

    owner_socket = socketio.test_client(app, flask_test_client=owner_client)
    assert owner_socket.is_connected()
    owner_socket.get_received()

    _login(outsider_client, 'leave_outsider')
    leave_response = outsider_client.post(f'/api/rooms/{room_id}/leave')
    assert leave_response.status_code == 403

    events = owner_socket.get_received()
    assert not any(evt['name'] in ('room_members_updated', 'room_updated') for evt in events)
    owner_socket.disconnect()
