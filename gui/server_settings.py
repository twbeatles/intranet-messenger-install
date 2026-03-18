# -*- coding: utf-8 -*-

from __future__ import annotations

import locale as pylocale

import winreg

from config import APP_NAME, DEFAULT_PORT, USE_HTTPS
from app.i18n import load_catalog, normalize_locale, to_display_locale


def detect_system_locale() -> str:
    try:
        code = pylocale.getdefaultlocale()[0]
    except Exception:
        code = None
    return normalize_locale(code)


def resolve_locale(preference: str) -> str:
    pref = (preference or "auto").strip().lower()
    if pref in ("ko", "en"):
        return pref
    return detect_system_locale()


def apply_language_preference(window, preference: str, *, persist: bool = True) -> None:
    pref = (preference or "auto").strip().lower()
    if pref not in ("auto", "ko", "en"):
        pref = "auto"
    window.language_preference = pref
    window.locale_code = resolve_locale(pref)
    window.display_locale = to_display_locale(window.locale_code)
    window.i18n_catalog = load_catalog(window.locale_code, "server_gui")
    if persist:
        window.settings.setValue("ui/language", window.language_preference)
    window.retranslate_ui()


def load_window_settings(window) -> None:
    window.port_spin.setValue(window.settings.value("port", DEFAULT_PORT, type=int))
    window.auto_start_check.setChecked(window.settings.value("auto_start_server", True, type=bool))
    window.minimize_to_tray_check.setChecked(window.settings.value("minimize_to_tray", True, type=bool))
    window.https_check.setChecked(window.settings.value("use_https", USE_HTTPS, type=bool))
    stored_language = str(window.settings.value("ui/language", window.language_preference) or "auto").lower()
    apply_language_preference(window, stored_language, persist=False)

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            window.windows_startup_check.setChecked(True)
        except FileNotFoundError:
            window.windows_startup_check.setChecked(False)
        winreg.CloseKey(key)
    except OSError:
        window.windows_startup_check.setChecked(False)


def save_window_settings(window) -> None:
    window.settings.setValue("port", window.port_spin.value())
    window.settings.setValue("auto_start_server", window.auto_start_check.isChecked())
    window.settings.setValue("minimize_to_tray", window.minimize_to_tray_check.isChecked())
    window.settings.setValue("use_https", window.https_check.isChecked())
    if hasattr(window, "language_combo"):
        window.settings.setValue("ui/language", str(window.language_combo.currentData() or window.language_preference))
