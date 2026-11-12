"""Plataforma de substituição (desenvolvimento e testes noutros sistemas).

Não interceta teclas nem envia texto: regista as ações em memória. Permite
abrir a interface em Linux/macOS para desenvolvimento."""
from __future__ import annotations

import os
from typing import Callable, Optional

from ..core.engine import KeyEvent, WindowInfo
from ..i18n import tr


class DummyPlatform:
    name = "dummy"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.fg: Optional[WindowInfo] = WindowInfo(1, 999_999, "C:\\Windows\\notepad.exe")
        self.mods: frozenset[str] = frozenset()
        self._autostart = False

    def own_pid(self) -> int:
        return os.getpid()

    def foreground(self) -> Optional[WindowInfo]:
        return self.fg

    def send_text(self, text: str, mode: str) -> None:
        self.sent.append(("text", text))

    def send_key(self, key: str) -> None:
        self.sent.append(("key", key))

    def modifiers_down(self) -> frozenset[str]:
        return self.mods

    def start_hook(self, handler: Callable[[KeyEvent], bool]) -> Optional[str]:
        return tr("dummy.no_hook")

    def stop_hook(self) -> None:
        pass

    def make_window_noactivate(self, win_id: int) -> None:
        pass

    def native_event_noactivate(self, event_type, message) -> Optional[int]:
        return None

    def style_title_bar(self, win_id: int, dark: bool, caption=None, text=None,
                        border=None) -> None:
        self.title_bars = getattr(self, "title_bars", {})
        self.title_bars[win_id] = (dark, caption, text)

    def system_prefers_dark(self):
        return getattr(self, "prefers_dark", None)

    fail_autostart = False

    def get_autostart(self) -> bool:
        return self._autostart

    def set_autostart(self, enabled: bool, extra_args: str = "") -> None:
        if self.fail_autostart:
            raise OSError("acesso negado (simulado)")
        self._autostart = enabled
        self.autostart_args = extra_args

    def acquire_single_instance(self, name: str) -> bool:
        return True

    def is_elevated_hint(self) -> str:
        return ""
