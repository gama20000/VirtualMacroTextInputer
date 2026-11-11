"""Widgets partilhados: botão-tile, grelha reordenável e captura de tecla."""
from __future__ import annotations

import sys
from typing import Callable, Optional

from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QKeyEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QLineEdit, QListWidget,
                               QListWidgetItem, QStyle, QStyledItemDelegate)

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

DEFAULT_STYLE = PanelSettings()


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(round(a.red() + (b.red() - a.red()) * t),
                  round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t))


# --------------------------------------------------------------------- tile
def paint_tile(p: QPainter, rect: QRect, title: str, key: str, style: PanelSettings,
               pal: theme.Palette, *, selected=False, error=False, dup=False, hover=False,
               pressed=False, dim=False, running=False) -> None:
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    side = min(rect.width(), rect.height())
    r = QRectF(rect.x() + (rect.width() - side) / 2 + 3, rect.y() + (rect.height() - side) / 2 + 3,
               side - 6, side - 6)
    bg = QColor(style.cor_botao)
    fg = QColor(style.cor_texto)
    radius = r.width() * style.arredondamento / 100.0
    path = QPainterPath()
    path.addRoundedRect(r, radius, radius)
    p.fillPath(path, _mix(bg, fg, 0.12) if pressed else (_mix(bg, fg, 0.05) if hover else bg))

    if error:
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
    key_h = fmk.height() + 2 if style.mostrar_tecla else 0

    f = QFont(p.font())
    f.setBold(True)
    f.setPointSizeF(max(6.5, r.height() / 9.5 * scale))
    p.setFont(f)
    fm = QFontMetrics(f)
    p.setPen(fg)
    if style.mostrar_icone:
        t = fm.elidedText(title, Qt.ElideRight, int(inner.width()))
        p.drawText(QRectF(inner.left(), inner.top(), inner.width(), fm.height()),
                   Qt.AlignHCenter | Qt.AlignTop, t)
        # ícone "[T]" ao centro, como no Stream Deck
        c = QPointF(r.center().x(), r.center().y() + r.height() * 0.04)
        s = r.width() * 0.17
        p.setPen(QPen(fg, max(1.5, r.width() / 45)))
        L = s * 0.35
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x, y = c.x() + dx * s, c.y() + dy * s
            p.drawLine(QPointF(x, y), QPointF(x - dx * L, y))
            p.drawLine(QPointF(x, y), QPointF(x, y - dy * L))
        ft = QFont(p.font())
        ft.setBold(False)
        ft.setPointSizeF(max(5.0, s * 0.95))
        p.setFont(ft)
        p.drawText(QRectF(c.x() - s, c.y() - s, 2 * s, 2 * s), Qt.AlignCenter, "T")
    else:
        area = QRectF(inner.left(), inner.top(), inner.width(), inner.height() - key_h)
        lines = max(1, int(area.height() // fm.lineSpacing()))
        txt = title
        bound = fm.boundingRect(area.toRect(), Qt.AlignCenter | Qt.TextWordWrap, txt)
        if bound.height() > area.height() or bound.width() > area.width():
            txt = fm.elidedText(title, Qt.ElideRight, int(area.width() * lines * 0.92))
        p.drawText(area, Qt.AlignCenter | Qt.TextWordWrap, txt)

    if style.mostrar_tecla:
        p.setFont(fk)
        label = key or "—"
        w = min(fmk.horizontalAdvance(label) + 12, inner.width())
        pill = QRectF(r.center().x() - w / 2, inner.bottom() - fmk.height() - 1, w, fmk.height() + 2)
        pp = QPainterPath()
        pp.addRoundedRect(pill, pill.height() / 2, pill.height() / 2)
        p.fillPath(pp, _mix(bg, fg, 0.22 if key else 0.1))
        p.setPen(_mix(bg, fg, 0.85 if key else 0.45))
        p.drawText(pill, Qt.AlignCenter, fmk.elidedText(label, Qt.ElideRight, int(w - 6)))

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
    """Botão do painel. Nunca recebe foco (o foco fica na aplicação de destino)."""

    def __init__(self, title: str, key: str, style: PanelSettings, pal: theme.Palette,
                 parent=None):
        super().__init__(parent)
        self.title, self.key = title, key
        self.tile_style, self.pal = style, pal
        self.running = False
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(style.tamanho_botao, style.tamanho_botao)
        self.setToolTip(tr("tile.tooltip", title=title, key=key or tr("tile.no_key")))
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        paint_tile(p, self.rect(), self.title, self.key, self.tile_style, self.pal,
                   hover=self.underMouse(), pressed=self.isDown(), dim=not self.isEnabled(),
                   running=self.running)
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
        r = option.rect
        side = min(r.width(), r.height(), self.grid.TILE)
        box = QRect(r.center().x() - side // 2, r.center().y() - side // 2, side, side)
        paint_tile(p, box, index.data(TITLE_ROLE) or "", index.data(KEY_ROLE) or "",
                   DEFAULT_STYLE, self.grid.pal,
                   selected=bool(option.state & QStyle.State_Selected),
                   error=bool(index.data(ERROR_ROLE)), dup=bool(index.data(DUP_ROLE)),
                   hover=bool(option.state & QStyle.State_MouseOver),
                   dim=self.grid.archived)

    def sizeHint(self, option, index):
        return QSize(self.grid.TILE + 8, self.grid.TILE + 8)


class MacroGrid(QListWidget):
    """Grelha de macros com reordenação por arrastar e largar.

    ``INDEX_ROLE`` guarda o índice real em ``MacroSet.macros``. A posição na
    grelha é independente da tecla atribuída."""

    reordered = Signal(list)          # nova ordem: lista de índices reais

    TILE = 92

    def __init__(self, pal: theme.Palette, archived: bool = False, parent=None):
        super().__init__(parent)
        self.pal = pal
        self.archived = archived
        self.setObjectName("grid")
        self.setViewMode(QListWidget.ListMode)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.Adjust)
        self.setUniformItemSizes(True)
        self.setGridSize(QSize(self.TILE + 12, self.TILE + 12))
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setMouseTracking(True)
        self.setItemDelegate(_TileDelegate(self))
        self.setFrameShape(QListWidget.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def set_tiles(self, tiles: list[dict], selected_real: int) -> None:
        """tiles: dicts com index, title, key, error, dup, tip."""
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
            it.setToolTip(t["tip"])
            it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
            self.addItem(it)
            if t["index"] == selected_real:
                sel_row = self.count() - 1
        if sel_row >= 0:
            self.setCurrentRow(sel_row)
        else:
            self.clearSelection()
            self.setCurrentRow(-1)
        self.blockSignals(False)
        self.fit_height()

    def real_index(self, row: int) -> int:
        it = self.item(row)
        return it.data(INDEX_ROLE) if it else -1

    def fit_height(self) -> None:
        """Altura suficiente para todas as linhas (sem barra de deslocamento)."""
        cols = max(1, (self.viewport().width() or self.width()) // self.gridSize().width())
        rows = max(1, -(-self.count() // cols))
        self.setFixedHeight(rows * self.gridSize().height() + 6)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        QTimer.singleShot(0, self.fit_height)

    def dropEvent(self, e):
        super().dropEvent(e)
        QTimer.singleShot(0, self._emit_order)

    def _emit_order(self) -> None:
        order = [self.item(i).data(INDEX_ROLE) for i in range(self.count())]
        if order != sorted(order):
            self.reordered.emit(order)


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
