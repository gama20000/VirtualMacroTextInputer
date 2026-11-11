"""Painel flutuante opcional e a vista partilhada com a pré-visualização.

O painel não aceita foco: clicar num botão deixa a aplicação de destino em
primeiro plano e com o cursor, e o texto vai para lá. A pré-visualização nas
preferências usa exatamente a mesma ``PanelView``, por isso tem a mesma
disposição e aparência da janela real."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QRectF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel,
                               QSizePolicy, QVBoxLayout, QWidget)

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


class PanelView(QWidget):
    """Barra de estado + grelha de botões, com o estilo configurado."""

    clicked = Signal(int)                 # índice real da macro

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panelview")
        self.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 8, 10, 10)
        v.setSpacing(6)
        self.header = QWidget()
        head = QHBoxLayout(self.header)
        head.setContentsMargins(0, 0, 0, 0)
        self.dot = QLabel("●")
        self.label = QLabel()
        self.label.setObjectName("status")
        head.addWidget(self.dot)
        head.addWidget(self.label, 1)
        v.addWidget(self.header)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.grid_host)
        v.addStretch(0)
        self.buttons: list[TileButton] = []
        self.indices: list[int] = []
        self.pal = theme.DAY
        self.style_ = PanelSettings()

    def rebuild(self, style: PanelSettings, pal: theme.Palette, ms: Optional[MacroSet]) -> None:
        self.style_, self.pal = style, pal
        for b in self.buttons:
            b.setParent(None)
            b.deleteLater()
        self.buttons, self.indices = [], []
        bg = style.cor_fundo or pal.panel_bg
        fg = _contrast_text(bg)
        self.setStyleSheet(
            f"#panelview, #panelview QWidget {{ background: {bg}; }}"
            f"#panelview QLabel#status {{ color: {fg}; font-size: 9pt; }}")
        self.header.setVisible(style.mostrar_estado)
        self.grid.setSpacing(style.espacamento)
        cols = style.colunas
        if ms is not None:
            for pos, i in enumerate(ms.active_indices()):
                m = ms.macros[i]
                b = TileButton(m.display_title(), m.tecla, style, pal)
                b.clicked.connect(lambda _=False, idx=i: self.clicked.emit(idx))
                self.grid.addWidget(b, pos // cols, pos % cols)
                b.show()      # senão o tamanho é calculado sem os botões novos
                self.buttons.append(b)
                self.indices.append(i)
        self.grid_host.adjustSize()
        self.adjustSize()

    def set_status(self, code: str, text: str, running_index: Optional[int] = None) -> None:
        colors = {"ativo": self.pal.ok, "suspenso": self.pal.error, "fora": self.pal.warn,
                  "executar": self.pal.accent}
        self.dot.setStyleSheet(f"color:{colors.get(code, '#888')}; background: transparent;")
        self.label.setText(text)
        enabled = code in ("ativo", "executar")
        for b, i in zip(self.buttons, self.indices):
            b.setEnabled(enabled)
            r = running_index is not None and running_index == i
            if b.running != r:
                b.running = r
                b.update()


class PanelWindow(QWidget):
    def __init__(self, app: "MacropadApp"):
        super().__init__(None)
        self.app = app
        self._on_top: Optional[bool] = None
        self.setWindowIcon(theme.app_icon())
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.view = PanelView()
        self.view.clicked.connect(self._clicked)
        lay.addWidget(self.view)
        self._apply_flags(True)
        self._timer = QTimer(self, interval=350, timeout=self.refresh_status)
        self._timer.start()
        self.rebuild()

    # O painel nunca é ativado (WS_EX_NOACTIVATE + MA_NOACTIVATE no Windows).
    def _apply_flags(self, on_top: bool) -> None:
        if on_top == self._on_top:
            return
        flags = Qt.Tool | Qt.WindowDoesNotAcceptFocus | Qt.WindowCloseButtonHint
        if on_top:
            flags |= Qt.WindowStaysOnTopHint
        self._on_top = on_top
        visible = self.isVisible()
        self.setWindowFlags(flags)
        if visible:
            self.show()

    def showEvent(self, e):
        super().showEvent(e)
        self.app.platform.make_window_noactivate(int(self.winId()))
        self.app.style_window(self)

    def nativeEvent(self, event_type, message):
        r = self.app.platform.native_event_noactivate(event_type, message)
        if r is not None:
            return True, r
        return super().nativeEvent(event_type, message)

    def apply_settings(self, s: PanelSettings) -> None:
        self._apply_flags(s.sempre_por_cima)
        self.setWindowOpacity(s.opacidade)

    def rebuild(self, style: Optional[PanelSettings] = None) -> None:
        style = style or self.app.engine.settings.painel
        ms = self.app.engine.active_set
        self.setWindowTitle(f"Macropad — {ms.nome}" if ms else "Macropad")
        self.view.rebuild(style, self.app.pal, ms)
        self.apply_settings(style)
        self.adjustSize()
        self.refresh_status()

    def _clicked(self, idx: int) -> None:
        ok, why = self.app.engine.trigger(idx, "painel")
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
        self.view.set_status(code, text, run.index if run is not None else None)

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


class _FakeTitleBar(QWidget):
    """Imitação da barra de título da janela do painel (cores do tema)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = "Macropad"
        self.caption, self.text = "#000000", "#ffffff"
        self.setFixedHeight(28)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(self.caption))
        p.drawPixmap(8, 6, theme.logo_pixmap(16))
        p.setPen(QColor(self.text))
        f = p.font()
        f.setPointSizeF(9)
        p.setFont(f)
        p.drawText(QRectF(30, 0, self.width() - 70, self.height()),
                   Qt.AlignVCenter | Qt.AlignLeft,
                   p.fontMetrics().elidedText(self.title, Qt.ElideRight, self.width() - 70))
        p.drawText(QRectF(self.width() - 34, 0, 26, self.height()), Qt.AlignCenter, "✕")
        p.end()


