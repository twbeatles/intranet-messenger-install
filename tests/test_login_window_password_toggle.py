# -*- coding: utf-8 -*-
"""LoginWindow 비밀번호 표시 토글 회귀 테스트.

``QLineEdit.addAction`` 은 ``None`` 을 반환하므로 반환값을 액션으로 쓰면
``RuntimeError('password visibility action could not be created')`` 가 발생한다.
이 테스트는 로그인 창 생성과 토글 동작을 Headless(offscreen)로 검증한다.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PySide6 = pytest.importorskip("PySide6.QtWidgets")


def _ensure_app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_login_window_builds_password_toggle():
    _ensure_app()
    from PySide6.QtWidgets import QLineEdit

    from client.ui.login_window import LoginWindow

    # 기존 버그에서는 이 생성자에서 RuntimeError가 발생했다.
    window = LoginWindow()
    try:
        assert window.password_input.echoMode() == QLineEdit.EchoMode.Password
        assert window._toggle_pw_action is not None
        actions = window.password_input.actions()
        assert window._toggle_pw_action in actions
    finally:
        window.close()


def test_password_visibility_toggle_flips_echo_mode():
    _ensure_app()
    from PySide6.QtWidgets import QLineEdit

    from client.ui.login_window import LoginWindow

    window = LoginWindow()
    try:
        window._toggle_password_visibility()
        assert window.password_input.echoMode() == QLineEdit.EchoMode.Normal
        window._toggle_password_visibility()
        assert window.password_input.echoMode() == QLineEdit.EchoMode.Password
    finally:
        window.close()
