"""Traduções da interface.

Cada idioma é um ficheiro ``locales/<código>.toml`` com ``nome = "..."`` e
tabelas aninhadas de mensagens (``[menu] abrir = "..."`` -> chave
``menu.abrir``). Para acrescentar um idioma basta copiar ``pt.toml`` para um
novo ficheiro (ex.: ``es.toml``) e traduzir os valores; aparece logo na lista
de idiomas. Chaves em falta usam o texto português.

As mensagens usam ``str.format``: ``{nome}`` é substituído; chavetas
literais escrevem-se ``{{`` e ``}}``.

Este módulo não depende do Qt, para poder ser usado pelo núcleo.
"""
from __future__ import annotations

import sys
import threading
import tomllib
from pathlib import Path

BASE = "pt"


def _locales_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)          # PyInstaller
    if base:
        p = Path(base) / "macropad" / "locales"
        if p.is_dir():
            return p
    return Path(__file__).resolve().parent / "locales"


_lock = threading.Lock()
_cache: dict[str, dict[str, str]] = {}
_names: dict[str, str] = {}
_lang = BASE


def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key + "."))
        elif isinstance(v, str):
            out[key] = v
    return out


def _load(code: str) -> dict[str, str]:
    with _lock:
        if code not in _cache:
            path = _locales_dir() / f"{code}.toml"
            try:
                data = tomllib.loads(path.read_text("utf-8"))
            except (OSError, tomllib.TOMLDecodeError):
                data = {}
            _names[code] = str(data.pop("nome", code))
            _cache[code] = _flatten(data)
        return _cache[code]


def available() -> list[tuple[str, str]]:
    """[(código, nome)] dos idiomas disponíveis, português primeiro."""
    codes = sorted(p.stem for p in _locales_dir().glob("*.toml"))
    codes.sort(key=lambda c: (c != BASE, c))
    out = []
    for c in codes:
        _load(c)
        out.append((c, _names.get(c, c)))
    return out


def set_language(code: str) -> None:
    global _lang
    codes = {c for c, _ in available()}
    _lang = code if code in codes else BASE


def language() -> str:
    return _lang


def tr(msg_id: str, /, **kw) -> str:
    msg = _load(_lang).get(msg_id)
    if msg is None:
        msg = _load(BASE).get(msg_id, msg_id)
    try:
        return msg.format(**kw)
    except (KeyError, IndexError, ValueError):
        return msg


def keys(code: str) -> set[str]:
    return set(_load(code))
