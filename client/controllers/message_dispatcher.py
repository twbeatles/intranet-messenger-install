# -*- coding: utf-8 -*-

from __future__ import annotations

import mimetypes
import time
from typing import Any

from client.controllers.types import PendingSend
from client.i18n import t


class MessageDispatcher:
    FILE_TOKEN_REFRESH_WINDOW_SECONDS = 240.0

    def __init__(self, controller) -> None:
        self.controller = controller

    @staticmethod
    def _is_file_payload(payload: dict[str, Any]) -> bool:
        return str(payload.get("type") or "").strip().lower() in ("file", "image")

    @staticmethod
    def _sanitize_socket_payload(payload: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if not str(key).startswith("_")}

    def _mark_entry_failed(self, client_msg_id: str, entry: dict[str, Any], message: str = "") -> None:
        entry["failed"] = True
        self.upsert_outbox_entry(client_msg_id, entry)
        if client_msg_id not in self.controller._failed_send_ids:
            self.controller._failed_send_ids.append(client_msg_id)
        if message:
            self.controller.main_window.show_error(message)
        self.refresh_delivery_state()

    def _refresh_file_upload_token(self, client_msg_id: str, entry: dict[str, Any]) -> dict[str, Any] | None:
        payload = dict(entry.get("payload") or {})
        local_path = str(payload.get("_local_path") or "").strip()
        room_id = int(payload.get("room_id") or 0)
        if not local_path or room_id <= 0:
            self._mark_entry_failed(
                client_msg_id,
                entry,
                t("files.local_not_found", "File not found."),
            )
            return None

        try:
            upload = self.controller.api.upload_file(room_id, local_path)
        except Exception as exc:
            self._mark_entry_failed(client_msg_id, entry, str(exc))
            return None

        token = str(upload.get("upload_token") or "").strip()
        file_name = str(upload.get("file_name") or payload.get("content") or "").strip()
        message_type = self.guess_message_type(file_name, upload.get("file_type"))
        if not token:
            self._mark_entry_failed(
                client_msg_id,
                entry,
                t("controller.upload_token_missing", "Upload token is missing."),
            )
            return None

        payload["upload_token"] = token
        payload["_upload_token_issued_at"] = time.time()
        payload["content"] = file_name
        payload["type"] = message_type
        entry["payload"] = payload
        entry["is_file"] = True
        entry["file_name"] = file_name
        self.upsert_outbox_entry(client_msg_id, entry)
        return payload

    def _prepare_payload_for_dispatch(self, client_msg_id: str, entry: dict[str, Any]) -> dict[str, Any] | None:
        payload = dict(entry.get("payload") or {})
        if not self._is_file_payload(payload):
            return self._sanitize_socket_payload(payload)

        token = str(payload.get("upload_token") or "").strip()
        token_issued_at = float(payload.get("_upload_token_issued_at") or 0.0)
        age_seconds = time.time() - token_issued_at if token_issued_at > 0 else self.FILE_TOKEN_REFRESH_WINDOW_SECONDS
        if not token or age_seconds >= self.FILE_TOKEN_REFRESH_WINDOW_SECONDS:
            payload = self._refresh_file_upload_token(client_msg_id, entry)
            if payload is None:
                return None
        return self._sanitize_socket_payload(payload)

    def upsert_outbox_entry(self, client_msg_id: str, entry: dict[str, Any]) -> None:
        if not self.controller.current_user:
            return
        user_id = int((self.controller.current_user or {}).get("id") or 0)
        if user_id <= 0:
            return
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        self.controller.outbox_store.upsert(
            user_id=user_id,
            server_url=self.controller.current_server_url,
            client_msg_id=client_msg_id,
            payload=payload,
            created_at=float(entry.get("created_at") or time.time()),
            last_attempt_at=float(entry.get("last_attempt_at") or 0.0),
            retry_count=int(entry.get("retry_count") or 0),
            failed=bool(entry.get("failed")),
        )

    def remove_outbox_entry(self, client_msg_id: str) -> None:
        if not self.controller.current_user:
            return
        user_id = int((self.controller.current_user or {}).get("id") or 0)
        if user_id <= 0:
            return
        self.controller.outbox_store.remove(
            user_id=user_id,
            server_url=self.controller.current_server_url,
            client_msg_id=client_msg_id,
        )

    def restore_pending_sends_from_outbox(self) -> None:
        self.controller._pending_sends.clear()
        self.controller._failed_send_ids = []
        if not self.controller.current_user:
            return
        user_id = int((self.controller.current_user or {}).get("id") or 0)
        if user_id <= 0:
            return
        entries = self.controller.outbox_store.list_entries(
            user_id=user_id,
            server_url=self.controller.current_server_url,
        )
        for row in entries:
            client_msg_id = str(row.get("client_msg_id") or "").strip()
            if not client_msg_id:
                continue
            pending = PendingSend.from_store_row(row)
            if pending is None:
                continue
            self.controller._pending_sends[client_msg_id] = pending.to_dict()
            if pending.failed:
                self.controller._failed_send_ids.append(client_msg_id)

    def dispatch_pending_send(self, client_msg_id: str) -> None:
        entry = self.controller._pending_sends.get(client_msg_id)
        if not entry:
            return
        entry["last_attempt_at"] = time.time()
        entry["failed"] = False
        self.upsert_outbox_entry(client_msg_id, entry)
        payload = self._prepare_payload_for_dispatch(client_msg_id, entry)
        if payload is None:
            return

        def ack_callback(raw_ack: dict[str, Any] | Any) -> None:
            ack = raw_ack if isinstance(raw_ack, dict) else {}
            self.handle_send_ack(client_msg_id, ack)

        try:
            self.controller.socket.send_message(payload, ack_callback=ack_callback)
        except Exception:
            pass

    def handle_send_ack(self, client_msg_id: str, ack: dict[str, Any]) -> None:
        entry = self.controller._pending_sends.get(client_msg_id)
        if not entry:
            return
        if bool(ack.get("ok")):
            if bool(entry.get("is_file")):
                file_name = str(entry.get("file_name") or "")
                if file_name:
                    self.controller.tray.notify(
                        t("app.name", "Intranet Messenger"),
                        t("files.upload", "Upload") + f": {file_name}",
                    )
            self.controller._pending_sends.pop(client_msg_id, None)
            self.remove_outbox_entry(client_msg_id)
            if client_msg_id in self.controller._failed_send_ids:
                self.controller._failed_send_ids.remove(client_msg_id)
            self.refresh_delivery_state()
            return

        if bool(entry.get("is_file")):
            payload = dict(entry.get("payload") or {})
            payload.pop("upload_token", None)
            payload["_upload_token_issued_at"] = 0.0
            entry["payload"] = payload
        entry["failed"] = True
        self.upsert_outbox_entry(client_msg_id, entry)
        if client_msg_id not in self.controller._failed_send_ids:
            self.controller._failed_send_ids.append(client_msg_id)
        error_message = str(ack.get("error") or "").strip()
        if error_message:
            self.controller.main_window.show_error(error_message)
        self.refresh_delivery_state()

    def process_pending_sends(self) -> None:
        now = time.time()
        changed = False
        for client_msg_id, entry in list(self.controller._pending_sends.items()):
            if entry.get("failed"):
                continue
            last_attempt = float(entry.get("last_attempt_at") or 0.0)
            if last_attempt <= 0:
                continue
            if now - last_attempt < self.controller._send_timeout_seconds:
                continue

            retries = int(entry.get("retry_count") or 0)
            if retries >= self.controller._send_retry_limit:
                entry["failed"] = True
                self.upsert_outbox_entry(client_msg_id, entry)
                if client_msg_id not in self.controller._failed_send_ids:
                    self.controller._failed_send_ids.append(client_msg_id)
                changed = True
                continue

            entry["retry_count"] = retries + 1
            self.upsert_outbox_entry(client_msg_id, entry)
            self.dispatch_pending_send(client_msg_id)
            changed = True

        if changed:
            self.refresh_delivery_state()

    def retry_failed_sends(self) -> None:
        pending_retry = [
            msg_id for msg_id in self.controller._failed_send_ids if msg_id in self.controller._pending_sends
        ]
        self.controller._failed_send_ids = []
        for client_msg_id in pending_retry:
            entry = self.controller._pending_sends.get(client_msg_id)
            if not entry:
                continue
            entry["failed"] = False
            entry["retry_count"] = 0
            self.upsert_outbox_entry(client_msg_id, entry)
            self.dispatch_pending_send(client_msg_id)
        self.refresh_delivery_state()

    def refresh_delivery_state(self) -> None:
        pending_count = len([1 for entry in self.controller._pending_sends.values() if not entry.get("failed")])
        failed_count = len(self.controller._failed_send_ids)
        if failed_count > 0:
            self.controller.main_window.set_delivery_state("failed", failed_count)
            return
        if pending_count > 0:
            self.controller.main_window.set_delivery_state("pending", pending_count)
            return
        self.controller.main_window.set_delivery_state("idle", 0)

    def on_typing_changed(self, is_typing: bool) -> None:
        if not self.controller.current_room_id:
            return
        self.controller._typing_pending = bool(is_typing)
        self.controller._typing_debounce_timer.start(500 if is_typing else 150)

    def flush_typing_state(self) -> None:
        if self.controller._typing_pending is None:
            return
        room_id = int(self.controller.current_room_id or 0)
        if room_id <= 0:
            return
        next_state = bool(self.controller._typing_pending)
        if next_state == self.controller._typing_sent and self.controller._typing_room_id == room_id:
            return
        try:
            self.controller.socket.send_typing(room_id, next_state)
            self.controller._typing_sent = next_state
            self.controller._typing_room_id = room_id
        except Exception:
            pass

    @staticmethod
    def guess_message_type(file_name: str, from_server: str | None = None) -> str:
        if from_server in ("image", "file"):
            return from_server
        mime, _ = mimetypes.guess_type(file_name)
        if mime and mime.startswith("image/"):
            return "image"
        return "file"
