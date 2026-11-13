"""Janela de configuração.

Separadores: Macros · Painel · Âmbito · Preferências.
As alterações válidas são gravadas automaticamente (de forma atómica) e
aplicadas a execuções futuras."""
from __future__ import annotations

import time

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QEvent, QMimeData, QObject, QTimer, Qt, QUrl
from PySide6.QtGui import QColor, QCursor, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QButtonGroup, QCheckBox,
                               QColorDialog, QComboBox, QFileDialog, QFormLayout, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMenu,
                               QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QSlider,
                               QSpinBox, QStackedWidget, QTabWidget, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget)

from ..core import macro_ops as ops
from ..core.commands import CommandError, describe_steps, parse_action
from ..core.configio import (ConfigError, Issue, macro_label, macros_from_clipboard,
                             macros_to_clipboard, validate_macros)
from ..core.keys import Binding, KeyBindingError, parse_binding
from ..core.model import (MAX_INTERVAL_MS, MAX_REPEAT, PANEL_PRESETS, PANEL_RANGES, POSITIONS,
                          MacroSet, PanelSettings, Settings, apply_preset, matching_preset)
from ..i18n import available as available_languages
from ..i18n import tr
from . import theme
from .dialogs import ask, get_text, info
from .panel import PanelPreview, panel_hint
from .widgets import (_MOD_KEYS, AreaDropZone, KeyCaptureEdit, MacroGrid, key_name_from_event,
                      mods_from_event)

if TYPE_CHECKING:
    from .app import MacropadApp

MIME_MACRO = "application/x-macropad-macro"


def _binding_or_none(text: str):
    if not text:
        return None
    try:
        return parse_binding(text)
    except KeyBindingError:
        return None


def _is_editable(w: Optional[QWidget]) -> bool:
    if w is None:
        return False
    if isinstance(w, (QLineEdit, QPlainTextEdit, QTextEdit, QAbstractSpinBox)):
        return True
    if isinstance(w, QComboBox) and w.isEditable():
        return True
    return False


class _ColorButton(QPushButton):
    def __init__(self, on_change, parent=None):
        super().__init__(parent)
        self._color = "#000000"
        self._on_change = on_change
        self.setFixedWidth(90)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick)

    def color(self) -> str:
        return self._color

    def set_color(self, c: str) -> None:
        self._color = c
        q = QColor(c)
        lum = 0.299 * q.red() + 0.587 * q.green() + 0.114 * q.blue()
        self.setText(c.upper())
        self.setStyleSheet(f"background:{c}; color:{'#000' if lum > 140 else '#fff'};")

    def _pick(self):
        c = QColorDialog.getColor(QColor(self._color), self, tr("panel.pick_color"))
        if c.isValid():
            self.set_color(c.name())
            self._on_change()


