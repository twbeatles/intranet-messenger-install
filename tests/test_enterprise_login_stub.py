# -*- coding: utf-8 -*-


def _register(client, username: str, password: str = 'Password123!'):
    response = client.post(
        '/api/register',
        json={'username': username, 'password': password, 'nickname': username},
    )
    assert response.status_code == 200


def test_enterprise_login_disabled_by_default(client):
    response = client.post('/api/auth/enterprise-login', json={'username': 'u', 'password': 'p'})
    assert response.status_code == 501


def test_enterprise_login_requires_provider_when_enabled(client):
    client.application.config['ENTERPRISE_AUTH_ENABLED'] = True
    client.application.config['ENTERPRISE_AUTH_PROVIDER'] = ''
    response = client.post('/api/auth/enterprise-login', json={'username': 'u', 'password': 'p'})
    assert response.status_code == 400


def test_enterprise_login_unknown_provider_returns_501(client):
    client.application.config['ENTERPRISE_AUTH_ENABLED'] = True
    client.application.config['ENTERPRISE_AUTH_PROVIDER'] = 'ldap'
    response = client.post('/api/auth/enterprise-login', json={'username': 'u', 'password': 'p'})
    assert response.status_code == 501


def test_enterprise_login_mock_success_with_existing_local_account(client):
    _register(client, 'ent_local')
    client.application.config['ENTERPRISE_AUTH_ENABLED'] = True
    client.application.config['ENTERPRISE_AUTH_PROVIDER'] = 'mock'
    client.application.config['ENTERPRISE_MOCK_USERS'] = {'ent_local': 'ent-pass'}

    response = client.post(
        '/api/auth/enterprise-login',
        json={'username': 'ent_local', 'password': 'ent-pass'},
    )
    assert response.status_code == 200
    payload = response.json
    assert payload['success'] is True
    assert payload['provider'] == 'mock'
    assert payload['user']['username'] == 'ent_local'
    assert payload.get('csrf_token')


def test_enterprise_login_mock_rejects_bad_credentials(client):
    _register(client, 'ent_bad')
    client.application.config['ENTERPRISE_AUTH_ENABLED'] = True
    client.application.config['ENTERPRISE_AUTH_PROVIDER'] = 'mock'
    client.application.config['ENTERPRISE_MOCK_USERS'] = {'ent_bad': 'correct-pass'}

    response = client.post(
        '/api/auth/enterprise-login',
        json={'username': 'ent_bad', 'password': 'wrong-pass'},
    )
    assert response.status_code == 401


def test_enterprise_login_mock_requires_existing_local_account(client):
    client.application.config['ENTERPRISE_AUTH_ENABLED'] = True
    client.application.config['ENTERPRISE_AUTH_PROVIDER'] = 'mock'
    client.application.config['ENTERPRISE_MOCK_USERS'] = {'ent_only_external': 'ent-pass'}

    response = client.post(
        '/api/auth/enterprise-login',
        json={'username': 'ent_only_external', 'password': 'ent-pass'},
    )
    assert response.status_code == 404
