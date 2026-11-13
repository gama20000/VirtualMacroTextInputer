"""Controlador da aplicação: ícone na área de notificação, janelas, motor,
observador de ficheiros, tema, idioma e persistência do estado."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication
from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from .. import i18n
from ..core.engine import Engine
from ..core.engine import CANCEL_MODIFIERS
from ..core.model import MacroSet, PanelSettings
from ..core.store import ConfigStore
from ..core.watcher import FileWatcher
from ..i18n import tr
from . import theme

log = logging.getLogger(__name__)


class _Bridge(QObject):
    """Reencaminha chamadas de outras threads para a thread da interface."""
    engine_event = Signal(str, object)
    files_changed = Signal(object)


class _WindowStyler(QObject):
    """Aplica as cores da barra de título a todas as janelas quando aparecem
    (incluindo caixas de diálogo)."""

    def __init__(self, app: "MacropadApp"):
        super().__init__()
        self.app = app

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Show and isinstance(obj, QWidget) and obj.isWindow():
            self.app.style_window(obj)
        return False


class MacropadApp(QObject):
    def __init__(self, qapp: QApplication, root: Path, platform,
                 server: Optional[QLocalServer] = None):
        super().__init__()
        self.qapp = qapp
        self.platform = platform
        self.store = ConfigStore(root)
        self.store.ensure_defaults()
        startup_issues = self.store.load_all()
        i18n.set_language(self.store.settings.idioma)
        if startup_issues:                    # mensagens no idioma escolhido
            startup_issues = self.store.load_all()
        self.state = self.store.load_state()
        migration_msgs = self.store.migrate(self.state)

        self.pal = theme.DAY
        self._theme_key = None
        qapp.setStyle("Fusion")
        self.apply_theme()
        self._styler = _WindowStyler(self)
        qapp.installEventFilter(self._styler)
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(lambda *_: self.apply_theme())
        # o Windows nem sempre notifica: verificação periódica barata (modo Automático)
        self._theme_poll = QTimer(self, interval=4000, timeout=self._poll_system_theme)
        self._theme_poll.start()

        self.engine = Engine(platform)
        self.engine.set_config(self.store.config())
        if self.state.conjunto in self.store.sets:
            self.engine.set_active_set(self.state.conjunto)
        self.engine.set_suspended(self.state.suspenso)

        self.bridge = _Bridge()
        self.bridge.engine_event.connect(self._on_engine_event)
        self.bridge.files_changed.connect(self._on_files_changed)
        self.engine.add_listener(lambda ev, p: self.bridge.engine_event.emit(ev, p))

        self.config_window = None
        from .panel import PanelWindow
        self.panel = PanelWindow(self)

        self._build_tray()
        self._counts_timer = QTimer(self, singleShot=True, interval=500,
                                    timeout=self._persist_state)
        autostart_err = self._sync_autostart()

        hook_error = platform.start_hook(self.engine.handle_key)
        if hook_error:
            log.warning(hook_error)
            self.notify("Macropad", hook_error, error=True)

        self.watcher = FileWatcher(self.store.watched_files,
                                   lambda paths: self.bridge.files_changed.emit(paths))
        self.watcher.start()

        if server is not None:
            server.newConnection.connect(lambda: self._on_instance_message(server))

        if startup_issues:
            self._report_issues(startup_issues, tr("msg.startup_errors"))
        for msg in migration_msgs:
            log.info(msg)
            self.notify("Macropad", msg)
        if autostart_err:
            self.notify("Macropad", autostart_err, error=True)
        if self.state.painel_visivel:
            self.set_panel_visible(True)
        self._persist_state()

    # ------------------------------------------------------------- tema
    def _system_dark(self) -> Optional[bool]:
        v = self.platform.system_prefers_dark()
        if v is not None:
            return v
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorScheme"):
            cs = hints.colorScheme()
            if cs == Qt.ColorScheme.Dark:
                return True
            if cs == Qt.ColorScheme.Light:
                return False
        return None

    def apply_theme(self, force: bool = False) -> None:
        tema = self.store.settings.tema
        pal = theme.palette_for(tema, self._system_dark() if tema == "automatico" else None)
        key = (tema, pal.name)
        if key == self._theme_key and not force:
            return
        self._theme_key = key
        self.pal = pal
        self.qapp.setPalette(theme.qpalette(pal))
        self.qapp.setStyleSheet(theme.stylesheet(pal))
        for w in self.qapp.topLevelWidgets():
            if w.isVisible():
                self.style_window(w)
        if getattr(self, "panel", None) is not None:
            self.panel.rebuild()
        if getattr(self, "config_window", None) is not None:
            self.config_window.set_palette(pal)   # sem recarregar os dados

    def _poll_system_theme(self) -> None:
        if self.store.settings.tema == "automatico":
            self.apply_theme()

    def style_window(self, w: QWidget) -> None:
        """Barra de título: Diurno = preta com texto branco; Noturno = escura."""
        try:
            self.platform.style_title_bar(int(w.winId()), True, self.pal.caption,
                                          self.pal.caption_text, None)
        except Exception:
            log.debug("não foi possível estilizar a barra de título", exc_info=True)

    # ------------------------------------------------------------- tray
    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(theme.tray_icon(self.engine.suspended), self)
        self.menu = QMenu()
        self.menu.aboutToShow.connect(self._fill_menu)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_tray_activated)
        self._update_tray()
        self.tray.show()

    def _fill_menu(self) -> None:
        m = self.menu
        m.clear()
        state = tr("state.suspended") if self.engine.suspended else tr("state.active")
        hdr = m.addAction(tr("tray.header", state=state))
        hdr.setEnabled(False)
        m.addSeparator()
        m.addAction(tr("tray.open_config"), self.show_config)
        pk = self.engine.settings.tecla_painel
        m.addAction((tr("tray.hide_panel") if self.panel.isVisible() else tr("tray.show_panel"))
                    + (f"\t{pk}" if pk else ""), self.toggle_panel)
        sets_menu = m.addMenu(tr("tray.active_set"))
        grp = QActionGroup(sets_menu)
        for ms in self.store.config().ordered_sets():
            a = QAction(ms.nome, sets_menu, checkable=True)
            a.setChecked(ms.id == self.engine.active_set_id)
            a.triggered.connect(lambda _=False, sid=ms.id: self.select_set(sid))
            grp.addAction(a)
            sets_menu.addAction(a)
        hk = self.engine.settings.tecla_suspensao
        m.addAction((tr("tray.resume") if self.engine.suspended else tr("tray.suspend"))
                    + f"\t{hk}", self.engine.toggle_suspended)
        m.addSeparator()
        m.addAction(tr("tray.quit"), self.quit)

    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_config()

    def _update_tray(self) -> None:
        susp = self.engine.suspended
        self.tray.setIcon(theme.tray_icon(susp))
        ms = self.engine.active_set
        self.tray.setToolTip(tr("tray.tooltip",
                                state=tr("state.suspended") if susp else tr("state.active"),
                                set=ms.nome if ms else tr("tray.no_set")))

    def notify(self, title: str, text: str, error: bool = False) -> None:
        icon = QSystemTrayIcon.Warning if error else QSystemTrayIcon.Information
        if QSystemTrayIcon.isSystemTrayAvailable() and self.tray.isVisible():
            self.tray.showMessage(title, text, icon, 8000)

    def _report_issues(self, issues, title: str) -> None:
        text = "\n".join(str(i) for i in issues[:5])
        if len(issues) > 5:
            text += "\n" + tr("msg.and_more", n=len(issues) - 5)
        log.warning("%s:\n%s", title, text)
        self.notify(title, text + "\n" + tr("msg.kept_last_valid"), error=True)
        if self.config_window is not None:
            self.config_window.show_status(f"{title}: {text}", error=True)

    # ------------------------------------------------------------ janelas
    def show_config(self, tab: Optional[int] = None) -> None:
        if self.config_window is None:
            from .config_window import ConfigWindow
            self.config_window = ConfigWindow(self)
        else:
            self.config_window.reload_from_store()
        w = self.config_window
        if tab is not None:
            w.tabs.setCurrentIndex(tab)
        w.show()
        w.setWindowState(w.windowState() & ~Qt.WindowMinimized)
        w.raise_()
        w.activateWindow()

    def _recreate_config_window(self) -> None:
        """Recria a janela (mudança de idioma), mantendo posição e separador."""
        old = self.config_window
        if old is None:
            return
        visible, geo, tab = old.isVisible(), old.saveGeometry(), old.tabs.currentIndex()
        old.dispose()
        old.hide()
        old.deleteLater()
        self.config_window = None
        if visible:
            self.show_config(tab)
            self.config_window.restoreGeometry(geo)

    def set_panel_visible(self, visible: bool) -> None:
        if visible:
            self.panel.rebuild()
            self.panel.show()
            self.panel.refresh_status()
        else:
            self.panel.hide()
        self.state.painel_visivel = visible
        self._persist_state()

    def toggle_panel(self) -> None:
        self.set_panel_visible(not self.panel.isVisible())

    def save_panel_position(self, x: int, y: int) -> None:
        self.state.painel_x, self.state.painel_y = x, y
        self._persist_state()

    # ------------------------------------------------------------ contadores
    def counts_for(self, ms: Optional[MacroSet]) -> dict[str, int]:
        """Contagem de cada contador do conjunto (id -> valor)."""
        from .panel import counter_key
        if ms is None:
            return {}
        out = {}
        for m in ms.macros:
            if m.is_counter:
                out[m.id] = self.state.contadores.get(counter_key(ms.id, m.id), m.reposicao)
        return out

    def set_count(self, set_id: str, counter_id: str, value: int) -> None:
        from .panel import counter_key
        self.state.contadores[counter_key(set_id, counter_id)] = int(value)
        self._counts_timer.start()            # agrupa gravações rápidas
        if set_id == self.engine.active_set_id:
            self.panel.set_count(counter_id, int(value))
        w = self.config_window
        if w is not None and w.ms is not None and w.ms.id == set_id:
            w.on_counts_changed()

    def _on_counter(self, p: dict) -> None:
        # o conjunto vem no evento: o ativo pode ter mudado entretanto
        ms = self.store.sets.get(p.get("set_id", self.engine.active_set_id))
        if ms is None:
            return
        cur = self.counts_for(ms).get(p["id"], p["value"])
        new = p["value"] if p["action"] == "reset" else cur + p["step"]
        self.set_count(ms.id, p["id"], new)

    def set_panel_opacity(self, value: float) -> None:
        """Transparência alterada com a roda do rato: grava (agrupando
        alterações rápidas) e atualiza a configuração, se estiver aberta."""
        self._pending_opacity = value
        if not hasattr(self, "_opacity_timer"):
            self._opacity_timer = QTimer(self, singleShot=True, interval=600,
                                         timeout=self._save_panel_opacity)
        self._opacity_timer.start()
        w = self.config_window
        if w is not None:
            w.settings.painel.opacidade = value
            w._loading = True
            w.p_opacity.setValue(round(value * 100))
            w.p_opacity_lbl.setText(f"{round(value * 100)} %")
            w._loading = False
            w._update_preview()

    def _save_panel_opacity(self) -> None:
        s = self.store.settings.clone()
        s.painel.opacidade = self._pending_opacity
        try:
            issues = self.store.save_settings(s)
        except OSError as e:
            log.exception("não foi possível gravar a transparência do painel")
            self.notify("Macropad", tr("status.write_failed", err=e.strerror or e), error=True)
            return
        if not issues:
            self.engine.set_config(self.store.config())

    def preview_panel_settings(self, p: PanelSettings) -> None:
        """Mostra as alterações no painel real (se visível) antes de gravar."""
        if self.panel.isVisible():
            self.panel.rebuild(p)

    # ----------------------------------------------------- configuração
    def apply_config(self) -> Optional[str]:
        """Aplica a configuração gravada. Devolve uma mensagem de erro se o
        arranque com o Windows não pôde ser atualizado."""
        old_lang = i18n.language()
        self.engine.set_config(self.store.config())
        err = self._sync_autostart()
        self.apply_theme()
        if self.store.settings.idioma != old_lang:
            i18n.set_language(self.store.settings.idioma)
            self._update_tray()
            self.panel.rebuild()
            QTimer.singleShot(0, self._recreate_config_window)
        return err

    def select_set(self, set_id: str) -> None:
        if self.config_window is not None:
            self.config_window.flush()
        self.engine.set_active_set(set_id)

    def autostart_args(self) -> str:
        """Argumentos do arranque automático (a pasta, se não for a habitual)."""
        from ..__main__ import default_root
        try:
            if Path(self.store.root).resolve() != default_root().resolve():
                return f'--config-dir "{self.store.root}"'
        except OSError:
            pass
        return ""

    def _sync_autostart(self) -> Optional[str]:
        """Põe o arranque com o Windows de acordo com a preferência e confirma
        que ficou aplicado. Devolve None ou a mensagem de erro."""
        want = self.store.settings.arrancar_com_windows
        try:
            if want or self.platform.get_autostart():
                # reescreve sempre ao ativar (o comando pode ter mudado)
                self.platform.set_autostart(want, self.autostart_args())
            if self.platform.get_autostart() != want:
                raise OSError(tr("msg.autostart_blocked"))
        except OSError as e:
            log.exception("não foi possível atualizar o arranque automático")
            return tr("msg.autostart_on_failed" if want else "msg.autostart_off_failed",
                      err=e.strerror or str(e))
        return None

    def _on_files_changed(self, paths) -> None:
        res = self.store.reload(list(paths))
        if res.issues:
            self._report_issues(res.issues, tr("msg.invalid_config"))
        if res.changed:
            log.info("recarregado: %s", ", ".join(res.messages))
            self.apply_config()
            if self.config_window is not None and self.config_window.isVisible():
                self.config_window.reload_from_store(tr("status.reloaded_from_files"),
                                                     changed=paths)

    # ------------------------------------------------------------- motor
    def _on_engine_event(self, ev: str, payload) -> None:
        if ev in ("suspended", "active_set", "config"):
            self._update_tray()
            self.state.suspenso = self.engine.suspended
            self.state.conjunto = self.engine.active_set_id
            self._persist_state()
            if ev != "suspended":
                self.panel.rebuild()
                if (ev == "active_set" and self.config_window is not None
                        and self.config_window.isVisible()):
                    self.config_window.reload_from_store()
            if self.config_window is not None:
                self.config_window.on_engine_state()
            self.panel.refresh_status()
        elif ev == "finished":
            if payload.get("error"):
                self.notify(tr("msg.send_error"), payload["error"], error=True)
            elif payload.get("cancelled") == CANCEL_MODIFIERS:
                self.notify("Macropad", tr("msg.cancel_modifiers", title=payload["title"]),
                            error=True)
            self.panel.refresh_status()
        elif ev == "started":
            self.panel.refresh_status()
        elif ev == "counter":
            self._on_counter(payload)
        elif ev == "toggle_panel":
            self.toggle_panel()

    def _persist_state(self) -> None:
        self.state.suspenso = self.engine.suspended
        self.state.conjunto = self.engine.active_set_id
        self.store.save_state(self.state)

    # ---------------------------------------------------------- instância
    def _on_instance_message(self, server: QLocalServer) -> None:
        sock = server.nextPendingConnection()
        if sock is None:
            return
        sock.waitForReadyRead(500)
        sock.readAll()
        sock.disconnectFromServer()
        self.show_config()

    # -------------------------------------------------------------- saída
    def quit(self) -> None:
        if self.config_window is not None:
            self.config_window.flush()
        self.engine.shutdown()
        self.platform.stop_hook()
        self.watcher.stop()
        self._counts_timer.stop()
        self._persist_state()
        self._theme_poll.stop()
        self.qapp.removeEventFilter(self._styler)
        if self.config_window is not None:
            self.config_window.dispose()
        self.tray.hide()
        self.qapp.quit()
