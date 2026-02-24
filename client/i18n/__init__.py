# -*- coding: utf-8 -*-
"""
Public i18n API for desktop client.
"""

from __future__ import annotations

from client.i18n.manager import I18NManager


i18n_manager = I18NManager(domain='client')


def t(key: str, fallback: str = '', **kwargs) -> str:
    return i18n_manager.t(key, fallback, **kwargs)
