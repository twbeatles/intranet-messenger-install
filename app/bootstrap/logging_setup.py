# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


def configure_logging(base_dir: str) -> logging.Logger:
    if getattr(configure_logging, "_configured", False):
        return logging.getLogger(__name__)

    handlers: list[logging.Handler]
    try:
        file_handler = RotatingFileHandler(
            os.path.join(base_dir, "server.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        handlers = [file_handler, logging.StreamHandler()]
    except (PermissionError, OSError):
        handlers = [logging.StreamHandler()]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=False,
    )
    configure_logging._configured = True  # type: ignore[attr-defined]
    return logging.getLogger(__name__)

