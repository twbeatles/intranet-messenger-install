# -*- coding: utf-8 -*-

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


def create_server_tray(window):
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("#10B981"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "💬")
    painter.end()

    tray_icon = QSystemTrayIcon(QIcon(pixmap), window)
    tray_menu = QMenu()

    show_action = QAction(window._tr("tray.open_window", "창 열기"), window)
    show_action.triggered.connect(window.show_window)
    tray_menu.addAction(show_action)
    tray_menu.addSeparator()

    start_action = QAction(window._tr("tray.start_server", "서버 시작"), window)
    start_action.triggered.connect(window.start_server)
    tray_menu.addAction(start_action)

    stop_action = QAction(window._tr("tray.stop_server", "서버 중지"), window)
    stop_action.triggered.connect(window.stop_server)
    tray_menu.addAction(stop_action)
    tray_menu.addSeparator()

    quit_action = QAction(window._tr("tray.quit", "종료"), window)
    quit_action.triggered.connect(window.quit_app)
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(window.tray_activated)
    tray_icon.show()
    return tray_icon, tray_menu, show_action, start_action, stop_action, quit_action
