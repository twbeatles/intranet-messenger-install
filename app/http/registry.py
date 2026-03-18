# -*- coding: utf-8 -*-

from __future__ import annotations

from app.http.auth import register_auth_routes
from app.http.messages import register_message_routes
from app.http.polls import register_poll_routes
from app.http.rooms import register_room_routes
from app.http.system import register_system_routes
from app.http.uploads import register_upload_routes
from app.http.users import register_user_routes
from app.http.web import register_web_routes


def register_routes(app) -> None:
    register_web_routes(app)
    register_auth_routes(app)
    register_system_routes(app)
    register_room_routes(app)
    register_message_routes(app)
    register_upload_routes(app)
    register_user_routes(app)
    register_poll_routes(app)
