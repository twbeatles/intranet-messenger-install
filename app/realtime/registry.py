# -*- coding: utf-8 -*-

from __future__ import annotations

from app.realtime.admin import register_admin_handlers
from app.realtime.messages import register_message_handlers
from app.realtime.presence import register_presence_handlers
from app.realtime.rooms import register_room_handlers
from app.realtime.state import set_socketio_instance
from app.realtime.typing import register_typing_handlers


def register_socket_events(socketio) -> None:
    set_socketio_instance(socketio)
    register_presence_handlers(socketio)
    register_room_handlers(socketio)
    register_message_handlers(socketio)
    register_typing_handlers(socketio)
    register_admin_handlers(socketio)
