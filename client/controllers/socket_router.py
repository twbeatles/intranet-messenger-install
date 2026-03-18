# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from client.i18n import t
from client.services.crypto_compat import CryptoError, decrypt_message


class SocketRouter:
    def __init__(self, controller) -> None:
        self.controller = controller

    def on_new_message(self, message: dict[str, Any]) -> None:
        client_msg_id = str(message.get("client_msg_id") or "").strip()
        if client_msg_id:
            self.controller._pending_sends.pop(client_msg_id, None)
            self.controller._remove_outbox_entry(client_msg_id)
            if client_msg_id in self.controller._failed_send_ids:
                self.controller._failed_send_ids.remove(client_msg_id)
            self.controller._refresh_delivery_state()

        room_id = int(message.get("room_id") or 0)
        sender_id = int(message.get("sender_id") or 0)
        current_user_id = int((self.controller.current_user or {}).get("id") or 0)
        self.controller._update_room_cache_from_message(
            room_id=room_id,
            message=message,
            increment_unread=bool(self.controller.current_room_id != room_id and sender_id != current_user_id),
        )
        if self.controller.current_room_id and room_id == int(self.controller.current_room_id):
            self.controller._decorate_message_content(message)
            self.controller.main_window.append_message(message)
            message_id = int(message.get("id") or 0)
            if message_id:
                self.controller.socket.send_read(room_id=room_id, message_id=message_id)
        else:
            sender = message.get("sender_name") or t("tray.new_message", "New message", sender="").split(":")[0]
            self.controller.tray.notify(
                t("app.name", "Intranet Messenger"),
                t("tray.new_message", "{sender}: New message", sender=str(sender)),
            )
        self.controller._set_rooms_view(self.controller.rooms_cache)

    def on_room_name_updated(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if room_id and self.controller.current_room_id == room_id:
            new_name = str(payload.get("name") or "")
            if new_name:
                self.controller.main_window.set_room_title(new_name)
        self.controller._update_room_cache_name(room_id, str(payload.get("name") or ""))
        self.controller._set_rooms_view(self.controller.rooms_cache)

    def on_room_updated(self, payload: dict[str, Any]) -> None:
        action = str(payload.get("action") or "").strip().lower()
        current_user_id = int((self.controller.current_user or {}).get("id") or 0)
        try:
            affected_user_id = int(payload.get("user_id") or 0)
        except (TypeError, ValueError):
            affected_user_id = 0

        if action == "room_renamed":
            return
        if action in ("members_invited", "member_left", "member_kicked"):
            if affected_user_id > 0 and affected_user_id == current_user_id:
                self.controller._schedule_rooms_reload(120)
            return
        if action == "room_created":
            self.controller._schedule_rooms_reload(120)
            return
        self.controller._schedule_rooms_reload(180)

    def on_room_members_updated(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        action = str(payload.get("action") or "").strip().lower()
        current_user_id = int((self.controller.current_user or {}).get("id") or 0)
        try:
            affected_user_id = int(payload.get("user_id") or 0)
        except (TypeError, ValueError):
            affected_user_id = 0

        if (
            room_id
            and self.controller.current_room_id == room_id
            and action in ("member_left", "member_kicked")
            and affected_user_id > 0
            and affected_user_id == current_user_id
        ):
            try:
                self.controller.socket.leave_room(room_id)
            except Exception:
                pass
            self.controller.current_room_id = None
            self.controller.current_room_key = ""
            self.controller.current_room_members = []
            self.controller.main_window.clear_room_selection()
            self.controller._schedule_rooms_reload(120)
            return

        if room_id and self.controller.current_room_id == room_id:
            self.controller._reload_current_room_messages(silent=True, refresh_admins=True)
        self.controller._schedule_rooms_reload(220 if action == "members_invited" else 200)

    def on_read_updated(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if room_id and self.controller.current_room_id == room_id:
            self.controller._set_room_unread(room_id, 0)
            self.controller._set_rooms_view(self.controller.rooms_cache)

    def on_user_typing(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if not room_id or self.controller.current_room_id != room_id:
            return
        user_id = int(payload.get("user_id") or 0)
        nickname = str(payload.get("nickname") or "")
        is_typing = bool(payload.get("is_typing"))
        self.controller.main_window.set_typing_user(user_id, nickname, is_typing)

    def on_message_edited(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if not room_id:
            return
        if self.controller.current_room_id and room_id == int(self.controller.current_room_id):
            message_id = int(payload.get("message_id") or 0)
            content = str(payload.get("content") or "")
            encrypted = bool(payload.get("encrypted", False))
            display_content = content
            if encrypted and self.controller.current_room_key:
                try:
                    display_content = decrypt_message(content, self.controller.current_room_key)
                except CryptoError:
                    display_content = t("app.messages.encrypted", "[encrypted message]")
            updated = self.controller.main_window.update_message_content(
                message_id=message_id,
                content=content,
                display_content=display_content,
                encrypted=encrypted,
            )
            if not updated:
                self.controller._reload_current_room_messages(silent=True)
        self.controller._schedule_rooms_reload(250)

    def on_message_deleted(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if not room_id:
            return
        if self.controller.current_room_id and room_id == int(self.controller.current_room_id):
            message_id = int(payload.get("message_id") or 0)
            updated = self.controller.main_window.mark_message_deleted(message_id)
            if not updated:
                self.controller._reload_current_room_messages(silent=True)
        self.controller._schedule_rooms_reload(250)

    def on_reaction_updated(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if room_id and self.controller.current_room_id == room_id:
            message_id = int(payload.get("message_id") or 0)
            reactions = payload.get("reactions")
            updated = self.controller.main_window.update_message_reactions(
                message_id=message_id,
                reactions=reactions if isinstance(reactions, list) else [],
            )
            if not updated:
                self.controller._reload_current_room_messages(silent=True)

    def on_poll_updated(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if room_id and self.controller.current_room_id == room_id and self.controller.polls_dialog.isVisible():
            self.controller._refresh_polls()

    def on_pin_updated(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if room_id and self.controller.current_room_id == room_id:
            return

    def on_admin_updated(self, payload: dict[str, Any]) -> None:
        room_id = self.controller._extract_room_id(payload)
        if room_id and self.controller.current_room_id == room_id and self.controller.admin_dialog.isVisible():
            self.controller._refresh_admins(silent=True)

    def on_error(self, payload: dict[str, Any]) -> None:
        message = payload.get("message_localized") or payload.get("message") or t(
            "controller.socket_error_generic",
            "Socket error",
        )
        self.controller.main_window.show_error(str(message))
