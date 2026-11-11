"""Temas (Diurno / Noturno), folha de estilos e ícones."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPalette, QPixmap


def assets_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base and (Path(base) / "macropad" / "ui" / "assets").is_dir():
        return Path(base) / "macropad" / "ui" / "assets"
    return Path(__file__).resolve().parent / "assets"


@dataclass(frozen=True)
class Palette:
    name: str
    dark: bool
    bg: str            # fundo das janelas
    surface: str       # zonas elevadas (editor)
    well: str          # zona da grelha / topo
    text: str
    muted: str
    border: str
    input: str
    input_border: str
    hover: str
    accent: str
    accent_text: str
    focus: str
    ok: str
    error: str
    warn: str
    dup: str           # realce de conteúdo duplicado
    caption: str       # barra de título
    caption_text: str
    panel_bg: str      # fundo do painel quando cor_fundo = ""


DAY = Palette(
    name="diurno", dark=False,
    bg="#f4f4f6", surface="#ffffff", well="#e9e9ee", text="#1b1b1f", muted="#5c5d66",
    border="#d3d4da", input="#ffffff", input_border="#b9bbc4", hover="#e4e5ea",
    accent="#0a64d8", accent_text="#ffffff", focus="#0a64d8",
    ok="#1a7f37", error="#c62828", warn="#9a6700", dup="#e0a800",
    caption="#000000", caption_text="#ffffff", panel_bg="#e9e9ee",
)

NIGHT = Palette(
    name="noturno", dark=True,
    bg="#262626", surface="#2b2b2b", well="#1c1c1c", text="#e6e6e6", muted="#a0a0a0",
    border="#3a3a3a", input="#383838", input_border="#4a4a4a", hover="#444444",
    accent="#2f81f7", accent_text="#ffffff", focus="#ffd33d",
    ok="#2ea043", error="#f85149", warn="#d29922", dup="#e3b341",
    caption="#1c1c1c", caption_text="#e6e6e6", panel_bg="#1c1c1c",
)


def palette_for(theme: str, system_dark: bool | None) -> Palette:
    if theme == "noturno":
        return NIGHT
    if theme == "automatico":
        return NIGHT if system_dark else DAY
    return DAY


def stylesheet(p: Palette) -> str:
    a = assets_dir()
    check = (a / "check_white.png").as_posix()
    tone = "light" if p.dark else "dark"
    up = (a / f"arrow_up_{tone}.png").as_posix()
    down = (a / f"arrow_down_{tone}.png").as_posix()
    return f"""
QWidget {{ background: {p.bg}; color: {p.text}; font-family: "Segoe UI", "Noto Sans", sans-serif; font-size: 10pt; }}
QWidget#well, QListWidget#grid {{ background: {p.well}; }}
QWidget#well QLabel, QWidget#editor QLabel, QWidget#top QLabel {{ background: transparent; }}
QWidget#editor {{ background: {p.surface}; }}
QWidget#top {{ background: {p.surface}; border-bottom: 1px solid {p.border}; }}
QLabel#hint {{ color: {p.muted}; font-size: 9pt; }}
QLabel#error {{ color: {p.error}; }}
QLabel#dupinfo {{ color: {p.warn}; }}
QLabel#h1 {{ font-size: 15pt; font-weight: 600; }}
QLabel#section {{ font-weight: 600; color: {p.muted}; }}
QFrame#divider {{ background: {p.border}; max-height: 1px; min-height: 1px; border: none; }}
QLineEdit, QPlainTextEdit, QSpinBox, QComboBox, QListWidget#apps {{
    background: {p.input}; color: {p.text}; border: 1px solid {p.input_border}; border-radius: 4px;
    padding: 4px 6px; selection-background-color: {p.accent}; selection-color: {p.accent_text}; }}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus, QListWidget#apps:focus {{
    border: 1px solid {p.accent}; }}
QLineEdit#keycapture[capturing="true"] {{ border: 2px solid {p.warn}; }}
QComboBox QAbstractItemView {{ background: {p.input}; color: {p.text};
    selection-background-color: {p.accent}; selection-color: {p.accent_text}; }}
QPushButton, QToolButton {{ background: {p.surface}; color: {p.text}; border: 1px solid {p.input_border};
    border-radius: 6px; padding: 5px 12px; }}
QPushButton:hover, QToolButton:hover {{ background: {p.hover}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {p.border}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {p.focus}; padding: 4px 11px; }}
QPushButton:disabled, QToolButton:disabled {{ color: {p.muted}; }}
QPushButton#primary {{ background: {p.accent}; border-color: {p.accent}; color: {p.accent_text}; }}
QToolButton::menu-indicator {{ image: none; }}
QPushButton#stateOn, QPushButton#stateOff {{ border-radius: 14px; padding: 5px 16px; font-weight: 600;
    background: transparent; color: {p.muted}; border: 1px solid {p.input_border}; }}
