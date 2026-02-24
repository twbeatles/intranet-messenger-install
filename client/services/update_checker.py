# -*- coding: utf-8 -*-
"""
Desktop client update checker.
"""

from __future__ import annotations

from typing import Any

from client.services.api_client import APIClient


class UpdateChecker:
    def __init__(self, api_client: APIClient, current_version: str, channel_getter=None):
        self.api_client = api_client
        self.current_version = current_version
        self._channel_getter = channel_getter

    def check(self) -> dict[str, Any]:
        channel = None
        if self._channel_getter:
            try:
                channel = str(self._channel_getter() or '').strip().lower()
            except Exception:
                channel = None
        return self.api_client.check_client_update(self.current_version, channel=channel)
