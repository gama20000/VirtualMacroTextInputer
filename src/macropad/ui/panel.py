"""Painel flutuante opcional e a vista partilhada com a pré-visualização.

O painel não aceita foco: clicar num botão deixa a aplicação de destino em
primeiro plano e com o cursor, e o texto vai para lá. Não usa a moldura do
sistema: desenha a sua própria barra de título (cores do tema), que se
arrasta para mover o painel. A pré-visualização nas preferências usa a mesma
barra e a mesma ``PanelView``, por isso é igual à janela real."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import (QButtonGroup, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout,
                               QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from ..core.model import MacroSet, PanelSettings
from ..i18n import tr
from . import theme
from .widgets import TileButton

if TYPE_CHECKING:
    from .app import MacropadApp


def _contrast_text(bg: str) -> str:
    c = QColor(bg)
    lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
    return "#1b1b1f" if lum > 150 else "#e6e6e6"


def counter_key(set_id: str, counter_id: str) -> str:
    """Chave da contagem em ``estado.toml`` (por conjunto e contador)."""
    return f"{set_id}/{counter_id}"


class PanelTitleBar(QWidget):
    """Barra de título do painel (e da pré-visualização): logótipo, nome do
    conjunto, tecla para mostrar/ocultar o painel e botão de fechar.
    Arrastá-la move a janela (sem a ativar)."""

    close_clicked = Signal()
    moved = Signal()                       # fim de um arrasto

    HEIGHT = 28

    def __init__(self, interactive: bool = True, parent=None):
        super().__init__(parent)
        self.title = "Macropad"
        self.hint = ""
        self.caption, self.text = "#000000", "#ffffff"
        self.interactive = interactive
        self._drag: Optional[QPoint] = None
        self._hover_close = False
        self.setFixedHeight(self.HEIGHT)
        self.setMouseTracking(True)

    def _close_rect(self) -> QRectF:
        return QRectF(self.width() - 32, 0, 32, self.height())

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(self.caption))
        p.drawPixmap(8, (self.height() - 16) // 2, theme.logo_pixmap(16))
        f = p.font()
        f.setPointSizeF(9)
        p.setFont(f)
        fm = QFontMetrics(f)
        close = self._close_rect()
        right = close.left() - 4
        hint_w = 0
        if self.hint:
            hint_w = min(fm.horizontalAdvance(self.hint) + 12, max(0, int(right - 90)))
            if hint_w > 24:
                c = QColor(self.text)
                c.setAlpha(150)
                p.setPen(c)
                p.drawText(QRectF(right - hint_w, 0, hint_w, self.height()),
                           Qt.AlignVCenter | Qt.AlignRight,
                           fm.elidedText(self.hint, Qt.ElideRight, hint_w))
            else:
                hint_w = 0
        p.setPen(QColor(self.text))
        avail = int(right - hint_w - 30 - 4)
        p.drawText(QRectF(30, 0, max(0, avail), self.height()), Qt.AlignVCenter | Qt.AlignLeft,
                   fm.elidedText(self.title, Qt.ElideRight, max(0, avail)))
        xc = QColor(self.text)
        if self._hover_close:
            p.fillRect(close, QColor("#c42b1c"))
            xc = QColor("#ffffff")
        # cruz desenhada (não depende de o tipo de letra ter o símbolo)
        p.setPen(QPen(xc, 1.4))
        c = close.center()
        d = 4.5
        p.drawLine(QPointF(c.x() - d, c.y() - d), QPointF(c.x() + d, c.y() + d))
        p.drawLine(QPointF(c.x() - d, c.y() + d), QPointF(c.x() + d, c.y() - d))
        p.end()

    # ---------------------------------------------------------------- rato
    def mousePressEvent(self, e):
        if not self.interactive or e.button() != Qt.LeftButton:
            return
        if self._close_rect().contains(e.position()):
            return
        self._drag = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
        e.accept()

    def mouseMoveEvent(self, e):
        if not self.interactive:
            return
        over = self._close_rect().contains(e.position())
        if over != self._hover_close:
            self._hover_close = over
            self.update()
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._drag)
            e.accept()

    def mouseReleaseEvent(self, e):
        if not self.interactive or e.button() != Qt.LeftButton:
            return
        if self._drag is not None:
            self._drag = None
            self.moved.emit()
        elif self._close_rect().contains(e.position()):
            self.close_clicked.emit()

    def leaveEvent(self, e):
        if self._hover_close:
            self._hover_close = False
            self.update()
        super().leaveEvent(e)


class PanelView(QWidget):
    """Barra de estado + grelha de botões, com o estilo configurado.

    Os espaços vazios ocupam a sua célula mas não se veem nem fazem nada."""

    clicked = Signal(int)                 # índice real da macro
    counter_pressed = Signal(int, bool)   # índice real, pressão longa?
    suspend_requested = Signal(bool)      # True = suspender, False = ativar

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panelview")
        self.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 8, 10, 10)
        v.setSpacing(6)
        self.header = QWidget(objectName="panelhead")
        head = QHBoxLayout(self.header)
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(6)
        self.dot = QLabel("●")
        self.label = QLabel()
        self.label.setObjectName("status")
        head.addWidget(self.dot)
        head.addWidget(self.label, 1)
        # Ativo / Suspenso — mesmo estado e comportamento da configuração.
        # NoFocus: clicar não tira o foco à aplicação de destino.
        self.btn_on = QPushButton("● " + tr("state.active"), objectName="stateOn")
        self.btn_off = QPushButton(theme.PAUSE + " " + tr("state.suspended"), objectName="stateOff")
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        for b in (self.btn_on, self.btn_off):
            b.setCheckable(True)
            b.setFocusPolicy(Qt.NoFocus)
            b.setCursor(Qt.PointingHandCursor)
            grp.addButton(b)
            head.addWidget(b)
        self.btn_on.setChecked(True)
        self.btn_on.clicked.connect(lambda: self.suspend_requested.emit(False))
        self.btn_off.clicked.connect(lambda: self.suspend_requested.emit(True))
        v.addWidget(self.header)
        self.grid_host = QWidget(objectName="panelgrid")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.grid_host)
        v.addStretch(0)
        self.buttons: list[TileButton] = []
        self.indices: list[int] = []
        self.spacers: list[QWidget] = []
        self.counter_buttons: dict[str, TileButton] = {}     # id do contador -> botão
        self.pal = theme.DAY
        self.style_ = PanelSettings()

    def rebuild(self, style: PanelSettings, pal: theme.Palette, ms: Optional[MacroSet],
                counts: Optional[dict[str, int]] = None) -> None:
        """``counts``: contagem atual de cada contador (id -> valor)."""
        self.style_, self.pal = style, pal
        counts = counts or {}
        for w in self.buttons + self.spacers:
            w.setParent(None)
            w.deleteLater()
        self.buttons, self.indices, self.spacers = [], [], []
        self.counter_buttons = {}
        bg = style.cor_fundo or pal.panel_bg
        fg = _contrast_text(bg)
        muted = "#6b6b73" if fg.startswith("#1") else "#8a8a8a"
        # Fundo só nos contentores (a folha de estilo do próprio widget tem
        # prioridade sobre a da aplicação, por isso não se usa "QWidget").
        self.setStyleSheet(
            f"#panelview, #panelhead, #panelgrid {{ background: {bg}; }}"
            f"#panelview QLabel {{ background: transparent; }}"
            f"#panelview QLabel#status {{ color: {fg}; font-size: 9pt; }}"
            + theme.state_button_css(pal, fg, muted, small=True))
        self.dot.setVisible(style.mostrar_estado)
        self.label.setVisible(style.mostrar_estado)
        self.btn_on.setVisible(style.mostrar_controlos)
        self.btn_off.setVisible(style.mostrar_controlos)
        self.header.setVisible(style.mostrar_estado or style.mostrar_controlos)
        self.grid.setSpacing(style.espacamento)
        cols = style.colunas
        if ms is not None:
            for pos, i in enumerate(ms.active_indices()):
                m = ms.macros[i]
                r, c = pos // cols, pos % cols
                if m.is_space:
                    sp = QWidget()
                    sp.setFixedSize(style.tamanho_botao, style.tamanho_botao)
                    sp.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                    sp.setStyleSheet("background: transparent;")
                    self.grid.addWidget(sp, r, c)
                    sp.show()
                    self.spacers.append(sp)
                    continue
                if m.is_counter:
                    b = TileButton(m.display_title(), m.tecla, style, pal,
                                   count=counts.get(m.id, m.reposicao),
                                   long_ms=m.pressao_longa_ms)
                    b.short_clicked.connect(lambda idx=i: self.counter_pressed.emit(idx, False))
                    b.long_pressed.connect(lambda idx=i: self.counter_pressed.emit(idx, True))
                    self.counter_buttons[m.id] = b
                else:
                    b = TileButton(m.display_title(), m.tecla, style, pal)
                    b.clicked.connect(lambda _=False, idx=i: self.clicked.emit(idx))
                self.grid.addWidget(b, r, c)
                b.show()      # senão o tamanho é calculado sem os botões novos
                self.buttons.append(b)
                self.indices.append(i)
        self.grid_host.adjustSize()
        self.adjustSize()

    def set_count(self, counter_id: str, value: int) -> None:
        b = self.counter_buttons.get(counter_id)
        if b is not None and b.count != value:
            b.count = value
            b.update()

    def set_status(self, code: str, text: str, running_index: Optional[int] = None,
                   suspended: Optional[bool] = None,
                   counters_ok: Optional[bool] = None) -> None:
        if suspended is None:
            suspended = code == "suspenso"
        self.btn_on.setChecked(not suspended)
        self.btn_off.setChecked(suspended)
        colors = {"ativo": self.pal.ok, "suspenso": self.pal.error, "fora": self.pal.warn,
                  "executar": self.pal.accent}
        self.dot.setStyleSheet(f"color:{colors.get(code, '#888')}; background: transparent;")
        self.label.setText(text)
        enabled = code in ("ativo", "executar")
        if counters_ok is None:
            counters_ok = not suspended
        for b, i in zip(self.buttons, self.indices):
            # contadores: respeitam a suspensão e o âmbito, mas funcionam com uma
            # janela do Macropad à frente (não escrevem nada)
            b.setEnabled(counters_ok if b.count is not None else enabled)
            r = running_index is not None and running_index == i
            if b.running != r:
                b.running = r
                b.update()


def panel_hint(app_settings) -> str:
    key = getattr(app_settings, "tecla_painel", "")
    return tr("panel.key_hint", key=key) if key else ""


class PanelWindow(QWidget):
    def __init__(self, app: "MacropadApp"):
        super().__init__(None)
        self.app = app
        self._on_top: Optional[bool] = None
        self.setObjectName("panelwindow")
        self.setWindowIcon(theme.app_icon())
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(1, 1, 1, 1)
        lay.setSpacing(0)
        self.titlebar = PanelTitleBar(interactive=True)
        self.titlebar.close_clicked.connect(lambda: self.app.set_panel_visible(False))
        self.titlebar.moved.connect(self._moved)
        self.view = PanelView()
        self.view.clicked.connect(self._clicked)
        self.view.counter_pressed.connect(self._counter)
        self.view.suspend_requested.connect(self.app.engine.set_suspended)
        lay.addWidget(self.titlebar)
        lay.addWidget(self.view)
        # Indicação breve da transparência (roda do rato)
        self.osd = QLabel(self)
        self.osd.setAlignment(Qt.AlignCenter)
        self.osd.setStyleSheet("background: rgba(0,0,0,190); color: white; border-radius: 8px;"
                               "padding: 6px 12px; font-weight: 600;")
        self.osd.hide()
        self._osd_timer = QTimer(self, singleShot=True, interval=900, timeout=self.osd.hide)
        self._wheel_acc = 0
        self.setToolTip(tr("panel.wheel_tip"))
        self._placed = False
        self._apply_flags(True)
        self._timer = QTimer(self, interval=350, timeout=self.refresh_status)
        self._timer.start()
        self.rebuild()

    # O painel nunca é ativado (WS_EX_NOACTIVATE + MA_NOACTIVATE no Windows).
    def _apply_flags(self, on_top: bool) -> None:
        if on_top == self._on_top:
            return
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
        if on_top:
            flags |= Qt.WindowStaysOnTopHint
        self._on_top = on_top
        visible = self.isVisible()
        pos = self.pos()
        self.setWindowFlags(flags)
        if visible:
            self.move(pos)
            self.show()

    def showEvent(self, e):
        if not self._placed:
            self._placed = True
            self._restore_position()
        super().showEvent(e)
        self.app.platform.make_window_noactivate(int(self.winId()))
        self.app.style_window(self)

    def _restore_position(self) -> None:
        st = self.app.state
        if st.painel_x is None or st.painel_y is None:
            scr = QGuiApplication.primaryScreen()
            if scr is not None:
                g = scr.availableGeometry()
                self.adjustSize()
                self.move(g.right() - self.width() - 24, g.bottom() - self.height() - 24)
            return
        p = QPoint(st.painel_x, st.painel_y)
        # só repõe se o canto (com alguma margem) estiver num ecrã ligado
        probe = p + QPoint(20, 10)
        if any(s.availableGeometry().contains(probe) for s in QGuiApplication.screens()):
            self.move(p)

    def _moved(self) -> None:
        self.app.save_panel_position(self.x(), self.y())

    def nativeEvent(self, event_type, message):
        r = self.app.platform.native_event_noactivate(event_type, message)
        if r is not None:
            return True, r
        return super().nativeEvent(event_type, message)

    def apply_settings(self, s: PanelSettings) -> None:
        self._apply_flags(s.sempre_por_cima)
        self.setWindowOpacity(s.opacidade)

    # Roda do rato sobre o painel: rodar para cima = mais opaco; para baixo =
    # mais transparente. Passos de 5 %, entre 20 % e 100 %. Só afeta o painel.
    STEP = 0.05

    def wheelEvent(self, e):
        self._wheel_acc += e.angleDelta().y()
        steps = int(self._wheel_acc / 120)
        if steps == 0:
            e.accept()
            return
        self._wheel_acc -= steps * 120
        cur = round(self.windowOpacity(), 2)
        new = min(1.0, max(0.2, round(cur + steps * self.STEP, 2)))
        if new != cur:
            self.setWindowOpacity(new)
            self.app.set_panel_opacity(new)
        self._show_osd(tr("panel.opacity_osd", pct=round(new * 100)))
        e.accept()

    def _show_osd(self, text: str) -> None:
        self.osd.setText(text)
        self.osd.adjustSize()
        self.osd.move((self.width() - self.osd.width()) // 2,
                      (self.height() - self.osd.height()) // 2)
        self.osd.raise_()
        self.osd.show()
        self._osd_timer.start()

    def paintEvent(self, _e):
        # contorno de 1 px (a janela não tem moldura do sistema)
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(self.app.pal.border))
        p.end()

    def rebuild(self, style: Optional[PanelSettings] = None) -> None:
        style = style or self.app.engine.settings.painel
        ms = self.app.engine.active_set
        self.setWindowTitle(f"Macropad — {ms.nome}" if ms else "Macropad")
        self.titlebar.title = ms.nome if ms else "Macropad"
        self.titlebar.hint = panel_hint(self.app.engine.settings)
        self.titlebar.setToolTip(self.titlebar.hint)
        self.titlebar.caption, self.titlebar.text = self.app.pal.caption, self.app.pal.caption_text
        self.titlebar.update()
        self.view.rebuild(style, self.app.pal, ms, self.app.counts_for(ms))
        self.apply_settings(style)
        self.adjustSize()
        self.refresh_status()

    def set_count(self, counter_id: str, value: int) -> None:
        self.view.set_count(counter_id, value)

    def _clicked(self, idx: int) -> None:
        ok, why = self.app.engine.trigger(idx, "painel")
        if not ok:
            self.view.label.setText(why[0].upper() + why[1:])

    def _counter(self, idx: int, long_press: bool) -> None:
        ok, why = self.app.engine.counter_press(idx, long_press)
        if not ok:
            self.view.label.setText(why[0].upper() + why[1:])

    def refresh_status(self) -> None:
        if not self.isVisible():
            return
        code, text = self.app.engine.status()
        ms = self.app.engine.active_set
        if ms is not None and code in ("ativo", "fora"):
            text = f"{text} · {ms.nome}"
        run = self.app.engine.running
        self.view.set_status(code, text, run.index if run is not None else None,
                             self.app.engine.suspended, self.app.engine.counter_allowed()[0])

    def closeEvent(self, e):
        e.ignore()
        self.app.set_panel_visible(False)


# --------------------------------------------------------------- pré-visualização
class _Checker(QWidget):
    """Fundo em xadrez, para se perceber a transparência do painel."""

    def paintEvent(self, _e):
        p = QPainter(self)
        s = 10
        c1, c2 = QColor("#cfcfd4"), QColor("#b4b4ba")
        for y in range(0, self.height(), s):
            for x in range(0, self.width(), s):
                p.fillRect(x, y, s, s, c1 if (x // s + y // s) % 2 == 0 else c2)
        p.end()


class PanelPreview(QWidget):
    """Pré-visualização do painel: mesma barra, vista, estilo e cores da janela
    real. Não executa macros (só mostra)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.backdrop = _Checker(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.backdrop)
        bl = QVBoxLayout(self.backdrop)
        bl.setContentsMargins(16, 16, 16, 16)
        self.window_frame = QWidget()
        self.window_frame.setObjectName("previewframe")
        wl = QVBoxLayout(self.window_frame)
        wl.setContentsMargins(1, 1, 1, 1)
        wl.setSpacing(0)
        self.titlebar = PanelTitleBar(interactive=False)
        self.view = PanelView()
        self.view.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        wl.addWidget(self.titlebar)
        wl.addWidget(self.view)
        bl.addWidget(self.window_frame, 0, Qt.AlignCenter)
        self.effect = QGraphicsOpacityEffect(self.window_frame)
        self.window_frame.setGraphicsEffect(self.effect)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def update_preview(self, style: PanelSettings, pal: theme.Palette, ms: Optional[MacroSet],
                       status: tuple, hint: str = "",
                       counts: Optional[dict[str, int]] = None) -> None:
        self.window_frame.setStyleSheet(f"#previewframe {{ background: {pal.border}; }}")
        self.titlebar.caption, self.titlebar.text = pal.caption, pal.caption_text
        self.titlebar.title = ms.nome if ms else "Macropad"
        self.titlebar.hint = hint
        self.titlebar.update()
        self.view.rebuild(style, pal, ms, counts)
        self.view.set_status(*status)
        self.effect.setOpacity(style.opacidade)
        self.view.grid.activate()
        self.view.layout().activate()
        self.view.adjustSize()
        w = max(self.view.sizeHint().width(), 220)
        self.window_frame.setFixedWidth(w + 2)
        self.window_frame.setFixedHeight(self.view.sizeHint().height() + PanelTitleBar.HEIGHT + 2)
        self.backdrop.setMinimumHeight(self.window_frame.height() + 32)
        self.backdrop.setMinimumWidth(self.window_frame.width() + 32)
        self.updateGeometry()

    def sizeHint(self):
        return QSize(self.backdrop.minimumWidth(), self.backdrop.minimumHeight())