QPushButton#stateOn:hover, QPushButton#stateOff:hover {{ background: {p.hover}; color: {p.text}; }}
QPushButton#stateOn:checked {{ background: {p.ok}; color: #ffffff; border: 1px solid {p.ok}; }}
QPushButton#stateOff:checked {{ background: {p.error}; color: #ffffff; border: 1px solid {p.error}; }}
QPushButton#stateOn:focus, QPushButton#stateOff:focus {{ border: 2px solid {p.focus}; padding: 4px 15px; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; padding: 8px 14px; color: {p.muted}; border: none;
    border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {p.text}; border-bottom: 2px solid {p.accent}; }}
QTabBar::tab:hover {{ color: {p.text}; }}
QTabBar::tab:focus {{ color: {p.text}; }}
QSlider::groove:horizontal {{ height: 4px; background: {p.border}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {p.accent}; width: 14px; margin: -6px 0; border-radius: 7px; }}
QMenu {{ background: {p.surface}; color: {p.text}; border: 1px solid {p.border}; }}
QMenu::item {{ padding: 6px 22px; }}
QMenu::item:selected {{ background: {p.accent}; color: {p.accent_text}; }}
QMenu::item:disabled {{ color: {p.muted}; }}
QToolTip {{ background: {p.surface}; color: {p.text}; border: 1px solid {p.border}; }}
QScrollArea {{ border: none; }}
QCheckBox, QRadioButton {{ background: transparent; spacing: 8px; }}
QCheckBox:focus, QRadioButton:focus {{ color: {p.accent}; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px;
    border: 1px solid {p.input_border}; background: {p.input}; }}
QCheckBox::indicator {{ border-radius: 3px; }}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {p.accent}; }}
QCheckBox::indicator:checked {{ background: {p.accent}; border-color: {p.accent}; image: url({check}); }}
QRadioButton::indicator:checked {{ border: 5px solid {p.accent}; background: #ffffff; width: 8px; height: 8px; }}
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{ background: {p.border}; }}
QSpinBox {{ padding-right: 22px; }}
QSpinBox::up-button, QSpinBox::down-button {{ subcontrol-origin: border; width: 20px;
    border: none; border-left: 1px solid {p.input_border}; background: transparent; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 4px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 4px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {p.hover}; }}
QSpinBox::up-arrow {{ image: url({up}); width: 10px; height: 10px; }}
QSpinBox::down-arrow {{ image: url({down}); width: 10px; height: 10px; }}
QComboBox {{ padding-right: 24px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right; width: 22px;
    border: none; background: transparent; }}
QComboBox::down-arrow {{ image: url({down}); width: 12px; height: 12px; }}
QMessageBox, QInputDialog, QDialog {{ background: {p.bg}; }}
"""


def qpalette(p: Palette) -> QPalette:
    pal = QPalette()
    c = QColor
    pal.setColor(QPalette.Window, c(p.bg))
    pal.setColor(QPalette.WindowText, c(p.text))
    pal.setColor(QPalette.Base, c(p.input))
    pal.setColor(QPalette.AlternateBase, c(p.well))
    pal.setColor(QPalette.Text, c(p.text))
    pal.setColor(QPalette.Button, c(p.surface))
    pal.setColor(QPalette.ButtonText, c(p.text))
    pal.setColor(QPalette.Highlight, c(p.accent))
    pal.setColor(QPalette.HighlightedText, c(p.accent_text))
    pal.setColor(QPalette.ToolTipBase, c(p.surface))
    pal.setColor(QPalette.ToolTipText, c(p.text))
    pal.setColor(QPalette.PlaceholderText, c(p.muted))
    pal.setColor(QPalette.Link, c(p.accent))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        pal.setColor(QPalette.Disabled, role, c(p.muted))
    return pal


# ------------------------------------------------------------------ ícones
@lru_cache(maxsize=None)
def _pixmap(name: str) -> QPixmap:
    return QPixmap(str(assets_dir() / name))


def app_icon() -> QIcon:
    """Logótipo do programa (janelas e executável)."""
    icon = QIcon()
    pm = _pixmap("logo.png")
    for s in (16, 20, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(pm.scaled(s, s, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return icon


def tray_icon(suspended: bool) -> QIcon:
    """Ícone da área de notificação: ativo (contorno ciano) ou suspenso
    (cinzento com ponto vermelho)."""
    pm = _pixmap("tray_suspended.png" if suspended else "tray_active.png")
    icon = QIcon()
    for s in (16, 20, 24, 32, 40, 48, 64):
        icon.addPixmap(pm.scaled(s, s, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return icon


def logo_pixmap(size: int) -> QPixmap:
    return _pixmap("logo.png").scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
