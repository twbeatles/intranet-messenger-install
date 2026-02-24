# -*- coding: utf-8 -*-
"""
Desktop messenger entrypoint.
"""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from client.app_controller import MessengerAppController
from client.i18n import i18n_manager
from client.ui.theme import apply_theme

CLIENT_VERSION = '1.0.0'


def main() -> int:
    parser = argparse.ArgumentParser(description='Intranet Messenger Desktop')
    parser.add_argument('--server-url', default='http://127.0.0.1:5000', help='Default server URL')
    parser.add_argument('--lang', default='auto', choices=['auto', 'ko', 'en'], help='Language preference')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    i18n_manager.initialize()
    if args.lang != 'auto':
        i18n_manager.set_preference(args.lang)
    apply_theme(app)

    controller = MessengerAppController(
        app=app,
        default_server_url=args.server_url,
        client_version=CLIENT_VERSION,
    )
    controller.start()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
