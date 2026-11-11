"""Seleção da implementação de plataforma.

Para portar para Linux basta criar ``platform/linux`` com a mesma interface
(``foreground``, ``send_text``, ``send_key``, ``modifiers_down``,
``start_hook``/``stop_hook``, ``make_window_noactivate``,
``native_event_noactivate``, ``get/set_autostart``,
``acquire_single_instance``) e escolhê-la aqui.
"""
from __future__ import annotations

import os
import sys


def create_platform():
    if sys.platform == "win32" and not os.environ.get("MACROPAD_FAKE_PLATFORM"):
        from .windows import WindowsPlatform
        return WindowsPlatform()
    from .dummy import DummyPlatform
    return DummyPlatform()
