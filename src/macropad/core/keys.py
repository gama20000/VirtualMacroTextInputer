"""Nomes de teclas e associações (bindings), independentes do sistema operativo.

Uma associação é escrita como texto, por exemplo ``"1"``, ``"F13"``,
``"Ctrl+Alt+P"`` ou ``"Shift+Numpad5"``. Os modificadores aparecem sempre pela
ordem Ctrl, Alt, Shift, Win. A tecla principal não pode ser um modificador.

A camada de cada sistema operativo traduz os seus códigos (no Windows, as
virtual-key codes) para estes nomes canónicos.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..i18n import tr

MODIFIERS: tuple[str, ...] = ("Ctrl", "Alt", "Shift", "Win")

_MOD_ALIASES = {
    "ctrl": "Ctrl", "control": "Ctrl", "ctl": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win", "windows": "Win", "super": "Win", "meta": "Win",
}


def _build_key_names() -> list[str]:
    names: list[str] = []
    names += [str(d) for d in range(10)]                       # fila superior
    names += [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    names += [f"F{n}" for n in range(1, 25)]
    names += [f"Numpad{d}" for d in range(10)]
    names += ["NumpadAdd", "NumpadSubtract", "NumpadMultiply", "NumpadDivide",
              "NumpadDecimal"]
    names += ["Space", "Tab", "Enter", "Backspace", "Escape", "Insert", "Delete",
              "Home", "End", "PageUp", "PageDown", "Up", "Down", "Left", "Right",
              "Pause", "ScrollLock", "CapsLock", "NumLock", "PrintScreen", "Apps"]
    # Teclas de pontuação: o carácter depende do layout, por isso usam-se os
    # nomes OEM do Windows (ex.: no layout PT, OEM4 é a tecla ' ? ao lado do 0).
    names += ["OEM1", "OEM2", "OEM3", "OEM4", "OEM5", "OEM6", "OEM7", "OEM8",
              "OEM102", "OEMPlus", "OEMComma", "OEMMinus", "OEMPeriod"]
    names += ["BrowserBack", "BrowserForward", "VolumeMute", "VolumeDown",
              "VolumeUp", "MediaNext", "MediaPrev", "MediaStop", "MediaPlayPause"]
    return names


KEY_NAMES: tuple[str, ...] = tuple(_build_key_names())
_KEY_LOOKUP = {n.lower(): n for n in KEY_NAMES}
_KEY_ALIASES = {
    "esc": "Escape", "return": "Enter", "del": "Delete", "ins": "Insert",
    "pgup": "PageUp", "pgdn": "PageDown", "spacebar": "Space",
    "printscr": "PrintScreen", "menu": "Apps",
}


class KeyBindingError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class Binding:
    """Tecla principal e conjunto exato de modificadores."""

    key: str
    mods: frozenset[str] = frozenset()

    def __str__(self) -> str:  # forma canónica
        parts = [m for m in MODIFIERS if m in self.mods]
        parts.append(self.key)
        return "+".join(parts)

    @property
    def bare(self) -> "Binding":
        return Binding(self.key)


def canonical_key(name: str) -> str:
    """Devolve o nome canónico da tecla ou lança KeyBindingError."""
    raw = name.strip()
    low = raw.lower()
    if low in _KEY_LOOKUP:
        return _KEY_LOOKUP[low]
    if low in _KEY_ALIASES:
        return _KEY_ALIASES[low]
    if low in _MOD_ALIASES:
        raise KeyBindingError(tr("key.modifier_as_key", key=raw))
    raise KeyBindingError(tr("key.unknown", key=raw))


def parse_binding(text: str) -> Binding:
    """Converte ``"Ctrl+Alt+P"`` num Binding. Aceita maiúsculas/minúsculas."""
    if text is None or not str(text).strip():
        raise KeyBindingError(tr("key.empty"))
    # "Ctrl++" não é suportado; "+" literal teria de ser OEMPlus.
    parts = [p.strip() for p in str(text).split("+")]
    if any(p == "" for p in parts):
        raise KeyBindingError(tr("key.malformed", text=text))
    *mod_parts, key_part = parts
    mods: set[str] = set()
    for p in mod_parts:
        m = _MOD_ALIASES.get(p.lower())
        if m is None:
            raise KeyBindingError(tr("key.unknown_mod", mod=p, text=text))
        if m in mods:
            raise KeyBindingError(tr("key.repeated_mod", mod=p, text=text))
        mods.add(m)
    return Binding(canonical_key(key_part), frozenset(mods))


# Teclas multimédia e afins: no ficheiro ficam com o nome canónico, na
# interface aparecem com um nome legível (traduzido).
MEDIA_KEYS: tuple[str, ...] = ("MediaPlayPause", "MediaPrev", "MediaNext")
_DISPLAY_KEYS = set(MEDIA_KEYS) | {"MediaStop", "VolumeMute", "VolumeDown", "VolumeUp",
                                   "BrowserBack", "BrowserForward"}


def display_binding(text: str) -> str:
    """Associação para mostrar ao utilizador: ``"Ctrl+MediaNext"`` passa a
    ``"Ctrl+Faixa seguinte"``. Texto que não é uma associação fica igual."""
    if not text:
        return text
    parts = text.split("+")
    if parts[-1] in _DISPLAY_KEYS:
        parts[-1] = tr(f"keyname.{parts[-1]}")
    return "+".join(parts)


def normalize_binding(text: str) -> str:
    """Forma canónica de uma associação (texto) ou "" se vazia."""
    if not text or not text.strip():
        return ""
    return str(parse_binding(text))
