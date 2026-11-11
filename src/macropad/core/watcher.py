"""Observador de ficheiros por amostragem (polling), portável.

Porquê polling: funciona igual em Windows e Linux, aguenta editores que gravam
substituindo o ficheiro (escrever temporário + renomear) e permite agrupar
eventos próximos de forma simples: um ficheiro só é reportado depois de a sua
assinatura (mtime, tamanho) estar estável durante ``settle`` segundos, o que
também evita ler ficheiros a meio da escrita.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger(__name__)

Signature = Optional[tuple[int, int]]   # (mtime_ns, size) ou None se não existe


class FileWatcher:
    def __init__(self, list_files: Callable[[], list[Path]],
                 on_change: Callable[[list[Path]], None],
                 interval: float = 0.25, settle: float = 0.35,
                 clock: Callable[[], float] = time.monotonic):
        self._list_files = list_files
        self._on_change = on_change
        self.interval = interval
        self.settle = settle
        self._clock = clock
        self._snapshot: dict[Path, Signature] = {}
        self._pending: dict[Path, tuple[Signature, float]] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @staticmethod
    def _sig(p: Path) -> Signature:
        try:
            st = p.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return None

    def _scan(self) -> dict[Path, Signature]:
        return {p: self._sig(p) for p in self._list_files()}

    def prime(self) -> None:
        """Regista o estado atual sem reportar alterações."""
        self._snapshot = self._scan()
        self._pending.clear()

    def poll(self) -> list[Path]:
        """Uma iteração. Devolve (e reporta) os ficheiros estabilizados."""
        now = self._clock()
        current = self._scan()
        # Ficheiros que desapareceram da listagem (apagados) mantêm-se como None.
        for p in self._snapshot:
            current.setdefault(p, self._sig(p))
        for p, sig in current.items():
            if self._snapshot.get(p, "missing") != sig:
                self._pending[p] = (sig, now)
        self._snapshot = {p: s for p, s in current.items() if s is not None}

        ready: list[Path] = []
        for p, (sig, since) in list(self._pending.items()):
            cur = current.get(p)
            if cur != sig:
                self._pending[p] = (cur, now)        # ainda a mudar
            elif now - since >= self.settle:
                ready.append(p)
                del self._pending[p]
        if ready:
            try:
                self._on_change(ready)
            except Exception:
                log.exception("erro ao processar alterações de ficheiros")
        return ready

    def start(self) -> None:
        if self._thread:
            return
        self.prime()

        def run() -> None:
            while not self._stop.wait(self.interval):
                try:
                    self.poll()
                except Exception:
                    log.exception("erro no observador de ficheiros")

        self._thread = threading.Thread(target=run, name="FileWatcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
