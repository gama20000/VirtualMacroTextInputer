"""Interpretação do texto de uma macro: texto literal com comandos intercalados.

Comandos suportados (nomes sem distinção de maiúsculas/minúsculas):

* ``{Enter}``      – pressiona Enter
* ``{Tab}``        – pressiona Tab
* ``{Delay:500}``  – espera 500 ms (0 a 600000)
* ``{MediaPlayPause}``, ``{MediaPrev}``, ``{MediaNext}``, ``{MediaStop}``,
  ``{VolumeUp}``, ``{VolumeDown}``, ``{VolumeMute}`` – pressionam a tecla
  multimédia correspondente (um botão do painel pode ser Reproduzir/Pausa)

Regras:

* ``{Enter}``, ``{Tab}`` e as teclas multimédia são sempre comandos.
* Uma chaveta seguida de um nome conhecido tem de formar um comando válido;
  caso contrário é um erro (ex.: ``{Delay:abc}``, ``{Enter``).
* ``{Palavra}`` ou ``{Palavra:...}`` com um nome desconhecido é um erro
  (normalmente é um erro de escrita, como ``{Entr}``).
* Qualquer outra chaveta (``{}``, ``{ x``, ``{1}``) é texto literal.
* Quebras de linha no texto equivalem a ``{Enter}`` e tabulações a ``{Tab}``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Union

from ..i18n import tr
from .keys import display_binding

MAX_DELAY_MS = 600_000


@dataclass(frozen=True)
class TextStep:
    text: str


@dataclass(frozen=True)
class KeyStep:
    key: str  # "Enter", "Tab" ou uma tecla multimédia (MEDIA_COMMANDS)


@dataclass(frozen=True)
class DelayStep:
    ms: int


Step = Union[TextStep, KeyStep, DelayStep]


class CommandError(ValueError):
    """Erro de sintaxe num texto de macro.

    ``position`` é o índice (0-based) do carácter onde o problema começa.
    """

    def __init__(self, message: str, position: int):
        super().__init__(message)
        self.message = message
        self.position = position

    def __str__(self) -> str:
        return tr("cmd.at_position", msg=self.message, pos=self.position + 1)


# Teclas multimédia que o texto de uma macro pode pressionar (nome canónico,
# o mesmo das associações de teclas).
MEDIA_COMMANDS: tuple[str, ...] = ("MediaPlayPause", "MediaPrev", "MediaNext", "MediaStop",
                                   "VolumeUp", "VolumeDown", "VolumeMute")
_KNOWN = {"enter": "Enter", "tab": "Tab", "delay": "Delay",
          **{k.lower(): k for k in MEDIA_COMMANDS}}
VALID_COMMANDS = "{Enter}, {Tab}, {Delay:ms}, {MediaPlayPause}, {MediaPrev}, {MediaNext}, …"
_NAME_RE = re.compile(r"[A-Za-z]+")


def parse_action(text: str) -> list[Step]:
    steps: list[Step] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            steps.append(TextStep("".join(buf)))
            buf.clear()

    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\r":
            # \r\n ou \r isolado -> Enter
            flush()
            steps.append(KeyStep("Enter"))
            i += 2 if i + 1 < n and text[i + 1] == "\n" else 1
            continue
        if ch == "\n":
            flush()
            steps.append(KeyStep("Enter"))
            i += 1
            continue
        if ch == "\t":
            flush()
            steps.append(KeyStep("Tab"))
            i += 1
            continue
        if ch != "{":
            buf.append(ch)
            i += 1
            continue

        m = _NAME_RE.match(text, i + 1)
        if not m:
            buf.append(ch)            # "{" literal
            i += 1
            continue
        name = m.group(0)
        j = m.end()
        nxt = text[j] if j < n else ""
        known = _KNOWN.get(name.lower())

        if known is None:
            if nxt in ("}", ":"):
                close = text.find("}", j)
                shown = text[i: close + 1] if close != -1 else text[i: j + 1]
                raise CommandError(tr("cmd.unknown", cmd=shown,
                                      valid=VALID_COMMANDS), i)
            buf.append(ch)            # ex.: "{abc def" -> literal
            i += 1
            continue

        if known != "Delay":
            if nxt != "}":
                if nxt == ":":
                    raise CommandError(tr("cmd.no_params", cmd="{" + known + "}"), i)
                raise CommandError(tr("cmd.not_closed", cmd="{" + known + "}", close="}"), i)
            flush()
            steps.append(KeyStep(known))
            i = j + 1
            continue

        # Delay
        if nxt != ":":
            if nxt == "}":
                raise CommandError(tr("cmd.delay_needs_value", cmd="{Delay}",
                                      example="{Delay:500}"), i)
            raise CommandError(tr("cmd.malformed", cmd="{Delay:ms}"), i)
        close = text.find("}", j)
        if close == -1:
            raise CommandError(tr("cmd.not_closed", cmd="{Delay:…}", close="}"), i)
        value = text[j + 1: close].strip()
        if not value.isdigit():
            raise CommandError(tr("cmd.delay_invalid", value=value,
                                  example="{Delay:500}"), i)
        ms = int(value)
        if ms > MAX_DELAY_MS:
            raise CommandError(tr("cmd.delay_too_big", ms=ms, max=MAX_DELAY_MS), i)
        flush()
        steps.append(DelayStep(ms))
        i = close + 1

    flush()
    return steps


def media_action(text: str) -> Optional[str]:
    """A tecla multimédia que a macro envia, se o texto for só esse comando
    (ex.: ``"{MediaPlayPause}"``; a mesma tecla repetida também conta). Serve
    para desenhar o ícone do botão. Qualquer outro texto: ``None``."""
    try:
        steps = parse_action(text)
    except CommandError:
        return None
    keys = {s.key for s in steps if isinstance(s, KeyStep)}
    if steps and len(keys) == 1 and all(isinstance(s, KeyStep) for s in steps):
        key = keys.pop()
        return key if key in MEDIA_COMMANDS else None
    return None


def describe_steps(steps: list[Step]) -> str:
    """Descrição legível (usada em mensagens e testes)."""
    out = []
    for s in steps:
        if isinstance(s, TextStep):
            out.append(tr("step.type", text=s.text))
        elif isinstance(s, KeyStep):
            out.append(tr("step.press", key=display_binding(s.key)))
        else:
            out.append(tr("step.wait", ms=s.ms))
    return ", ".join(out)
