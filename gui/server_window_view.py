# -*- coding: utf-8 -*-

from __future__ import annotations


def show_toast(window, toast_cls, message: str, toast_type: str = "info", duration: int = 3000):
    toast = toast_cls(window, message, toast_type, duration)
    toast.move(window.width() - toast.width() - 20, 60)
    toast.show()
