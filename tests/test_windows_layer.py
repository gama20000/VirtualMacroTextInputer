"""Testes da camada Windows com a API Win32 simulada.

Não substituem a verificação manual no Windows, mas validam a construção das
estruturas (INPUT, KBDLLHOOKSTRUCT), a marcação dos eventos próprios e a
decisão do hook, em qualquer sistema operativo."""
import ctypes
import importlib
import sys
import types

import pytest

from macropad.core.engine import KeyEvent


class _FakeFn:
    def __init__(self, name, impl):
        self.name, self.impl = name, impl
        self.restype = None
        self.argtypes = None
        self.calls = []

    def __call__(self, *a):
        self.calls.append(a)
        return self.impl(*a)


class _FakeDLL:
    def __init__(self, impls):
        self._impls = impls
        self._fns = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._fns:
            self._fns[name] = _FakeFn(name, self._impls.get(name, lambda *a: 1))
        return self._fns[name]


@pytest.fixture
def win(monkeypatch):
    sent = []
    keys_down = set()

    def send_input(n, arr, size):
        for i in range(n):
            ki = arr[i].ki
            sent.append((arr[i].type, ki.wVk, ki.wScan, ki.dwFlags, ki.dwExtraInfo))
        return n

    def async_state(vk):
        return -32768 if vk in keys_down else 0

    impls = {"SendInput": send_input, "GetAsyncKeyState": async_state,
             "MapVirtualKeyW": lambda vk, t: vk + 1000,
             "CallNextHookEx": lambda *a: 0}
    dll = _FakeDLL(impls)
    monkeypatch.setattr(ctypes, "WinDLL", lambda *a, **k: dll, raising=False)
    monkeypatch.setattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE, raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 0, raising=False)
    monkeypatch.setattr(ctypes, "set_last_error", lambda v: 0, raising=False)
    for m in [m for m in sys.modules if m.startswith("macropad.platform.windows")]:
        del sys.modules[m]
    mod = importlib.import_module("macropad.platform.windows")
    hook_mod = importlib.import_module("macropad.platform.windows.hook")
    w32 = importlib.import_module("macropad.platform.windows.win32")
    yield types.SimpleNamespace(mod=mod, hook=hook_mod, w=w32, sent=sent, keys_down=keys_down)
    for m in [m for m in sys.modules if m.startswith("macropad.platform.windows")]:
        del sys.modules[m]


def test_estrutura_input_tem_tamanho_correto(win):
    from ctypes import wintypes
    if ctypes.sizeof(wintypes.DWORD) != 4:
        pytest.skip("tamanhos Win32 só são reais no Windows (DWORD de 32 bits)")
    expected = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
    assert ctypes.sizeof(win.w.INPUT) == expected
    assert ctypes.sizeof(win.w.KBDLLHOOKSTRUCT) == (24 if expected == 40 else 20)


def test_texto_unicode_com_marca_propria(win):
    p = win.mod.WindowsPlatform()
    p.send_text("Aç😀", "escrever")
    W = win.w
    units = [0x41, 0xE7, 0xD83D, 0xDE00]          # 😀 = par substituto
    assert len(win.sent) == 2 * len(units)
    for i, u in enumerate(units):
        down, up = win.sent[2 * i], win.sent[2 * i + 1]
        assert down == (W.INPUT_KEYBOARD, 0, u, W.KEYEVENTF_UNICODE, W.MAGIC_EXTRA_INFO)
        assert up[3] == W.KEYEVENTF_UNICODE | W.KEYEVENTF_KEYUP


def test_enter_e_tab(win):
    p = win.mod.WindowsPlatform()
    p.send_key("Enter")
    p.send_key("Tab")
    vks = [(s[1], s[3] & win.w.KEYEVENTF_KEYUP) for s in win.sent]
    assert vks == [(0x0D, 0), (0x0D, 2), (0x09, 0), (0x09, 2)]
    assert all(s[4] == win.w.MAGIC_EXTRA_INFO for s in win.sent)


def _call_hook(win, kb_hook, vk, msg, extra=0):
    W = win.w
    st = W.KBDLLHOOKSTRUCT(vk, 0, 0, 0, extra)
    return kb_hook._callback(W.HC_ACTION, msg, ctypes.addressof(st))


def test_hook_suprime_conforme_o_motor(win):
    seen = []

    def handler(ev: KeyEvent):
        seen.append(ev)
        return ev.key == "1" and not ev.mods

    h = win.hook.KeyboardHook(handler)
    W = win.w
    assert _call_hook(win, h, 0x31, W.WM_KEYDOWN) == 1          # 1 -> suprimido
    assert _call_hook(win, h, 0x61, W.WM_KEYDOWN) == 0          # Numpad1 -> passa
    assert seen[-1].key == "Numpad1"
    win.keys_down.add(W.VK_CONTROL)
    assert _call_hook(win, h, 0x31, W.WM_KEYDOWN) == 0          # Ctrl+1 -> passa
    assert seen[-1].mods == frozenset({"Ctrl"})
    n = len(seen)
    assert _call_hook(win, h, 0x31, W.WM_KEYDOWN, W.MAGIC_EXTRA_INFO) == 0  # evento próprio
    assert _call_hook(win, h, 0x11, W.WM_KEYDOWN) == 0          # modificador
    assert len(seen) == n                                       # nem chegam ao motor
    assert _call_hook(win, h, 0x31, W.WM_KEYUP) == 0
    assert seen[-1].down is False


