# -*- coding: utf-8 -*-
"""
Shared visual theme for desktop messenger UI.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


_BASE_STYLESHEET = """
QWidget {
    color: #1e293b;
    font-family: "Pretendard", "Segoe UI Variable", "Segoe UI", "Malgun Gothic", sans-serif;
    font-size: 10.5pt;
}

QMainWindow, QDialog {
    background: #f8fafc;
}

QWidget#AppRoot {
    background: #f8fafc;
}

QFrame[card="true"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
}

QFrame[sidebar="true"] {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
}

QFrame[chatArea="true"] {
    background: #ffffff;
}

QFrame[messageOwn="true"] {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 16px;
    border-top-right-radius: 4px;
}

QFrame[messageOwn="false"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    border-top-left-radius: 4px;
}

QLabel[title="true"] {
    font-size: 18pt;
    font-weight: 700;
    color: #0f172a;
}

QLabel[section="true"] {
    font-size: 13pt;
    font-weight: 700;
    color: #1e293b;
}

QLabel[subtitle="true"] {
    font-size: 10pt;
    color: #475569;
}

QLabel[muted="true"] {
    color: #94a3b8;
    font-size: 9.5pt;
}

QLabel[badge="true"] {
    background: #ef4444;
    color: #ffffff;
    font-weight: 700;
    font-size: 9pt;
    border-radius: 10px;
    padding: 2px 6px;
}

QLineEdit,
QTextEdit,
QListWidget {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 12px;
}

QTextEdit {
    padding-top: 8px;
}

QLineEdit:focus,
QTextEdit:focus,
QListWidget:focus {
    border: 1px solid #3b82f6;
}

QLineEdit::placeholder,
QTextEdit::placeholder {
    color: #94a3b8;
}

QListWidget {
    background: transparent;
    border: none;
}

QListWidget::item {
    border: none;
    border-radius: 8px;
    margin-bottom: 2px;
}

QListWidget::item:hover {
    background: #f1f5f9;
}

QListWidget::item:selected {
    background: #e2e8f0;
    color: #0f172a;
}

QPushButton {
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    padding: 8px 16px;
    font-weight: 600;
    color: #334155;
    min-height: 28px;
}

QPushButton:hover {
    background: #f8fafc;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background: #f1f5f9;
}

QPushButton:disabled {
    color: #94a3b8;
    border-color: #e2e8f0;
    background: #f8fafc;
}

QPushButton[variant="primary"] {
    color: #ffffff;
    border: 1px solid #2563eb;
    background: #3b82f6;
}

QPushButton[variant="primary"]:hover {
    border-color: #1d4ed8;
    background: #2563eb;
}

QPushButton[variant="primary"]:pressed {
    background: #1d4ed8;
}

QPushButton[variant="danger"] {
    color: #ef4444;
    border: 1px solid #fecaca;
    background: #ffffff;
}

QPushButton[variant="danger"]:hover {
    border-color: #f87171;
    background: #fef2f2;
}

QCheckBox {
    spacing: 8px;
}

QSplitter::handle {
    background: #e2e8f0;
    width: 1px;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    height: 0px;
}
"""


def apply_theme(app: QApplication) -> None:
    """Apply a unified palette and stylesheet for all PySide windows."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f8fafc"))
    palette.setColor(QPalette.WindowText, QColor("#1e293b"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.Text, QColor("#1e293b"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#334155"))
    palette.setColor(QPalette.Highlight, QColor("#3b82f6"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(_BASE_STYLESHEET)
