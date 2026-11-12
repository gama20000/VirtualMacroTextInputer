"""Caixas de diálogo com botões traduzidos (independentes das traduções do Qt)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QCheckBox, QInputDialog, QLineEdit, QMessageBox, QWidget

from ..i18n import tr


def ask(parent: QWidget, title: str, text: str, yes: Optional[str] = None,
        no: Optional[str] = None, checkbox: Optional[str] = None,
        danger: bool = False, only_ok: bool = False) -> tuple[bool, bool]:
    """Pergunta sim/não (ou só aviso, com ``only_ok``).
    Devolve (confirmado, caixa_marcada)."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning if danger else QMessageBox.Question)
    box.setWindowTitle(title)
    box.setText(text)
    b_yes = box.addButton(yes or tr("btn.yes"), QMessageBox.AcceptRole)
    if only_ok:
        box.setIcon(QMessageBox.Warning)
        b_no = b_yes
        box.setDefaultButton(b_yes)
        box.setEscapeButton(b_yes)
    else:
        b_no = box.addButton(no or tr("btn.cancel"), QMessageBox.RejectRole)
        box.setDefaultButton(b_no if danger else b_yes)
        box.setEscapeButton(b_no)
    cb = None
    if checkbox:
        cb = QCheckBox(checkbox)
        box.setCheckBox(cb)
    box.exec()
    return box.clickedButton() is b_yes, bool(cb and cb.isChecked())


def info(parent: QWidget, title: str, text: str, warning: bool = False) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning if warning else QMessageBox.Information)
    box.setWindowTitle(title)
    box.setText(text)
    box.addButton(tr("btn.ok"), QMessageBox.AcceptRole)
    box.exec()


def get_text(parent: QWidget, title: str, label: str, text: str = "") -> tuple[str, bool]:
    dlg = QInputDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setLabelText(label)
    dlg.setTextValue(text)
    dlg.setTextEchoMode(QLineEdit.Normal)
    dlg.setOkButtonText(tr("btn.ok"))
    dlg.setCancelButtonText(tr("btn.cancel"))
    ok = dlg.exec() == QInputDialog.Accepted
    return dlg.textValue(), ok
