# -*- coding: utf-8 -*-
"""
Shared visual theme for desktop messenger UI.

Design tokens, stylesheet definitions, palette and colour helpers.
"""

from __future__ import annotations

import colorsys
import hashlib

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


# ─────────────────────────────────────────────────────────
# Colour helpers
# ─────────────────────────────────────────────────────────

# 10 pre-tuned hues (saturation 55-65%, lightness 42-52%) for avatars.
_AVATAR_PALETTE: list[str] = [
    "#6366f1",  # indigo
    "#8b5cf6",  # violet
    "#ec4899",  # pink
    "#ef4444",  # red
    "#f97316",  # orange
    "#eab308",  # yellow
    "#22c55e",  # green
    "#14b8a6",  # teal
    "#0ea5e9",  # sky
    "#6d28d9",  # purple
]


def avatar_color(key: str) -> str:
    """Deterministic avatar background colour from a string key (username, id, etc.)."""
    digest = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()
    index = int(digest[:8], 16) % len(_AVATAR_PALETTE)
    return _AVATAR_PALETTE[index]


def avatar_text_color(bg_hex: str) -> str:
    """Return '#ffffff' or '#1e293b' depending on background luminance."""
    bg_hex = bg_hex.lstrip("#")
    r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#ffffff" if luminance < 160 else "#1e293b"


# ─────────────────────────────────────────────────────────
# Base stylesheet
# ─────────────────────────────────────────────────────────

