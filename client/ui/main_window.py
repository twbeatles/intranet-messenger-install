# -*- coding: utf-8 -*-
"""
Main desktop messenger UI.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

from client.i18n import i18n_manager, t
from client.ui.main_window_sections import build_main_window_layout
from client.ui.message_formatters import contains_mention, format_reactions
from client.ui.message_list import build_message_container
from client.ui.room_list import build_room_item_widget, populate_rooms_list


class _ComposerTextEdit(QTextEdit):
    send_shortcut_triggered = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            event.accept()
            self.send_shortcut_triggered.emit()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    user_label: QLabel
    connection_label: QLabel
    settings_btn: QPushButton
    profile_btn: QPushButton
    search_input: QLineEdit
    rooms_list: QListWidget
    new_room_btn: QPushButton
    refresh_btn: QPushButton
    logout_btn: QPushButton
    room_title: QLabel
    room_meta: QLabel
    invite_btn: QPushButton
    rename_btn: QPushButton
    leave_btn: QPushButton
    polls_btn: QPushButton
    files_btn: QPushButton
    admin_btn: QPushButton
    messages_list: QListWidget
    message_input: _ComposerTextEdit
    compose_hint_label: QLabel
    delivery_state_label: QLabel
    retry_send_btn: QPushButton
    attach_btn: QPushButton
    send_btn: QPushButton
    _inbox_title_label: QLabel

    room_selected = Signal(int)
    refresh_rooms_requested = Signal()
    create_room_requested = Signal()
    invite_members_requested = Signal()
    rename_room_requested = Signal()
    leave_room_requested = Signal()
    edit_profile_requested = Signal()
    send_message_requested = Signal(str)
    logout_requested = Signal()
    search_requested = Signal(str)
    startup_toggled = Signal(bool)
    close_to_tray_requested = Signal()
    open_settings_requested = Signal()
    open_polls_requested = Signal()
    open_files_requested = Signal()
    open_admin_requested = Signal()
    send_file_requested = Signal(str)  # local path
    load_older_messages_requested = Signal(int)  # before message id
    typing_changed = Signal(bool)
    retry_send_requested = Signal()

    def __init__(self):
        super().__init__()
        self.resize(1260, 780)
        self.setMinimumSize(1080, 680)
        self.minimize_to_tray = True
        self._room_id_by_row: dict[int, int] = {}
        self._user_aliases: set[str] = set()
        self._current_user_id: int = 0
        self._current_room_name = t('main.select_room', 'Select a room')
        self._room_meta_base = t('main.select_room_desc', 'Choose a conversation from the left list.')
        self._typing_user = ''
        self._max_rendered_messages = 600
        self._connected = False
        self._history_has_more = False
        self._history_loading = False
        self._history_scroll_blocked = False
        self._history_banner_key = '__history_banner__'
        self._message_row_by_id: dict[int, int] = {}
        self._message_row_index_dirty = False
        self._delivery_state = 'idle'
        self._delivery_count = 0
        self._build_ui()
        i18n_manager.subscribe(self.retranslate_ui)
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = build_main_window_layout(self, _ComposerTextEdit)
        self.setCentralWidget(root)
        self._set_room_actions_enabled(False)

    # ── Public API ──────────────────────────────────────────

    def set_user(self, user: dict[str, Any]) -> None:
        nickname = user.get('nickname') or user.get('username') or t('common.unknown', 'Unknown')
        username = user.get('username')
        try:
            self._current_user_id = int(user.get('id') or 0)
        except (TypeError, ValueError):
            self._current_user_id = 0
        if username and username != nickname:
            self.user_label.setText(f'{nickname} (@{username})')
        else:
            self.user_label.setText(str(nickname))
        self._user_aliases = {str(v) for v in (nickname, username) if v}

    def set_connected(self, connected: bool) -> None:
        self._set_connection_style(connected)

    def select_room(self, room_id: int) -> None:
        for row, mapped_id in self._room_id_by_row.items():
            if int(mapped_id) == int(room_id):
                self.rooms_list.setCurrentRow(row)
                return

    def clear_room_selection(self) -> None:
        self.rooms_list.setCurrentRow(-1)
        self.set_messages([], has_more=False)
        self.set_room_title(t('main.select_room', 'Select a room'))
        self._set_room_actions_enabled(False)

    def set_rooms(self, rooms: list[dict[str, Any]]) -> None:
        populate_rooms_list(self, rooms)

    def set_room_title(self, title: str) -> None:
        self._current_room_name = title or t('main.select_room', 'Select a room')
        self.room_title.setText(self._current_room_name)
        self._update_compose_hint()

    def set_messages(self, messages: list[dict[str, Any]], has_more: bool = False) -> None:
        self._history_scroll_blocked = True
        self.messages_list.clear()
        self._clear_message_row_index()
        self._history_has_more = bool(has_more)
        self._history_loading = False

        if len(messages) > self._max_rendered_messages:
            messages = messages[-self._max_rendered_messages:]
        if not messages:
            placeholder = QListWidgetItem(t('main.messages_empty', 'No messages yet.'))
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            placeholder.setData(Qt.ItemDataRole.UserRole, '__placeholder__')
            self.messages_list.addItem(placeholder)
            self._history_scroll_blocked = False
            return

        if self._history_has_more:
            self._insert_history_banner()

        for message in messages:
            self._append_message_item(message)
        self._rebuild_message_row_index()
        self._update_history_banner()
        self.messages_list.scrollToBottom()
        self._history_scroll_blocked = False

    def prepend_messages(self, messages: list[dict[str, Any]], has_more: bool) -> None:
        self._history_scroll_blocked = True
        self._history_has_more = bool(has_more)
        self._history_loading = False

        if not messages:
            self._update_history_banner()
            self._history_scroll_blocked = False
            return

        scrollbar = self.messages_list.verticalScrollBar()
        prev_value = scrollbar.value()
        prev_max = scrollbar.maximum()

        if self.messages_list.count() == 1:
            first = self.messages_list.item(0)
            if first and str(first.data(Qt.ItemDataRole.UserRole) or '') == '__placeholder__':
                self.messages_list.clear()

        if self._history_has_more and not self._has_history_banner():
            self._insert_history_banner()

        for message in reversed(messages):
            self._insert_message_item(message, at_top=True)

        while self.messages_list.count() > self._max_rendered_messages + (1 if self._has_history_banner() else 0):
            self.messages_list.takeItem(self.messages_list.count() - 1)

        self._rebuild_message_row_index()
        self._update_history_banner()

        new_max = scrollbar.maximum()
        delta = max(0, new_max - prev_max)
        scrollbar.setValue(prev_value + delta)
        self._history_scroll_blocked = False

    def append_message(self, message: dict[str, Any]) -> None:
        if self.messages_list.count() == 1:
            first_item = self.messages_list.item(0)
            if first_item and str(first_item.data(Qt.ItemDataRole.UserRole) or '') == '__placeholder__':
                self.messages_list.clear()
                self._clear_message_row_index()
        self._append_message_item(message)
        trimmed = False
        while self.messages_list.count() > self._max_rendered_messages + (1 if self._has_history_banner() else 0):
            remove_index = 1 if self._has_history_banner() else 0
            self.messages_list.takeItem(remove_index)
            trimmed = True
        if trimmed:
            self._rebuild_message_row_index()
        else:
            try:
                message_id = int((message or {}).get('id') or 0)
            except (TypeError, ValueError):
                message_id = 0
            if message_id > 0:
                self._message_row_by_id[message_id] = self.messages_list.count() - 1
        self.messages_list.scrollToBottom()

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, t('common.error', 'Error'), message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, t('common.info', 'Info'), message)

    # ── Private slots ───────────────────────────────────────

    def _emit_send_message(self) -> None:
        text = self.message_input.toPlainText().strip()
        if not text:
            return
        self.send_message_requested.emit(text)
        self.message_input.clear()
        self._update_compose_hint()

    def _on_message_text_changed(self) -> None:
        self._update_compose_hint()
        self.typing_changed.emit(bool(self.message_input.toPlainText().strip()))

    def set_delivery_state(self, state: str, count: int = 0) -> None:
        self._delivery_state = state
        self._delivery_count = max(0, int(count))

        if state == 'pending' and self._delivery_count > 0:
            self.delivery_state_label.setText(
                t('main.delivery_pending', 'Sending... ({count})', count=self._delivery_count)
            )
            self.delivery_state_label.setProperty('delivery', 'pending')
            self.delivery_state_label.style().unpolish(self.delivery_state_label)
            self.delivery_state_label.style().polish(self.delivery_state_label)
            self.retry_send_btn.setVisible(False)
            return

        if state == 'failed' and self._delivery_count > 0:
            self.delivery_state_label.setText(
                t('main.delivery_failed', 'Failed to send ({count})', count=self._delivery_count)
            )
            self.delivery_state_label.setProperty('delivery', 'failed')
            self.delivery_state_label.style().unpolish(self.delivery_state_label)
            self.delivery_state_label.style().polish(self.delivery_state_label)
            self.retry_send_btn.setVisible(True)
            return

        self.delivery_state_label.setText('')
        self.delivery_state_label.setProperty('delivery', '')
        self.delivery_state_label.style().unpolish(self.delivery_state_label)
        self.delivery_state_label.style().polish(self.delivery_state_label)
        self.retry_send_btn.setVisible(False)

    def _select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, t('main.select_file', 'Select file'))
        if path:
            self.send_file_requested.emit(path)

    def _on_room_row_changed(self, row: int) -> None:
        room_id = self._room_id_by_row.get(row)
        if room_id:
            self._set_room_actions_enabled(True)
            self._room_meta_base = t('main.room_number', 'Room #{room_id}', room_id=room_id)
            self._typing_user = ''
            self._update_room_meta_label()
            self.room_selected.emit(room_id)
            return

        self._set_room_actions_enabled(False)
        self.room_title.setText(t('main.select_room', 'Select a room'))
        self._room_meta_base = t('main.select_room_desc', 'Choose a conversation from the left list.')
        self._typing_user = ''
        self._update_room_meta_label()
        self.compose_hint_label.setText(t('main.compose_no_room', 'No room selected'))

    def _set_connection_style(self, connected: bool) -> None:
        self._connected = connected
        if connected:
            self.connection_label.setText(t('common.connected', 'Connected'))
            self.connection_label.setProperty('status', 'connected')
        else:
            self.connection_label.setText(t('common.disconnected', 'Disconnected'))
            self.connection_label.setProperty('status', 'disconnected')
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)

    def _set_room_actions_enabled(self, enabled: bool) -> None:
        self.polls_btn.setEnabled(enabled)
        self.files_btn.setEnabled(enabled)
        self.admin_btn.setEnabled(enabled)
        self.invite_btn.setEnabled(enabled)
        self.rename_btn.setEnabled(enabled)
        self.leave_btn.setEnabled(enabled)
        self.message_input.setEnabled(enabled)
        self.attach_btn.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self._update_compose_hint()

    def _update_compose_hint(self) -> None:
        if not self.message_input.isEnabled():
            self.compose_hint_label.setText(t('main.compose_no_room', 'No room selected'))
            return
        char_count = len(self.message_input.toPlainText())
        self.compose_hint_label.setText(
            t(
                'main.compose_hint_format',
                '{room} | {count} chars | Ctrl+Enter to send',
                room=self._current_room_name,
                count=char_count,
            )
        )

    # ── Message rendering ───────────────────────────────────

    def _append_message_item(self, message: dict[str, Any]) -> None:
        self._insert_message_item(message, at_top=False)

    def _insert_message_item(self, message: dict[str, Any], *, at_top: bool) -> None:
        message_copy = dict(message or {})
        container = self._build_message_container(message_copy)
        message_id = 0
        try:
            message_id = int(message_copy.get('id') or 0)
        except Exception:
            message_id = 0

        item = QListWidgetItem()
        if message_id > 0:
            item.setData(Qt.ItemDataRole.UserRole, int(message_id))
            item.setData(Qt.ItemDataRole.UserRole + 1, message_copy)
        item.setSizeHint(container.sizeHint())
        if at_top:
            insert_row = 1 if self._has_history_banner() else 0
            self.messages_list.insertItem(insert_row, item)
            if message_id > 0:
                self._message_row_index_dirty = True
        else:
            self.messages_list.addItem(item)
            if message_id > 0:
                self._message_row_by_id[message_id] = self.messages_list.count() - 1
        self.messages_list.setItemWidget(item, container)

    def _build_message_container(self, message: dict[str, Any]) -> QWidget:
        return build_message_container(self, message)

    # ── Message index management ────────────────────────────

    def _find_message_row(self, message_id: int) -> int:
        if message_id <= 0:
            return -1
        if self._message_row_index_dirty:
            self._rebuild_message_row_index()
        return int(self._message_row_by_id.get(int(message_id), -1))

    def _clear_message_row_index(self) -> None:
        self._message_row_by_id.clear()
        self._message_row_index_dirty = False

    def _rebuild_message_row_index(self) -> None:
        self._message_row_by_id.clear()
        start = 1 if self._has_history_banner() else 0
        for row in range(start, self.messages_list.count()):
            item = self.messages_list.item(row)
            if not item:
                continue
            try:
                message_id = int(item.data(Qt.ItemDataRole.UserRole) or 0)
            except (TypeError, ValueError):
                message_id = 0
            if message_id > 0:
                self._message_row_by_id[message_id] = row
        self._message_row_index_dirty = False

    def _replace_message_item(self, row: int, message: dict[str, Any]) -> bool:
        if row < 0 or row >= self.messages_list.count():
            return False
        item = self.messages_list.item(row)
        if not item:
            return False
        item.setData(Qt.ItemDataRole.UserRole + 1, dict(message))
        widget = self._build_message_container(dict(message))
        item.setSizeHint(widget.sizeHint())
        self.messages_list.setItemWidget(item, widget)
        return True

    def update_message_reactions(self, message_id: int, reactions: list[dict[str, Any]]) -> bool:
        row = self._find_message_row(message_id)
        if row < 0:
            return False
        item = self.messages_list.item(row)
        if not item:
            return False
        stored = item.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(stored, dict):
            return False
        updated = dict(stored)
        updated['reactions'] = reactions
        return self._replace_message_item(row, updated)

    def update_message_content(
        self,
        *,
        message_id: int,
        content: str,
        display_content: str,
        encrypted: bool,
    ) -> bool:
        row = self._find_message_row(message_id)
        if row < 0:
            return False
        item = self.messages_list.item(row)
        if not item:
            return False
        stored = item.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(stored, dict):
            return False
        updated = dict(stored)
        updated['content'] = content
        updated['display_content'] = display_content
        updated['encrypted'] = bool(encrypted)
        return self._replace_message_item(row, updated)

    def mark_message_deleted(self, message_id: int) -> bool:
        row = self._find_message_row(message_id)
        if row < 0:
            return False
        item = self.messages_list.item(row)
        if not item:
            return False
        stored = item.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(stored, dict):
            return False
        updated = dict(stored)
        deleted_text = t('main.message_deleted', '[deleted message]')
        updated['content'] = deleted_text
        updated['display_content'] = deleted_text
        updated['encrypted'] = False
        updated['file_path'] = ''
        updated['file_name'] = ''
        updated['message_type'] = 'text'
        return self._replace_message_item(row, updated)

    # ── History banner ──────────────────────────────────────

    def _on_messages_scrolled(self, value: int) -> None:
        if self._history_scroll_blocked or value > 2 or not self._history_has_more or self._history_loading:
            return
        oldest_message_id = self._get_oldest_rendered_message_id()
        if oldest_message_id <= 0:
            return
        self._history_loading = True
        self._update_history_banner()
        self.load_older_messages_requested.emit(oldest_message_id)

    def _get_oldest_rendered_message_id(self) -> int:
        start = 1 if self._has_history_banner() else 0
        for row in range(start, self.messages_list.count()):
            item = self.messages_list.item(row)
            if not item:
                continue
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, int) and data > 0:
                return int(data)
        return 0

    def _has_history_banner(self) -> bool:
        if self.messages_list.count() == 0:
            return False
        item = self.messages_list.item(0)
        if not item:
            return False
        return str(item.data(Qt.ItemDataRole.UserRole) or '') == self._history_banner_key

    def _insert_history_banner(self) -> None:
        if self._has_history_banner():
            return
        banner = QListWidgetItem('')
        banner.setFlags(Qt.ItemFlag.NoItemFlags)
        banner.setData(Qt.ItemDataRole.UserRole, self._history_banner_key)
        self.messages_list.insertItem(0, banner)
        self._message_row_index_dirty = True

    def _update_history_banner(self) -> None:
        if self._history_has_more and not self._has_history_banner():
            self._insert_history_banner()

        if not self._has_history_banner():
            return

        banner = self.messages_list.item(0)
        if not banner:
            return

        if self._history_loading:
            banner.setText(t('main.history_loading', 'Loading earlier messages...'))
            return

        if self._history_has_more:
            banner.setText(t('main.history_more_hint', 'Scroll up to load earlier messages'))
            return

        banner.setText(t('main.history_reached_start', 'Reached the beginning of the conversation'))

    # ── Typing indicator ────────────────────────────────────

    def set_typing_user(self, user_id: int, nickname: str, is_typing: bool) -> None:
        sender = (nickname or '').strip()
        if int(user_id or 0) == int(self._current_user_id):
            sender = ''
        self._typing_user = sender if is_typing else ''
        self._update_room_meta_label()

    def _update_room_meta_label(self) -> None:
        meta = self._room_meta_base or t('main.select_room_desc', 'Choose a conversation from the left list.')
        if self._typing_user:
            self.room_meta.setText(
                t(
                    'main.typing_meta',
                    '{meta} | ✏️ {user} is typing...',
                    meta=meta,
                    user=self._typing_user,
                )
            )
            return
        self.room_meta.setText(meta)

    def _contains_mention(self, content: str) -> bool:
        return contains_mention(self._user_aliases, content)

    @staticmethod
    def _format_reactions(reactions: Any) -> str:
        return format_reactions(reactions)

    # ── Room list item widget ───────────────────────────────

    def _build_room_item_widget(self, room: dict[str, Any]) -> QWidget:
        return build_room_item_widget(room)

    # ── i18n retranslation ──────────────────────────────────

    def retranslate_ui(self) -> None:
        self.setWindowTitle(t('app.desktop_title', 'Intranet Messenger Desktop'))
        self._inbox_title_label.setText(t('main.conversations', 'Conversations'))
        self.search_input.setPlaceholderText(t('main.search_placeholder', 'Search rooms or previews'))
        self.profile_btn.setText(t('main.profile', 'Profile'))
        self.new_room_btn.setText(t('main.new_room', 'New Room'))
        self.refresh_btn.setText(t('main.refresh', 'Refresh'))
        self.settings_btn.setText(t('main.settings', 'Settings'))
        self.logout_btn.setText(t('main.logout', 'Logout'))
        self.invite_btn.setText(t('main.invite_members', 'Invite'))
        self.rename_btn.setText(t('main.rename_room', 'Rename'))
        self.leave_btn.setText(t('main.leave_room', 'Leave'))
        self.polls_btn.setText(t('main.polls', 'Polls'))
        self.files_btn.setText(t('main.files', 'Files'))
        self.admin_btn.setText(t('main.admin', 'Admin'))
        self.message_input.setPlaceholderText(t('main.compose_placeholder', 'Write a message... (Ctrl+Enter to send)'))
        self.attach_btn.setText(t('main.attach', 'Attach'))
        self.send_btn.setText(t('main.send', 'Send'))
        self.retry_send_btn.setText(t('main.retry_send', 'Retry'))
        if not self.message_input.isEnabled():
            self._current_room_name = t('main.select_room', 'Select a room')
            self.room_title.setText(self._current_room_name)
            self._room_meta_base = t('main.select_room_desc', 'Choose a conversation from the left list.')
            self._typing_user = ''
            self._update_room_meta_label()
        self._set_connection_style(self._connected)
        self._update_compose_hint()
        self.set_delivery_state(self._delivery_state, self._delivery_count)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.minimize_to_tray:
            event.ignore()
            self.hide()
            self.close_to_tray_requested.emit()
            return
        super().closeEvent(event)
