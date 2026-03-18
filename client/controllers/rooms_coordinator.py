# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import Any

from client.i18n import t


class RoomsCoordinator:
    @staticmethod
    def normalize_room_ids(rooms: list[dict[str, Any]]) -> tuple[int, ...]:
        ids: set[int] = set()
        for room in rooms:
            try:
                room_id = int(room.get("id") or 0)
            except (TypeError, ValueError):
                room_id = 0
            if room_id > 0:
                ids.add(room_id)
        return tuple(sorted(ids))

    @staticmethod
    def build_rooms_signature(rooms: list[dict[str, Any]]) -> tuple[tuple[int, str, str, int, int, str], ...]:
        signature: list[tuple[int, str, str, int, int, str]] = []
        for room in rooms:
            try:
                room_id = int(room.get("id") or 0)
            except (TypeError, ValueError):
                room_id = 0
            signature.append(
                (
                    room_id,
                    str(room.get("name") or ""),
                    str(room.get("last_message_time") or ""),
                    int(room.get("unread_count") or 0),
                    int(room.get("pinned") or 0),
                    str(room.get("last_message_preview") or ""),
                )
            )
        return tuple(signature)

    def __init__(self, controller) -> None:
        self.controller = controller

    def set_rooms_view(self, rooms: list[dict[str, Any]], *, force: bool = False) -> bool:
        signature = self.build_rooms_signature(rooms)
        if not force and self.controller._visible_rooms_signature == signature:
            return False
        self.controller.main_window.set_rooms(rooms)
        self.controller._visible_rooms_signature = signature
        return True

    def sync_socket_room_subscriptions(self, rooms: list[dict[str, Any]]) -> None:
        room_ids = self.normalize_room_ids(rooms)
        if room_ids == self.controller._last_subscribed_room_ids:
            return
        self.controller.socket.subscribe_rooms(list(room_ids))
        self.controller._last_subscribed_room_ids = room_ids

    def clear_remote_search_cache(self) -> None:
        self.controller._remote_search_cache.clear()

    def get_cached_remote_search_room_ids(self, query: str, room_id: int) -> set[int] | None:
        key = (str(query or "").strip().lower(), int(room_id or 0))
        if not key[0]:
            return None
        entry = self.controller._remote_search_cache.get(key)
        if not entry:
            return None
        cached_at, matched_ids = entry
        if (time.time() - float(cached_at)) > float(self.controller._remote_search_cache_ttl_seconds):
            self.controller._remote_search_cache.pop(key, None)
            return None
        return set(matched_ids)

    def store_cached_remote_search_room_ids(self, query: str, room_id: int, matched_ids: set[int]) -> None:
        key = (str(query or "").strip().lower(), int(room_id or 0))
        if not key[0]:
            return
        self.controller._remote_search_cache[key] = (time.time(), set(matched_ids))

    @staticmethod
    def extract_room_id(payload: dict[str, Any]) -> int | None:
        value = payload.get("room_id")
        if value is None:
            poll_value = payload.get("poll")
            poll = poll_value if isinstance(poll_value, dict) else {}
            value = poll.get("room_id")
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def preview_for_message(message: dict[str, Any]) -> str:
        message_type = str(message.get("message_type") or message.get("type") or "text")
        content = str(message.get("display_content") or message.get("content") or "")
        encrypted = bool(message.get("encrypted", False))
        file_name = str(message.get("file_name") or content or "")

        if message_type == "image":
            return t("rooms.preview.image", "📷 Image")
        if message_type == "file":
            return file_name or t("rooms.preview.file", "📎 File")
        if message_type == "system":
            preview = content.strip()
            return preview[:25] + ("..." if len(preview) > 25 else "") if preview else t("rooms.preview.system", "🔔 System message")
        if encrypted:
            return t("rooms.preview.encrypted", "🔒 Encrypted message")
        preview = content.strip()
        if not preview:
            return t("rooms.preview.message", "Message")
        return preview[:25] + ("..." if len(preview) > 25 else "")

    def sort_rooms_cache(self) -> None:
        def sort_key(room: dict[str, Any]):
            pinned = int(room.get("pinned") or 0)
            ts = str(room.get("last_message_time") or "")
            return (pinned, ts)

        self.controller.rooms_cache.sort(key=sort_key, reverse=True)

    def update_room_cache_name(self, room_id: int | None, name: str) -> None:
        if not room_id or not name:
            return
        for room in self.controller.rooms_cache:
            if int(room.get("id") or 0) == int(room_id):
                room["name"] = name
                break

    def set_room_unread(self, room_id: int, unread: int) -> None:
        for room in self.controller.rooms_cache:
            if int(room.get("id") or 0) == int(room_id):
                room["unread_count"] = max(0, int(unread))
                break

    def update_room_cache_from_message(
        self,
        *,
        room_id: int,
        message: dict[str, Any],
        increment_unread: bool,
    ) -> None:
        if room_id <= 0:
            return
        target = None
        for room in self.controller.rooms_cache:
            if int(room.get("id") or 0) == room_id:
                target = room
                break
        if not target:
            self.controller._schedule_rooms_reload(150)
            return

        target["last_message_preview"] = self.preview_for_message(message)
        target["last_message_time"] = str(message.get("created_at") or target.get("last_message_time") or "")
        if increment_unread:
            target["unread_count"] = int(target.get("unread_count") or 0) + 1
        elif self.controller.current_room_id and int(self.controller.current_room_id) == room_id:
            target["unread_count"] = 0
        self.sort_rooms_cache()

    def on_search_input_changed(self, query: str) -> None:
        self.controller._pending_search_query = str(query or "")
        self.controller._search_debounce_timer.start(300)

    def flush_search_request(self) -> None:
        self.on_search_requested(self.controller._pending_search_query)

    def on_search_requested(self, query: str) -> None:
        query = query.strip()
        if not query:
            self.set_rooms_view(self.controller.rooms_cache)
            return

        lowered = query.lower()
        filtered = [
            room
            for room in self.controller.rooms_cache
            if lowered in str(room.get("name", "")).lower()
            or lowered in str(room.get("last_message_preview", "")).lower()
        ]
        if filtered:
            self.set_rooms_view(filtered)
            return

        if len(query) < 2:
            self.set_rooms_view([])
            return

        try:
            scoped_room_id = int(self.controller.current_room_id) if self.controller.current_room_id else 0
            matched_room_ids = self.get_cached_remote_search_room_ids(query, scoped_room_id)
            if matched_room_ids is None:
                results = self.controller.api.search_messages(
                    query,
                    int(self.controller.current_room_id) if self.controller.current_room_id else None,
                    limit=20,
                )
                matched_room_ids = {
                    int(row.get("room_id") or 0)
                    for row in results
                    if isinstance(row, dict) and int(row.get("room_id") or 0) > 0
                }
                self.store_cached_remote_search_room_ids(query, scoped_room_id, matched_room_ids)

            remote_filtered = [
                room for room in self.controller.rooms_cache if int(room.get("id") or 0) in matched_room_ids
            ]
            self.set_rooms_view(remote_filtered)
        except Exception:
            self.set_rooms_view([])
