# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import Any, cast

from client.controllers.message_dispatcher import MessageDispatcher


class _FakeOutboxStore:
    def upsert(self, **kwargs):
        self.last_upsert = kwargs

    def remove(self, **kwargs):
        self.last_remove = kwargs


class _FakeMainWindow:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.delivery_states: list[tuple[str, int]] = []

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def set_delivery_state(self, state: str, count: int) -> None:
        self.delivery_states.append((state, count))


class _FakeTray:
    def notify(self, title: str, message: str) -> None:
        self.last_notification = (title, message)


class _FakeAPI:
    def __init__(self) -> None:
        self.upload_calls: list[tuple[int, str]] = []

    def upload_file(self, room_id: int, local_path: str) -> dict[str, str]:
        self.upload_calls.append((room_id, local_path))
        return {
            "upload_token": "fresh-token",
            "file_name": "photo.png",
            "file_type": "image",
        }


class _FakeSocket:
    def __init__(self) -> None:
        self.sent_payloads: list[dict[str, object]] = []

    def send_message(self, payload: dict[str, object], ack_callback=None) -> None:
        self.sent_payloads.append(payload)


class _FakeController:
    def __init__(self) -> None:
        self.api = _FakeAPI()
        self.socket = _FakeSocket()
        self.outbox_store = _FakeOutboxStore()
        self.main_window = _FakeMainWindow()
        self.tray = _FakeTray()
        self.current_user = {"id": 1}
        self.current_server_url = "http://server.invalid"
        self._failed_send_ids: list[str] = []
        self._pending_sends: dict[str, dict[str, object]] = {}
        self._send_timeout_seconds = 5.0
        self._send_retry_limit = 3


def test_dispatch_pending_send_refreshes_stale_file_token():
    controller = _FakeController()
    dispatcher = MessageDispatcher(controller)
    client_msg_id = "msg-1"
    controller._pending_sends[client_msg_id] = {
        "created_at": time.time(),
        "failed": False,
        "is_file": True,
        "file_name": "photo.png",
        "payload": {
            "room_id": 10,
            "content": "photo.png",
            "type": "file",
            "upload_token": "stale-token",
            "_local_path": "C:/tmp/photo.png",
            "_upload_token_issued_at": time.time() - 600,
        },
        "retry_count": 0,
    }

    dispatcher.dispatch_pending_send(client_msg_id)

    assert controller.api.upload_calls == [(10, "C:/tmp/photo.png")]
    assert controller.socket.sent_payloads
    sent_payload = controller.socket.sent_payloads[0]
    assert sent_payload["upload_token"] == "fresh-token"
    assert sent_payload["type"] == "image"
    assert "_local_path" not in sent_payload
    assert "_upload_token_issued_at" not in sent_payload


def test_handle_send_ack_failure_resets_file_upload_token():
    controller = _FakeController()
    dispatcher = MessageDispatcher(controller)
    client_msg_id = "msg-2"
    controller._pending_sends[client_msg_id] = {
        "created_at": time.time(),
        "failed": False,
        "is_file": True,
        "file_name": "report.pdf",
        "payload": {
            "room_id": 20,
            "content": "report.pdf",
            "type": "file",
            "upload_token": "used-token",
            "_local_path": "C:/tmp/report.pdf",
            "_upload_token_issued_at": time.time(),
        },
        "retry_count": 0,
    }

    dispatcher.handle_send_ack(client_msg_id, {"ok": False, "error": "upload token expired"})

    payload = cast(dict[str, Any], controller._pending_sends[client_msg_id]["payload"])
    assert "upload_token" not in payload
    assert payload["_upload_token_issued_at"] == 0.0
    assert client_msg_id in controller._failed_send_ids
    assert controller.main_window.errors == ["upload token expired"]
