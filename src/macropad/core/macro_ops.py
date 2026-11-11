"""Operações sobre macros de um conjunto: arquivo, restauro, duplicados,
cópia/colagem e reordenação. Puras (sem UI), para poderem ser testadas.

Convenção de ordem: em ``MacroSet.macros`` as macros ativas vêm primeiro e as
arquivadas depois. A ordem de cada grupo é a ordem visual."""
from __future__ import annotations

import copy
from typing import Optional

from .commands import CommandError, parse_action
from .keys import KeyBindingError, parse_binding
from .model import Macro, MacroSet


def normalize_order(ms: MacroSet) -> None:
    """Ativas primeiro, arquivadas depois (ordem relativa preservada)."""
    ms.macros = ([m for m in ms.macros if not m.arquivada]
                 + [m for m in ms.macros if m.arquivada])


def _binding(key: str):
    try:
        return parse_binding(key) if key.strip() else None
    except KeyBindingError:
        return None


# ------------------------------------------------------------- duplicados
def content_key(text: str) -> Optional[tuple]:
    """Sequência de texto e comandos normalizada. ``{enter}`` = ``{Enter}`` =
    quebra de linha. None para texto vazio ou inválido."""
    try:
        steps = parse_action(text)
    except CommandError:
        return None
    return tuple(steps) or None


def duplicate_groups(macros: list[Macro]) -> dict[int, list[int]]:
    """Para cada macro com conteúdo repetido, os índices das outras macros com
    o mesmo conteúdo (independentemente do título, tecla ou arquivo)."""
    by_key: dict[tuple, list[int]] = {}
    for i, m in enumerate(macros):
        k = content_key(m.texto)
        if k is not None:
            by_key.setdefault(k, []).append(i)
    out: dict[int, list[int]] = {}
    for idxs in by_key.values():
        if len(idxs) > 1:
            for i in idxs:
                out[i] = [j for j in idxs if j != i]
    return out


# ------------------------------------------------------------------ arquivo
def archive(ms: MacroSet, i: int) -> int:
    """Arquiva a macro ``i``; passa para o início do arquivo. Devolve o novo índice."""
    m = ms.macros.pop(i)
    m.arquivada = True
    pos = len([x for x in ms.macros if not x.arquivada])
    ms.macros.insert(pos, m)
    return pos


def archive_many(ms: MacroSet, idxs: list[int]) -> list[int]:
    """Arquiva várias macros (mantendo a ordem relativa); ficam no início do
    arquivo. Devolve os novos índices."""
    chosen = [ms.macros[i] for i in sorted(set(idxs)) if not ms.macros[i].arquivada]
    ids = {id(m) for m in chosen}
    for m in chosen:
        m.arquivada = True
    actives = [m for m in ms.macros if not m.arquivada]
    arch = [m for m in ms.macros if m.arquivada and id(m) not in ids]
    ms.macros = actives + chosen + arch
    return list(range(len(actives), len(actives) + len(chosen)))


def delete_many(ms: MacroSet, idxs: list[int]) -> None:
    for i in sorted(set(idxs), reverse=True):
        del ms.macros[i]


def index_of(ms: MacroSet, m: Macro) -> int:
    return next(i for i, x in enumerate(ms.macros) if x is m)


def key_conflict(ms: MacroSet, i: int) -> Optional[int]:
    """Índice da macro ativa que já usa a tecla da macro ``i`` (ou None)."""
    b = _binding(ms.macros[i].tecla)
    if b is None:
        return None
    for j, m in enumerate(ms.macros):
        if j != i and not m.arquivada and _binding(m.tecla) == b:
            return j
    return None


def restore(ms: MacroSet, i: int) -> int:
    """Restaura a macro ``i`` para o fim das ativas. Devolve o novo índice.
    Não verifica conflitos de tecla (ver ``key_conflict``)."""
    m = ms.macros.pop(i)
    m.arquivada = False
    pos = len([x for x in ms.macros if not x.arquivada])
    ms.macros.insert(pos, m)
    return pos


def restore_replacing(ms: MacroSet, i: int, j: int) -> int:
    """Restaura a macro arquivada ``i`` no lugar da macro ativa ``j`` (com a
    mesma tecla) e arquiva ``j``. Devolve o índice da macro restaurada."""
    restored, replaced = ms.macros[i], ms.macros[j]
    restored.arquivada = False
    replaced.arquivada = True
    ms.macros[j] = restored
    ms.macros.pop(i)
    # a substituída vai para o início do arquivo
    pos = len([x for x in ms.macros if not x.arquivada])
    ms.macros.insert(pos, replaced)
    return next(k for k, m in enumerate(ms.macros) if m is restored)


def matches_query(m: Macro, query: str) -> bool:
    q = query.strip().lower()
    if not q:
        return True
    return q in m.titulo.lower() or q in m.texto.lower() or q in m.tecla.lower()


# --------------------------------------------------------- copiar / colar
def insert_copy(ms: MacroSet, m: Macro, after: Optional[int]) -> int:
    """Insere uma cópia ativa de ``m`` a seguir a ``after`` (ou no fim das
    ativas). A tecla é limpa se já estiver em uso por uma macro ativa."""
    new = copy.deepcopy(m)
    new.arquivada = False
    b = _binding(new.tecla)
    if b is not None and any(not x.arquivada and _binding(x.tecla) == b for x in ms.macros):
        new.tecla = ""
    n_active = len([x for x in ms.macros if not x.arquivada])
    pos = n_active if after is None or after >= n_active or after < 0 else after + 1
    ms.macros.insert(pos, new)
    return pos


def new_macro(ms: MacroSet, title: str) -> int:
    """Acrescenta uma única macro nova (sem tecla, texto vazio) no fim das ativas."""
    pos = len([x for x in ms.macros if not x.arquivada])
    ms.macros.insert(pos, Macro(titulo=title))
    return pos


# ---------------------------------------------------------------- reordenar
def reorder_group(ms: MacroSet, archived: bool, order: list[int]) -> None:
    """Aplica uma nova ordem (lista de índices atuais) a um dos grupos."""
    group = [ms.macros[i] for i in order]
    actives = [m for m in ms.macros if not m.arquivada]
    arch = [m for m in ms.macros if m.arquivada]
    ms.macros = (actives + group) if archived else (group + arch)


def move(ms: MacroSet, i: int, delta: int) -> int:
    """Move a macro ``i`` dentro do seu grupo. Devolve o novo índice."""
    j = i + delta
    if not (0 <= j < len(ms.macros)) or ms.macros[j].arquivada != ms.macros[i].arquivada:
        return i
    ms.macros[i], ms.macros[j] = ms.macros[j], ms.macros[i]
    return j
