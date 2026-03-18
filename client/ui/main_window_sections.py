# -*- coding: utf-8 -*-

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


def build_sidebar_panel(window) -> QFrame:
    left_panel = QFrame()
    left_panel.setProperty("sidebar", True)
    left_panel.setMinimumWidth(320)
    left_panel.setMaximumWidth(420)
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(24, 28, 24, 24)
    left_layout.setSpacing(20)

    user_header = QHBoxLayout()
    user_info = QVBoxLayout()
    window.user_label = QLabel("")
    window.user_label.setProperty("section", True)
    window.connection_label = QLabel("")
    window.connection_label.setProperty("status", "disconnected")
    user_info.addWidget(window.user_label)
    user_info.addSpacing(2)
    user_info.addWidget(window.connection_label)

    window.settings_btn = QPushButton("⚙️")
    window.settings_btn.setProperty("variant", "icon")
    window.settings_btn.setFixedSize(36, 36)
    window.profile_btn = QPushButton("")

    user_header.addLayout(user_info)
    user_header.addStretch()
    user_header.addWidget(window.profile_btn)
    user_header.addWidget(window.settings_btn)

    inbox_title = QLabel("")
    inbox_title.setProperty("subtitle", True)
    window._inbox_title_label = inbox_title

    window.search_input = QLineEdit()
    window.rooms_list = QListWidget()
    window.rooms_list.setSpacing(6)
    window.rooms_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    window.rooms_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    left_layout.addLayout(user_header)
    left_layout.addSpacing(4)
    left_layout.addWidget(window.search_input)
    left_layout.addSpacing(4)
    left_layout.addWidget(inbox_title)
    left_layout.addWidget(window.rooms_list)

    left_actions = QHBoxLayout()
    window.new_room_btn = QPushButton("")
    window.refresh_btn = QPushButton("")
    window.logout_btn = QPushButton("")
    window.logout_btn.setProperty("variant", "danger")
    left_actions.addWidget(window.new_room_btn)
    left_actions.addWidget(window.refresh_btn)
    left_actions.addStretch()
    left_actions.addWidget(window.logout_btn)
    left_layout.addLayout(left_actions)
    return left_panel


