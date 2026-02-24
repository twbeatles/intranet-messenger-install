# -*- coding: utf-8 -*-

from __future__ import annotations

from client.i18n.manager import I18NManager


def test_detect_system_locale_prefers_ui_languages(monkeypatch):
    import client.i18n.manager as manager_module

    class _Locale:
        def uiLanguages(self):
            return ['ko-KR', 'en-US']

        def name(self):
            return 'en_US'

    class _QLocale:
        @staticmethod
        def system():
            return _Locale()

    monkeypatch.setattr(manager_module, 'QLocale', _QLocale)

    manager = I18NManager(domain='client')
    assert manager.detect_system_locale() == 'ko'


def test_detect_system_locale_fallback_to_name(monkeypatch):
    import client.i18n.manager as manager_module

    class _Locale:
        def uiLanguages(self):
            return []

        def name(self):
            return 'en_US'

    class _QLocale:
        @staticmethod
        def system():
            return _Locale()

    monkeypatch.setattr(manager_module, 'QLocale', _QLocale)

    manager = I18NManager(domain='client')
    assert manager.detect_system_locale() == 'en'


def test_normalize_preference_accepts_display_locale_variants():
    manager = I18NManager(domain='client')
    assert manager._normalize_preference('ko-KR') == 'ko'
    assert manager._normalize_preference('en-US') == 'en'
    assert manager._normalize_preference('invalid') == 'auto'


def test_initialize_migrates_legacy_language_without_explicit(monkeypatch):
    class _DummySettings:
        def __init__(self):
            self.data = {'ui/language': 'en'}

        def value(self, key, default=None, **kwargs):
            return self.data.get(key, default)

        def setValue(self, key, value):
            self.data[key] = value

        def sync(self):
            return None

    manager = I18NManager(domain='client')
    manager._settings = _DummySettings()  # type: ignore[assignment]
    monkeypatch.setattr(manager, 'detect_system_locale', lambda: 'ko')
    manager.initialize()
    assert manager.preference == 'auto'
    assert manager.locale == 'ko'


def test_initialize_keeps_explicit_user_language(monkeypatch):
    class _DummySettings:
        def __init__(self):
            self.data = {
                'ui/language': 'en',
                'ui/language_explicit': True,
            }

        def value(self, key, default=None, **kwargs):
            return self.data.get(key, default)

        def setValue(self, key, value):
            self.data[key] = value

        def sync(self):
            return None

    manager = I18NManager(domain='client')
    manager._settings = _DummySettings()  # type: ignore[assignment]
    monkeypatch.setattr(manager, 'detect_system_locale', lambda: 'ko')
    manager.initialize()
    assert manager.preference == 'en'
    assert manager.locale == 'en'
