# -*- coding: utf-8 -*-


def test_client_update_endpoint_shape(client):
    response = client.get('/api/client/update', query_string={'client_version': '1.0.0'})
    assert response.status_code == 200

    payload = response.json
    assert payload['channel'] == 'stable'
    assert 'desktop_only_mode' in payload
    assert 'minimum_version' in payload
    assert 'latest_version' in payload
    assert 'update_available' in payload
    assert 'force_update' in payload
    assert payload['client_version'] == '1.0.0'


def test_client_update_default_version(client):
    response = client.get('/api/client/update')
    assert response.status_code == 200
    payload = response.json
    assert payload['channel'] == 'stable'
    assert payload['client_version'] is None


def test_client_update_canary_channel(client, monkeypatch):
    import app.routes as routes

    monkeypatch.setattr(routes, 'DESKTOP_CLIENT_CANARY_MIN_VERSION', '2.0.0')
    monkeypatch.setattr(routes, 'DESKTOP_CLIENT_CANARY_LATEST_VERSION', '2.1.0')
    monkeypatch.setattr(routes, 'DESKTOP_CLIENT_CANARY_DOWNLOAD_URL', 'https://example.invalid/canary')
    monkeypatch.setattr(routes, 'DESKTOP_CLIENT_CANARY_RELEASE_NOTES_URL', 'https://example.invalid/canary-notes')

    response = client.get('/api/client/update', query_string={'client_version': '1.0.0', 'channel': 'canary'})
    assert response.status_code == 200

    payload = response.json
    assert payload['channel'] == 'canary'
    assert payload['minimum_version'] == '2.0.0'
    assert payload['latest_version'] == '2.1.0'
    assert payload['download_url'] == 'https://example.invalid/canary'
    assert payload['release_notes_url'] == 'https://example.invalid/canary-notes'
    assert payload['force_update'] is True
