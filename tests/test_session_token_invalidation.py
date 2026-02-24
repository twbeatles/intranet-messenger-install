# -*- coding: utf-8 -*-


def test_password_change_invalidates_other_logged_in_sessions(app):
    client_a = app.test_client()
    client_b = app.test_client()

    register = client_a.post(
        '/api/register',
        json={
            'username': 'token_guard_user',
            'password': 'Password123!',
            'nickname': 'Token Guard',
        },
    )
    assert register.status_code == 200

    login_a = client_a.post('/api/login', json={'username': 'token_guard_user', 'password': 'Password123!'})
    login_b = client_b.post('/api/login', json={'username': 'token_guard_user', 'password': 'Password123!'})
    assert login_a.status_code == 200
    assert login_b.status_code == 200

    change = client_a.put(
        '/api/me/password',
        json={
            'current_password': 'Password123!',
            'new_password': 'Password456!',
        },
    )
    assert change.status_code == 200
    assert change.json.get('success') is True

    still_valid = client_a.get('/api/users')
    assert still_valid.status_code == 200

    invalidated = client_b.get('/api/users')
    assert invalidated.status_code == 401
    assert '세션이 만료' in str(invalidated.json.get('error') or '')
