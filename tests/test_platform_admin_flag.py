# -*- coding: utf-8 -*-

from __future__ import annotations


def _register(client, username: str, password: str = 'Password123!'):
    response = client.post(
        '/api/register',
        json={'username': username, 'password': password, 'nickname': username},
    )
    assert response.status_code == 200


def _login(client, username: str, password: str = 'Password123!'):
    response = client.post('/api/login', json={'username': username, 'password': password})
    assert response.status_code == 200


def test_first_user_bootstrapped_as_platform_admin(app, client):
    from app.models import get_db

    _register(client, 'platform_owner')
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT is_platform_admin FROM users WHERE username = ?', ('platform_owner',))
        row = cursor.fetchone()
        assert row is not None
        assert int(row['is_platform_admin'] or 0) == 1


def test_platform_admin_approval_uses_flag_not_user_id(app, client):
    from app.models import get_db

    _register(client, 'platform_owner')      # first user, auto-admin initially
    _register(client, 'platform_delegate')   # will become admin by flag
    _register(client, 'platform_target')

    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_platform_admin = 0 WHERE username = ?', ('platform_owner',))
        cursor.execute('UPDATE users SET is_platform_admin = 1 WHERE username = ?', ('platform_delegate',))
        cursor.execute('SELECT id FROM users WHERE username = ?', ('platform_target',))
        target_id = int(cursor.fetchone()['id'])
        conn.commit()

    _login(client, 'platform_owner')
    denied = client.post('/api/admin/users/approve', json={'user_id': target_id, 'action': 'approve'})
    assert denied.status_code == 403

    client.post('/api/logout')
    _login(client, 'platform_delegate')
    allowed = client.post('/api/admin/users/approve', json={'user_id': target_id, 'action': 'approve'})
    assert allowed.status_code == 200
    assert allowed.json.get('success') is True
