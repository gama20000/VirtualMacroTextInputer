"""Widgets partilhados: botão-tile, grelhas com arrasto posicional e captura
de tecla. O desenho dos botões (``paint_tile``) é o mesmo no painel, na
pré-visualização e na área «Ativo» da configuração."""
from __future__ import annotations

import sys
from typing import Callable, Optional

from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QKeyEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QLineEdit, QListWidget,
                               QListWidgetItem, QStyle, QStyledItemDelegate, QWidget)

from ..core.keys import MODIFIERS, Binding
from ..core.model import PanelSettings
from ..i18n import tr
from ..platform.winkeys import VK_TO_NAME
from . import theme

TITLE_ROLE = Qt.UserRole + 1
KEY_ROLE = Qt.UserRole + 2
ERROR_ROLE = Qt.UserRole + 3
INDEX_ROLE = Qt.UserRole + 4
DUP_ROLE = Qt.UserRole + 5
KIND_ROLE = Qt.UserRole + 6
COUNT_ROLE = Qt.UserRole + 7

DEFAULT_STYLE = PanelSettings()


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(round(a.red() + (b.red() - a.red()) * t),
                  round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t))


# --------------------------------------------------------------------- tile
def _tile_rect(rect: QRect) -> QRectF:
    side = min(rect.width(), rect.height())
    return QRectF(rect.x() + (rect.width() - side) / 2 + 3,
                  rect.y() + (rect.height() - side) / 2 + 3, side - 6, side - 6)


