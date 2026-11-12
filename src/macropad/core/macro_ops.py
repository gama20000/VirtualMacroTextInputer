"""Operações sobre macros de um conjunto: arquivo, restauro, duplicados,
cópia/colagem e reordenação. Puras (sem UI), para poderem ser testadas.

Convenção de ordem: em ``MacroSet.macros`` as macros ativas vêm primeiro e as
arquivadas depois. A ordem de cada grupo é a ordem visual."""
from __future__ import annotations

import copy
import uuid
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
        if m.tipo != "texto":
            continue                    # espaços e contadores não têm conteúdo
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
    chosen = [ms.macros[i] for i in sorted(set(idxs))
              if not ms.macros[i].arquivada and not ms.macros[i].is_space]
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
    """Insere uma cópia de ``m`` logo a seguir a ``after``, na mesma área de
    ``after`` (Ativo ou Arquivo); sem ``after``, no fim das ativas.

    Numa cópia ativa, a tecla é limpa se já estiver em uso por uma macro ativa.
    Os contadores copiados recebem um id novo (contagem própria)."""
    new = copy.deepcopy(m)
    valid_after = after is not None and 0 <= after < len(ms.macros)
    new.arquivada = bool(valid_after and ms.macros[after].arquivada) and not new.is_space
    if new.is_counter:
        new.id = new_id()
    b = _binding(new.tecla)
    if (not new.arquivada and b is not None
            and any(not x.arquivada and _binding(x.tecla) == b for x in ms.macros)):
        new.tecla = ""
    if valid_after and ms.macros[after].arquivada == new.arquivada:
        pos = after + 1
    else:
        pos = len([x for x in ms.macros if not x.arquivada])
    ms.macros.insert(pos, new)
    return pos


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def new_macro(ms: MacroSet, title: str) -> int:
    """Acrescenta uma única macro nova (sem tecla, texto vazio) no fim das ativas."""
    return _append_active(ms, Macro(titulo=title))


def new_space(ms: MacroSet) -> int:
    """Acrescenta um espaço vazio no fim das ativas."""
    return _append_active(ms, Macro(tipo="espaco"))


def new_counter(ms: MacroSet, title: str) -> int:
    """Acrescenta um contador (incremento 1, reposição 0) no fim das ativas."""
    return _append_active(ms, Macro(titulo=title, tipo="contador", id=new_id()))


def _append_active(ms: MacroSet, m: Macro) -> int:
    pos = len([x for x in ms.macros if not x.arquivada])
    ms.macros.insert(pos, m)
    return pos


def move_items(ms: MacroSet, items: list[Macro], to_archive: bool,
               anchor: Optional[Macro] = None, after: bool = False) -> list[int]:
    """Move ``items`` para a área indicada, imediatamente antes (ou depois) de
    ``anchor``; sem âncora, para o fim da área. Serve para reorganizar dentro de
    uma área e para mover entre Ativo e Arquivo.

    Espaços vazios não vão para o Arquivo (ficam onde estão). A âncora tem de
    estar na área de destino e não pode ser um dos itens movidos. Devolve os
    novos índices dos itens movidos, pela ordem dada. Não verifica conflitos de
    tecla (ver ``key_conflict``)."""
    if to_archive:
        items = [m for m in items if not m.is_space]
    if not items:
        return []
    moving = {id(m) for m in items}
    if anchor is not None and (id(anchor) in moving or anchor.arquivada != to_archive):
        anchor = None
    rest = [m for m in ms.macros if id(m) not in moving]
    for m in items:
        m.arquivada = to_archive
    if anchor is not None:
        pos = next(k for k, m in enumerate(rest) if m is anchor) + (1 if after else 0)
    else:
        n_active = len([m for m in rest if not m.arquivada])
        pos = len(rest) if to_archive else n_active
    ms.macros = rest[:pos] + list(items) + rest[pos:]
    normalize_order(ms)
    return [index_of(ms, m) for m in items]


def swap(ms: MacroSet, a: int, b: int) -> None:
    """Troca dois itens da mesma área (ex.: um botão com um espaço vazio)."""
    if ms.macros[a].arquivada == ms.macros[b].arquivada:
        ms.macros[a], ms.macros[b] = ms.macros[b], ms.macros[a]


# ---------------------------------------------------------------- reordenar
def reorder_group(ms: MacroSet, archived: bool, order: list[int]) -> None:
    """Aplica uma nova ordem a parte de um grupo.

    ``order`` são os índices atuais das macros *visíveis* na grelha, pela nova
    ordem. Com a pesquisa do Arquivo ativa, só uma parte das arquivadas está
    visível: as visíveis trocam de posição entre si, ocupando as mesmas
    posições que já tinham, e as ocultas ficam onde estão. Nenhuma macro é
    descartada."""
    n = len(ms.macros)
    if (len(set(order)) != len(order)
            or any(not (0 <= i < n) or ms.macros[i].arquivada != archived for i in order)):
        return                                # ordem inválida: não altera nada
    new = list(ms.macros)
    for slot, src in zip(sorted(order), order):
        new[slot] = ms.macros[src]
    ms.macros = new
    normalize_order(ms)


def move(ms: MacroSet, i: int, delta: int) -> int:
    """Move a macro ``i`` dentro do seu grupo. Devolve o novo índice."""
    j = i + delta
    if not (0 <= j < len(ms.macros)) or ms.macros[j].arquivada != ms.macros[i].arquivada:
        return i
    ms.macros[i], ms.macros[j] = ms.macros[j], ms.macros[i]
    return j
