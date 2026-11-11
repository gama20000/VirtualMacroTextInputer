"""Declarações ctypes da API Win32 usadas pelo Macropad (só Windows)."""
from __future__ import annotations

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

ULONG_PTR = ctypes.c_size_t
LRESULT = ctypes.c_ssize_t
HHOOK = wintypes.HANDLE

# ----------------------------------------------------------------- constantes
WH_KEYBOARD_LL = 13
HC_ACTION = 0
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0100, 0x0101, 0x0104, 0x0105
WM_QUIT = 0x0012
WM_MOUSEACTIVATE = 0x0021
MA_NOACTIVATE = 3
LLKHF_EXTENDED = 0x01
LLKHF_INJECTED = 0x10

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
ERROR_ALREADY_EXISTS = 183

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

# Marca colocada em dwExtraInfo dos eventos enviados pelo Macropad, para que
# o hook os reconheça e não os trate como teclas do utilizador.
MAGIC_EXTRA_INFO = 0x4D50_4144  # "MPAD"

# ------------------------------------------------------------------ estruturas
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# ------------------------------------------------------------------- funções
def _fn(dll, name, restype, *argtypes):
    f = getattr(dll, name)
    f.restype = restype
    f.argtypes = list(argtypes)
    return f


SetWindowsHookExW = _fn(user32, "SetWindowsHookExW", HHOOK,
                        ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD)
UnhookWindowsHookEx = _fn(user32, "UnhookWindowsHookEx", wintypes.BOOL, HHOOK)
CallNextHookEx = _fn(user32, "CallNextHookEx", LRESULT,
                     HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
GetMessageW = _fn(user32, "GetMessageW", wintypes.BOOL,
                  ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
TranslateMessage = _fn(user32, "TranslateMessage", wintypes.BOOL, ctypes.POINTER(wintypes.MSG))
DispatchMessageW = _fn(user32, "DispatchMessageW", LRESULT, ctypes.POINTER(wintypes.MSG))
PostThreadMessageW = _fn(user32, "PostThreadMessageW", wintypes.BOOL,
                         wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
GetCurrentThreadId = _fn(kernel32, "GetCurrentThreadId", wintypes.DWORD)
GetModuleHandleW = _fn(kernel32, "GetModuleHandleW", wintypes.HMODULE, wintypes.LPCWSTR)

SendInput = _fn(user32, "SendInput", wintypes.UINT,
                wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
MapVirtualKeyW = _fn(user32, "MapVirtualKeyW", wintypes.UINT, wintypes.UINT, wintypes.UINT)
GetAsyncKeyState = _fn(user32, "GetAsyncKeyState", ctypes.c_short, ctypes.c_int)

GetForegroundWindow = _fn(user32, "GetForegroundWindow", wintypes.HWND)
GetWindowThreadProcessId = _fn(user32, "GetWindowThreadProcessId", wintypes.DWORD,
                               wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
OpenProcess = _fn(kernel32, "OpenProcess", wintypes.HANDLE,
                  wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
CloseHandle = _fn(kernel32, "CloseHandle", wintypes.BOOL, wintypes.HANDLE)
QueryFullProcessImageNameW = _fn(kernel32, "QueryFullProcessImageNameW", wintypes.BOOL,
                                 wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                 ctypes.POINTER(wintypes.DWORD))
GetCurrentProcessId = _fn(kernel32, "GetCurrentProcessId", wintypes.DWORD)

CreateMutexW = _fn(kernel32, "CreateMutexW", wintypes.HANDLE,
                   wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)

OpenClipboard = _fn(user32, "OpenClipboard", wintypes.BOOL, wintypes.HWND)
CloseClipboard = _fn(user32, "CloseClipboard", wintypes.BOOL)
EmptyClipboard = _fn(user32, "EmptyClipboard", wintypes.BOOL)
SetClipboardData = _fn(user32, "SetClipboardData", wintypes.HANDLE, wintypes.UINT, wintypes.HANDLE)
GlobalAlloc = _fn(kernel32, "GlobalAlloc", wintypes.HGLOBAL, wintypes.UINT, ctypes.c_size_t)
GlobalLock = _fn(kernel32, "GlobalLock", wintypes.LPVOID, wintypes.HGLOBAL)
GlobalUnlock = _fn(kernel32, "GlobalUnlock", wintypes.BOOL, wintypes.HGLOBAL)
GlobalFree = _fn(kernel32, "GlobalFree", wintypes.HGLOBAL, wintypes.HGLOBAL)

if ctypes.sizeof(ctypes.c_void_p) == 8:
    GetWindowLongPtrW = _fn(user32, "GetWindowLongPtrW", ctypes.c_ssize_t,
                            wintypes.HWND, ctypes.c_int)
    SetWindowLongPtrW = _fn(user32, "SetWindowLongPtrW", ctypes.c_ssize_t,
                            wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t)
else:  # Python 32-bit
    GetWindowLongPtrW = _fn(user32, "GetWindowLongW", ctypes.c_long,
                            wintypes.HWND, ctypes.c_int)
    SetWindowLongPtrW = _fn(user32, "SetWindowLongW", ctypes.c_long,
                            wintypes.HWND, ctypes.c_int, ctypes.c_long)

# ------------------------------------------------------ barra de título (DWM)
DWMWA_USE_IMMERSIVE_DARK_MODE = 20       # Windows 10 20H1+ (19 em builds anteriores)
DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
DWMWA_BORDER_COLOR = 34                  # Windows 11
DWMWA_CAPTION_COLOR = 35                 # Windows 11
DWMWA_TEXT_COLOR = 36                    # Windows 11
try:
    dwmapi = ctypes.WinDLL("dwmapi")
    DwmSetWindowAttribute = _fn(dwmapi, "DwmSetWindowAttribute", ctypes.c_long,
                                wintypes.HWND, wintypes.DWORD, wintypes.LPCVOID, wintypes.DWORD)
except (OSError, AttributeError):          # pragma: no cover - sem DWM
    DwmSetWindowAttribute = None

# -------------------------------------------------------------- teclas (VK)
from ..winkeys import (MODIFIER_VKS, NAME_TO_VK, VK_CONTROL, VK_LWIN, VK_MENU,  # noqa: E402,F401
                    VK_RETURN, VK_RWIN, VK_SHIFT, VK_TAB, VK_TO_NAME, VK_V)
