"""Implementação Windows da camada de plataforma."""
from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
import time
from ctypes import wintypes
from typing import Callable, Optional

from ...core.engine import KeyEvent, WindowInfo
from ...i18n import tr
from . import win32 as w
from .hook import KeyboardHook, current_modifiers

log = logging.getLogger(__name__)

APP_NAME = "Macropad"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class WindowsPlatform:
    name = "windows"

    def __init__(self) -> None:
        self._pid = os.getpid()
        self._exe_cache: dict[int, tuple[str, float]] = {}
        self._cache_lock = threading.Lock()
        self._hook: Optional[KeyboardHook] = None
        self._mutex = None

    # ------------------------------------------------------- janelas/processos
    def own_pid(self) -> int:
        return self._pid

    def _exe_for_pid(self, pid: int) -> str:
        now = time.monotonic()
        with self._cache_lock:
            hit = self._exe_cache.get(pid)
            if hit and now - hit[1] < 3.0:
                return hit[0]
        path = ""
        h = w.OpenProcess(w.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h:
            try:
                buf = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(len(buf))
                if w.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                    path = buf.value
            finally:
                w.CloseHandle(h)
        with self._cache_lock:
            if len(self._exe_cache) > 256:
                self._exe_cache.clear()
            self._exe_cache[pid] = (path, now)
        return path

    def foreground(self) -> Optional[WindowInfo]:
        hwnd = w.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wintypes.DWORD(0)
        w.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return WindowInfo(int(hwnd), int(pid.value), self._exe_for_pid(int(pid.value)))

    # ------------------------------------------------------------- envio
    @staticmethod
    def _key_input(vk: int = 0, scan: int = 0, flags: int = 0) -> w.INPUT:
        inp = w.INPUT()
        inp.type = w.INPUT_KEYBOARD
        inp.ki = w.KEYBDINPUT(vk, scan, flags, 0, w.MAGIC_EXTRA_INFO)
        return inp

    def _send(self, inputs: list) -> None:
        if not inputs:
            return
        arr = (w.INPUT * len(inputs))(*inputs)
        sent = w.SendInput(len(inputs), arr, ctypes.sizeof(w.INPUT))
        if sent != len(inputs):
            err = ctypes.get_last_error()
            raise OSError(tr("win.sendinput_failed", sent=sent, total=len(inputs), err=err))

    def _type_unicode(self, text: str) -> None:
        data = text.encode("utf-16-le")
        units = [int.from_bytes(data[i:i + 2], "little") for i in range(0, len(data), 2)]
        inputs = []
        for u in units:
            inputs.append(self._key_input(0, u, w.KEYEVENTF_UNICODE))
            inputs.append(self._key_input(0, u, w.KEYEVENTF_UNICODE | w.KEYEVENTF_KEYUP))
        self._send(inputs)

    def _tap_vk(self, vk: int, with_ctrl: bool = False) -> None:
        scan = w.MapVirtualKeyW(vk, 0)
        seq = []
        if with_ctrl:
            seq.append(self._key_input(w.VK_CONTROL, w.MapVirtualKeyW(w.VK_CONTROL, 0), 0))
        seq.append(self._key_input(vk, scan, 0))
        seq.append(self._key_input(vk, scan, w.KEYEVENTF_KEYUP))
        if with_ctrl:
            seq.append(self._key_input(w.VK_CONTROL, w.MapVirtualKeyW(w.VK_CONTROL, 0),
                                       w.KEYEVENTF_KEYUP))
        self._send(seq)

    def _set_clipboard(self, text: str) -> None:
        data = (text + "\0").encode("utf-16-le")
        for _ in range(20):
            if w.OpenClipboard(None):
                break
            time.sleep(0.02)
        else:
            raise OSError(tr("win.clipboard_open"))
        try:
            w.EmptyClipboard()
            h = w.GlobalAlloc(w.GMEM_MOVEABLE, len(data))
            if not h:
                raise MemoryError("GlobalAlloc falhou")
            p = w.GlobalLock(h)
            ctypes.memmove(p, data, len(data))
            w.GlobalUnlock(h)
            if not w.SetClipboardData(w.CF_UNICODETEXT, h):
                w.GlobalFree(h)
                raise OSError(tr("win.clipboard_set"))
        finally:
            w.CloseClipboard()

    def send_text(self, text: str, mode: str) -> None:
        if not text:
            return
        if mode == "colar":
            self._set_clipboard(text)
            self._tap_vk(w.VK_V, with_ctrl=True)
            # A aplicação lê a área de transferência de forma assíncrona; dar
            # tempo antes de um eventual passo seguinte a substituir.
            time.sleep(0.08)
        else:
            self._type_unicode(text)

    def send_key(self, key: str) -> None:
        vk = {"Enter": w.VK_RETURN, "Tab": w.VK_TAB}[key]
        self._tap_vk(vk)

    def modifiers_down(self) -> frozenset[str]:
        return current_modifiers()

    # ------------------------------------------------------------- hook
    def start_hook(self, handler: Callable[[KeyEvent], bool]) -> Optional[str]:
        self._hook = KeyboardHook(handler)
        if not self._hook.start():
            return self._hook.error
        return None

    def stop_hook(self) -> None:
        if self._hook:
            self._hook.stop()

    # ------------------------------------------------------- painel sem foco
    def make_window_noactivate(self, win_id: int) -> None:
        hwnd = wintypes.HWND(win_id)
        style = w.GetWindowLongPtrW(hwnd, w.GWL_EXSTYLE)
        style |= w.WS_EX_NOACTIVATE | w.WS_EX_TOOLWINDOW
        style &= ~w.WS_EX_APPWINDOW
        w.SetWindowLongPtrW(hwnd, w.GWL_EXSTYLE, style)

    def native_event_noactivate(self, event_type, message) -> Optional[int]:
        """Para QWidget.nativeEvent: responde MA_NOACTIVATE a WM_MOUSEACTIVATE."""
        try:
            et = bytes(event_type)
        except TypeError:
            et = str(event_type).encode()
        if et != b"windows_generic_MSG":
            return None
        try:
            msg = wintypes.MSG.from_address(int(message))
        except (TypeError, ValueError):
            return None
        if msg.message == w.WM_MOUSEACTIVATE:
            return w.MA_NOACTIVATE
        return None

    # ------------------------------------------------------ tema / barra de título
    def style_title_bar(self, win_id: int, dark: bool, caption: Optional[str] = None,
                        text: Optional[str] = None, border: Optional[str] = None) -> None:
        """Modo escuro da barra de título e, no Windows 11, cores explícitas
        (``"#rrggbb"``). No Windows 10 só o modo escuro tem efeito."""
        if w.DwmSetWindowAttribute is None:
            return
        hwnd = wintypes.HWND(win_id)

        def set_attr(attr: int, value: int) -> int:
            v = ctypes.c_int(value)
            return w.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))

        if set_attr(w.DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0) != 0:
            set_attr(w.DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, 1 if dark else 0)
        for attr, color in ((w.DWMWA_CAPTION_COLOR, caption), (w.DWMWA_TEXT_COLOR, text),
                            (w.DWMWA_BORDER_COLOR, border)):
            if color:
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                set_attr(attr, r | (g << 8) | (b << 16))      # COLORREF 0x00BBGGRR
            else:
                set_attr(attr, 0xFFFFFFFF)                    # DWMWA_COLOR_DEFAULT

    def system_prefers_dark(self) -> Optional[bool]:
        """Preferência de tema das aplicações no Windows (None se desconhecida)."""
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
                v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
                return int(v) == 0
        except OSError:
            return None

    # ------------------------------------------------------------- arranque
    @staticmethod
    def autostart_command() -> str:
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        exe = sys.executable
        pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(pyw):
            exe = pyw
        return f'"{exe}" -m macropad'

    def get_autostart(self) -> bool:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                winreg.QueryValueEx(k, APP_NAME)
                return True
        except OSError:
            return False

    def set_autostart(self, enabled: bool) -> None:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            if enabled:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, self.autostart_command())
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except FileNotFoundError:
                    pass

    # -------------------------------------------------------- instância única
    def acquire_single_instance(self, name: str) -> bool:
        ctypes.set_last_error(0)
        self._mutex = w.CreateMutexW(None, False, f"Local\\{name}")
        return ctypes.get_last_error() != w.ERROR_ALREADY_EXISTS

    def is_elevated_hint(self) -> str:
        return ("O Windows impede que uma aplicação sem privilégios intercete ou "
                "envie teclas para janelas executadas como administrador.")
