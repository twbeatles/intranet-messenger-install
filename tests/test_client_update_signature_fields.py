# -*- coding: utf-8 -*-


def test_client_update_signature_fields_optional_absent(client):
    response = client.get('/api/client/update', query_string={'client_version': '1.0.0'})
    assert response.status_code == 200
    payload = response.json
    assert payload['signature_required'] is False
    assert 'artifact_sha256' not in payload
    assert 'artifact_signature' not in payload


def test_client_update_signature_fields_present_when_configured(client, monkeypatch):
    import app.routes as routes

    monkeypatch.setattr(routes, 'DESKTOP_CLIENT_ARTIFACT_SHA256', 'abc123')
    monkeypatch.setattr(routes, 'DESKTOP_CLIENT_ARTIFACT_SIGNATURE', 'sig')
    monkeypatch.setattr(routes, 'DESKTOP_CLIENT_SIGNATURE_ALG', 'sha256')

    response = client.get('/api/client/update', query_string={'client_version': '1.0.0'})
    assert response.status_code == 200
    payload = response.json
    assert payload['artifact_sha256'] == 'abc123'
    assert payload['artifact_signature'] == 'sig'
    assert payload['signature_alg'] == 'sha256'


def test_client_update_signature_required_flag_can_be_true_without_metadata(client):
    client.application.config['APP_ENV'] = 'prod'
    client.application.config['REQUIRE_SIGNED_UPDATES_IN_PROD'] = True

    response = client.get('/api/client/update', query_string={'client_version': '1.0.0'})
    assert response.status_code == 200
    payload = response.json
    assert payload['signature_required'] is True
    assert 'artifact_sha256' not in payload
    assert 'artifact_signature' not in payload