def test_hook_nao_propaga_excecoes(win):
    def boom(ev):
        raise RuntimeError("x")
    h = win.hook.KeyboardHook(boom)
    assert _call_hook(win, h, 0x31, win.w.WM_KEYDOWN) == 0


def test_barra_de_titulo_cores_colorref(win):
    p = win.mod.WindowsPlatform()
    calls = []
    W = win.w

    def fake_set(hwnd, attr, ptr, size):
        calls.append((attr, ctypes.cast(ptr, ctypes.POINTER(ctypes.c_int)).contents.value))
        return 0
    W.DwmSetWindowAttribute = fake_set
    p.style_title_bar(123, True, "#000000", "#ffffff", None)
    d = dict(calls)
    assert d[W.DWMWA_USE_IMMERSIVE_DARK_MODE] == 1
    assert d[W.DWMWA_CAPTION_COLOR] == 0x000000
    assert d[W.DWMWA_TEXT_COLOR] == 0xFFFFFF
    calls.clear()
    p.style_title_bar(123, True, "#1c2b3a", None, None)
    assert dict(calls)[W.DWMWA_CAPTION_COLOR] == 0x3A2B1C       # 0x00BBGGRR


def _clipboard_sim(win, *, alloc_ok=True, set_ok=True):
    """Simula a área de transferência e regista a ordem das chamadas."""
    order = []
    buf = ctypes.create_string_buffer(4096)
    W = win.w

    def rec(name, result):
        def f(*a):
            order.append((name, a))
            return result(*a) if callable(result) else result
        return f
    W.GlobalAlloc.impl = rec("GlobalAlloc", 77 if alloc_ok else 0)
    W.GlobalLock.impl = rec("GlobalLock", ctypes.addressof(buf))
    W.GlobalUnlock.impl = rec("GlobalUnlock", 1)
    W.GlobalFree.impl = rec("GlobalFree", 0)
    W.CreateWindowExW.impl = rec("CreateWindowExW", 555)
    W.DestroyWindow.impl = rec("DestroyWindow", 1)
    W.OpenClipboard.impl = rec("OpenClipboard", 1)
    W.EmptyClipboard.impl = rec("EmptyClipboard", 1)
    W.SetClipboardData.impl = rec("SetClipboardData", 77 if set_ok else 0)
    W.CloseClipboard.impl = rec("CloseClipboard", 1)
    return order, buf


def test_area_de_transferencia_com_dono_e_dados_preparados(win):
    """Revisão Codex: OpenClipboard(NULL) + EmptyClipboard deixa o dono a NULL
    e SetClipboardData falha. Abre-se com uma janela própria; os dados são
    preparados antes de esvaziar a área."""
    order, buf = _clipboard_sim(win)
    win.mod.WindowsPlatform()._set_clipboard("Olá")
    names = [n for n, _ in order]
    assert names.index("GlobalAlloc") < names.index("EmptyClipboard")
    opened = [a for n, a in order if n == "OpenClipboard"][0]
    assert opened[0] == 555                          # a janela dona, não NULL
    assert names[-1] == "DestroyWindow"
    assert names.index("CloseClipboard") < names.index("DestroyWindow")
    assert "GlobalFree" not in names                 # a memória passou para o sistema
    assert buf.raw[:8] == "Olá\0".encode("utf-16-le")


def test_area_de_transferencia_sem_memoria_nao_esvazia(win):
    order, _ = _clipboard_sim(win, alloc_ok=False)
    with pytest.raises(MemoryError):
        win.mod.WindowsPlatform()._set_clipboard("x")
    assert "EmptyClipboard" not in [n for n, _ in order]


def test_area_de_transferencia_falha_ao_definir(win):
    order, _ = _clipboard_sim(win, set_ok=False)
    with pytest.raises(OSError):
        win.mod.WindowsPlatform()._set_clipboard("x")
    names = [n for n, _ in order]
    assert "GlobalFree" in names and "CloseClipboard" in names and "DestroyWindow" in names


def test_teclas_multimedia_enviadas_como_estendidas(win):
    """{MediaPlayPause} e afins: código virtual da tecla, com a marca própria
    e a flag de tecla estendida (Enter e Tab continuam sem ela)."""
    p = win.mod.WindowsPlatform()
    p.send_key("MediaPlayPause")
    p.send_key("VolumeUp")
    ext = win.w.KEYEVENTF_EXTENDEDKEY
    got = [(s[1], s[3]) for s in win.sent]
    assert got == [(0xB3, ext), (0xB3, ext | 2), (0xAF, ext), (0xAF, ext | 2)]
    assert all(s[4] == win.w.MAGIC_EXTRA_INFO for s in win.sent)
