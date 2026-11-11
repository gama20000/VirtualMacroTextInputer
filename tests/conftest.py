import threading
import time

import pytest

from macropad.core.engine import Engine, WindowInfo
from macropad.core.model import Config, Macro, MacroSet, Scope, Settings

TARGET = WindowInfo(100, 4242, "C:\\Program Files\\App\\Editor.exe")
OTHER = WindowInfo(200, 5555, "C:\\Windows\\explorer.exe")


class FakePlatform:
    def __init__(self):
        self.fg = TARGET
        self.mods = frozenset()
        self.log = []
        self.lock = threading.Lock()
        self.on_send = None

    def own_pid(self):
        return 1

    def foreground(self):
        return self.fg

    def send_text(self, text, mode):
        with self.lock:
            self.log.append(("text", text, mode))
        if self.on_send:
            self.on_send(("text", text))

    def send_key(self, key):
        with self.lock:
            self.log.append(("key", key))
        if self.on_send:
            self.on_send(("key", key))

    def modifiers_down(self):
        return self.mods

    def typed(self):
        """Texto equivalente ao que foi enviado."""
        out = []
        for e in self.log:
            if e[0] == "text":
                out.append(e[1])
            else:
                out.append("{" + e[1] + "}")
        return "".join(out)


def make_config(macros, scope=None, settings=None):
    ms = MacroSet("teste", "Teste", scope or Scope(), macros)
    return Config(settings or Settings(), {"teste": ms})


@pytest.fixture
def fake():
    return FakePlatform()


@pytest.fixture
def engine(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "3E03305"), Macro("B", "2", "X{Enter}")]))
    return e


def wait_idle(engine, timeout=5.0):
    end = time.monotonic() + timeout
    while engine.running is not None and time.monotonic() < end:
        time.sleep(0.005)
    assert engine.running is None, "execução não terminou"
