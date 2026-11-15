"""Ponto de entrada: ``python -m macropad`` (ou ``pythonw -m macropad``).

Opções:
  --config-dir PASTA   usar outra pasta de configuração (por omissão
                       %APPDATA%\\VirtualMacroTextInputer; também via MACROPAD_HOME)
  --show-config        abrir a configuração ao arrancar
"""
from __future__ import annotations

import argparse
import getpass
import logging
import logging.handlers
import os
import shutil
import sys
from pathlib import Path

from .branding import (APP_NAME, EXE_NAME, LEGACY_LINUX_DIR_NAME, LEGACY_NAME,
                       LINUX_DIR_NAME)


def _base_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home()))
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def default_root() -> Path:
    env = os.environ.get("MACROPAD_HOME")
    if env:
        return Path(env)
    return _base_dir() / (EXE_NAME if sys.platform == "win32" else LINUX_DIR_NAME)


def legacy_root() -> Path:
    """Pasta de dados do nome anterior (Macropad)."""
    return _base_dir() / (LEGACY_NAME if sys.platform == "win32" else LEGACY_LINUX_DIR_NAME)


def migrate_legacy_root(root: Path, legacy: Path) -> bool:
    """Primeiro arranque com o nome novo: copia as macros e preferências da
    pasta antiga. A pasta antiga fica intacta (serve de cópia de segurança).
    Devolve True se copiou."""
    if root.exists() or not legacy.is_dir():
        return False
    shutil.copytree(legacy, root)
    return True


def setup_logging(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    h = logging.handlers.RotatingFileHandler(root / "macropad.log", maxBytes=512_000,
                                             backupCount=2, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[h])

    def hook(exc_type, exc, tb):
        logging.getLogger("macropad").critical("exceção não tratada",
                                               exc_info=(exc_type, exc, tb))
    sys.excepthook = hook


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="macropad")
    ap.add_argument("--config-dir", type=Path, default=None)
    ap.add_argument("--show-config", action="store_true")
    args = ap.parse_args(argv)
    root = args.config_dir or default_root()
    migrated = False
    if args.config_dir is None and not os.environ.get("MACROPAD_HOME"):
        try:
            migrated = migrate_legacy_root(root, legacy_root())
        except OSError:
            migrated = False      # continua com uma pasta nova; o erro fica no registo
    setup_logging(root)
    if migrated:
        logging.info("dados copiados de %s para %s", legacy_root(), root)

    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon

    from .platform import create_platform
    from .ui import theme
    from .ui.app import MacropadApp

    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    instance_name = f"{EXE_NAME}-{user}"
    legacy_instance = f"{LEGACY_NAME}-{user}"

    qapp = QApplication(sys.argv[:1])
    qapp.setApplicationName(APP_NAME)
    qapp.setQuitOnLastWindowClosed(False)      # fechar janelas não termina a app
    qapp.setWindowIcon(theme.app_icon())

    # A versão com o nome antigo (Macropad) ainda a correr teria o seu próprio
    # hook: as macros seriam escritas duas vezes. Pede para a fechar.
    old = QLocalSocket()
    old.connectToServer(legacy_instance)
    if old.waitForConnected(300):
        old.disconnectFromServer()
        from PySide6.QtWidgets import QMessageBox

        from . import i18n
        QMessageBox.warning(None, APP_NAME, i18n.tr("app.legacy_running", old=LEGACY_NAME,
                                                     new=APP_NAME))
        return 1

    platform = create_platform()
    if not platform.acquire_single_instance(instance_name):
        # Já existe uma instância: pede-lhe que abra a configuração e sai.
        sock = QLocalSocket()
        sock.connectToServer(instance_name)
        if sock.waitForConnected(1000):
            sock.write(b"show")
            sock.flush()
            sock.waitForBytesWritten(500)
            sock.disconnectFromServer()
        return 0

    QLocalServer.removeServer(instance_name)
    server = QLocalServer()
    server.listen(instance_name)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        logging.warning("área de notificação indisponível")

    app = MacropadApp(qapp, root, platform, server)
    if args.show_config:
        app.show_config()
    rc = qapp.exec()
    logging.info("terminado (%s)", rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
