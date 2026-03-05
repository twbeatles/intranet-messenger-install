# -*- coding: utf-8 -*-

from __future__ import annotations


def _register_and_login(client, username: str) -> int:
    register = client.post(
        '/api/register',
        json={'username': username, 'password': 'Password123!', 'nickname': username},
    )
    assert register.status_code == 200
    login = client.post('/api/login', json={'username': username, 'password': 'Password123!'})
    assert login.status_code == 200
    me = client.get('/api/me')
    assert me.status_code == 200
    return int(me.json['user']['id'])


def test_advanced_search_date_to_includes_end_of_day(app, client):
    from app.models import create_message, get_db

    user_id = _register_and_login(client, 'search_boundary_user')
    created = client.post('/api/rooms', json={'name': 'Boundary Room', 'members': []})
    assert created.status_code == 200
    room_id = int(created.json['room_id'])

    with app.app_context():
        message = create_message(room_id, user_id, 'boundary-target', 'text', encrypted=False)
        assert message is not None
        message_id = int(message['id'])
        conn = get_db()
        conn.execute(
            'UPDATE messages SET created_at = ? WHERE id = ?',
            ('2026-02-27 23:59:59', message_id),
        )
        conn.commit()

    response = client.post(
        '/api/search/advanced',
        json={
            'query': 'boundary-target',
            'room_id': room_id,
            'date_from': '2026-02-27',
            'date_to': '2026-02-27',
            'limit': 50,
            'offset': 0,
        },
    )
    assert response.status_code == 200
    payload = response.json or {}
    messages = payload.get('messages') or []
    assert any(int(m.get('id') or 0) == message_id for m in messages)
