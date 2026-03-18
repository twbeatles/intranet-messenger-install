# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidgetItem, QVBoxLayout, QWidget

from client.i18n import t
from client.ui.theme import avatar_color, avatar_text_color


def build_room_item_widget(room: dict[str, Any]) -> QWidget:
    name = str(room.get("name") or t("main.room_default_name", "Room {room_id}", room_id=room.get("id")))
    preview = str(room.get("last_message_preview") or t("main.no_recent_message", "No recent message."))
    unread = int(room.get("unread_count") or 0)
    last_time = str(room.get("last_message_time") or "")

    wrapper = QWidget()
    wrapper_layout = QHBoxLayout(wrapper)
    wrapper_layout.setContentsMargins(12, 12, 12, 12)
    wrapper_layout.setSpacing(14)

    avatar_key = str(room.get("id") or name)
    bg = avatar_color(avatar_key)
    fg = avatar_text_color(bg)
    avatar_label = QLabel(name[0].upper() if name else "?")
    avatar_label.setFixedSize(44, 44)
    avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    avatar_label.setStyleSheet(
        f"background-color: {bg}; color: {fg}; border-radius: 22px;"
        " font-weight: bold; font-size: 14pt;"
    )

    content_layout = QVBoxLayout()
    content_layout.setSpacing(2)

    top = QHBoxLayout()
    title = QLabel(name)
    title.setStyleSheet("font-size: 11pt; font-weight: 600; color: #1e293b;")
    top.addWidget(title)
    top.addStretch()

    if last_time:
        time_label = QLabel(last_time)
        time_label.setProperty("muted", True)
        time_label.setStyleSheet("font-size: 8.5pt; color: #94a3b8;")
        top.addWidget(time_label)

    if unread > 0:
        badge = QLabel(str(unread))
        badge.setProperty("badge", True)
        top.addWidget(badge)

    preview_label = QLabel(preview)
    preview_label.setProperty("muted", True)
    preview_label.setStyleSheet("color: #64748b; font-size: 9.5pt;")
    preview_label.setFixedHeight(20)

    content_layout.addLayout(top)
    content_layout.addWidget(preview_label)

    wrapper_layout.addWidget(avatar_label)
    wrapper_layout.addLayout(content_layout)
    return wrapper


def populate_rooms_list(window, rooms: list[dict[str, Any]]) -> None:
    current_room_id = window._room_id_by_row.get(window.rooms_list.currentRow())
    window.rooms_list.clear()
    window._room_id_by_row.clear()
    selected_row = -1

    for room in rooms:
        room_id = room.get("id")
        if room_id is None:
            continue
        try:
            normalized_room_id = int(room_id)
        except (TypeError, ValueError):
            continue

        item = QListWidgetItem()
        widget = build_room_item_widget(room)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, normalized_room_id)
        window.rooms_list.addItem(item)
        row = window.rooms_list.count() - 1
        window.rooms_list.setItemWidget(item, widget)
        window._room_id_by_row[row] = normalized_room_id
        if current_room_id and normalized_room_id == current_room_id:
            selected_row = row

    if window.rooms_list.count() == 0:
        empty_item = QListWidgetItem(t("main.rooms_empty", "No rooms available."))
        empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
        window.rooms_list.addItem(empty_item)
        window._set_room_actions_enabled(False)
        window.compose_hint_label.setText(t("main.compose_no_room", "No room selected"))
        return

    if selected_row >= 0:
        window.rooms_list.setCurrentRow(selected_row)
