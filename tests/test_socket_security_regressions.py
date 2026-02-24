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


def _create_room(client, name: str) -> int:
    response = client.post('/api/rooms', json={'name': name, 'members': []})
    assert response.status_code == 200
    return int(response.json['room_id'])


def _socket_client(app, flask_client):
    from app import socketio

    return socketio.test_client(app, flask_test_client=flask_client)


def test_socket_connect_requires_authenticated_session(app):
    client = app.test_client()
    sc = _socket_client(app, client)
    assert not sc.is_connected()


def test_cross_room_reply_to_is_rejected(app):
    client = app.test_client()
    _register(client, 'replyguard')
    _login(client, 'replyguard')

    room_a = _create_room(client, 'Room A')
    room_b = _create_room(client, 'Room B')

    sc = _socket_client(app, client)
    assert sc.is_connected()
    try:
        sc.emit(
            'send_message',
            {
                'room_id': room_a,
                'content': 'origin',
                'type': 'text',
                'encrypted': False,
            },
        )
        received = sc.get_received()
        message_events = [evt for evt in received if evt['name'] == 'new_message']
        assert message_events
        origin_id = int(message_events[-1]['args'][0]['id'])

        sc.emit(
            'send_message',
            {
                'room_id': room_b,
                'content': 'invalid reply',
                'type': 'text',
                'reply_to': origin_id,
                'encrypted': False,
            },
        )
        blocked = sc.get_received()
        errors = [evt for evt in blocked if evt['name'] == 'error']
        assert errors
        assert any('잘못된 요청' in str(evt['args'][0].get('message') or '') for evt in errors)
        assert not any(
            evt['name'] == 'new_message' and int((evt['args'][0] or {}).get('room_id') or 0) == room_b
            for evt in blocked
        )
    finally:
        sc.disconnect()


def test_reply_preview_never_joins_other_room_message(app):
    from app.models import create_message

    client = app.test_client()
    _register(client, 'replyjoin')
    _login(client, 'replyjoin')

    me = client.get('/api/me').json['user']
    user_id = int(me['id'])
    room_a = _create_room(client, 'Join A')
    room_b = _create_room(client, 'Join B')

    with app.app_context():
        origin = create_message(room_a, user_id, 'origin-room-a', 'text', encrypted=False)
        assert origin
        created = create_message(room_b, user_id, 'child-room-b', 'text', reply_to=int(origin['id']), encrypted=False)
        assert created

    response = client.get(f'/api/rooms/{room_b}/messages')
    assert response.status_code == 200
    messages = response.json['messages']
    target = next(msg for msg in messages if msg.get('content') == 'child-room-b')
    assert target.get('reply_content') in (None, '')
    assert target.get('reply_sender') in (None, '')


def test_message_read_room_mismatch_is_rejected(app):
    client = app.test_client()
    _register(client, 'readguard')
    _login(client, 'readguard')

    room_a = _create_room(client, 'Read A')
    room_b = _create_room(client, 'Read B')

    sc = _socket_client(app, client)
    assert sc.is_connected()
    try:
        sc.emit(
            'send_message',
            {
                'room_id': room_a,
                'content': 'message in room a',
                'type': 'text',
                'encrypted': False,
            },
        )
        received = sc.get_received()
        message_events = [evt for evt in received if evt['name'] == 'new_message']
        assert message_events
        message_id = int(message_events[-1]['args'][0]['id'])

        sc.emit('message_read', {'room_id': room_b, 'message_id': message_id})
        blocked = sc.get_received()
        assert any(evt['name'] == 'error' for evt in blocked)
        assert not any(evt['name'] == 'read_updated' for evt in blocked)
    finally:
        sc.disconnect()


def test_rest_room_rename_emits_socket_event(app):
    client = app.test_client()
    _register(client, 'renamebridge')
    _login(client, 'renamebridge')

    room_id = _create_room(client, 'Before Rename')
    sc = _socket_client(app, client)
    assert sc.is_connected()
    try:
        sc.get_received()
        response = client.put(f'/api/rooms/{room_id}/name', json={'name': 'After Rename'})
        assert response.status_code == 200

        events = sc.get_received()
        assert any(evt['name'] == 'room_name_updated' for evt in events)
    finally:
        sc.disconnect()


def test_client_cannot_send_system_message_type(app):
    client = app.test_client()
    _register(client, 'systemguard')
    _login(client, 'systemguard')

    room_id = _create_room(client, 'System Guard Room')
    sc = _socket_client(app, client)
    assert sc.is_connected()
    try:
        ack = sc.emit(
            'send_message',
            {
                'room_id': room_id,
                'content': 'fake system',
                'type': 'system',
                'encrypted': False,
            },
            callback=True,
        )
        assert isinstance(ack, dict)
        assert ack.get('ok') is False
        assert '잘못된 요청' in str(ack.get('error') or '')

        events = sc.get_received()
        assert any(evt['name'] == 'error' for evt in events)
        assert not any(evt['name'] == 'new_message' for evt in events)
    finally:
        sc.disconnect()


def test_room_updated_not_emitted_to_unrelated_user(app):
    from app import socketio

    owner_client = app.test_client()
    outsider_client = app.test_client()

    _register(owner_client, 'roomscope_owner')
    _register(owner_client, 'roomscope_member')
    _register(owner_client, 'roomscope_outsider')

    _login(owner_client, 'roomscope_owner')
    users = owner_client.get('/api/users').json
    member = next(u for u in users if u['username'] == 'roomscope_member')
    created = owner_client.post('/api/rooms', json={'name': 'Scope Room', 'members': [member['id']]})
    assert created.status_code == 200
    room_id = int(created.json['room_id'])

    owner_socket = socketio.test_client(app, flask_test_client=owner_client)
    assert owner_socket.is_connected()
    owner_socket.get_received()

    _login(outsider_client, 'roomscope_outsider')
    outsider_socket = socketio.test_client(app, flask_test_client=outsider_client)
    assert outsider_socket.is_connected()
    outsider_socket.get_received()

    rename = owner_client.put(f'/api/rooms/{room_id}/name', json={'name': 'Scope Room Renamed'})
    assert rename.status_code == 200

    owner_events = owner_socket.get_received()
    outsider_events = outsider_socket.get_received()
    assert any(evt['name'] == 'room_updated' for evt in owner_events)
    assert not any(evt['name'] == 'room_updated' for evt in outsider_events)

    owner_socket.disconnect()
    outsider_socket.disconnect()
