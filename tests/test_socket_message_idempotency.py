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


def test_send_message_is_idempotent_by_client_msg_id(app):
    from app import socketio

    client = app.test_client()
    _register(client, 'idem_owner')
    _register(client, 'idem_peer')
    _login(client, 'idem_owner')

    users = client.get('/api/users').json
    peer = next(u for u in users if u['username'] == 'idem_peer')
    created = client.post('/api/rooms', json={'name': 'Idempotency', 'members': [peer['id']]})
    assert created.status_code == 200
    room_id = int(created.json['room_id'])

    socket_client = socketio.test_client(app, flask_test_client=client)
    assert socket_client.is_connected()
    socket_client.get_received()

    payload = {
        'room_id': room_id,
        'content': 'idempotent hello',
        'type': 'text',
        'encrypted': False,
        'client_msg_id': 'same-client-msg-id',
    }

    first_ack = socket_client.emit('send_message', payload, callback=True)
    first_events = socket_client.get_received()
    second_ack = socket_client.emit('send_message', payload, callback=True)
    second_events = socket_client.get_received()

    assert first_ack.get('ok') is True
    assert second_ack.get('ok') is True
    assert int(first_ack.get('message_id') or 0) > 0
    assert first_ack.get('message_id') == second_ack.get('message_id')

    # Duplicate retry should not trigger another new_message broadcast.
    assert any(evt['name'] == 'new_message' for evt in first_events)
    assert not any(evt['name'] == 'new_message' for evt in second_events)

    messages_resp = client.get(f'/api/rooms/{room_id}/messages')
    assert messages_resp.status_code == 200
    messages = messages_resp.json.get('messages') or []
    matched = [m for m in messages if str(m.get('client_msg_id') or '') == 'same-client-msg-id']
    assert len(matched) == 1

    socket_client.disconnect()
