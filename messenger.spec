# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller server spec
Builds: MessengerServer.exe
Entry point: server.py
Bundles: app/** (including app/bootstrap, app/http, app/realtime),
         gui/**, static/ (including CSS manifest/fragments + JS module bridge),
         templates/, i18n/, certs/

Usage:
  pyinstaller messenger.spec --noconfirm --clean
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


block_cipher = None
ROOT = Path(SPECPATH)

EXCLUDES = [
    "tkinter",
    "_tkinter",
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "cv2",
    "IPython",
    "jupyter",
    "pytest",
    "unittest",
    "doctest",
    "test",
    "pysqlite2",
    "MySQLdb",
    # Server build uses PySide6 only.
    "PyQt6",
]

hiddenimports = sorted(
    set(
        [
            "flask",
            "flask_socketio",
            "flask_session",
            "flask_session.cachelib",
            "flask_session.filesystem",
            "flask_limiter",
            "flask_wtf",
            "wtforms",
            "flask_compress",
            "cachelib",
            "msgspec",
            # Compression backends used by Flask-Compress.
            "brotli",
            "brotlicffi",
            "socketio",
            "engineio",
            "engineio.async_drivers.gevent",
            "engineio.async_drivers.threading",
            "simple_websocket",
            "gevent",
            "geventwebsocket",
            "greenlet",
            "zope.event",
            "zope.interface",
            "bcrypt",
            "ldap3",
            "pyasn1",
            "Crypto",
            "Crypto.Cipher.AES",
            "Crypto.Util.Padding",
            "cryptography",
            "httpx",
            "keyring",
            "keyring.backends",
            "PySide6",
        ]
        # Split server packages are pulled in automatically.
        + collect_submodules("app")
        # Server desktop management window lives under gui/ and uses PySide6.
        + collect_submodules("gui")
    )
)

a = Analysis(
    ["server.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        ("static", "static"),
        ("templates", "templates"),
        ("i18n", "i18n"),
        ("certs", "certs"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[str(ROOT)],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Python 3.15 abi3t: cryptography _rust.pyd links python3t.dll
# (<prefix>\abi3t-compat), which PyInstaller does not auto-collect.
# Without it the frozen exe dies with "DLL load failed while importing _rust".
_py3t_dll = os.path.join(sys.base_prefix, 'abi3t-compat', 'python3t.dll')
_py3t_dest = 'python3t.dll'
if os.path.isfile(_py3t_dll) and not any(
        (b[0] or '').lower() == _py3t_dest for b in a.binaries):
    a.binaries.append((_py3t_dest, _py3t_dll, 'BINARY'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MessengerServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
