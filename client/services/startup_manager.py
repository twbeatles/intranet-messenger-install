# -*- coding: utf-8 -*-
"""
Windows startup registration helper.
"""

from __future__ import annotations

import os
import sys


if sys.platform == 'win32':
    import winreg
else:  # pragma: no cover
    winreg = None


RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
APP_RUN_NAME = 'IntranetMessengerDesktop'


class StartupManager:
    def __init__(self, app_path: str | None = None):
        self.app_path = app_path or self._default_startup_command()

    @staticmethod
    def _default_startup_command() -> str:
        if getattr(sys, 'frozen', False):
            return f'"{os.path.abspath(sys.executable)}"'

        entry_script = os.path.abspath(sys.argv[0])
        if entry_script.lower().endswith('.exe'):
            return f'"{entry_script}"'

        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        python_cmd = pythonw if os.path.exists(pythonw) else sys.executable
        return f'"{os.path.abspath(python_cmd)}" -m client.main'

    def is_enabled(self) -> bool:
        if not winreg:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, APP_RUN_NAME)
                return bool(value)
            finally:
                winreg.CloseKey(key)
        except OSError:
            return False

    def set_enabled(self, enabled: bool) -> None:
        if not winreg:
            return
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            if enabled:
                winreg.SetValueEx(key, APP_RUN_NAME, 0, winreg.REG_SZ, str(self.app_path))
            else:
                try:
                    winreg.DeleteValue(key, APP_RUN_NAME)
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