def paint_space(p: QPainter, rect: QRect, style: PanelSettings, pal: theme.Palette,
                *, selected=False, hover=False) -> None:
    """Espaço vazio: só se vê na configuração (contorno tracejado)."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    r = _tile_rect(rect)
    radius = r.width() * style.arredondamento / 100.0
    color = QColor(pal.accent if selected else pal.muted)
    if not selected and not hover:
        color.setAlpha(150)
    p.setPen(QPen(color, 3 if selected else 1.5, Qt.DashLine))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(r, radius, radius)
    p.restore()


def paint_tile(p: QPainter, rect: QRect, title: str, key: str, style: PanelSettings,
               pal: theme.Palette, *, selected=False, error=False, dup=False, hover=False,
               pressed=False, dim=False, running=False, waiting=False,
               count: Optional[int] = None) -> None:
    """Desenha um botão de macro (ou de contador, se ``count`` não for None).

    O título e a tecla ocupam as faixas indicadas no estilo (em cima, ao centro,
    em baixo). Elementos na mesma faixa empilham-se; o título é cortado com
    reticências se não couber, para nunca se sobrepor à tecla nem à contagem.
    """
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    r = _tile_rect(rect)
    bg = QColor(style.cor_botao)
    fg = QColor(style.cor_texto)
    radius = r.width() * style.arredondamento / 100.0
    path = QPainterPath()
    path.addRoundedRect(r, radius, radius)
    p.fillPath(path, _mix(bg, fg, 0.12) if pressed else (_mix(bg, fg, 0.05) if hover else bg))

    if waiting:
        border, width = QColor(pal.warn), 3
    elif error:
        border, width = QColor(pal.error), 3
    elif running:
        border, width = QColor(pal.ok), 3
    elif selected:
        border, width = QColor(pal.accent), 3
    elif dup:
        border, width = QColor(pal.dup), 3
    else:
        border = QColor(style.cor_borda)
        if hover:
            border = _mix(border, fg, 0.35)
        width = style.borda
    if width > 0:
        p.setPen(QPen(border, width))
        p.drawPath(path)

    if dim:
        p.setOpacity(0.35)
    scale = style.escala_texto / 100.0
    inner = r.adjusted(6, 5, -6, -5)

    fk = QFont(p.font())
    fk.setBold(True)
    fk.setPointSizeF(max(6.0, r.height() / 11 * scale))
    fmk = QFontMetrics(fk)
    ft = QFont(p.font())
    ft.setBold(True)
    ft.setPointSizeF(max(6.5, r.height() / 9.5 * scale))
    fmt = QFontMetrics(ft)
    fc = QFont(p.font())
    fc.setBold(True)
    fc.setPointSizeF(max(8.0, r.height() / 4.2 * scale))
    fmc = QFontMetrics(fc)

    key_label = (tr("tile.press_key") if waiting else (key or "—"))
    key_h = fmk.height() + 2
    # faixas: o contador ocupa sempre o centro; o título vai para cima se
    # também tiver sido posto ao centro.
    pos_title = style.posicao_titulo
    pos_key = style.posicao_tecla
    if count is not None and pos_title == "centro":
        pos_title = "cima"
    show_key = style.mostrar_tecla or waiting
    bands: dict[str, list[str]] = {"cima": [], "centro": [], "baixo": []}
    if count is not None:
        bands["centro"].append("count")
    bands[pos_title].append("title")
    if show_key:
        bands[pos_key].append("key")

    def fixed_h(el: str) -> float:
        return key_h if el == "key" else (fmc.height() if el == "count" else 0)

    # altura disponível para o título (o resto é fixo)
    fixed_total = sum(fixed_h(e) for b in bands.values() for e in b) + 4 * (
        sum(len(b) for b in bands.values()) - 1)
    lines_avail = max(1, int((inner.height() - fixed_total) // fmt.lineSpacing()))
    title_lines = min(3, lines_avail)
    # quebra o título em linhas que caibam
    words = title.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if fmt.horizontalAdvance(t) <= inner.width() or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > title_lines:
        lines = lines[:title_lines]
        lines[-1] = lines[-1] + "…"
    lines = [fmt.elidedText(ln, Qt.ElideRight, int(inner.width())) for ln in lines] or [""]
    title_h = fmt.lineSpacing() * len(lines)

    def h(el: str) -> float:
        return title_h if el == "title" else fixed_h(el)

    def draw(el: str, y: float) -> None:
        if el == "title":
            p.setFont(ft)
            p.setPen(fg)
            for k, ln in enumerate(lines):
                p.drawText(QRectF(inner.left(), y + k * fmt.lineSpacing(), inner.width(),
                                  fmt.lineSpacing()), Qt.AlignHCenter | Qt.AlignVCenter, ln)
        elif el == "count":
            p.setFont(fc)
            p.setPen(fg)
            p.drawText(QRectF(inner.left(), y, inner.width(), fmc.height()), Qt.AlignCenter,
                       fmc.elidedText(str(count), Qt.ElideRight, int(inner.width())))
        else:
            p.setFont(fk)
            w = min(fmk.horizontalAdvance(key_label) + 12, inner.width())
            pill = QRectF(r.center().x() - w / 2, y, w, key_h)
            pp = QPainterPath()
            pp.addRoundedRect(pill, pill.height() / 2, pill.height() / 2)
            if waiting:
                p.fillPath(pp, QColor(pal.warn))
                p.setPen(QColor("#000000"))
            else:
                p.fillPath(pp, _mix(bg, fg, 0.22 if key else 0.1))
                p.setPen(_mix(bg, fg, 0.85 if key else 0.45))
            p.drawText(pill, Qt.AlignCenter, fmk.elidedText(key_label, Qt.ElideRight, int(w - 6)))

    gap = 4
    y = inner.top()
    for el in bands["cima"]:
        draw(el, y)
        y += h(el) + gap
    top_end = y
    y = inner.bottom()
    for el in reversed(bands["baixo"]):
        y -= h(el)
        draw(el, y)
        y -= gap
    bottom_start = y
    center = bands["centro"]
    if center:
        total = sum(h(e) for e in center) + gap * (len(center) - 1)
        y = max(top_end, min((inner.top() + inner.bottom() - total) / 2, bottom_start - total))
        for el in center:
            draw(el, y)
            y += h(el) + gap

    # selos: erro (vermelho, "!") e conteúdo duplicado (amarelo, "=")
    p.setOpacity(1.0)
    badges = []
    if error:
        badges.append((pal.error, "!"))
    if dup:
        badges.append((pal.dup, "="))
    bs = max(14.0, r.width() * 0.2)
    for n, (color, ch) in enumerate(badges):
        br = QRectF(r.right() - bs + 4 - n * (bs + 2), r.top() - 4, bs, bs)
        p.setPen(QPen(QColor(pal.bg), 2))
        p.setBrush(QColor(color))
        p.drawEllipse(br)
        bf = QFont(p.font())
        bf.setBold(True)
        bf.setPointSizeF(bs * 0.45)
        p.setFont(bf)
        p.setPen(QColor("#000000") if ch == "=" else QColor("#ffffff"))
        p.drawText(br, Qt.AlignCenter, ch)
    p.restore()


class TileButton(QAbstractButton):
    """Botão do painel. Nunca recebe foco (o foco fica na aplicação de destino).

    Num contador (``count`` não None), um clique curto emite ``short_clicked`` e
    manter premido durante ``long_ms`` emite ``long_pressed`` (sem clique)."""

    short_clicked = Signal()
    long_pressed = Signal()

    def __init__(self, title: str, key: str, style: PanelSettings, pal: theme.Palette,
                 count: Optional[int] = None, long_ms: int = 800, parent=None):
        super().__init__(parent)
        self.title, self.key = title, key
        self.tile_style, self.pal = style, pal
        self.count = count
        self.running = False
        self._long_done = False
        self._long_timer = QTimer(self, singleShot=True, interval=long_ms,
                                  timeout=self._on_long)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(style.tamanho_botao, style.tamanho_botao)
        tip = tr("tile.tooltip", title=title, key=key or tr("tile.no_key"))
        if count is not None:
            tip += "\n" + tr("tile.counter_tip", ms=long_ms)
        self.setToolTip(tip)
        self.setCursor(Qt.PointingHandCursor)

    def _on_long(self):
        self._long_done = True
        self.long_pressed.emit()
        self.update()

    def mousePressEvent(self, e):
        self._long_done = False
        if self.count is not None and e.button() == Qt.LeftButton and self.isEnabled():
            self._long_timer.start()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._long_timer.stop()
        was_long = self._long_done
        super().mouseReleaseEvent(e)
        if self.count is not None and not was_long and e.button() == Qt.LeftButton \
                and self.rect().contains(e.position().toPoint()) and self.isEnabled():
            self.short_clicked.emit()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        paint_tile(p, self.rect(), self.title, self.key, self.tile_style, self.pal,
                   hover=self.underMouse(), pressed=self.isDown(), dim=not self.isEnabled(),
                   running=self.running, count=self.count)
        p.end()

    def enterEvent(self, e):
        self.update(); super().enterEvent(e)

    def leaveEvent(self, e):
        self.update(); super().leaveEvent(e)


# ------------------------------------------------------------ grelha editável
class _TileDelegate(QStyledItemDelegate):
    def __init__(self, grid: "MacroGrid"):
        super().__init__(grid)
        self.grid = grid

    def paint(self, p, option, index):
        g = self.grid
        r = option.rect
        side = min(r.width(), r.height(), g.style_.tamanho_botao)
        box = QRect(r.center().x() - side // 2, r.center().y() - side // 2, side, side)
        selected = bool(option.state & QStyle.State_Selected)
        hover = bool(option.state & QStyle.State_MouseOver)
        real = index.data(INDEX_ROLE)
        if index.data(KIND_ROLE) == "espaco":
            paint_space(p, box, g.style_, g.pal, selected=selected, hover=hover)
            return
        paint_tile(p, box, index.data(TITLE_ROLE) or "", index.data(KEY_ROLE) or "",
                   g.style_, g.pal, selected=selected,
                   error=bool(index.data(ERROR_ROLE)), dup=bool(index.data(DUP_ROLE)),
                   hover=hover, dim=g.archived,
                   waiting=g.capture_hover and real == g.hovered,
                   count=index.data(COUNT_ROLE))

    def sizeHint(self, option, index):
        c = self.grid.cell()
        return QSize(c, c)


class MacroGrid(QListWidget):
    """Grelha de macros (área Ativo ou Arquivo).

    * ``INDEX_ROLE`` guarda o índice real em ``MacroSet.macros``.
    * Arrastar e largar é tratado aqui (não pelo ``QListWidget``), para que a
      largada fique na posição indicada — antes ou depois do item sob o
      ponteiro — também entre grelhas diferentes. ``dropped`` comunica o
      pedido; quem gere os dados reconstrói a grelha.
    * Com ``columns`` definido, a grelha tem a largura exata dessas colunas
      (como o painel); sem ele, ocupa a largura disponível.
    """

    # origem, índices reais arrastados, índice real da âncora (-1 = fim),
    # depois da âncora?, índice real do espaço vazio sob o ponteiro (-1 = nenhum)
    dropped = Signal(object, list, int, bool, int)
    hover_changed = Signal(int)            # índice real sob o ponteiro (-1 = nenhum)

    def __init__(self, pal: theme.Palette, archived: bool = False, parent=None):
        super().__init__(parent)
        self.pal = pal
        self.archived = archived
        self.style_ = PanelSettings()
        self.columns: Optional[int] = None
        self.hovered = -1
        self.capture_hover = False
        self._drop_line: Optional[QRect] = None
        self.setObjectName("grid")
        self.setViewMode(QListWidget.ListMode)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.Adjust)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setMouseTracking(True)
        self.setItemDelegate(_TileDelegate(self))
        self.setFrameShape(QListWidget.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.itemEntered.connect(lambda it: self._set_hover(it.data(INDEX_ROLE)))
        self.apply_style(self.style_)

    # ----------------------------------------------------------- aspeto
    def cell(self) -> int:
        return self.style_.tamanho_botao + self.style_.espacamento

    def apply_style(self, style: PanelSettings, columns: Optional[int] = None) -> None:
        self.style_ = style
        self.columns = columns
        c = self.cell()
        self.setGridSize(QSize(c, c))
        self.setSpacing(0)
        self.fit_size()
        self.viewport().update()

    def fit_size(self) -> None:
        """Tamanho fixo que mostra todas as linhas (e colunas, se fixas)."""
        c = self.cell()
        n = max(1, self.count())
        if self.columns:
            cols = self.columns
            self.setFixedWidth(cols * c + 4)
        else:
            self.setMinimumWidth(c + 4)
            self.setMaximumWidth(16777215)
            cols = max(1, (self.viewport().width() or self.width()) // c)
        rows = -(-n // cols)
        self.setFixedHeight(rows * c + 4)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if not self.columns:
            QTimer.singleShot(0, self.fit_size)

    # ----------------------------------------------------------- conteúdo
    def set_tiles(self, tiles: list[dict], selected, current: int = -1) -> None:
        """tiles: dicts com index, kind, title, key, error, dup, tip, count."""
        if isinstance(selected, int):
            selected = {selected}
        selected = set(selected)
        self.blockSignals(True)
        self.clear()
        sel_row = -1
        for t in tiles:
            it = QListWidgetItem()
            it.setData(TITLE_ROLE, t["title"])
            it.setData(KEY_ROLE, t["key"])
            it.setData(ERROR_ROLE, t["error"])
            it.setData(DUP_ROLE, t["dup"])
            it.setData(INDEX_ROLE, t["index"])
            it.setData(KIND_ROLE, t.get("kind", "texto"))
            it.setData(COUNT_ROLE, t.get("count"))
            it.setToolTip(t["tip"])
            it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
            self.addItem(it)
            if t["index"] in selected:
                it.setSelected(True)
                if sel_row < 0 or t["index"] == current:
                    sel_row = self.count() - 1
        if sel_row >= 0:
            from PySide6.QtCore import QItemSelectionModel
            self.selectionModel().setCurrentIndex(self.indexFromItem(self.item(sel_row)),
                                                  QItemSelectionModel.NoUpdate)
        else:
            self.clearSelection()
            self.setCurrentRow(-1)
        self.blockSignals(False)
        self.fit_size()

    def real_index(self, row: int) -> int:
        it = self.item(row)
        return it.data(INDEX_ROLE) if it else -1

    def selected_real(self) -> list[int]:
        """Índices reais selecionados, pela ordem visual."""
        return [self.item(r).data(INDEX_ROLE) for r in range(self.count())
                if self.item(r).isSelected()]

    # -------------------------------------------------------------- hover
    def _set_hover(self, real: int) -> None:
        if real != self.hovered:
            self.hovered = real
            self.viewport().update()
            self.hover_changed.emit(real)

    def leaveEvent(self, e):
        self._set_hover(-1)
        super().leaveEvent(e)

    def mouseMoveEvent(self, e):
        if self.itemAt(e.position().toPoint()) is None:
            self._set_hover(-1)
        super().mouseMoveEvent(e)

    # ------------------------------------------------------ arrastar/largar
    def _target(self, pos: QPoint):
        """(âncora real, depois?, espaço real, retângulo da linha)"""
        it = self.itemAt(pos)
        if it is None:
            # depois do último item da linha mais próxima, ou fim da grelha
            return -1, False, -1, None
        rect = self.visualItemRect(it)
        real = it.data(INDEX_ROLE)
        if it.data(KIND_ROLE) == "espaco":
            return real, False, real, rect
        after = pos.x() > rect.center().x()
        x = rect.right() if after else rect.left()
        return real, after, -1, QRect(x - 2, rect.top() + 4, 4, rect.height() - 8)

    @staticmethod
    def _accepts(e) -> bool:
        src = e.source()
        return isinstance(src, MacroGrid) and bool(src.selected_real())

    def dragEnterEvent(self, e):
        if self._accepts(e):
            e.setDropAction(Qt.CopyAction)   # cópia: a grelha de origem não remove itens
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if not self._accepts(e):
            e.ignore()
            return
        anchor, after, space, line = self._target(e.position().toPoint())
        self._drop_line = line
        self._drop_space = space
        self.viewport().update()
        e.setDropAction(Qt.CopyAction)
        e.accept()

    def dragLeaveEvent(self, e):
        self._drop_line = None
        self.viewport().update()
        super().dragLeaveEvent(e)

    def dropEvent(self, e):
        self._drop_line = None
        self.viewport().update()
        if not self._accepts(e):
            e.ignore()
            return
        src = e.source()
        idxs = src.selected_real()
        anchor, after, space, _ = self._target(e.position().toPoint())
        e.setDropAction(Qt.CopyAction)
        e.accept()
        # depois de o arrasto terminar (a origem ainda está no QDrag.exec)
        QTimer.singleShot(0, lambda: self.dropped.emit(src, idxs, anchor, after, space))

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._drop_line is not None:
            p = QPainter(self.viewport())
            if getattr(self, "_drop_space", -1) >= 0:
                p.setPen(QPen(QColor(self.pal.accent), 3, Qt.DashLine))
                p.drawRect(self._drop_line.adjusted(4, 4, -4, -4))
            else:
                p.fillRect(self._drop_line, QColor(self.pal.accent))
            p.end()


class AreaDropZone(QWidget):
    """Área (Ativo ou Arquivo) que aceita macros largadas fora da grelha (no
    título, na zona vazia): ficam no fim dessa área. Os arrastos que a grelha
    não aceita chegam aqui por propagação."""

    dropped = Signal(object, list)        # grelha de origem, índices reais

    def __init__(self, pal: theme.Palette, archived: bool, parent=None):
        super().__init__(parent)
        self.pal = pal
        self.archived = archived
        self.setAcceptDrops(True)
        self._hover = False

    def _accepts(self, e) -> bool:
        src = e.source()
        return isinstance(src, MacroGrid) and bool(src.selected_real())

    def dragEnterEvent(self, e):
        if self._accepts(e):
            e.setDropAction(Qt.CopyAction)
            e.accept()
            self._set_hover(True)
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if self._accepts(e):
            e.setDropAction(Qt.CopyAction)
            e.accept()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        self._set_hover(False)

    def dropEvent(self, e):
        self._set_hover(False)
        if not self._accepts(e):
            e.ignore()
            return
        src = e.source()
        idxs = src.selected_real()
        e.setDropAction(Qt.CopyAction)
        e.accept()
        QTimer.singleShot(0, lambda: self.dropped.emit(src, idxs))

    def _set_hover(self, on: bool) -> None:
        self._hover = on
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._hover:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor(self.pal.accent), 2, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 10, 10)
            p.end()


# ------------------------------------------------------------ captura de tecla
_QT_FALLBACK = {Qt.Key_Space: "Space", Qt.Key_Tab: "Tab", Qt.Key_Backtab: "Tab",
                Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter", Qt.Key_Backspace: "Backspace",
                Qt.Key_Escape: "Escape", Qt.Key_Insert: "Insert", Qt.Key_Delete: "Delete",
                Qt.Key_Home: "Home", Qt.Key_End: "End", Qt.Key_PageUp: "PageUp",
                Qt.Key_PageDown: "PageDown", Qt.Key_Up: "Up", Qt.Key_Down: "Down",
                Qt.Key_Left: "Left", Qt.Key_Right: "Right", Qt.Key_Pause: "Pause",
                Qt.Key_ScrollLock: "ScrollLock"}
_MOD_KEYS = {Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_AltGr,
             Qt.Key_Super_L, Qt.Key_Super_R}


def key_name_from_event(e: QKeyEvent) -> Optional[str]:
    if sys.platform == "win32":
        vk = e.nativeVirtualKey()
        if vk and vk in VK_TO_NAME:
            return VK_TO_NAME[vk]
    k = e.key()
    kp = bool(e.modifiers() & Qt.KeypadModifier)
    if Qt.Key_0 <= k <= Qt.Key_9:
        return f"Numpad{k - Qt.Key_0}" if kp else str(k - Qt.Key_0)
    if Qt.Key_A <= k <= Qt.Key_Z:
        return chr(k)
    if Qt.Key_F1 <= k <= Qt.Key_F24:
        return f"F{k - Qt.Key_F1 + 1}"
    return _QT_FALLBACK.get(k)


def mods_from_event(e: QKeyEvent) -> frozenset[str]:
    m = e.modifiers()
    out = set()
    if m & Qt.ControlModifier:
        out.add("Ctrl")
    if m & Qt.AltModifier:
        out.add("Alt")
    if m & Qt.ShiftModifier:
        out.add("Shift")
    if m & Qt.MetaModifier:
        out.add("Win")
    return frozenset(out)


class KeyCaptureEdit(QLineEdit):
    """Campo que grava a próxima tecla (com modificadores) premida.

    Enquanto está em captura, o motor deixa passar todas as teclas
    (inclusive a tecla de suspensão) para que possam ser gravadas."""

    captured = Signal(str)

    def __init__(self, set_capture_mode: Callable[[bool], None], parent=None):
        super().__init__(parent)
        self.setObjectName("keycapture")
        self.setReadOnly(True)
        self.setPlaceholderText(tr("key.placeholder"))
        self._set_capture_mode = set_capture_mode
        self._binding = ""
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tr("key.tooltip"))

    def binding(self) -> str:
        return self._binding

    def set_binding(self, b: str) -> None:
        self._binding = b
        self.setText(b)

    def _capturing(self, on: bool) -> None:
        self.setProperty("capturing", on)
        self.style().unpolish(self)
        self.style().polish(self)
        self._set_capture_mode(on)
        self.setText(tr("key.press_now") if on else self._binding)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._capturing(True)

    def focusOutEvent(self, e):
        self._capturing(False)
        super().focusOutEvent(e)

    def event(self, e):
        # Tab/Shift+Tab também podem ser gravadas (não mudam de campo).
        if e.type() == QEvent.KeyPress and e.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            self.keyPressEvent(e)
            return True
        return super().event(e)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in _MOD_KEYS:
            mods = mods_from_event(e)
            self.setText("+".join(m for m in MODIFIERS if m in mods) + "+…")
            return
        name = key_name_from_event(e)
        if name is None:
            self.setText(tr("key.unsupported"))
            return
        b = str(Binding(name, mods_from_event(e)))
        self._binding = b
        self.clearFocus()          # termina a captura
        self.captured.emit(b)

    def keyReleaseEvent(self, e):
        pass
