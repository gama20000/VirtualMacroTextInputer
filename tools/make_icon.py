"""Regenera assets/macropad.ico a partir de src/macropad/ui/assets/logo.png.

O .ico já vem incluído; só é preciso correr isto se trocar o logótipo."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
src = QPixmap(str(ROOT / "src" / "macropad" / "ui" / "assets" / "logo.png"))
out = ROOT / "assets" / "macropad.ico"
ok = src.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(str(out), "ICO")
print(out if ok else "falhou (formato ICO indisponível)")
