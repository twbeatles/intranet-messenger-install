# -*- coding: utf-8 -*-

from __future__ import annotations

from app.sockets import register_socket_events


EXPECTED_SOCKET_EVENTS = {
    "admin_updated",
    "connect",
    "delete_message",
    "disconnect",
    "edit_message",
    "join_room",
    "leave_room",
    "message_read",
    "pin_updated",
    "poll_created",
    "poll_updated",
    "profile_updated",
    "reaction_updated",
    "room_members_updated",
    "room_name_updated",
    "send_message",
    "subscribe_rooms",
    "typing",
}


class _FakeSocketIO:
    def __init__(self) -> None:
        self.handlers: dict[str, object] = {}

    def on(self, event: str):
        def decorator(func):
            self.handlers[event] = func
            return func

        return decorator


def test_socket_event_contract():
    fake_socketio = _FakeSocketIO()

    register_socket_events(fake_socketio)

    assert set(fake_socketio.handlers) == EXPECTED_SOCKET_EVENTS
