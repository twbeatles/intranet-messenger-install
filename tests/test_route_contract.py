# -*- coding: utf-8 -*-

from __future__ import annotations


EXPECTED_ROUTE_METHODS = {
    "/": ("GET",),
    "/api/admin/users/approve": ("POST",),
    "/api/auth/enterprise-login": ("POST",),
    "/api/client/update": ("GET",),
    "/api/device-sessions": ("GET", "POST"),
    "/api/device-sessions/current": ("DELETE",),
    "/api/device-sessions/refresh": ("POST",),
    "/api/device-sessions/<int:device_session_id>": ("DELETE",),
    "/api/i18n/<domain>": ("GET",),
    "/api/login": ("POST",),
    "/api/logout": ("POST",),
    "/api/me": ("DELETE", "GET"),
    "/api/me/password": ("PUT",),
    "/api/messages/<int:message_id>": ("DELETE", "PUT"),
    "/api/messages/<int:message_id>/reactions": ("GET", "POST"),
    "/api/polls/<int:poll_id>/close": ("POST",),
    "/api/polls/<int:poll_id>/vote": ("POST",),
    "/api/profile": ("GET", "PUT"),
    "/api/profile/image": ("DELETE", "POST"),
    "/api/register": ("POST",),
    "/api/rooms": ("GET", "POST"),
    "/api/rooms/<int:room_id>/admin-check": ("GET",),
    "/api/rooms/<int:room_id>/admins": ("GET", "POST"),
    "/api/rooms/<int:room_id>/files": ("GET",),
    "/api/rooms/<int:room_id>/files/<int:file_id>": ("DELETE",),
    "/api/rooms/<int:room_id>/info": ("GET",),
    "/api/rooms/<int:room_id>/leave": ("POST",),
    "/api/rooms/<int:room_id>/members": ("POST",),
    "/api/rooms/<int:room_id>/members/<int:target_user_id>": ("DELETE",),
    "/api/rooms/<int:room_id>/messages": ("GET",),
    "/api/rooms/<int:room_id>/mute": ("POST",),
    "/api/rooms/<int:room_id>/name": ("PUT",),
    "/api/rooms/<int:room_id>/pin": ("POST",),
    "/api/rooms/<int:room_id>/pin-room": ("POST",),
    "/api/rooms/<int:room_id>/pins": ("GET", "POST"),
    "/api/rooms/<int:room_id>/pins/<int:pin_id>": ("DELETE",),
    "/api/rooms/<int:room_id>/polls": ("GET", "POST"),
    "/api/search": ("GET",),
    "/api/search/advanced": ("POST",),
    "/api/security/audit": ("GET",),
    "/api/system/health": ("GET",),
    "/api/upload": ("POST",),
    "/api/users": ("GET",),
    "/api/users/online": ("GET",),
    "/sw.js": ("GET",),
    "/uploads/<path:filename>": ("GET",),
}


def _collect_public_routes(app) -> dict[str, tuple[str, ...]]:
    route_methods: dict[str, set[str]] = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        methods = {method for method in rule.methods if method not in {"HEAD", "OPTIONS"}}
        route_methods.setdefault(rule.rule, set()).update(methods)
    return {path: tuple(sorted(methods)) for path, methods in route_methods.items()}


def test_http_route_contract(app):
    assert _collect_public_routes(app) == EXPECTED_ROUTE_METHODS