class PanelPreview(QWidget):
    """Pré-visualização do painel: mesma vista, estilo e cores da janela real.
    Não executa macros (só mostra)."""

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
        self.window_frame.setStyleSheet("#previewframe { border: 1px solid #555; }")
        wl = QVBoxLayout(self.window_frame)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        self.titlebar = _FakeTitleBar()
        self.view = PanelView()
        self.view.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        wl.addWidget(self.titlebar)
        wl.addWidget(self.view)
        bl.addWidget(self.window_frame, 0, Qt.AlignLeft | Qt.AlignTop)
        bl.addStretch(1)
        self.effect = QGraphicsOpacityEffect(self.window_frame)
        self.window_frame.setGraphicsEffect(self.effect)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def update_preview(self, style: PanelSettings, pal: theme.Palette, ms: Optional[MacroSet],
                       status: tuple[str, str]) -> None:
        self.titlebar.caption, self.titlebar.text = pal.caption, pal.caption_text
        self.titlebar.title = f"Macropad — {ms.nome}" if ms else "Macropad"
        self.titlebar.update()
        self.view.rebuild(style, pal, ms)
        self.view.set_status(*status)
        self.effect.setOpacity(style.opacidade)
        self.view.grid.activate()
        self.view.layout().activate()
        self.view.adjustSize()
        w = max(self.view.sizeHint().width(), 220)
        self.window_frame.setFixedWidth(w + 2)
        self.window_frame.setFixedHeight(self.view.sizeHint().height() + 30)
        self.backdrop.setMinimumHeight(self.window_frame.height() + 32)
        self.backdrop.setMinimumWidth(self.window_frame.width() + 32)
        self.updateGeometry()

    def sizeHint(self):
        return QSize(self.backdrop.minimumWidth(), self.backdrop.minimumHeight())
