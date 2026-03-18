# -*- coding: utf-8 -*-

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QLabel


class ToastWidget(QLabel):
    def __init__(self, parent=None, message: str = "", toast_type: str = "info", duration: int = 3000):
        super().__init__(parent)
        styles = {
            "success": ("✅", "#22C55E", "#0F3D0F"),
            "error": ("❌", "#EF4444", "#3D0F0F"),
            "warning": ("⚠️", "#F59E0B", "#3D2E0F"),
            "info": ("ℹ️", "#3B82F6", "#0F1D3D"),
        }
        icon, border_color, bg_color = styles.get(toast_type, styles["info"])
        self.setText(f"{icon} {message}")
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg_color};
                color: #F8FAFC;
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: 500;
            }}
            """
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adjustSize()

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
        QTimer.singleShot(duration, self._start_fade_out)

    def _start_fade_out(self):
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.fade_anim.finished.connect(self.deleteLater)
        self.fade_anim.start()
