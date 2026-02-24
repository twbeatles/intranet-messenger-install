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


def test_desktop_autologin_refresh_flow(app):
    client = app.test_client()
    _register(client, 'e2eautologin')

    created = client.post(
        '/api/device-sessions',
        json={
            'username': 'e2eautologin',
            'password': 'Password123!',
            'device_name': 'E2E Device',
            'remember': True,
        },
    )
    assert created.status_code == 200
    original_token = str(created.json.get('device_token') or '')
    assert original_token

    refreshed = client.post(
        '/api/device-sessions/refresh',
        json={'device_token': original_token},
        headers={'X-Device-Token': original_token},
    )
    assert refreshed.status_code == 200
    rotated_token = str(refreshed.json.get('device_token_rotated') or '')
    assert rotated_token
    assert rotated_token != original_token

    me = client.get('/api/me')
    assert me.status_code == 200
    assert me.json.get('logged_in') is True
    assert (me.json.get('user') or {}).get('username') == 'e2eautologin'


def test_desktop_socket_reconnect_flow(app):
    from app import socketio

    client = app.test_client()
    _register(client, 'e2ereconnect')
    login = client.post('/api/login', json={'username': 'e2ereconnect', 'password': 'Password123!'})
    assert login.status_code == 200

    create_room = client.post('/api/rooms', json={'name': 'Reconnect Room', 'members': []})
    assert create_room.status_code == 200
    room_id = int(create_room.json['room_id'])

    first = socketio.test_client(app, flask_test_client=client)
    assert first.is_connected()
    first.disconnect()

    second = socketio.test_client(app, flask_test_client=client)
    assert second.is_connected()
    try:
        second.emit(
            'send_message',
            {
                'room_id': room_id,
                'content': 'reconnect ok',
                'type': 'text',
                'encrypted': False,
            },
        )
        events = second.get_received()
        assert any(evt['name'] == 'new_message' for evt in events)
    finally:
        second.disconnect()


def test_desktop_startup_command_smoke(monkeypatch):
    import client.services.startup_manager as startup_manager

    monkeypatch.setattr(startup_manager.sys, 'frozen', False, raising=False)
    monkeypatch.setattr(startup_manager.sys, 'argv', ['launcher.py'])
    command = startup_manager.StartupManager._default_startup_command()
    assert isinstance(command, str)
    assert command.strip()
    assert ('-m client.main' in command) or command.lower().endswith('.exe"')
