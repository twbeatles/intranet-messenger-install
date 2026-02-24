# -*- coding: utf-8 -*-


from app.api_response import build_socket_error_payload


def test_api_error_enrichment_accept_language_en(client):
    response = client.get('/api/rooms', headers={'Accept-Language': 'en-US,en;q=0.9'})
    assert response.status_code == 401

    payload = response.get_json()
    assert payload['error'] == '로그인이 필요합니다.'
    assert payload['error_code'] == 'AUTH_LOGIN_REQUIRED'
    assert payload['locale'] == 'en-US'
    assert 'Login required' in payload['error_localized']


def test_api_error_language_header_precedence(client):
    response = client.get(
        '/api/rooms',
        headers={
            'X-App-Language': 'ko',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    )
    assert response.status_code == 401

    payload = response.get_json()
    assert payload['error'] == '로그인이 필요합니다.'
    assert payload['locale'] == 'ko-KR'
    assert payload['error_localized'] == '로그인이 필요합니다.'


def test_socket_error_payload_localized_en():
    payload = build_socket_error_payload('로그인이 필요합니다.', locale_code='en')
    assert payload['message'] == '로그인이 필요합니다.'
    assert payload['message_code'] == 'AUTH_LOGIN_REQUIRED'
    assert payload['locale'] == 'en-US'
    assert 'Login required' in payload['message_localized']


def test_i18n_catalog_endpoint_uses_request_language(client):
    response = client.get('/api/i18n/web', headers={'X-App-Language': 'en-US'})
    assert response.status_code == 200

    payload = response.get_json()
    assert payload['domain'] == 'web'
    assert payload['locale'] == 'en-US'
    assert isinstance(payload['catalog'], dict)