class ConfigWindow(QWidget):
    def __init__(self, app: "MacropadApp"):
        super().__init__()
        self.app = app
        self.setWindowTitle(tr("win.config_title"))
        self.setWindowIcon(theme.app_icon())
        self.resize(700, 860)
        self.ms: Optional[MacroSet] = None       # cópia de trabalho do conjunto ativo
        self.settings: Settings = app.store.settings.clone()
        self.cur = -1                            # índice real da macro atual (editor)
        self.selected: list[int] = []            # índices reais selecionados
        self._loading = False
        self._last_add = 0.0
        self._capture_field = False              # um campo de tecla está a gravar
        self._capture_hover = False              # o rato está sobre um botão (atribuir tecla)
        self._hover_real = -1
        self._hover_grid: Optional[MacroGrid] = None
        # tecla Qt -> (conjunto, id do contador, início)
        self._counter_keys: dict[int, tuple[str, str, float]] = {}
        self._dirty_set = False        # o conjunto em edição tem alterações por gravar
        self._dirty_settings = False   # as preferências têm alterações por gravar
        self._save_set_timer = QTimer(self, singleShot=True, interval=450,
                                      timeout=self._save_set_now)
        self._save_settings_timer = QTimer(self, singleShot=True, interval=450,
                                           timeout=self._save_settings_now)
        self._build()
        QApplication.instance().installEventFilter(self)
        self.reload_from_store()

    @property
    def pal(self) -> theme.Palette:
        return self.app.pal

    # ================================================================ layout
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top = QWidget(objectName="top")
        row = QHBoxLayout(top)
        row.setContentsMargins(16, 12, 16, 12)
        logo = QLabel()
        logo.setPixmap(theme.logo_pixmap(30))
        row.addWidget(logo)
        row.addWidget(QLabel("Macropad", objectName="h1"))
        row.addSpacing(10)
        self.set_combo = QComboBox()
        self.set_combo.setMinimumWidth(180)
        self.set_combo.setToolTip(tr("cfg.set_combo_tip"))
        self.set_combo.activated.connect(self._on_set_chosen)
        row.addWidget(self.set_combo)
        self.set_menu_btn = QToolButton(text="⋯")
        self.set_menu_btn.setToolTip(tr("cfg.manage_sets"))
        self.set_menu_btn.setPopupMode(QToolButton.InstantPopup)
        m = QMenu(self)
        m.addAction(tr("sets.new"), self._new_set)
        m.addAction(tr("sets.duplicate"), self._dup_set)
        m.addAction(tr("sets.rename"), self._rename_set)
        m.addAction(tr("sets.delete"), self._delete_set)
        m.addSeparator()
        m.addAction(tr("sets.import"), self._import_set)
        m.addAction(tr("sets.export"), self._export_set)
        m.addSeparator()
        m.addAction(tr("sets.open_folder"), self._open_folder)
        self.set_menu_btn.setMenu(m)
        row.addWidget(self.set_menu_btn)
        row.addStretch(1)

        # Estado: dois botões exclusivos, claramente clicáveis
        row.addWidget(QLabel(tr("state.label")))
        self.btn_on = QPushButton("●  " + tr("state.active"), objectName="stateOn")
        self.btn_off = QPushButton(theme.PAUSE + "  " + tr("state.suspended"), objectName="stateOff")
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        for b in (self.btn_on, self.btn_off):
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.StrongFocus)
            grp.addButton(b)
            row.addWidget(b)
        hk = self.app.store.settings.tecla_suspensao
        self.btn_on.setToolTip(tr("state.on_tip", hotkey=hk))
        self.btn_off.setToolTip(tr("state.off_tip", hotkey=hk))
        self.btn_on.clicked.connect(lambda: self.app.engine.set_suspended(False))
        self.btn_off.clicked.connect(lambda: self.app.engine.set_suspended(True))
        root.addWidget(top)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_macros_tab(), tr("tab.macros"))
        self.tabs.addTab(self._build_panel_tab(), tr("tab.panel"))
        self.tabs.addTab(self._build_scope_tab(), tr("tab.scope"))
        self.tabs.addTab(self._build_prefs_tab(), tr("tab.prefs"))
        root.addWidget(self.tabs, 1)

        self.status = QLabel(objectName="hint")
        self.status.setWordWrap(True)
        self.status.setContentsMargins(16, 6, 16, 8)
        self.status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.status)
        self._refresh_state_buttons()

    # ------------------------------------------------------------- Macros
    def _build_macros_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        well = QWidget(objectName="well")
        gl = QVBoxLayout(well)
        gl.setContentsMargins(14, 10, 14, 10)
        gl.setSpacing(8)

        # ----- área «Ativo»: mesmo aspeto do painel real (centrada)
        self.active_zone = AreaDropZone(self.pal, archived=False)
        self.active_zone.dropped.connect(lambda src, idxs: self._on_drop(False, src, idxs))
        al = QVBoxLayout(self.active_zone)
        al.setContentsMargins(8, 6, 8, 8)
        al.setSpacing(8)
        hrow = QHBoxLayout()
        self.active_title = QLabel(objectName="section")
        hrow.addWidget(self.active_title)
        line = QFrame(objectName="divider")
        line.setFrameShape(QFrame.HLine)
        hrow.addWidget(line, 1)
        al.addLayout(hrow)
        self.active_box = QFrame(objectName="activebox")
        bl = QHBoxLayout(self.active_box)
        bl.setContentsMargins(10, 10, 10, 10)
        self.grid = MacroGrid(self.pal)
        self.grid.itemSelectionChanged.connect(lambda: self._on_selection(self.grid))
        self.grid.dropped.connect(lambda *a: self._on_drop(False, *a))
        self.grid.hover_changed.connect(lambda r: self._on_hover(self.grid, r))
        bl.addWidget(self.grid)
        self.empty_label = QLabel(tr("macros.empty"), objectName="hint")
        self.empty_label.setAlignment(Qt.AlignCenter)
        bl.addWidget(self.empty_label)
        crow = QHBoxLayout()
        crow.addStretch(1)
        crow.addWidget(self.active_box)
        crow.addStretch(1)
        al.addLayout(crow)

        brow = QHBoxLayout()
        self.add_btn = QPushButton("＋  " + tr("macros.new"))
        self.add_btn.clicked.connect(lambda: self._add_item("texto"))
        self.add_counter_btn = QPushButton("＋  " + tr("macros.new_counter"))
        self.add_counter_btn.setToolTip(tr("macros.new_counter_tip"))
        self.add_counter_btn.clicked.connect(lambda: self._add_item("contador"))
        self.add_space_btn = QPushButton("＋  " + tr("macros.new_space"))
        self.add_space_btn.setToolTip(tr("macros.new_space_tip"))
        self.add_space_btn.clicked.connect(lambda: self._add_item("espaco"))
        for b in (self.add_btn, self.add_counter_btn, self.add_space_btn):
            brow.addWidget(b)
        brow.addStretch(1)
        al.addLayout(brow)
        hint = QLabel(tr("macros.drag_hint"), objectName="hint", wordWrap=True)
        al.addWidget(hint)
        gl.addWidget(self.active_zone)

        # ----- área «Arquivo» — também é zona para largar macros
        self.archive_zone = AreaDropZone(self.pal, archived=True)
        self.archive_zone.dropped.connect(lambda src, idxs: self._on_drop(True, src, idxs))
        zl = QVBoxLayout(self.archive_zone)
        zl.setContentsMargins(8, 6, 8, 8)
        zl.setSpacing(6)
        arow = QHBoxLayout()
        self.archive_title = QLabel(objectName="section")
        arow.addWidget(self.archive_title)
        line = QFrame(objectName="divider")
        line.setFrameShape(QFrame.HLine)
        arow.addWidget(line, 1)
        self.archive_search = QLineEdit()
        self.archive_search.setPlaceholderText(tr("archive.search"))
        self.archive_search.setClearButtonEnabled(True)
        self.archive_search.setMinimumWidth(280)
        self.archive_search.textChanged.connect(lambda _t: self._refresh_grid())
        arow.addWidget(self.archive_search)
        zl.addLayout(arow)
        self.archive_grid = MacroGrid(self.pal, archived=True)
        self.archive_grid.itemSelectionChanged.connect(lambda: self._on_selection(self.archive_grid))
        self.archive_grid.dropped.connect(lambda *a: self._on_drop(True, *a))
        self.archive_grid.hover_changed.connect(lambda r: self._on_hover(self.archive_grid, r))
        zl.addWidget(self.archive_grid)
        self.archive_empty = QLabel(objectName="hint")
        self.archive_empty.setMinimumHeight(48)
        zl.addWidget(self.archive_empty)
        zl.addWidget(QLabel(tr("archive.drop_hint"), objectName="hint", wordWrap=True))
        gl.addSpacing(6)
        gl.addWidget(self.archive_zone)
        gl.addStretch(1)
        scroll.setWidget(well)
        v.addWidget(scroll, 5)

        ed = QWidget(objectName="editor")
        el = QVBoxLayout(ed)
        el.setContentsMargins(18, 12, 18, 8)
        hdr = QHBoxLayout()
        self.editor_title = QLabel()
        hdr.addWidget(self.editor_title)
        hdr.addStretch(1)
        self.left_btn = QToolButton(text="◀")
        self.left_btn.setToolTip(tr("macros.move_left"))
        self.left_btn.clicked.connect(lambda: self._move(-1))
        self.right_btn = QToolButton(text="▶")
        self.right_btn.setToolTip(tr("macros.move_right"))
        self.right_btn.clicked.connect(lambda: self._move(1))
        self.archive_btn = QPushButton()
        self.archive_btn.clicked.connect(self._toggle_archive)
        self.del_btn = QToolButton(text="🗑")
        self.del_btn.setToolTip(tr("macros.delete_tip"))
        self.del_btn.clicked.connect(self._delete_macro)
        for b in (self.left_btn, self.right_btn, self.archive_btn, self.del_btn):
            hdr.addWidget(b)
        el.addLayout(hdr)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        self.f_title = QLineEdit()
        self.f_title.setMaxLength(40)
        self.f_title.textEdited.connect(self._on_edit)
        form.addRow(tr("field.title"), self.f_title)

        krow = QHBoxLayout()
        self.f_key = KeyCaptureEdit(self._set_capture_mode)
        self.f_key.captured.connect(self._on_key_captured)
        krow.addWidget(self.f_key, 1)
        clear = QPushButton(tr("field.no_key"))
        clear.setToolTip(tr("field.no_key_tip"))
        clear.clicked.connect(lambda: self._on_key_captured(""))
        krow.addWidget(clear)
        self.no_key_btn = clear
        form.addRow(tr("field.key"), krow)

        el.addLayout(form)

        # páginas próprias de cada tipo de botão
        self.type_pages = QStackedWidget()
        page_text = QWidget()
        tf = QFormLayout(page_text)
        tf.setContentsMargins(0, 0, 0, 0)
        tf.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tf.setHorizontalSpacing(14)
        tf.setVerticalSpacing(8)
        self.f_text = QPlainTextEdit()
        self.f_text.setTabChangesFocus(True)
        self.f_text.setPlaceholderText(tr("field.text_placeholder"))
        self.f_text.setFixedHeight(80)
        self.f_text.textChanged.connect(self._on_edit)
        tf.addRow(tr("field.text"), self.f_text)
        self.f_preview = QLabel(objectName="hint")
        self.f_preview.setWordWrap(True)
        tf.addRow("", self.f_preview)

        rrow = QHBoxLayout()
        self.f_repeat = QSpinBox()
        self.f_repeat.setRange(1, MAX_REPEAT)
        self.f_repeat.valueChanged.connect(self._on_edit)
        rrow.addWidget(self.f_repeat)
        rrow.addSpacing(18)
        rrow.addWidget(QLabel(tr("field.interval")))
        self.f_interval = QSpinBox()
        self.f_interval.setRange(0, MAX_INTERVAL_MS)
        self.f_interval.setSingleStep(100)
        self.f_interval.setSuffix(" ms")
        self.f_interval.valueChanged.connect(self._on_edit)
        rrow.addWidget(self.f_interval)
        rrow.addStretch(1)
        tf.addRow(tr("field.repeats"), rrow)
        tf.addRow("", QLabel(tr("macros.commands_hint"), objectName="hint", wordWrap=True))
        self.type_pages.addWidget(page_text)

        page_counter = QWidget()
        cf = QFormLayout(page_counter)
        cf.setContentsMargins(0, 0, 0, 0)
        cf.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cf.setHorizontalSpacing(14)
        cf.setVerticalSpacing(8)
        self.f_step = QSpinBox()
        self.f_step.setRange(-1_000_000, 1_000_000)
        self.f_step.valueChanged.connect(self._on_edit)
        cf.addRow(tr("field.counter_step"), self.f_step)
        self.f_reset = QSpinBox()
        self.f_reset.setRange(-1_000_000_000, 1_000_000_000)
        self.f_reset.valueChanged.connect(self._on_edit)
        cf.addRow(tr("field.counter_reset"), self.f_reset)
        self.f_long = QSpinBox()
        self.f_long.setRange(200, 10_000)
        self.f_long.setSingleStep(100)
        self.f_long.setSuffix(" ms")
        self.f_long.valueChanged.connect(self._on_edit)
        cf.addRow(tr("field.counter_long"), self.f_long)
        cnow = QHBoxLayout()
        self.f_count = QLabel()
        cnow.addWidget(self.f_count)
        cnow.addSpacing(10)
        reset_now = QPushButton(tr("field.counter_reset_now"))
        reset_now.clicked.connect(self._reset_counter_now)
        cnow.addWidget(reset_now)
        cnow.addStretch(1)
        cf.addRow(tr("field.counter_value"), cnow)
        cf.addRow("", QLabel(tr("macros.counter_hint"), objectName="hint", wordWrap=True))
        self.type_pages.addWidget(page_counter)

        page_space = QWidget()
        sl = QVBoxLayout(page_space)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(QLabel(tr("macros.space_hint"), objectName="hint", wordWrap=True))
        sl.addStretch(1)
        self.type_pages.addWidget(page_space)
        self.type_pages.setObjectName("typepages")
        for k in range(self.type_pages.count()):
            self.type_pages.widget(k).setObjectName("typepage")
        self.type_pages.setStyleSheet(
            "QStackedWidget#typepages, QWidget#typepage { background: transparent; }")
        el.addWidget(self.type_pages)
        # rótulos alinhados entre o formulário comum e as páginas de cada tipo
        forms = [form, tf, cf]
        labels = [f.labelForField(f.itemAt(r, QFormLayout.FieldRole).widget()
                                  or f.itemAt(r, QFormLayout.FieldRole).layout())
                  for f in forms for r in range(f.rowCount())
                  if f.itemAt(r, QFormLayout.FieldRole) is not None]
        labels = [lb for lb in labels if isinstance(lb, QLabel)]
        width = max(lb.sizeHint().width() for lb in labels)
        for lb in labels:
            lb.setMinimumWidth(width)
            lb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.f_dup = QLabel(objectName="dupinfo")
        self.f_dup.setWordWrap(True)
        el.addWidget(self.f_dup)
        self.f_error = QLabel(objectName="error")
        self.f_error.setWordWrap(True)
        el.addWidget(self.f_error)
        el.addStretch(1)
        v.addWidget(ed, 4)
        self.editor = ed
        return w

    # ----------------------------------------------- Preferências do painel
    def _build_panel_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        v = QVBoxLayout(body)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(10)

        v.addWidget(QLabel(tr("panel.preview"), objectName="section"))
        self.preview = PanelPreview()
        pscroll = QScrollArea()
        pscroll.setWidgetResizable(True)
        pscroll.setFrameShape(QFrame.NoFrame)
        pscroll.setMaximumHeight(340)
        pscroll.setWidget(self.preview)
        self.preview_scroll = pscroll
        v.addWidget(pscroll)

        srow = QHBoxLayout()
        srow.addWidget(QLabel(tr("panel.style")))
        self.p_preset = QComboBox()
        for key in PANEL_PRESETS:
            self.p_preset.addItem(tr(f"preset.{key}"), key)
        self.p_preset.addItem(tr("preset.custom"), "")
        self.p_preset.activated.connect(self._on_preset)
        srow.addWidget(self.p_preset, 1)
        reset = QPushButton(tr("panel.reset"))
        reset.setToolTip(tr("panel.reset_tip"))
        reset.clicked.connect(lambda: self._apply_preset("predefinido"))
        srow.addWidget(reset)
        v.addLayout(srow)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        self.p_spins: dict[str, QSpinBox] = {}
        spec = [("colunas", "panel.columns", ""), ("tamanho_botao", "panel.size", " px"),
                ("espacamento", "panel.spacing", " px"), ("arredondamento", "panel.radius", " %"),
                ("borda", "panel.border", " px"), ("escala_texto", "panel.text_scale", " %")]
        for n, (name, label, suffix) in enumerate(spec):
            sb = QSpinBox()
            lo, hi = PANEL_RANGES[name]
            sb.setRange(int(lo), int(hi))
            sb.setSuffix(suffix)
            sb.valueChanged.connect(self._on_panel_edit)
            self.p_spins[name] = sb
            grid.addWidget(QLabel(tr(label)), n // 2, (n % 2) * 2, Qt.AlignRight)
            grid.addWidget(sb, n // 2, (n % 2) * 2 + 1)
        v.addLayout(grid)

        crow = QGridLayout()
        crow.setHorizontalSpacing(14)
        self.p_colors: dict[str, _ColorButton] = {}
        for n, (name, label) in enumerate([("cor_botao", "panel.color_button"),
                                           ("cor_texto", "panel.color_text"),
                                           ("cor_borda", "panel.color_border"),
                                           ("cor_fundo", "panel.color_bg")]):
            cb = _ColorButton(self._on_panel_edit)
            self.p_colors[name] = cb
            crow.addWidget(QLabel(tr(label)), n // 2, (n % 2) * 2, Qt.AlignRight)
            crow.addWidget(cb, n // 2, (n % 2) * 2 + 1)
        self.p_bg_theme = QCheckBox(tr("panel.bg_follows_theme"))
        self.p_bg_theme.toggled.connect(self._on_panel_edit)
        crow.addWidget(self.p_bg_theme, 2, 2, 1, 2)
        v.addLayout(crow)

        pos = QHBoxLayout()
        self.p_title_pos = QComboBox()
        self.p_key_pos = QComboBox()
        for combo in (self.p_title_pos, self.p_key_pos):
            for key in POSITIONS:
                combo.addItem(tr(f"panel.pos_{key}"), key)
            combo.currentIndexChanged.connect(self._on_panel_edit)
        pos.addWidget(QLabel(tr("panel.title_pos")))
        pos.addWidget(self.p_title_pos)
        pos.addSpacing(18)
        pos.addWidget(QLabel(tr("panel.key_pos")))
        pos.addWidget(self.p_key_pos)
        pos.addStretch(1)
        v.addLayout(pos)

        show = QHBoxLayout()
        self.p_show_key = QCheckBox(tr("panel.show_key"))
        self.p_show_status = QCheckBox(tr("panel.show_status"))
        self.p_show_controls = QCheckBox(tr("panel.show_controls"))
        for cb in (self.p_show_key, self.p_show_status, self.p_show_controls):
            cb.toggled.connect(self._on_panel_edit)
            show.addWidget(cb)
        show.addStretch(1)
        v.addLayout(show)

        win = QFormLayout()
        win.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.p_ontop = QCheckBox(tr("panel.on_top"))
        self.p_ontop.toggled.connect(self._on_panel_edit)
        win.addRow("", self.p_ontop)
        orow = QHBoxLayout()
        self.p_opacity = QSlider(Qt.Horizontal)
        self.p_opacity.setRange(20, 100)
        self.p_opacity.valueChanged.connect(self._on_panel_edit)
        self.p_opacity_lbl = QLabel()
        self.p_opacity_lbl.setMinimumWidth(44)
        orow.addWidget(self.p_opacity, 1)
        orow.addWidget(self.p_opacity_lbl)
        win.addRow(tr("panel.opacity"), orow)
        win.addRow("", QLabel(tr("panel.wheel_tip"), objectName="hint", wordWrap=True))
        showp = QPushButton(tr("panel.toggle"))
        showp.clicked.connect(self.app.toggle_panel)
        win.addRow("", showp)
        v.addLayout(win)
        self.p_error = QLabel(objectName="error")
        v.addWidget(self.p_error)
        v.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll)
        return w

    # ------------------------------------------------------------- Âmbito
    def _build_scope_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(18, 16, 18, 12)
        v.addWidget(QLabel(tr("scope.intro")))
        self.r_global = QRadioButton(tr("scope.global"))
        self.r_apps = QRadioButton(tr("scope.apps"))
        grp = QButtonGroup(self)
        grp.addButton(self.r_global)
        grp.addButton(self.r_apps)
        self.r_global.toggled.connect(self._on_scope_edit)
        v.addWidget(self.r_global)
        v.addWidget(self.r_apps)
        self.apps = QListWidget(objectName="apps")
        v.addWidget(self.apps, 1)
        row = QHBoxLayout()
        b1 = QPushButton(tr("scope.pick_exe"))
        b1.clicked.connect(self._add_app_file)
        b2 = QPushButton(tr("scope.type_name"))
        b2.clicked.connect(self._add_app_name)
        b3 = QPushButton(tr("scope.remove"))
        b3.clicked.connect(self._remove_app)
        for b in (b1, b2, b3):
            row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)
        v.addWidget(QLabel(tr("scope.hint"), objectName="hint", wordWrap=True))
        self.scope_error = QLabel(objectName="error")
        self.scope_error.setWordWrap(True)
        v.addWidget(self.scope_error)
        return w

    # ------------------------------------------------------- Preferências
    def _build_prefs_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(18, 16, 18, 12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setVerticalSpacing(10)

        self.p_theme = QComboBox()
        for key in ("diurno", "noturno", "automatico"):
            self.p_theme.addItem(tr(f"theme.{key}"), key)
        self.p_theme.currentIndexChanged.connect(self._on_prefs_edit)
        form.addRow(tr("prefs.theme"), self.p_theme)

        self.p_lang = QComboBox()
        for code, name in available_languages():
            self.p_lang.addItem(name, code)
        self.p_lang.currentIndexChanged.connect(self._on_prefs_edit)
        form.addRow(tr("prefs.language"), self.p_lang)

        self.p_autostart = QCheckBox(tr("prefs.autostart"))
        self.p_autostart.toggled.connect(self._on_prefs_edit)
        form.addRow("", self.p_autostart)
        self.autostart_error = QLabel(objectName="error")
        self.autostart_error.setWordWrap(True)
        self.autostart_error.hide()
        form.addRow("", self.autostart_error)

        # marcado = NÃO pedir confirmação (texto pedido pelo utilizador)
        self.p_no_confirm = QCheckBox(tr("prefs.no_confirm_delete"))
        self.p_no_confirm.toggled.connect(self._on_prefs_edit)
        form.addRow("", self.p_no_confirm)

        self.p_warn_conflict = QCheckBox(tr("prefs.warn_key_conflict"))
        self.p_warn_conflict.toggled.connect(self._on_prefs_edit)
        form.addRow("", self.p_warn_conflict)

        self.p_hotkey = KeyCaptureEdit(self._set_capture_mode)
        self.p_hotkey.captured.connect(lambda _b: self._on_prefs_edit())
        form.addRow(tr("prefs.hotkey"), self.p_hotkey)

        pk = QHBoxLayout()
        self.p_panelkey = KeyCaptureEdit(self._set_capture_mode)
        self.p_panelkey.captured.connect(lambda _b: self._on_prefs_edit())
        pk.addWidget(self.p_panelkey, 1)
        nopk = QPushButton(tr("field.no_key"))
        nopk.setToolTip(tr("prefs.panel_key_none_tip"))
        nopk.clicked.connect(lambda: (self.p_panelkey.set_binding(""), self._on_prefs_edit()))
        pk.addWidget(nopk)
        form.addRow(tr("prefs.panel_key"), pk)

        self.p_mods = QComboBox()
        self.p_mods.addItem(tr("prefs.mods_exact"), "exatos")
        self.p_mods.addItem(tr("prefs.mods_ignore"), "ignorar")
        self.p_mods.currentIndexChanged.connect(self._on_prefs_edit)
        form.addRow(tr("prefs.modifiers"), self.p_mods)

        self.p_textmode = QComboBox()
        self.p_textmode.addItem(tr("prefs.mode_type"), "escrever")
        self.p_textmode.addItem(tr("prefs.mode_paste"), "colar")
        self.p_textmode.currentIndexChanged.connect(self._on_prefs_edit)
        form.addRow(tr("prefs.text_mode"), self.p_textmode)

        self.g_error = QLabel(objectName="error")
        self.g_error.setWordWrap(True)
        form.addRow("", self.g_error)
        info_lbl = QLabel(objectName="hint")
        info_lbl.setWordWrap(True)
        info_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_lbl.setText(tr("prefs.info", folder=self.app.store.root))
        form.addRow("", info_lbl)
        return w

    # ============================================================== dados
    def set_palette(self, pal) -> None:
        """Mudança de tema: só o aspeto. Não toca na cópia de trabalho, por
        isso as edições ainda por gravar mantêm-se."""
        for w in (self.grid, self.archive_grid, self.archive_zone, self.active_zone):
            w.pal = pal
        self._refresh_grid()
        self._refresh_state_buttons()
        self._update_preview()

    def reload_from_store(self, notice: str = "", changed=None) -> None:
        """(Re)carrega a vista a partir da configuração gravada.

        Se o próprio ficheiro de uma edição pendente foi alterado por fora
        (``changed``: caminhos alterados), vale o ficheiro: a edição local é
        descartada SEM ser gravada (gravá-la apagaria a alteração externa) e
        avisa-se. As outras edições pendentes válidas são gravadas primeiro; as
        que não se podem gravar (por ex. com conflitos) mantêm-se."""
        st = self.app.store
        sid = self.app.engine.active_set_id
        changed_names = None if changed is None else {Path(p).resolve() for p in changed}

        def touched(path) -> bool:
            return changed_names is not None and Path(path).resolve() in changed_names

        # antes de gravar seja o que for: não escrever por cima do ficheiro externo
        if self.ms is not None and touched(st.set_path(self.ms.id)):
            self._save_set_timer.stop()
        if touched(st.config_path):
            self._save_settings_timer.stop()
        self.flush()
        replaced = False
        keep_settings = self._dirty_settings and not touched(st.config_path)
        replaced |= self._dirty_settings and not keep_settings
        if not keep_settings:
            self.settings = st.settings.clone()
            self._dirty_settings = False
        keep_set = (self._dirty_set and self.ms is not None and self.ms.id == sid
                    and sid in st.sets and not touched(st.set_path(sid)))
        replaced |= self._dirty_set and self.ms is not None and not keep_set
        if not keep_set:
            self.ms = st.sets[sid].clone() if sid in st.sets else None
            self._dirty_set = False
        if replaced:
            notice = tr("status.unsaved_replaced")
        if self.ms is not None:
            ops.normalize_order(self.ms)
            if not (0 <= self.cur < len(self.ms.macros)):
                act = self.ms.active_indices()
                self.cur = act[0] if act else (0 if self.ms.macros else -1)
                self.selected = [self.cur] if self.cur >= 0 else []
        else:
            self.cur = -1
            self.selected = []
        self._loading = True
        self.set_combo.clear()
        for s in sorted(st.sets.values(), key=lambda s: (s.nome.lower(), s.id)):
            self.set_combo.addItem(s.nome, s.id)
        self.set_combo.setCurrentIndex(self.set_combo.findData(sid))
        self._load_prefs()
        self._load_panel_prefs()
        self._load_scope()
        self._loading = False
        self._refresh_grid()
        self._load_editor()
        self._refresh_state_buttons()
        if notice:
            self.show_status(notice, error=replaced)

    def _load_prefs(self) -> None:
        s = self.settings
        self.p_theme.setCurrentIndex(max(0, self.p_theme.findData(s.tema)))
        self.p_lang.setCurrentIndex(max(0, self.p_lang.findData(s.idioma)))
        self.p_autostart.setChecked(s.arrancar_com_windows)
        self.p_no_confirm.setChecked(not s.confirmar_eliminacao)
        self.p_warn_conflict.setChecked(s.avisar_conflito_tecla)
        self.p_hotkey.set_binding(s.tecla_suspensao)
        self.p_panelkey.set_binding(s.tecla_painel)
        self.p_mods.setCurrentIndex(max(0, self.p_mods.findData(s.modificadores)))
        self.p_textmode.setCurrentIndex(max(0, self.p_textmode.findData(s.modo_texto)))
        self.g_error.clear()

    def _load_panel_prefs(self) -> None:
        p = self.settings.painel
        for name, sb in self.p_spins.items():
            sb.setValue(getattr(p, name))
        for name, cb in self.p_colors.items():
            cb.set_color(getattr(p, name) or self.pal.panel_bg)
        self.p_bg_theme.setChecked(p.cor_fundo == "")
        self.p_colors["cor_fundo"].setEnabled(p.cor_fundo != "")
        self.p_title_pos.setCurrentIndex(max(0, self.p_title_pos.findData(p.posicao_titulo)))
        self.p_key_pos.setCurrentIndex(max(0, self.p_key_pos.findData(p.posicao_tecla)))
        self.p_show_key.setChecked(p.mostrar_tecla)
        self.p_show_status.setChecked(p.mostrar_estado)
        self.p_show_controls.setChecked(p.mostrar_controlos)
        self.p_ontop.setChecked(p.sempre_por_cima)
        self.p_opacity.setValue(round(p.opacidade * 100))
        self.p_opacity_lbl.setText(f"{round(p.opacidade * 100)} %")
        self.p_preset.setCurrentIndex(self.p_preset.findData(matching_preset(p)))
        self.p_error.clear()
        self._update_preview()

    def _load_scope(self) -> None:
        self.apps.clear()
        if not self.ms:
            return
        (self.r_apps if self.ms.ambito.modo == "aplicacoes" else self.r_global).setChecked(True)
        self.apps.addItems(self.ms.ambito.aplicacoes)
        self.scope_error.clear()

    def _issues(self) -> list[Issue]:
        if not self.ms:
            return []
        issues = validate_macros(self.ms.clone(), self.app.store.settings)
        if self.ms.ambito.modo == "aplicacoes" and not self.ms.ambito.aplicacoes:
            issues.append(Issue("", tr("store.scope_need_app")))
        return issues

    def _dup_text(self, i: int, dups: dict[int, list[int]]) -> str:
        if i not in dups:
            return ""
        parts = []
        for j in dups[i]:
            lab = macro_label(j, self.ms.macros[j])
            if self.ms.macros[j].arquivada:
                lab += " " + tr("dup.archived_suffix")
            parts.append(lab)
        return tr("dup.info", others=", ".join(parts))

    def _counts(self) -> dict[str, int]:
        return self.app.counts_for(self.ms) if self.ms else {}

    def _tile(self, i: int, bad: set, dups: dict, counts: Optional[dict] = None) -> dict:
        m = self.ms.macros[i]
        if m.is_space:
            return {"index": i, "kind": "espaco", "title": "", "key": "", "error": i in bad,
                    "dup": False, "tip": tr("tile.space_tip"), "count": None}
        tip = tr("tile.tooltip", title=m.display_title(), key=m.tecla or tr("tile.no_key"))
        if i in dups:
            tip += "\n" + self._dup_text(i, dups)
        if i in bad:
            tip += "\n" + tr("tile.has_error")
        if not m.arquivada:
            tip += "\n" + tr("tile.hover_key_tip")
        count = None
        if m.is_counter:
            counts = self._counts() if counts is None else counts
            count = counts.get(m.id, m.reposicao)
        return {"index": i, "kind": m.tipo, "title": m.display_title(), "key": m.tecla,
                "error": i in bad, "dup": i in dups, "tip": tip, "count": count}

    def _refresh_grid(self) -> None:
        if not self.ms:
            self.grid.set_tiles([], -1)
            self.archive_grid.set_tiles([], -1)
            self.editor.setEnabled(False)
            self.active_title.setText(tr("active.title", n=0))
            self.archive_title.setText(tr("archive.title", n=0))
            return
        n = len(self.ms.macros)
        self.selected = [i for i in self.selected if 0 <= i < n]
        if not self.selected and 0 <= self.cur < n:
            self.selected = [self.cur]
        bad = {i.macro_index for i in self._issues() if i.macro_index is not None}
        dups = ops.duplicate_groups(self.ms.macros)
        act = self.ms.active_indices()
        arch = self.ms.archived_indices()
        q = self.archive_search.text()
        shown = [i for i in arch if ops.matches_query(self.ms.macros[i], q)]
        sel = set(self.selected)
        counts = self._counts()
        style = self.settings.painel
        self.grid.apply_style(style, columns=style.colunas)
        self.archive_grid.apply_style(style)
        bg = style.cor_fundo or self.pal.panel_bg
        self.active_box.setStyleSheet(
            f"QFrame#activebox {{ background: {bg}; border: 1px solid {self.pal.border};"
            f" border-radius: 8px; }} QFrame#activebox QListWidget#grid {{ background: {bg}; }}"
            f" QFrame#activebox QLabel {{ background: transparent; }}")
        self.grid.set_tiles([self._tile(i, bad, dups, counts) for i in act], sel, self.cur)
        self.archive_grid.set_tiles([self._tile(i, bad, dups, counts) for i in shown], sel,
                                    self.cur)
        self.empty_label.setVisible(not act)
        self.grid.setVisible(bool(act))
        self.active_title.setText(tr("active.title", n=len(act)))
        self.archive_title.setText(tr("archive.title", n=len(arch)))
        self.archive_grid.setVisible(bool(shown))
        self.archive_empty.setVisible(not shown)
        self.archive_empty.setText(tr("archive.no_results") if arch and q.strip()
                                   else tr("archive.empty"))
        self.editor.setEnabled(0 <= self.cur < n)

    def _sel_macros(self) -> list:
        if not self.ms:
            return []
        return [self.ms.macros[i] for i in self.selected if 0 <= i < len(self.ms.macros)]

    def _multi(self) -> bool:
        return len(self.selected) > 1

    def _load_editor(self) -> None:
        self._loading = True
        m = self._macro()
        multi = self._multi()
        single = m is not None and not multi
        is_space = single and m.is_space
        for wdg in (self.f_title, self.f_key, self.no_key_btn):
            wdg.setEnabled(single and not is_space)
        for wdg in (self.f_text, self.f_repeat, self.f_interval, self.f_step, self.f_reset,
                    self.f_long, self.left_btn, self.right_btn):
            wdg.setEnabled(single)
        self.type_pages.setCurrentIndex(2 if is_space else (1 if single and m.is_counter else 0))
        self.type_pages.setVisible(single)
        if m is None or multi:
            self.f_title.setText("")
            self.f_key.set_binding("")
            self.f_text.setPlainText("")
            self.f_preview.clear()
            self.f_error.clear()
            self.f_dup.clear()
            self.editor.setEnabled(multi)
        else:
            self.editor.setEnabled(True)
            self.f_title.setText(m.titulo)
            self.f_key.set_binding(m.tecla)
            self.f_text.setPlainText(m.texto)
            self.f_repeat.setValue(m.repeticoes)
            self.f_interval.setValue(m.intervalo_ms)
            self.f_step.setValue(m.incremento)
            self.f_reset.setValue(m.reposicao)
            self.f_long.setValue(m.pressao_longa_ms)
            self._update_count_label()
            self._update_preview_and_errors()
        self._update_editor_header()
        self._loading = False

    def _update_editor_header(self) -> None:
        m = self._macro()
        if m is None:
            self.editor_title.setText(tr("editor.none"))
            return
        archived = m.arquivada
        if self._multi():
            n = len(self.selected)
            self.editor_title.setText(tr("editor.multi", n=n))
            self.archive_btn.setText(tr("macros.restore_n", n=n) if archived
                                     else tr("macros.archive_n", n=n))
            self.del_btn.setToolTip(tr("macros.delete_n_tip", n=n))
        else:
            key = ("editor.header_space" if m.is_space else
                   "editor.header_counter" if m.is_counter else
                   "editor.header_archived" if archived else "editor.header")
            self.editor_title.setText(tr(key))
            self.archive_btn.setText(tr("macros.restore") if archived else tr("macros.archive"))
            self.del_btn.setToolTip(tr("macros.delete_tip"))
        self.archive_btn.setToolTip(tr("macros.restore_tip") if archived
                                    else tr("macros.archive_tip"))

    def _macro(self):
        if self.ms and 0 <= self.cur < len(self.ms.macros):
            return self.ms.macros[self.cur]
        return None

    def _update_preview_and_errors(self) -> list[Issue]:
        m = self._macro()
        issues = self._issues()
        if m is not None and not self._multi() and m.tipo == "texto":
            if not m.texto:
                self.f_preview.setText(tr("editor.empty_text"))
            else:
                try:
                    d = describe_steps(parse_action(m.texto))
                    if m.repeticoes > 1:
                        d += f" — {m.repeticoes}×"
                    self.f_preview.setText(d if len(d) < 220 else d[:217] + "…")
                except CommandError:
                    self.f_preview.clear()
            self.f_dup.setText(self._dup_text(self.cur, ops.duplicate_groups(self.ms.macros)))
        mine = [i.message for i in issues if i.macro_index == self.cur]
        others = [i for i in issues if i.macro_index not in (self.cur, None)]
        txt = "\n".join(mine)
        if others:
            txt += ("\n" if txt else "") + tr("editor.other_errors", n=len(others))
        self.f_error.setText(txt)
        self.scope_error.setText("\n".join(i.message for i in issues if i.macro_index is None))
        return issues

    # ============================================================ edição
    def _on_selection(self, grid: MacroGrid) -> None:
        """Seleção numa grelha (clique, Ctrl+clique, Shift+clique). A seleção
        fica sempre numa só grelha (ativas ou arquivo)."""
        if self._loading:
            return
        sel = grid.selected_real()
        if not sel:
            return
        other = self.archive_grid if grid is self.grid else self.grid
        other.blockSignals(True)
        other.clearSelection()
        other.setCurrentRow(-1)
        other.blockSignals(False)
        self.selected = sel
        cur_item = grid.currentItem()
        ci = grid.real_index(grid.row(cur_item)) if cur_item is not None else -1
        self.cur = ci if ci in sel else sel[0]
        self._load_editor()

    def _on_edit(self, *_):
        if self._loading or self._multi():
            return
        m = self._macro()
        if m is None or m.is_space:
            return
        m.titulo = self.f_title.text()
        if m.is_counter:
            m.incremento = self.f_step.value()
            m.reposicao = self.f_reset.value()
            m.pressao_longa_ms = self.f_long.value()
        else:
            m.texto = self.f_text.toPlainText()
            m.repeticoes = self.f_repeat.value()
            m.intervalo_ms = self.f_interval.value()
        self._changed(refresh=False)

    def _update_count_label(self) -> None:
        m = self._macro()
        if m is not None and m.is_counter:
            self.f_count.setText(str(self._counts().get(m.id, m.reposicao)))

    def _reset_counter_now(self) -> None:
        m = self._macro()
        if m is None or not m.is_counter or not self.ms:
            return
        self.app.set_count(self.ms.id, m.id, m.reposicao)

    def on_counts_changed(self) -> None:
        """Uma contagem mudou (painel ou tecla): atualiza os botões e o editor."""
        if not self.ms:
            return
        counts = self._counts()
        from .widgets import COUNT_ROLE, INDEX_ROLE
        for g in (self.grid, self.archive_grid):
            for r in range(g.count()):
                it = g.item(r)
                m = self.ms.macros[it.data(INDEX_ROLE)]
                if m.is_counter:
                    it.setData(COUNT_ROLE, counts.get(m.id, m.reposicao))
            g.viewport().update()
        self._update_count_label()
        self._update_preview()

    def _on_key_captured(self, b: str) -> None:
        m = self._macro()
        if m is None or self._multi():
            return
        m.tecla = b
        self.f_key.set_binding(b)
        self._changed()

    def _changed(self, refresh: bool = True) -> None:
        self._dirty_set = True
        issues = self._update_preview_and_errors()
        if refresh:
            self._refresh_grid()
        else:
            # atualização leve dos tiles (sem reconstruir a grelha)
            bad = {i.macro_index for i in issues if i.macro_index is not None}
            dups = ops.duplicate_groups(self.ms.macros)
            from .widgets import COUNT_ROLE, DUP_ROLE, ERROR_ROLE, INDEX_ROLE, KEY_ROLE, TITLE_ROLE
            counts = self._counts()
            for g in (self.grid, self.archive_grid):
                for r in range(g.count()):
                    it = g.item(r)
                    i = it.data(INDEX_ROLE)
                    t = self._tile(i, bad, dups, counts)
                    it.setData(COUNT_ROLE, t["count"])
                    it.setData(TITLE_ROLE, t["title"])
                    it.setData(KEY_ROLE, t["key"])
                    it.setData(ERROR_ROLE, t["error"])
                    it.setData(DUP_ROLE, t["dup"])
                    it.setToolTip(t["tip"])
                g.viewport().update()
        if issues:
            self._save_set_timer.stop()
            self.show_status(tr("status.fix_errors"), error=True)
        else:
            self._save_set_timer.start()
            self.show_status(tr("status.saving"))

    def _save_set_now(self) -> None:
        if not self.ms:
            return
        try:
            issues = self.app.store.save_set(self.ms)
        except OSError as e:
            self.show_status(tr("status.write_failed", err=e.strerror or e), error=True)
            return
        if issues:
            self.show_status(str(issues[0]), error=True)
            return
        self._dirty_set = False
        self.app.apply_config()
        self.show_status(tr("status.saved"))
        self._update_preview()

    def flush(self) -> None:
        if self._save_set_timer.isActive():
            self._save_set_timer.stop()
            self._save_set_now()
        if self._save_settings_timer.isActive():
            self._save_settings_timer.stop()
            self._save_settings_now()

    def _select(self, real_index: int) -> None:
        self._select_many([real_index] if real_index >= 0 else [])

    def _select_many(self, idxs: list[int]) -> None:
        self.selected = list(idxs)
        self.cur = idxs[0] if idxs else -1
        self._refresh_grid()
        self._load_editor()

    def _add_macro(self) -> None:
        self._add_item("texto")

    def _add_item(self, kind: str) -> None:
        """Nova macro, contador ou espaço vazio (no fim da área Ativo)."""
        if not self.ms:
            return
        # Uma pressão = um item (ignora cliques repetidos muito rápidos).
        import time
        now = time.monotonic()
        if now - self._last_add < 0.35:
            return
        self._last_add = now
        if kind == "contador":
            i = ops.new_counter(self.ms, tr("macros.new_counter_title"))
        elif kind == "espaco":
            i = ops.new_space(self.ms)
        else:
            i = ops.new_macro(self.ms, tr("macros.new_title"))
        self._select(i)
        self._changed()
        self.flush()
        if kind == "texto":
            self.f_text.setFocus()
        elif kind == "contador":
            self.f_title.setFocus()
            self.f_title.selectAll()

    def _delete_macro(self) -> None:
        """Elimina a macro selecionada, ou todas as selecionadas."""
        targets = self._sel_macros()
        if not targets:
            return
        if len(targets) > 1:
            # várias: confirmação sempre, com a quantidade
            ok, _ = ask(self, tr("delete.many_title"), tr("delete.many_text", n=len(targets)),
                        yes=tr("delete.confirm_n", n=len(targets)), danger=True)
            if not ok:
                return
        elif self.app.store.settings.confirmar_eliminacao:
            ok, dont_ask = ask(self, tr("delete.title"),
                               tr("delete.text", title=targets[0].display_title()),
                               yes=tr("delete.confirm"), checkbox=tr("delete.dont_ask"),
                               danger=True)
            if not ok:
                return
            if dont_ask:
                s = self.app.store.settings.clone()
                s.confirmar_eliminacao = False
                self.settings.confirmar_eliminacao = False
                self.app.store.save_settings(s)
                self.app.apply_config()
                self._loading = True
                self.p_no_confirm.setChecked(True)
                self._loading = False
        was_archived = targets[0].arquivada
        first = min(self.selected)
        ops.delete_many(self.ms, self.selected)
        group = self.ms.archived_indices() if was_archived else self.ms.active_indices()
        nxt = max([i for i in group if i < first], default=group[0] if group else -1)
        self._select(nxt)
        self._changed()
        self.show_status(tr("status.deleted") if len(targets) == 1
                         else tr("status.deleted_n", n=len(targets)))

    def _move(self, delta: int) -> None:
        if self._macro() is None or self._multi():
            return
        self._select(ops.move(self.ms, self.cur, delta))
        self._changed()

    def _on_drop(self, to_archive: bool, src, idxs: list, anchor: int = -1,
                 after: bool = False, space: int = -1) -> None:
        """Macros largadas numa área (Ativo ou Arquivo), na posição indicada.

        * ``anchor``/``after``: inserir antes/depois desse item (-1 = no fim);
        * ``space``: largou-se um único item sobre um espaço vazio da mesma
          área — trocam de lugar.
        Ao passar do Arquivo para Ativo, um conflito de tecla pede
        confirmação (como «Restaurar»). Grava logo a seguir."""
        if not self.ms:
            return
        n = len(self.ms.macros)
        idxs = [i for i in idxs if 0 <= i < n]
        if not idxs:
            return
        items = [self.ms.macros[i] for i in idxs]
        anchor_m = self.ms.macros[anchor] if 0 <= anchor < n else None
        # troca com um espaço vazio (mesma área, um só item)
        if (0 <= space < n and len(items) == 1 and space != idxs[0]
                and self.ms.macros[space].arquivada == items[0].arquivada == to_archive):
            ops.swap(self.ms, idxs[0], space)
            self._select_many([ops.index_of(self.ms, items[0])])
            self._changed()
            self.flush()
            return
        left_out = 0
        if to_archive:
            spaces = [m for m in items if m.is_space]
            items = [m for m in items if not m.is_space]
            if spaces and not items:
                self.show_status(tr("status.space_not_archived"), error=True)
                return
        else:
            # do Arquivo para Ativo: conflitos de tecla
            keep = []
            group_keys: dict = {}            # teclas já usadas por itens deste grupo
            for m in items:
                if not m.arquivada:
                    keep.append(m)
                    continue
                b = _binding_or_none(m.tecla)
                if b is not None and b in group_keys:
                    # duas arquivadas do mesmo grupo com a mesma tecla: só a
                    # primeira é restaurada; a outra fica no Arquivo
                    left_out += 1
                    continue
                i = ops.index_of(self.ms, m)
                j = ops.key_conflict(self.ms, i)
                if j is not None and self.ms.macros[j] not in items:
                    other = self.ms.macros[j]
                    ok, _ = ask(self, tr("restore.title"),
                                tr("restore.conflict", key=m.tecla, title=m.display_title(),
                                   other=other.display_title()),
                                yes=tr("restore.replace"))
                    if not ok:
                        continue
                    if anchor_m is other:
                        anchor_m = None
                    # a ativa em conflito vai para o Arquivo, onde estava esta
                    ops.move_items(self.ms, [other], True, m, False)
                keep.append(m)
                if b is not None:
                    group_keys[b] = m
            items = keep
        if not items:
            if left_out:
                self.show_status(tr("status.group_key_conflict", n=left_out), error=True)
            return
        if anchor_m is not None and anchor_m in items:
            anchor_m = None
        moved_between = any(m.arquivada != to_archive for m in items)
        ops.move_items(self.ms, items, to_archive, anchor_m, after)
        self._select_many([ops.index_of(self.ms, m) for m in items])
        self._changed()
        self.flush()
        if moved_between:
            key = "status.archived" if to_archive else "status.restored"
            self.show_status(tr(key, title=items[0].display_title()) if len(items) == 1
                             else tr(key + "_n", n=len(items)))
        if left_out:
            self.show_status(tr("status.group_key_conflict", n=left_out), error=True)

    def _archive_indices(self, idxs: list[int]) -> None:
        """Arquiva as macros ativas indicadas (botão, menu ou arrasto)."""
        if not self.ms:
            return
        idxs = [i for i in idxs if 0 <= i < len(self.ms.macros) and not self.ms.macros[i].arquivada]
        if not idxs:
            return
        titles = [self.ms.macros[i].display_title() for i in idxs]
        self._select_many(ops.archive_many(self.ms, idxs))
        self._changed()
        self.show_status(tr("status.archived", title=titles[0]) if len(titles) == 1
                         else tr("status.archived_n", n=len(titles)))

    def _restore_indices(self, idxs: list[int]) -> None:
        """Restaura macros arquivadas, pedindo confirmação em caso de conflito
        de tecla (Substituir troca-a com a ativa; Cancelar não altera essa)."""
        targets = [self.ms.macros[i] for i in idxs if self.ms.macros[i].arquivada]
        restored = []
        for m in targets:
            i = ops.index_of(self.ms, m)
            j = ops.key_conflict(self.ms, i)
            if j is None:
                ops.restore(self.ms, i)
            else:
                other = self.ms.macros[j]
                ok, _ = ask(self, tr("restore.title"),
                            tr("restore.conflict", key=m.tecla, title=m.display_title(),
                               other=other.display_title()),
                            yes=tr("restore.replace"))
                if not ok:
                    continue
                ops.restore_replacing(self.ms, i, j)
            restored.append(m)
        if not restored:
            return
        self._select_many([ops.index_of(self.ms, m) for m in restored])
        self._changed()
        self.show_status(tr("status.restored", title=restored[0].display_title())
                         if len(restored) == 1 else tr("status.restored_n", n=len(restored)))

    def _toggle_archive(self) -> None:
        targets = self._sel_macros()
        if not targets:
            return
        if targets[0].arquivada:
            self._restore_indices(list(self.selected))
        else:
            self._archive_indices(list(self.selected))

    # ------------------------------------------------------- copiar / colar
    def _copy_macro(self) -> None:
        targets = self._sel_macros()
        if not targets:
            return
        data = macros_to_clipboard(targets)
        mime = QMimeData()
        mime.setData(MIME_MACRO, data.encode("utf-8"))
        mime.setText(data)
        QApplication.clipboard().setMimeData(mime)
        self.show_status(tr("status.copied", title=targets[0].display_title())
                         if len(targets) == 1 else tr("status.copied_n", n=len(targets)))

    def _paste_macro(self) -> None:
        if not self.ms:
            return
        mime = QApplication.clipboard().mimeData()
        text = ""
        if mime is not None and mime.hasFormat(MIME_MACRO):
            text = bytes(mime.data(MIME_MACRO)).decode("utf-8")
        elif mime is not None and mime.hasText():
            text = mime.text()
        macros = macros_from_clipboard(text) if text else []
        if not macros:
            self.show_status(tr("status.nothing_to_paste"), error=True)
            return
        # cola logo a seguir à seleção, na mesma área (Ativo ou Arquivo)
        after = max(self.selected) if self.selected else None
        new = []
        for m in macros:
            pos = ops.insert_copy(self.ms, m, after)
            new.append(self.ms.macros[pos])
            after = pos
        self._select_many([ops.index_of(self.ms, m) for m in new])
        self._changed()
        self.show_status(tr("status.pasted", title=macros[0].display_title())
                         if len(macros) == 1 else tr("status.pasted_n", n=len(macros)))

    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        """Atalhos da grelha: Delete/Backspace elimina, Ctrl+C copia, Ctrl+V cola.
        Só atuam quando o foco não está num campo de edição (aí mantêm o
        comportamento normal de texto). As teclas dos contadores também
        contam com esta janela à frente."""
        if e.type() not in (QEvent.KeyPress, QEvent.KeyRelease) or not self.isVisible() \
                or not self.isActiveWindow():
            return False
        if self._counter_key(e):
            return True
        if e.type() != QEvent.KeyPress:
            return False
        fw = QApplication.focusWidget()
        if fw is None or fw.window() is not self or _is_editable(fw):
            return False
        if self.tabs.currentIndex() != 0:
            return False
        has_sel = bool(self._sel_macros())
        if self._hover_assign_key(e):
            return True
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace) and not (
                e.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)):
            if has_sel:
                QTimer.singleShot(0, self._delete_macro)
                return True
            return False
        if e.matches(QKeySequence.Copy) and has_sel:
            self._copy_macro()
            return True
        if e.matches(QKeySequence.Paste):
            self._paste_macro()
            return True
        return False

    def _counter_key(self, e) -> bool:
        """Tecla de um contador premida com esta janela à frente (o hook deixa
        passar as teclas nas janelas do Macropad). Toque curto soma; manter
        premida repõe — decidido ao largar, como no hook."""
        k = e.key()
        if e.type() == QEvent.KeyRelease:
            if e.isAutoRepeat() or k not in self._counter_keys:
                return k in self._counter_keys
            sid, cid, t0 = self._counter_keys.pop(k)
            eng = self.app.engine
            # mudou de conjunto enquanto a tecla estava premida: não conta
            idx = eng.counter_index(cid) if eng.active_set_id == sid else None
            if idx is not None:
                m = eng.active_set.macros[idx]
                ok, why = eng.counter_press(idx, (time.monotonic() - t0) * 1000
                                            >= m.pressao_longa_ms)
                if not ok:
                    self.show_status(why, error=True)
            return True
        if e.isAutoRepeat():
            return k in self._counter_keys
        if k in _MOD_KEYS:
            return False
        fw = QApplication.focusWidget()
        if fw is not None and _is_editable(fw):
            return False
        if self._hover_target() >= 0:
            return False                      # rato sobre um botão: atribui a tecla
        name = key_name_from_event(e)
        if name is None:
            return False
        idx = self.app.engine.counter_for(Binding(name, mods_from_event(e)))
        if idx is None:
            return False
        ms = self.app.engine.active_set
        self._counter_keys[k] = (ms.id, ms.macros[idx].id, time.monotonic())
        return True

    # ============================================== tecla pelo rato (hover)
    def _on_hover(self, grid: MacroGrid, real: int) -> None:
        """O rato entrou/saiu de um botão: enquanto estiver sobre ele, a próxima
        tecla premida fica atribuída a esse botão."""
        if real < 0 and grid is not self._hover_grid:
            return
        valid = (real >= 0 and self.ms is not None and real < len(self.ms.macros)
                 and not self.ms.macros[real].is_space)
        if self._hover_grid is not None and self._hover_grid is not grid:
            self._hover_grid.capture_hover = False
            self._hover_grid.viewport().update()
        self._hover_grid = grid if valid else None
        self._hover_real = real if valid else -1
        grid.hovered = real
        for g in (self.grid, self.archive_grid):
            g.capture_hover = valid and g is grid
            g.viewport().update()
        self._capture_hover = valid
        self._sync_capture()

    def _hover_target(self) -> int:
        """Índice real do botão sob o cursor, consultado agora (a grelha pode
        ter sido reconstruída depois do último movimento do rato)."""
        g = self._hover_grid
        if g is None or not g.isVisible() or not self.ms:
            return -1
        real = g.real_at(g.viewport().mapFromGlobal(QCursor.pos()))
        if not (0 <= real < len(self.ms.macros)) or self.ms.macros[real].is_space:
            return -1
        return real

    def _hover_assign_key(self, e) -> bool:
        """Atribui a tecla premida ao botão sob o rato. Delete/Backspace, Tab,
        Ctrl+C e Ctrl+V mantêm as suas funções; Esc sozinho cancela."""
        real = self._hover_target()
        if real < 0 or not self.ms:
            return False
        k = e.key()
        if k in _MOD_KEYS:
            return True                      # espera pela tecla principal
        if k in (Qt.Key_Delete, Qt.Key_Backspace, Qt.Key_Tab, Qt.Key_Backtab):
            return False
        if e.matches(QKeySequence.Copy) or e.matches(QKeySequence.Paste):
            return False
        mods = mods_from_event(e)
        if k == Qt.Key_Escape and not mods:
            return True
        name = key_name_from_event(e)
        if name is None:
            self.show_status(tr("key.unsupported"), error=True)
            return True
        self.assign_key(real, str(Binding(name, mods)))
        return True

    def assign_key(self, real: int, binding: str) -> bool:
        """Atribui ``binding`` ao item ``real`` se não estiver em uso por outra
        macro ativa nem for uma tecla global. Devolve True se atribuiu."""
        m = self.ms.macros[real]
        if m.is_space:
            return False
        b = parse_binding(binding)
        conflict = ""
        st = self.app.store.settings
        for label, hk in ((tr("prefs.hotkey").rstrip(":").lower(), st.tecla_suspensao),
                          (tr("prefs.panel_key").rstrip(":").lower(), st.tecla_painel)):
            try:
                if hk and parse_binding(hk) == b:
                    conflict = tr("hover.conflict_global", key=binding, what=label)
            except KeyBindingError:
                pass
        if not conflict and not m.arquivada:
            for j, x in enumerate(self.ms.macros):
                if j == real or x.arquivada or x.is_space or not x.tecla:
                    continue
                try:
                    if parse_binding(x.tecla) == b:
                        conflict = tr("hover.conflict", key=binding, title=x.display_title())
                        break
                except KeyBindingError:
                    continue
        if conflict:
            self.show_status(conflict, error=True)
            if st.avisar_conflito_tecla:
                _ok, dont_show = ask(self, tr("hover.conflict_title"), conflict,
                                     yes=tr("btn.ok"), no=None,
                                     checkbox=tr("hover.dont_show"), only_ok=True)
                if dont_show:
                    self.settings.avisar_conflito_tecla = False
                    self._loading = True
                    self.p_warn_conflict.setChecked(False)
                    self._loading = False
                    self._save_settings_now()
            return False
        m.tecla = binding
        self._select(real)
        self._changed()
        self.flush()
        self.show_status(tr("status.key_assigned", key=binding, title=m.display_title()))
        return True

    # ============================================================ âmbito
    def _on_scope_edit(self, *_):
        if self._loading or not self.ms:
            return
        self.ms.ambito.modo = "aplicacoes" if self.r_apps.isChecked() else "global"
        self.ms.ambito.aplicacoes = [self.apps.item(i).text() for i in range(self.apps.count())]
        self._changed()

    def _add_app_file(self) -> None:
        start = os.environ.get("ProgramFiles", str(Path.home()))
        path, _ = QFileDialog.getOpenFileName(self, tr("scope.pick_title"), start,
                                              tr("scope.exe_filter"))
        if path:
            self._add_app(Path(path).name)

    def _add_app_name(self) -> None:
        name, ok = get_text(self, tr("scope.add_title"), tr("scope.add_label"))
        if ok and name.strip():
            self._add_app(name.strip())

    def _add_app(self, name: str) -> None:
        existing = {self.apps.item(i).text().lower() for i in range(self.apps.count())}
        if name.lower() not in existing:
            self.apps.addItem(name)
        self.r_apps.setChecked(True)
        self._on_scope_edit()

    def _remove_app(self) -> None:
        for it in self.apps.selectedItems():
            self.apps.takeItem(self.apps.row(it))
        self._on_scope_edit()

    # ===================================================== painel (prefs)
    def _read_panel(self) -> PanelSettings:
        p = self.settings.painel
        for name, sb in self.p_spins.items():
            setattr(p, name, sb.value())
        for name, cb in self.p_colors.items():
            setattr(p, name, cb.color())
        if self.p_bg_theme.isChecked():
            p.cor_fundo = ""
        self.p_colors["cor_fundo"].setEnabled(not self.p_bg_theme.isChecked())
        p.posicao_titulo = self.p_title_pos.currentData()
        p.posicao_tecla = self.p_key_pos.currentData()
        p.mostrar_tecla = self.p_show_key.isChecked()
        p.mostrar_estado = self.p_show_status.isChecked()
        p.mostrar_controlos = self.p_show_controls.isChecked()
        p.sempre_por_cima = self.p_ontop.isChecked()
        p.opacidade = self.p_opacity.value() / 100
        self.p_opacity_lbl.setText(f"{self.p_opacity.value()} %")
        return p

    def _on_panel_edit(self, *_):
        if self._loading:
            return
        p = self._read_panel()
        self._loading = True
        self.p_preset.setCurrentIndex(self.p_preset.findData(matching_preset(p)))
        self._loading = False
        self._update_preview()
        self.app.preview_panel_settings(p)
        self._dirty_settings = True
        self._save_settings_timer.start()

    def _on_preset(self, idx: int) -> None:
        key = self.p_preset.itemData(idx)
        if key:
            self._apply_preset(key)

    def _apply_preset(self, key: str) -> None:
        self.settings.painel = apply_preset(self._read_panel(), key)
        self._loading = True
        self._load_panel_prefs()
        self._loading = False
        self.app.preview_panel_settings(self.settings.painel)
        self._dirty_settings = True
        self._save_settings_timer.start()

    def _update_preview(self) -> None:
        if not hasattr(self, "preview"):
            return
        ms = self.ms
        status = self.app.engine.status()
        txt = status[1] + (f" · {ms.nome}" if ms and status[0] in ("ativo", "fora") else "")
        eng = self.app.engine
        self.preview.update_preview(self.settings.painel, self.pal, ms,
                                    (status[0], txt, None, eng.suspended,
                                     eng.counter_allowed()[0]),
                                    panel_hint(self.settings), self._counts())
        self.preview_scroll.setMinimumHeight(min(self.preview.sizeHint().height() + 4, 340))

    # ======================================================= preferências
    def _on_prefs_edit(self, *_):
        if self._loading:
            return
        s = self.settings
        s.tema = self.p_theme.currentData()
        s.idioma = self.p_lang.currentData()
        s.arrancar_com_windows = self.p_autostart.isChecked()
        s.confirmar_eliminacao = not self.p_no_confirm.isChecked()
        s.avisar_conflito_tecla = self.p_warn_conflict.isChecked()
        s.tecla_suspensao = self.p_hotkey.binding()
        s.tecla_painel = self.p_panelkey.binding()
        s.modificadores = self.p_mods.currentData()
        s.modo_texto = self.p_textmode.currentData()
        try:
            parse_binding(s.tecla_suspensao)
        except KeyBindingError as e:
            self.g_error.setText(tr("prefs.hotkey_error", err=e))
            return
        self.g_error.clear()
        # aplicadas de imediato (não esperam pelo temporizador)
        self._save_settings_timer.stop()
        self._save_settings_now()

    def _save_settings_now(self) -> None:
        self._read_panel()
        self._dirty_settings = True
        try:
            issues = self.app.store.save_settings(self.settings)
        except OSError as e:
            msg = tr("status.write_failed", err=e.strerror or e)
            self.g_error.setText(msg)
            self.p_error.setText(msg)
            self.show_status(msg, error=True)
            return
        if issues:
            msg = tr("status.prefs_not_saved") + "\n" + "\n".join(i.message for i in issues[:4])
            self.g_error.setText(msg)
            self.p_error.setText(msg)
            self.show_status(tr("status.prefs_conflict"), error=True)
            return
        self._dirty_settings = False
        self.g_error.clear()
        self.p_error.clear()
        err = self.app.apply_config()
        self.show_autostart_error(err)
        self._refresh_grid()
        hk = self.app.store.settings.tecla_suspensao
        self.btn_on.setToolTip(tr("state.on_tip", hotkey=hk))
        self.btn_off.setToolTip(tr("state.off_tip", hotkey=hk))
        if err:
            self.show_status(err, error=True)
        else:
            self.show_status(tr("status.prefs_saved"))

    def show_autostart_error(self, err: Optional[str]) -> None:
        self.autostart_error.setText(err or "")
        self.autostart_error.setVisible(bool(err))

    def _set_capture_mode(self, on: bool) -> None:
        self._capture_field = on
        self._sync_capture()

    def _sync_capture(self) -> None:
        # Enquanto se grava uma tecla (campo ou rato sobre um botão), o motor
        # deixa passar todas as teclas, incluindo as teclas globais.
        # O rato sobre um botão só conta com esta janela ativa: noutra aplicação
        # as teclas globais e as macros têm de continuar a funcionar.
        hover = self._capture_hover and self.isVisible() and self.isActiveWindow()
        self.app.engine.capture_mode = self._capture_field or hover

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == QEvent.ActivationChange:
            self._counter_keys.clear()        # o keyup pode ir para outra janela
            self._sync_capture()

    def hideEvent(self, e):
        super().hideEvent(e)
        self._sync_capture()

    # =========================================================== conjuntos
    def _on_set_chosen(self, idx: int) -> None:
        sid = self.set_combo.itemData(idx)
        if sid and sid != self.app.engine.active_set_id:
            self.flush()
            self.cur = -1
            self.selected = []
            self.app.select_set(sid)

    def _new_set(self) -> None:
        name, ok = get_text(self, tr("sets.new_title"), tr("sets.name_label"))
        if ok and name.strip():
            self.flush()
            ms = self.app.store.create_set(name)
            self.app.apply_config()
            self.cur = -1
            self.selected = []
            self.app.select_set(ms.id)

    def _dup_set(self) -> None:
        if not self.ms:
            return
        self.flush()
        ms = self.app.store.duplicate_set(self.ms.id)
        self.app.apply_config()
        self.app.select_set(ms.id)

    def _rename_set(self) -> None:
        if not self.ms:
            return
        name, ok = get_text(self, tr("sets.rename_title"), tr("sets.name_label"), self.ms.nome)
        if ok and name.strip():
            self.ms.nome = name.strip()
            self._save_set_now()
            self.reload_from_store()

    def _delete_set(self) -> None:
        if not self.ms:
            return
        if len(self.app.store.sets) <= 1:
            info(self, tr("sets.delete_title"), tr("sets.need_one"))
            return
        ok, _ = ask(self, tr("sets.delete_title"), tr("sets.delete_text", name=self.ms.nome),
                    yes=tr("delete.confirm"), danger=True)
        if not ok:
            return
        self._save_set_timer.stop()
        self.app.store.delete_set(self.ms.id)
        self.app.apply_config()
        self.cur = -1
        self.selected = []
        self.reload_from_store(tr("status.set_deleted"))

    def _import_set(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("sets.import_title"), str(Path.home()),
                                              tr("sets.toml_filter"))
        if not path:
            return
        try:
            ms = self.app.store.import_set(Path(path))
        except ConfigError as e:
            info(self, tr("sets.import_title"),
                 tr("sets.import_invalid") + "\n\n" + "\n".join(str(i) for i in e.issues[:8]),
                 warning=True)
            return
        except (OSError, UnicodeDecodeError) as e:
            info(self, tr("sets.import_title"), str(e), warning=True)
            return
        self.app.apply_config()
        self.reload_from_store(tr("status.imported", name=ms.nome))

    def _export_set(self) -> None:
        if not self.ms:
            return
        self.flush()
        path, _ = QFileDialog.getSaveFileName(self, tr("sets.export_title"),
                                              str(Path.home() / f"{self.ms.id}.toml"),
                                              tr("sets.toml_filter"))
        if path:
            try:
                self.app.store.export_set(self.ms.id, Path(path))
                self.show_status(tr("status.exported", path=path))
            except OSError as e:
                info(self, tr("sets.export_title"), str(e), warning=True)

    def _open_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.app.store.root)))

    # =============================================================== estado
    def _refresh_state_buttons(self) -> None:
        susp = self.app.engine.suspended
        self.btn_on.setChecked(not susp)
        self.btn_off.setChecked(susp)

    def on_engine_state(self) -> None:
        self._refresh_state_buttons()
        self._update_preview()

    def show_status(self, text: str, error: bool = False) -> None:
        self.status.setStyleSheet(f"color:{self.pal.error}" if error else "")
        self.status.setText(text)

    def closeEvent(self, e):
        self.flush()
        e.ignore()
        self.hide()        # fechar a janela não termina a aplicação

    def dispose(self) -> None:
        QApplication.instance().removeEventFilter(self)
        self.flush()                 # não perder edições pendentes (ex.: mudança de idioma)
        self._save_set_timer.stop()
        self._save_settings_timer.stop()
