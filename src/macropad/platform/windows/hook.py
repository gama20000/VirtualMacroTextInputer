"""Hook de teclado de baixo nível (WH_KEYBOARD_LL) numa thread dedicada.

O callback tem de responder depressa: se exceder o LowLevelHooksTimeout
(cerca de 1 s no Windows 10/11) várias vezes, o Windows remove o hook sem
aviso. Por isso o callback só consulta o motor (operações em memória) e
nunca executa macros diretamente.
"""
from __future__ import annotations

import ctypes
import logging
import threading
from ctypes import wintypes
from typing import Callable, Optional

from ...core.engine import KeyEvent
from ...i18n import tr
from . import win32 as w

log = logging.getLogger(__name__)


def current_modifiers() -> frozenset[str]:
    mods = set()
    if w.GetAsyncKeyState(w.VK_CONTROL) & 0x8000:
        mods.add("Ctrl")
    if w.GetAsyncKeyState(w.VK_MENU) & 0x8000:
        mods.add("Alt")
    if w.GetAsyncKeyState(w.VK_SHIFT) & 0x8000:
        mods.add("Shift")
    if (w.GetAsyncKeyState(w.VK_LWIN) & 0x8000) or (w.GetAsyncKeyState(w.VK_RWIN) & 0x8000):
        mods.add("Win")
    return frozenset(mods)


class KeyboardHook:
    def __init__(self, handler: Callable[[KeyEvent], bool]):
        self._handler = handler
        self._thread: Optional[threading.Thread] = None
        self._thread_id = 0
        self._hook = None
        self._ready = threading.Event()
        self.error: Optional[str] = None
        # Manter referência ao callback: se for recolhido pelo GC, o processo cai.
        self._proc = w.HOOKPROC(self._callback)

    def _callback(self, n_code: int, w_param: int, l_param: int) -> int:
        try:
            if n_code == w.HC_ACTION:
                kb = w.KBDLLHOOKSTRUCT.from_address(l_param)
                down = w_param in (w.WM_KEYDOWN, w.WM_SYSKEYDOWN)
                vk = kb.vkCode
                ours = kb.dwExtraInfo == w.MAGIC_EXTRA_INFO
                if ours or vk in w.MODIFIER_VKS:
                    ev = KeyEvent(None, down, ours=ours, is_modifier=not ours)
                else:
                    name = w.VK_TO_NAME.get(vk)
                    ev = KeyEvent(name, down, current_modifiers() if name else frozenset())
                if ev.key is not None and self._handler(ev):
                    return 1                  # suprime o evento
        except Exception:
            log.exception("erro no hook de teclado")
        return w.CallNextHookEx(None, n_code, w_param, l_param)

    def _run(self) -> None:
        self._thread_id = w.GetCurrentThreadId()
        self._hook = w.SetWindowsHookExW(w.WH_KEYBOARD_LL, self._proc,
                                         w.GetModuleHandleW(None), 0)
        if not self._hook:
            self.error = tr("win.hook_failed", err=ctypes.get_last_error())
            log.error(self.error)
            self._ready.set()
            return
        self._ready.set()
        msg = wintypes.MSG()
        while True:
            r = w.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if r == 0 or r == -1:
                break
            w.TranslateMessage(ctypes.byref(msg))
            w.DispatchMessageW(ctypes.byref(msg))
        w.UnhookWindowsHookEx(self._hook)
        self._hook = None

    def start(self) -> bool:
        self._thread = threading.Thread(target=self._run, name="KeyboardHook", daemon=True)
        self._thread.start()
        self._ready.wait(5)
        return self.error is None

    def stop(self) -> None:
        if self._thread and self._thread_id:
            w.PostThreadMessageW(self._thread_id, w.WM_QUIT, 0, 0)
            self._thread.join(2)
        self._thread = None
