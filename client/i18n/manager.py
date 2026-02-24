# -*- coding: utf-8 -*-
"""
Desktop i18n manager with auto-detection and runtime language switch.
"""

from __future__ import annotations

import os
from typing import Callable

from PySide6.QtCore import QLocale, QSettings

from client.i18n.catalog_loader import DEFAULT, load_catalog, normalize_locale, to_display_locale


TranslateCallback = Callable[[], None]


class I18NManager:
    def __init__(self, domain: str = 'client'):
        self.domain = domain
        self._settings = QSettings('IntranetMessenger', 'Desktop')
        self._preference = 'auto'
        self._locale = DEFAULT
        self._catalog: dict[str, str] = {}
        self._fallback_catalog: dict[str, str] = load_catalog(self.domain, DEFAULT)
        self._callbacks: list[TranslateCallback] = []

    @property
    def preference(self) -> str:
        return self._preference

    @property
    def locale(self) -> str:
        return self._locale

    @property
    def display_locale(self) -> str:
        return to_display_locale(self._locale)

    def initialize(self) -> None:
        pref = self._normalize_preference(self._settings.value('ui/language', 'auto'))
        explicit = self._settings.value('ui/language_explicit', None)
        # Legacy migration: old clients may have stored 'en' without explicit user intent.
        # If explicit marker is missing, trust auto-detection.
        if pref in ('ko', 'en') and explicit is None:
            pref = 'auto'
        self.set_preference(pref, persist=False, notify=False)

    def detect_system_locale(self) -> str:
        def _from_hint(value: str | None) -> str:
            raw = (value or '').strip().lower().replace('_', '-')
            if not raw:
                return ''
            if '.' in raw:
                raw = raw.split('.', 1)[0]
            for token in raw.replace(';', ':').replace(',', ':').split(':'):
                token = token.strip()
                if token.startswith('ko'):
                    return 'ko'
                if token.startswith('en'):
                    return 'en'
            return ''

        try:
            system_locale = QLocale.system()
            # Prefer UI language ordering from OS. This is more reliable than
            # format locale on multilingual Windows environments.
            for lang in system_locale.uiLanguages() or []:
                detected = _from_hint(lang)
                if detected:
                    return detected
            detected = _from_hint(system_locale.name())  # e.g. ko_KR, en_US
            if detected:
                return detected
        except Exception:
            pass

        for key in ('LC_ALL', 'LANG', 'LANGUAGE'):
            detected = _from_hint(os.environ.get(key))
            if detected:
                return detected

        return DEFAULT

    def set_preference(self, preference: str, *, persist: bool = True, notify: bool = True) -> None:
        pref = self._normalize_preference(preference)
        self._preference = pref
        next_locale = self.detect_system_locale() if pref == 'auto' else pref
        self._locale = normalize_locale(next_locale)
        self._catalog = load_catalog(self.domain, self._locale)
        if persist:
            self._settings.setValue('ui/language', self._preference)
            self._settings.setValue('ui/language_explicit', self._preference != 'auto')
            self._settings.sync()
        if notify:
            self._notify()

    def subscribe(self, callback: TranslateCallback) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(self, callback: TranslateCallback) -> None:
        self._callbacks = [cb for cb in self._callbacks if cb is not callback]

    def _notify(self) -> None:
        for callback in list(self._callbacks):
            try:
                callback()
            except Exception:
                continue

    def t(self, key: str, fallback: str = '', **kwargs) -> str:
        text = self._catalog.get(key)
        if text is None:
            text = self._fallback_catalog.get(key)
        if text is None:
            text = fallback or key
        try:
            return text.format(**kwargs) if kwargs else text
        except Exception:
            return text

    @staticmethod
    def _normalize_preference(preference: object) -> str:
        raw = str(preference or 'auto').strip().lower().replace('_', '-')
        if raw in ('ko', 'ko-kr'):
            return 'ko'
        if raw in ('en', 'en-us'):
            return 'en'
        if raw == 'auto':
            return 'auto'
        return 'auto'
