# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from client.i18n import t
from client.ui.message_formatters import contains_mention, format_reactions
from client.ui.theme import avatar_color, avatar_text_color


def build_message_container(window, message: dict[str, Any]) -> QWidget:
    sender = str(
        message.get("sender_name")
        or message.get("sender_id")
        or t("common.unknown", "unknown")
    )
    content = str(message.get("display_content") or message.get("content") or "")
    timestamp = str(message.get("created_at") or "")
    reply_sender = str(message.get("reply_sender") or "")
    reply_content = str(message.get("reply_content") or "")
    reactions = message.get("reactions") or []
    try:
        sender_id = int(message.get("sender_id") or 0)
    except (TypeError, ValueError):
        sender_id = 0
    is_own = sender_id > 0 and sender_id == window._current_user_id

    container = QWidget()
    container.setStyleSheet("background: transparent;")
    container_layout = QHBoxLayout(container)
    container_layout.setContentsMargins(4, 2, 4, 2)
    container_layout.setSpacing(12)

    bubble = QFrame()
    bubble.setProperty("messageOwn", is_own)
    bubble_layout = QVBoxLayout(bubble)
    bubble_layout.setContentsMargins(16, 12, 16, 12)
    bubble_layout.setSpacing(6)

    if not is_own:
        sender_label = QLabel(sender)
        sender_label.setProperty("msgSender", True)
        bubble_layout.addWidget(sender_label)

    if reply_content:
        preview = reply_content if len(reply_content) <= 60 else f"{reply_content[:57]}..."
        reply = QLabel(
            t(
                "main.reply_preview",
                "Reply to {sender}: {preview}",
                sender=reply_sender or t("common.unknown", "unknown"),
                preview=preview,
            )
        )
        reply.setProperty("msgReply", True)
        reply.setWordWrap(True)
        bubble_layout.addWidget(reply)

    body = QLabel(content)
    body.setWordWrap(True)
    if contains_mention(window._user_aliases, content):
        body.setProperty("msgBody", "mention")
    else:
        body.setProperty("msgBody", True)
    body.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByKeyboard
        | Qt.TextInteractionFlag.TextSelectableByMouse
    )
    bubble_layout.addWidget(body)

    reaction_text = format_reactions(reactions)
    if reaction_text:
        reaction_label = QLabel(reaction_text)
        reaction_label.setProperty("muted", True)
        bubble_layout.addWidget(reaction_label)

    time_label = QLabel(timestamp)
    time_label.setProperty("msgTime", True)
    time_layout = QVBoxLayout()
    time_layout.addStretch()
    time_layout.addWidget(time_label)

    if is_own:
        container_layout.addStretch()
        container_layout.addLayout(time_layout)
        container_layout.addWidget(bubble)
    else:
        avatar_key = str(message.get("sender_id") or sender)
        bg = avatar_color(avatar_key)
        fg = avatar_text_color(bg)
        avatar_label = QLabel(sender[0].upper() if sender else "?")
        avatar_label.setFixedSize(40, 40)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: 20px;"
            " font-weight: bold; font-size: 14pt;"
        )

        avatar_layout = QVBoxLayout()
        avatar_layout.addWidget(avatar_label)
        avatar_layout.addStretch()

        container_layout.addLayout(avatar_layout)
        container_layout.addWidget(bubble)
        container_layout.addLayout(time_layout)
        container_layout.addStretch()

    return container
