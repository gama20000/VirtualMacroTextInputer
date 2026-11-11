"""Motor de macros: decide que teclas suprimir, executa macros e gere a
suspensão. Não depende do Qt nem do Windows; recebe uma implementação de
``PlatformAPI``.

Threads:
* ``handle_key`` é chamado pela thread do hook de teclado e tem de ser rápido
  (o Windows remove hooks que demoram demasiado). Nunca bloqueia: a execução
  corre numa thread própria.
* ``trigger`` é chamado pela interface (painel).
* Os ouvintes (``add_listener``) são chamados a partir de qualquer thread; a
  interface reencaminha-os para a thread principal.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

from ..i18n import tr
from .commands import DelayStep, KeyStep, Step, TextStep, parse_action
from .keys import Binding, KeyBindingError, parse_binding
from .model import Config, MacroSet, Settings, scope_allows

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Interface com o sistema operativo
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class WindowInfo:
    handle: int
    pid: int
    exe: str          # caminho completo do executável ("" se desconhecido)


class PlatformAPI(Protocol):
    def foreground(self) -> Optional[WindowInfo]: ...
    def own_pid(self) -> int: ...
    def send_text(self, text: str, mode: str) -> None: ...
    def send_key(self, key: str) -> None: ...
    def modifiers_down(self) -> frozenset[str]: ...


@dataclass(frozen=True)
class KeyEvent:
    key: Optional[str]                 # nome canónico (None = tecla não mapeada)
    down: bool
    mods: frozenset[str] = frozenset()
    ours: bool = False                 # gerado pelo próprio Macropad
    is_modifier: bool = False


# --------------------------------------------------------------------------
# Execução
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class MacroPlan:
    """Cópia imutável do necessário para executar (não muda com recarregamentos)."""
    title: str
    steps: tuple[Step, ...]
    repeat: int
    interval_ms: int
    text_mode: str


CANCEL_SUSPEND = "suspensão"
CANCEL_WINDOW = "mudança de janela"
CANCEL_SHUTDOWN = "saída"


class Execution:
    POLL = 0.03            # granularidade das esperas (verifica janela/cancelamento)
    CHUNK = 24             # caracteres por envio no modo "escrever"
    MOD_WAIT = 1.5         # espera máxima pela libertação de Ctrl/Alt/Shift/Win

    def __init__(self, plan: MacroPlan, target: WindowInfo, platform: PlatformAPI,
                 on_done: Callable[["Execution"], None]):
        self.plan = plan
        self.target = target
        self.platform = platform
        self._on_done = on_done
        self._cancel = threading.Event()
        self.cancel_reason: Optional[str] = None
        self.error: Optional[BaseException] = None
        self.completed_steps = 0
        self.completed_reps = 0
        self.index = -1
        self.thread = threading.Thread(target=self._run, name="MacroExecution", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def cancel(self, reason: str) -> None:
        if not self._cancel.is_set():
            self.cancel_reason = reason
            self._cancel.set()

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def _same_window(self) -> bool:
        fg = self.platform.foreground()
        return fg is not None and fg.handle == self.target.handle

    def _check(self) -> bool:
        """True se pode continuar."""
        if self._cancel.is_set():
            return False
        if not self._same_window():
            self.cancel(CANCEL_WINDOW)
            return False
        return True

    def _sleep(self, ms: int) -> bool:
        end = time.monotonic() + ms / 1000.0
        while True:
            if not self._check():
                return False
            left = end - time.monotonic()
            if left <= 0:
                return True
            if self._cancel.wait(min(self.POLL, left)):
                return False

    def _wait_modifiers(self) -> bool:
        end = time.monotonic() + self.MOD_WAIT
        while self.platform.modifiers_down() and time.monotonic() < end:
            if self._cancel.wait(0.015):
                return False
        return not self._cancel.is_set()

    def _run(self) -> None:
        try:
            if not self._wait_modifiers():
                return
            for rep in range(self.plan.repeat):
                if rep > 0 and not self._sleep(self.plan.interval_ms):
                    return
                for step in self.plan.steps:
                    if not self._check():
                        return
                    if isinstance(step, TextStep):
                        if self.plan.text_mode == "colar":
                            self.platform.send_text(step.text, "colar")
                        else:
                            t = step.text
                            for i in range(0, len(t), self.CHUNK):
                                if i and not self._check():
                                    return
                                self.platform.send_text(t[i:i + self.CHUNK], "escrever")
                    elif isinstance(step, KeyStep):
                        self.platform.send_key(step.key)
                    elif isinstance(step, DelayStep):
                        if not self._sleep(step.ms):
                            return
                    self.completed_steps += 1
                self.completed_reps += 1
        except BaseException as e:      # noqa: BLE001 - reportado ao ouvinte
            self.error = e
            log.exception("erro durante a execução da macro")
        finally:
            self._on_done(self)

    def join(self, timeout: Optional[float] = None) -> None:
        self.thread.join(timeout)


# --------------------------------------------------------------------------
# Motor
# --------------------------------------------------------------------------
@dataclass
class _ActiveSet:
    ms: MacroSet
    bindings: dict[Binding, int] = field(default_factory=dict)
    plans: list[Optional[MacroPlan]] = field(default_factory=list)


class Engine:
    def __init__(self, platform: PlatformAPI):
        self.platform = platform
        self._lock = threading.RLock()
        self._config: Optional[Config] = None
        self._settings = Settings()
        self._active: Optional[_ActiveSet] = None
        self._active_id = ""
        self._suspended = False
        self._hotkey: Optional[Binding] = None
        self._running: Optional[Execution] = None
        self._held: set[str] = set()        # teclas cujo keydown foi suprimido
        self._passed: set[str] = set()      # teclas premidas que passaram normalmente
        self.capture_mode = False           # a interface está a capturar uma tecla
        self._last_reason = ""
        self._listeners: list[Callable[[str, dict], None]] = []

    # ------------------------------------------------------------ ouvintes
    def add_listener(self, fn: Callable[[str, dict], None]) -> None:
        self._listeners.append(fn)

    def _emit(self, event: str, **payload) -> None:
        for fn in list(self._listeners):
            try:
                fn(event, payload)
            except Exception:
                log.exception("erro num ouvinte do motor")

    # ---------------------------------------------------------- configuração
    def set_config(self, config: Config) -> None:
        """Aplica uma configuração. Não altera o estado ativo/suspenso; uma
        execução em curso continua com o plano com que começou."""
        with self._lock:
            self._config = config
            self._settings = config.settings
            try:
                self._hotkey = parse_binding(config.settings.tecla_suspensao)
            except KeyBindingError:
                self._hotkey = None
            if self._active_id not in config.sets:
                ordered = config.ordered_sets()
                self._active_id = ordered[0].id if ordered else ""
            self._rebuild_active()
        self._emit("config")

    def _rebuild_active(self) -> None:
        cfg = self._config
        if not cfg or self._active_id not in cfg.sets:
            self._active = None
            return
        ms = cfg.sets[self._active_id]
        act = _ActiveSet(ms)
        for i, m in enumerate(ms.macros):
            if m.arquivada:                 # arquivadas: fora das teclas e do painel
                act.plans.append(None)
                continue
            try:
                steps = tuple(parse_action(m.texto))
            except ValueError:
                steps = ()
            act.plans.append(MacroPlan(m.display_title(), steps, m.repeticoes,
                                       m.intervalo_ms, self._settings.modo_texto)
                             if steps else None)
            if steps and m.tecla:
                try:
                    act.bindings.setdefault(parse_binding(m.tecla), i)
                except KeyBindingError:
                    pass
        self._active = act

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def active_set_id(self) -> str:
        return self._active_id

    @property
    def active_set(self) -> Optional[MacroSet]:
        a = self._active
        return a.ms if a else None

    def set_active_set(self, set_id: str) -> None:
        with self._lock:
            if self._config and set_id in self._config.sets:
                self._active_id = set_id
                self._rebuild_active()
        self._emit("active_set", set_id=self._active_id)

    # ------------------------------------------------------------ suspensão
    @property
    def suspended(self) -> bool:
        return self._suspended

    def set_suspended(self, value: bool) -> None:
        with self._lock:
            changed = value != self._suspended
            self._suspended = value
            run = self._running
        if value and run is not None:
            run.cancel(CANCEL_SUSPEND)
        if changed:
            self._emit("suspended", suspended=value)

    def toggle_suspended(self) -> None:
        self.set_suspended(not self._suspended)

    # ------------------------------------------------------------- execução
    @property
    def running(self) -> Optional[Execution]:
        return self._running

    def _target_ok(self, fg: Optional[WindowInfo]) -> tuple[bool, str]:
        """(ok, motivo traduzido). ``self._last_reason`` guarda o código."""
        if fg is None:
            self._last_reason = "no_window"
            return False, tr("eng.no_window")
        if fg.pid == self.platform.own_pid():
            self._last_reason = "own"
            return False, tr("eng.own_window")
        act = self._active
        if act is None:
            self._last_reason = "no_set"
            return False, tr("eng.no_set")
        if not scope_allows(act.ms.ambito, fg.exe):
            self._last_reason = "scope"
            name = fg.exe.replace("/", "\\").rsplit("\\", 1)[-1] or "?"
            return False, tr("eng.out_of_scope", app=name)
        self._last_reason = ""
        return True, ""

    def status(self) -> tuple[str, str]:
        """Estado para o painel: (código, descrição).
        código ∈ {"suspenso", "ativo", "fora", "executar"}"""
        if self._suspended:
            return "suspenso", tr("eng.status_suspended")
        if self._running is not None:
            return "executar", tr("eng.status_running", title=self._running.plan.title)
        ok, why = self._target_ok(self.platform.foreground())
        if ok or self._last_reason == "own":
            return "ativo", tr("eng.status_active")
        return "fora", why[0].upper() + why[1:]

    def _start(self, index: int, target: WindowInfo, source: str) -> bool:
        with self._lock:
            if self._running is not None:
                return False         # ignora disparos durante uma execução
            act = self._active
            if act is None or index >= len(act.plans) or act.plans[index] is None:
                return False
            plan = act.plans[index]
            exe = Execution(plan, target, self.platform, self._finished)
            exe.index = index
            self._running = exe
        self._emit("started", title=plan.title, index=index, source=source)
        exe.start()
        return True

    def _finished(self, exe: Execution) -> None:
        with self._lock:
            if self._running is exe:
                self._running = None
        self._emit("finished", title=exe.plan.title, cancelled=exe.cancel_reason,
                   error=str(exe.error) if exe.error else None)

    def trigger(self, index: int, source: str = "painel") -> tuple[bool, str]:
        """Executa a macro ``index`` do conjunto ativo (painel)."""
        if self._suspended:
            return False, tr("eng.suspended")
        act = self._active
        if act is not None and 0 <= index < len(act.ms.macros):
            if act.ms.macros[index].arquivada:
                return False, tr("eng.archived")
            if act.plans[index] is None:
                return False, tr("eng.empty")
        fg = self.platform.foreground()
        ok, why = self._target_ok(fg)
        if not ok:
            return False, why
        if self._running is not None:
            return False, tr("eng.busy")
        assert fg is not None
        return (True, "") if self._start(index, fg, source) else (False, tr("eng.not_run"))

    def shutdown(self) -> None:
        run = self._running
        if run:
            run.cancel(CANCEL_SHUTDOWN)
            run.join(1.0)

    # ------------------------------------------------------- hook de teclado
    def handle_key(self, ev: KeyEvent) -> bool:
        """Devolve True se o evento deve ser suprimido."""
        if ev.ours or ev.key is None or ev.is_modifier:
            return False
        key = ev.key
        if not ev.down:
            if key in self._held:
                self._held.discard(key)
                return True
            self._passed.discard(key)
            return False

        # Auto-repetição de uma tecla já premida: mantém a decisão inicial.
        if key in self._held:
            return True
        if key in self._passed:
            return False

        if self.capture_mode:
            self._passed.add(key)
            return False

        hk = self._hotkey
        if hk is not None and hk.key == key and hk.mods == ev.mods:
            self._held.add(key)
            self.toggle_suspended()
            return True

        if self._suspended:
            self._passed.add(key)
            return False

        act = self._active
        if act is None:
            self._passed.add(key)
            return False
        b = Binding(key, ev.mods)
        idx = act.bindings.get(b)
        if idx is None and ev.mods and self._settings.modificadores == "ignorar":
            idx = act.bindings.get(Binding(key))
        if idx is None:
            self._passed.add(key)
            return False

        fg = self.platform.foreground()
        ok, _why = self._target_ok(fg)
        if not ok:
            self._passed.add(key)
            return False

        self._held.add(key)
        assert fg is not None
        self._start(idx, fg, "tecla")   # ignorado se já houver uma execução
        return True