_BASE_STYLESHEET = """
/* ========================================================= */
/* 글로벌 폰트 & 윈도우 기본                                    */
/* ========================================================= */
QWidget {
    color: #0f172a;
    font-family: "Pretendard", "Segoe UI Variable", "Segoe UI", "Malgun Gothic", sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
}

QMainWindow, QDialog, QWidget#AppRoot {
    background: #f1f5f9;
}

/* ========================================================= */
/* 레이아웃 & 패널                                              */
/* ========================================================= */
QFrame[card="true"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
}

QFrame[sidebar="true"] {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
    border-top-left-radius: 12px;
    border-bottom-left-radius: 12px;
}

QFrame[chatArea="true"] {
    background: #ffffff;
    border-top-right-radius: 12px;
    border-bottom-right-radius: 12px;
}

QFrame[separator="true"] {
    background: #e2e8f0;
    max-height: 1px;
    min-height: 1px;
    margin: 4px 0px;
}

/* ========================================================= */
/* 메시지 버블                                                 */
/* ========================================================= */
QFrame[messageOwn="true"] {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 18px;
    border-bottom-right-radius: 4px;
}

QFrame[messageOwn="false"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    border-bottom-left-radius: 4px;
}

/* ========================================================= */
/* 타이포그래피                                                 */
/* ========================================================= */
QLabel[title="true"] {
    font-size: 22pt;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
}

QLabel[section="true"] {
    font-size: 14pt;
    font-weight: 700;
    color: #1e293b;
}

QLabel[subtitle="true"] {
    font-size: 11pt;
    color: #475569;
    font-weight: 500;
}

QLabel[muted="true"] {
    color: #64748b;
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

/* --- 상태 뱃지 (연결/오프라인/경고) --- */
QLabel[status="connected"] {
    color: #065f46;
    background: #d1fae5;
    border-radius: 9px;
    padding: 3px 10px;
    font-size: 9pt;
    font-weight: 600;
}

QLabel[status="disconnected"] {
    color: #7f1d1d;
    background: #fee2e2;
    border-radius: 9px;
    padding: 3px 10px;
    font-size: 9pt;
    font-weight: 600;
}

QLabel[status="warning"] {
    color: #78350f;
    background: #fef3c7;
    border-radius: 9px;
    padding: 3px 10px;
    font-size: 9pt;
    font-weight: 600;
}

/* --- 배달 상태 뱃지 --- */
QLabel[delivery="pending"] {
    color: #7c2d12;
    background: #ffedd5;
    border-radius: 8px;
    padding: 2px 8px;
}

QLabel[delivery="failed"] {
    color: #7f1d1d;
    background: #fee2e2;
    border-radius: 8px;
    padding: 2px 8px;
}

/* --- 메시지 내부 라벨 --- */
QLabel[msgSender="true"] {
    color: #3b82f6;
    font-weight: 700;
    font-size: 9.5pt;
}

QLabel[msgReply="true"] {
    color: #64748b;
    font-size: 9pt;
    border-left: 2.5px solid #cbd5e1;
    padding-left: 8px;
}

QLabel[msgBody="true"] {
    font-size: 10.5pt;
    line-height: 1.5;
}

QLabel[msgBody="mention"] {
    background: rgba(250, 204, 21, 0.25);
    border-radius: 6px;
    padding: 4px 6px;
    font-size: 10.5pt;
}

QLabel[msgTime="true"] {
    font-size: 8pt;
    color: #94a3b8;
    margin-bottom: 2px;
}

/* ========================================================= */
/* 입력 폼 & 목록                                              */
/* ========================================================= */
QLineEdit,
QTextEdit {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
    color: #1e293b;
    selection-background-color: #bfdbfe;
    selection-color: #0f172a;
}

QTextEdit {
    padding-top: 10px;
}

QLineEdit:focus,
QTextEdit:focus {
    border: 2px solid #3b82f6;
    background: #ffffff;
}

QLineEdit:disabled,
QTextEdit:disabled {
    background: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}

QLineEdit::placeholder,
QTextEdit::placeholder {
    color: #94a3b8;
}

QListWidget {
    background: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    border: none;
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 4px;
}

QListWidget::item:hover {
    background: #f1f5f9;
}

QListWidget::item:selected {
    background: #e0ecff;
    color: #0f172a;
}

/* ========================================================= */
/* 버튼                                                       */
/* ========================================================= */
QPushButton {
    border-radius: 10px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    padding: 8px 18px;
    font-weight: 600;
    color: #334155;
    min-height: 32px;
}

QPushButton:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background: #e2e8f0;
}

QPushButton:disabled {
    color: #94a3b8;
    border-color: #e2e8f0;
    background: #f8fafc;
}

/* Primary Button */
QPushButton[variant="primary"] {
    color: #ffffff;
    border: 1px solid #2563eb;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #3b82f6, stop: 1 #2563eb);
}

QPushButton[variant="primary"]:hover {
    border-color: #1d4ed8;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2563eb, stop: 1 #1d4ed8);
}

QPushButton[variant="primary"]:pressed {
    background: #1e40af;
}

QPushButton[variant="primary"]:disabled {
    background: #93c5fd;
    border-color: #93c5fd;
    color: #e0ecff;
}

/* Danger Button */
QPushButton[variant="danger"] {
    color: #ef4444;
    border: 1px solid #fecaca;
    background: #ffffff;
}

QPushButton[variant="danger"]:hover {
    border-color: #f87171;
    background: #fef2f2;
}

QPushButton[variant="danger"]:pressed {
    background: #fee2e2;
}

/* Icon Button (circle, no border) */
QPushButton[variant="icon"] {
    border-radius: 18px;
    border: none;
    background: #e2e8f0;
    font-size: 14pt;
    padding: 0px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
}

QPushButton[variant="icon"]:hover {
    background: #cbd5e1;
}

QPushButton[variant="icon"]:pressed {
    background: #94a3b8;
}

/* ========================================================= */
/* ComboBox                                                   */
/* ========================================================= */
QComboBox {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 8px 14px;
    color: #1e293b;
    min-height: 32px;
    font-size: 10.5pt;
}

QComboBox:hover {
    border-color: #94a3b8;
}

QComboBox:focus {
    border: 2px solid #3b82f6;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}

QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #e0ecff;
    selection-color: #0f172a;
    outline: 0;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 6px;
    min-height: 28px;
}

QComboBox QAbstractItemView::item:hover {
    background: #f1f5f9;
}

/* ========================================================= */
/* DateTimeEdit                                               */
/* ========================================================= */
QDateTimeEdit {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 8px 14px;
    color: #1e293b;
    min-height: 32px;
    font-size: 10.5pt;
}

QDateTimeEdit:hover {
    border-color: #94a3b8;
}

QDateTimeEdit:focus {
    border: 2px solid #3b82f6;
}

QDateTimeEdit::up-button,
QDateTimeEdit::down-button {
    subcontrol-origin: border;
    width: 20px;
    border: none;
    background: transparent;
}

QDateTimeEdit::up-button:hover,
QDateTimeEdit::down-button:hover {
    background: #f1f5f9;
    border-radius: 4px;
}

/* ========================================================= */
/* 체크박스                                                    */
/* ========================================================= */
QCheckBox {
    spacing: 10px;
    color: #475569;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1.5px solid #cbd5e1;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #94a3b8;
}

QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
}

QCheckBox:disabled {
    color: #94a3b8;
}

QCheckBox::indicator:disabled {
    background-color: #f1f5f9;
    border-color: #e2e8f0;
}

/* ========================================================= */
/* 스플리터 & 스크롤바                                          */
/* ========================================================= */
QSplitter::handle {
    background: #e2e8f0;
    width: 2px;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 10px;
    margin: 4px 0px 4px 0px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 10px;
    margin: 0px 4px 0px 4px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 5px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    width: 0px;
}

/* ========================================================= */
/* 툴팁                                                       */
/* ========================================================= */
QToolTip {
    background: #1e293b;
    color: #f1f5f9;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 9.5pt;
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
    palette.setColor(QPalette.ToolTipBase, QColor("#1e293b"))
    palette.setColor(QPalette.ToolTipText, QColor("#f1f5f9"))
    app.setPalette(palette)
    app.setStyleSheet(_BASE_STYLESHEET)