def build_chat_panel(window, composer_cls) -> QFrame:
    right_panel = QFrame()
    right_panel.setProperty("chatArea", True)
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)

    room_header = QFrame()
    room_header.setStyleSheet(
        "background: #ffffff; border-bottom: 1px solid #e2e8f0; border-top-right-radius: 12px;"
    )
    room_header_layout = QHBoxLayout(room_header)
    room_header_layout.setContentsMargins(28, 22, 28, 22)

    window.room_title = QLabel("")
    window.room_title.setProperty("section", True)
    window.room_title.setStyleSheet("font-size: 16pt;")
    window.room_meta = QLabel("")
    window.room_meta.setProperty("muted", True)

    window.invite_btn = QPushButton("")
    window.rename_btn = QPushButton("")
    window.leave_btn = QPushButton("")
    window.leave_btn.setProperty("variant", "danger")

    window.polls_btn = QPushButton("")
    window.files_btn = QPushButton("")
    window.admin_btn = QPushButton("")
    window.polls_btn.setProperty("variant", "primary")

    header_titles = QVBoxLayout()
    header_titles.setSpacing(4)
    header_titles.addWidget(window.room_title)
    header_titles.addWidget(window.room_meta)
    room_header_layout.addLayout(header_titles)
    room_header_layout.addStretch()

    feature_group = QHBoxLayout()
    feature_group.setSpacing(4)
    feature_group.addWidget(window.polls_btn)
    feature_group.addWidget(window.files_btn)
    feature_group.addWidget(window.admin_btn)
    room_header_layout.addLayout(feature_group)

    header_sep = QFrame()
    header_sep.setFrameShape(QFrame.Shape.VLine)
    header_sep.setStyleSheet("color: #e2e8f0; max-width: 1px; margin: 4px 6px;")
    room_header_layout.addWidget(header_sep)

    manage_group = QHBoxLayout()
    manage_group.setSpacing(4)
    manage_group.addWidget(window.invite_btn)
    manage_group.addWidget(window.rename_btn)
    manage_group.addWidget(window.leave_btn)
    room_header_layout.addLayout(manage_group)

    window.messages_list = QListWidget()
    window.messages_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    window.messages_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    window.messages_list.setSpacing(18)
    window.messages_list.setStyleSheet(
        "background: #f8fafc; padding: 24px 32px; border: none;"
    )
    window.messages_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    window.messages_list.verticalScrollBar().valueChanged.connect(window._on_messages_scrolled)

    compose_box = QFrame()
    compose_box.setStyleSheet(
        "background: #ffffff; border-top: 1px solid #e2e8f0; border-bottom-right-radius: 12px;"
    )
    compose_box_layout = QVBoxLayout(compose_box)
    compose_box_layout.setContentsMargins(24, 20, 24, 20)
    compose_box_layout.setSpacing(12)

    window.message_input = composer_cls()
    window.message_input.setFixedHeight(94)
    window.message_input.setStyleSheet(
        "border: none; background: transparent; font-size: 11pt;"
    )

    compose_meta = QHBoxLayout()
    window.compose_hint_label = QLabel("")
    window.compose_hint_label.setProperty("muted", True)
    compose_meta.addWidget(window.compose_hint_label)
    window.delivery_state_label = QLabel("")
    window.delivery_state_label.setProperty("muted", True)
    window.retry_send_btn = QPushButton("")
    window.retry_send_btn.setVisible(False)
    window.retry_send_btn.setProperty("variant", "danger")
    compose_meta.addWidget(window.delivery_state_label)
    compose_meta.addWidget(window.retry_send_btn)
    compose_meta.addStretch()

    window.attach_btn = QPushButton("")
    window.send_btn = QPushButton("")
    window.send_btn.setProperty("variant", "primary")
    window.send_btn.setMinimumWidth(80)
    compose_meta.addWidget(window.attach_btn)
    compose_meta.addWidget(window.send_btn)

    compose_box_layout.addWidget(window.message_input)
    compose_box_layout.addLayout(compose_meta)

    right_layout.addWidget(room_header)
    right_layout.addWidget(window.messages_list)
    right_layout.addWidget(compose_box)
    return right_panel


def connect_main_window_signals(window) -> None:
    window.profile_btn.clicked.connect(window.edit_profile_requested.emit)
    window.refresh_btn.clicked.connect(window.refresh_rooms_requested.emit)
    window.new_room_btn.clicked.connect(window.create_room_requested.emit)
    window.logout_btn.clicked.connect(window.logout_requested.emit)
    window.settings_btn.clicked.connect(window.open_settings_requested.emit)
    window.invite_btn.clicked.connect(window.invite_members_requested.emit)
    window.rename_btn.clicked.connect(window.rename_room_requested.emit)
    window.leave_btn.clicked.connect(window.leave_room_requested.emit)
    window.polls_btn.clicked.connect(window.open_polls_requested.emit)
    window.files_btn.clicked.connect(window.open_files_requested.emit)
    window.admin_btn.clicked.connect(window.open_admin_requested.emit)
    window.retry_send_btn.clicked.connect(window.retry_send_requested.emit)
    window.send_btn.clicked.connect(window._emit_send_message)
    window.attach_btn.clicked.connect(window._select_file)
    window.rooms_list.currentRowChanged.connect(window._on_room_row_changed)
    window.search_input.textChanged.connect(window.search_requested.emit)
    window.message_input.send_shortcut_triggered.connect(window._emit_send_message)
    window.message_input.textChanged.connect(window._on_message_text_changed)


def build_main_window_layout(window, composer_cls) -> QWidget:
    root = QWidget()
    root.setObjectName("AppRoot")

    layout = QVBoxLayout(root)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(build_sidebar_panel(window))
    splitter.addWidget(build_chat_panel(window, composer_cls))
    splitter.setSizes([330, 930])
    layout.addWidget(splitter)

    connect_main_window_signals(window)
    return root
