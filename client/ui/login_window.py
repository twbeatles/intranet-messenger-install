# -*- coding: utf-8 -*-
"""
Login window for desktop messenger.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from client.i18n import i18n_manager, t


class LoginWindow(QDialog):
    login_requested = Signal(str, str, str, str, bool)  # server_url, username, password, device_name, remember
    register_requested = Signal(str, str, str, str)  # server_url, username, password, nickname

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 520)
        self.setObjectName("AppRoot")
        self._build_ui()
        i18n_manager.subscribe(self.retranslate_ui)
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel('')
        title.setProperty('title', True)
        subtitle = QLabel('')
        subtitle.setProperty('subtitle', True)
        root.addWidget(title)
        root.addWidget(subtitle)
        self._title_label = title
        self._subtitle_label = subtitle

        card = QFrame()
        card.setProperty('card', True)
        root.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)

        section = QLabel('')
        section.setProperty('section', True)
        card_layout.addWidget(section)
        self._section_label = section

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.server_url_input = QLineEdit('http://127.0.0.1:5000')
        self.server_url_label = QLabel('')
        form.addRow(self.server_url_label, self.server_url_input)

        self.username_input = QLineEdit()
        self.username_label = QLabel('')
        form.addRow(self.username_label, self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_label = QLabel('')
        form.addRow(self.password_label, self.password_input)

        self.nickname_input = QLineEdit()
        self.nickname_label = QLabel('')
        form.addRow(self.nickname_label, self.nickname_input)

        self.device_name_input = QLineEdit('Windows Desktop')
        self.device_name_label = QLabel('')
        form.addRow(self.device_name_label, self.device_name_input)

        self.remember_check = QCheckBox('')
        self.remember_check.setChecked(True)
        form.addRow('', self.remember_check)

        card_layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.login_btn = QPushButton('')
        self.register_btn = QPushButton('')
        self.login_btn.setProperty('variant', 'primary')
        btn_row.addWidget(self.login_btn)
        btn_row.addWidget(self.register_btn)
        card_layout.addLayout(btn_row)

        help_text = QLabel('')
        help_text.setWordWrap(True)
        help_text.setProperty('muted', True)
        card_layout.addWidget(help_text)
        self._help_label = help_text

        self.status_label = QLabel('')
        self.status_label.setProperty('muted', True)
        root.addWidget(self.status_label)
        root.addStretch()

        self.login_btn.clicked.connect(self._on_login_clicked)
        self.register_btn.clicked.connect(self._on_register_clicked)
        self.password_input.returnPressed.connect(self._on_login_clicked)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

    def set_server_url(self, server_url: str) -> None:
        self.server_url_input.setText(server_url)

    def set_busy(self, busy: bool) -> None:
        self.server_url_input.setEnabled(not busy)
        self.username_input.setEnabled(not busy)
        self.password_input.setEnabled(not busy)
        self.nickname_input.setEnabled(not busy)
        self.device_name_input.setEnabled(not busy)
        self.remember_check.setEnabled(not busy)
        self.login_btn.setEnabled(not busy)
        self.register_btn.setEnabled(not busy)
        self.status_label.setText(t('login.signing_in', 'Signing in...') if busy else '')
        self.setCursor(Qt.WaitCursor if busy else Qt.ArrowCursor)

    def _read_common(self) -> tuple[str, str, str]:
        server_url = self.server_url_input.text().strip().rstrip('/')
        username = self.username_input.text().strip()
        password = self.password_input.text()
        return server_url, username, password

    def _on_login_clicked(self) -> None:
        server_url, username, password = self._read_common()
        device_name = self.device_name_input.text().strip() or 'Windows Desktop'
        if not server_url or not username or not password:
            self.show_error(t('login.required_fields', 'Server URL, username and password are required.'))
            self.status_label.setText(t('login.required_fields', 'Server URL, username and password are required.'))
            return
        self.login_requested.emit(
            server_url,
            username,
            password,
            device_name,
            self.remember_check.isChecked(),
        )

    def _on_register_clicked(self) -> None:
        server_url, username, password = self._read_common()
        nickname = self.nickname_input.text().strip() or username
        if not server_url or not username or not password:
            self.show_error(t('login.required_fields', 'Server URL, username and password are required.'))
            self.status_label.setText(t('login.required_fields', 'Server URL, username and password are required.'))
            return
        self.register_requested.emit(server_url, username, password, nickname)

    def show_error(self, message: str) -> None:
        self.status_label.setText(message)
        QMessageBox.critical(self, t('common.error', 'Error'), message)

    def show_info(self, message: str) -> None:
        self.status_label.setText(message)
        QMessageBox.information(self, t('common.info', 'Info'), message)

    def retranslate_ui(self) -> None:
        self.setWindowTitle(t('login.window_title', 'Intranet Messenger Sign In'))
        self._title_label.setText(t('login.title', 'Intranet Messenger'))
        self._subtitle_label.setText(
            t('login.subtitle', 'Desktop-native secure chat for internal teams.')
        )
        self._section_label.setText(t('login.section.account_access', 'Account Access'))

        self.server_url_label.setText(t('login.server_url', 'Server URL'))
        self.username_label.setText(t('login.username', 'Username'))
        self.password_label.setText(t('login.password', 'Password'))
        self.nickname_label.setText(t('login.nickname', 'Nickname'))
        self.device_name_label.setText(t('login.device_name', 'Device'))

        self.server_url_input.setPlaceholderText('http://server:5000')
        self.username_input.setPlaceholderText(t('login.username', 'Username').lower())
        self.password_input.setPlaceholderText(t('login.password', 'Password').lower())
        self.nickname_input.setPlaceholderText(t('login.nickname', 'Nickname'))
        self.device_name_input.setPlaceholderText(t('login.device_name', 'Device'))

        self.remember_check.setText(t('login.remember', 'Remember this device'))
        self.login_btn.setText(t('common.login', 'Login'))
        self.register_btn.setText(t('common.register', 'Register'))
        self._help_label.setText(
            t(
                'login.help',
                'Tip: Login uses device session tokens. Register creates an account if it does not exist.',
            )
        )
