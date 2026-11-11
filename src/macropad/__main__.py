"""Ponto de entrada: ``python -m macropad`` (ou ``pythonw -m macropad``).

Opções:
  --config-dir PASTA   usar outra pasta de configuração (por omissão
                       %APPDATA%\\Macropad; também via MACROPAD_HOME)
  --show-config        abrir a configuração ao arrancar
"""
from __future__ import annotations

import argparse
import getpass
import logging
import logging.handlers
import os
import sys
from pathlib import Path


def default_root() -> Path:
    env = os.environ.get("MACROPAD_HOME")
    if env:
        return Path(env)
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "Macropad"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "macropad"


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
    setup_logging(root)

    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon

    from .platform import create_platform
    from .ui import theme
    from .ui.app import MacropadApp

    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    instance_name = f"Macropad-{user}"

    qapp = QApplication(sys.argv[:1])
    qapp.setApplicationName("Macropad")
    qapp.setQuitOnLastWindowClosed(False)      # fechar janelas não termina a app
    qapp.setWindowIcon(theme.app_icon())

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
