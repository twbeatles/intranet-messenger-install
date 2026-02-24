# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller client spec
Builds: MessengerClient.exe

Usage:
  pyinstaller messenger_client.spec --noconfirm --clean
"""

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
    # Client build uses PySide6 only.
    "PyQt6",
]

hiddenimports = sorted(
    set(
        [
            "httpx",
            "socketio",
            "engineio",
            "simple_websocket",
            "keyring",
            "keyring.backends",
            "keyring.backends.Windows",
            "keyring.backends.null",
            "Crypto",
            "Crypto.Cipher.AES",
            "Crypto.Util.Padding",
            "PySide6",
        ]
        + collect_submodules("client")
    )
)

a = Analysis(
    ["client/main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MessengerClient",
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
