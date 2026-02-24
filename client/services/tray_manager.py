# -*- coding: utf-8 -*-
"""
System tray helper for desktop client.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayManager(QObject):
    show_requested = Signal()
    quit_requested = Signal()
    logout_requested = Signal()

    def __init__(self, app_name: str = 'Intranet Messenger', translator: Callable[[str, str], str] | None = None):
        super().__init__()
        self.app_name = app_name
        self._tr = translator or (lambda _key, fallback='': fallback)
        self._tray = QSystemTrayIcon(self._build_icon())
        self._tray.setToolTip(app_name)
        self._menu = self._build_menu()
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)
        self.retranslate()

    def _build_icon(self) -> QIcon:
        pix = QPixmap(32, 32)
        pix.fill(QColor('#1f2937'))
        painter = QPainter(pix)
        painter.setPen(QColor('#10b981'))
        painter.setFont(QFont('Segoe UI', 18, QFont.Bold))
        painter.drawText(pix.rect(), Qt.AlignCenter, 'M')
        painter.end()
        return QIcon(pix)

    def _build_menu(self) -> QMenu:
        menu = QMenu()
        self._open_action = QAction('', menu)
        self._open_action.triggered.connect(self.show_requested.emit)
        menu.addAction(self._open_action)

        self._logout_action = QAction('', menu)
        self._logout_action.triggered.connect(self.logout_requested.emit)
        menu.addAction(self._logout_action)

        menu.addSeparator()

        self._quit_action = QAction('', menu)
        self._quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(self._quit_action)
        return menu

    def set_translator(self, translator: Callable[[str, str], str]) -> None:
        self._tr = translator
        self.retranslate()

    def retranslate(self) -> None:
        self._tray.setToolTip(self.app_name)
        self._open_action.setText(self._tr('tray.open', 'Open'))
        self._logout_action.setText(self._tr('tray.logout', 'Logout'))
        self._quit_action.setText(self._tr('tray.quit', 'Quit'))

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def notify(self, title: str, message: str) -> None:
        self._tray.showMessage(title, message, QSystemTrayIcon.Information, 2500)
