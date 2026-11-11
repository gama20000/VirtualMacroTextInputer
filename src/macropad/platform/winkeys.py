"""Tabela virtual-key code -> nome canónico (sem ctypes; importável em qualquer SO)."""
from __future__ import annotations

VK_SHIFT, VK_CONTROL, VK_MENU = 0x10, 0x11, 0x12
VK_LWIN, VK_RWIN = 0x5B, 0x5C
VK_RETURN, VK_TAB = 0x0D, 0x09
VK_V = 0x56

MODIFIER_VKS = {0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C}


def _vk_table() -> dict[int, str]:
    t: dict[int, str] = {}
    for d in range(10):
        t[0x30 + d] = str(d)               # fila superior
        t[0x60 + d] = f"Numpad{d}"         # teclado numérico
    for c in range(26):
        t[0x41 + c] = chr(ord("A") + c)
    for n in range(1, 25):
        t[0x70 + n - 1] = f"F{n}"
    t.update({
        0x6A: "NumpadMultiply", 0x6B: "NumpadAdd", 0x6D: "NumpadSubtract",
        0x6E: "NumpadDecimal", 0x6F: "NumpadDivide",
        0x20: "Space", 0x09: "Tab", 0x0D: "Enter", 0x08: "Backspace", 0x1B: "Escape",
        0x2D: "Insert", 0x2E: "Delete", 0x24: "Home", 0x23: "End",
        0x21: "PageUp", 0x22: "PageDown", 0x26: "Up", 0x28: "Down",
        0x25: "Left", 0x27: "Right", 0x13: "Pause", 0x91: "ScrollLock",
        0x14: "CapsLock", 0x90: "NumLock", 0x2C: "PrintScreen", 0x5D: "Apps",
        0xBA: "OEM1", 0xBF: "OEM2", 0xC0: "OEM3", 0xDB: "OEM4", 0xDC: "OEM5",
        0xDD: "OEM6", 0xDE: "OEM7", 0xDF: "OEM8", 0xE2: "OEM102",
        0xBB: "OEMPlus", 0xBC: "OEMComma", 0xBD: "OEMMinus", 0xBE: "OEMPeriod",
        0xA6: "BrowserBack", 0xA7: "BrowserForward", 0xAD: "VolumeMute",
        0xAE: "VolumeDown", 0xAF: "VolumeUp", 0xB0: "MediaNext", 0xB1: "MediaPrev",
        0xB2: "MediaStop", 0xB3: "MediaPlayPause",
    })
    return t


VK_TO_NAME: dict[int, str] = _vk_table()
NAME_TO_VK: dict[str, int] = {v: k for k, v in VK_TO_NAME.items()}
