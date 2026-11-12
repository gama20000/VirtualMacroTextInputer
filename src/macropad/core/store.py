"""Gestão dos ficheiros de configuração em disco.

* Mantém a última versão válida de cada ficheiro.
* Grava de forma atómica (ficheiro temporário + ``os.replace``).
* Regista o hash do conteúdo gravado/aplicado para que o observador de
  ficheiros não provoque recarregamentos em ciclo.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import tempfile
import threading
import time
import tomllib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .configio import (ConfigError, Issue, dump_settings, dump_set, parse_set,
                       parse_settings, toml_str, validate_macros)
from ..i18n import tr
from .model import LEGACY_HOTKEY, Config, Macro, MacroSet, Scope, Settings, State

log = logging.getLogger(__name__)

CONFIG_NAME = "config.toml"
SETS_DIR = "conjuntos"
STATE_NAME = "estado.toml"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, text: str) -> bytes:
    """Escreve ``text`` em ``path`` de forma atómica. Devolve os bytes gravados."""
    data = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        for attempt in range(20):
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                # No Windows, outro processo (antivírus, editor) pode ter o
                # ficheiro aberto momentaneamente.
                if attempt == 19:
                    raise
                time.sleep(0.05)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return data


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "conjunto"


def default_set() -> MacroSet:
    return MacroSet(
        id="predefinido",
        nome=tr("store.default_set_name"),
        ambito=Scope("global", []),
        macros=[
            Macro("3E03305", "1", "3E03305"),
            Macro("Z51.11", "2", "Z51.11{Enter}"),
            Macro("C50.912", "3", "C50.912"),
            Macro(tr("store.example_title"), "4", "ABC{Tab}DEF{Delay:500}{Enter}"),
        ],
    )


@dataclass
class ReloadResult:
    changed: bool = False
    issues: list[Issue] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


class ConfigStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.config_path = self.root / CONFIG_NAME
        self.sets_dir = self.root / SETS_DIR
        self.state_path = self.root / STATE_NAME
        self.settings = Settings()
        self.sets: dict[str, MacroSet] = {}
        self._known_hash: dict[Path, str] = {}     # último conteúdo aplicado/gravado
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ util
    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def set_path(self, set_id: str) -> Path:
        return self.sets_dir / f"{set_id}.toml"

    def config(self) -> Config:
        with self._lock:
            return Config(self.settings.clone(), {k: v.clone() for k, v in self.sets.items()})

    def watched_files(self) -> list[Path]:
        files = [self.config_path]
        if self.sets_dir.is_dir():
            files += sorted(p for p in self.sets_dir.glob("*.toml")
                            if not p.name.startswith("."))
        return files

    @staticmethod
    def is_watched_name(path: Path, root: Path) -> bool:
        if path.name.startswith(".") or path.suffix.lower() != ".toml":
            return False
        if path.parent == root and path.name == CONFIG_NAME:
            return True
        return path.parent == root / SETS_DIR

    # -------------------------------------------------------------- arranque
    def ensure_defaults(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.sets_dir.mkdir(exist_ok=True)
        if not self.config_path.exists():
            self._write(self.config_path, dump_settings(Settings()))
        if not any(p for p in self.sets_dir.glob("*.toml") if not p.name.startswith(".")):
            ds = default_set()
            self._write(self.set_path(ds.id), dump_set(ds))

    def load_all(self) -> list[Issue]:
        """Carrega tudo. Ficheiros inválidos são ignorados (e reportados)."""
        with self._lock:
            issues: list[Issue] = []
            self.settings = Settings()
            self.sets = {}
            self._known_hash.clear()
            if self.config_path.exists():
                data = self.config_path.read_bytes()
                try:
                    self.settings = parse_settings(data.decode("utf-8-sig"),
                                                   self.rel(self.config_path))
                    self._known_hash[self.config_path] = _hash(data)
                except ConfigError as e:
                    issues += e.issues
                except UnicodeDecodeError:
                    issues.append(Issue(self.rel(self.config_path), tr("store.not_utf8")))
            for p in self.watched_files()[1:]:
                issues += self._load_set_file(p)
            return issues

    def _load_set_file(self, p: Path) -> list[Issue]:
        data = p.read_bytes()
        try:
            ms = parse_set(data.decode("utf-8-sig"), p.stem, self.rel(p))
        except ConfigError as e:
            return e.issues
        except UnicodeDecodeError:
            return [Issue(self.rel(p), tr("store.not_utf8"))]
        cross = validate_macros(ms.clone(), self.settings, self.rel(p),
                                data.decode("utf-8-sig"))
        if cross:
            return cross
        self.sets[ms.id] = ms
        self._known_hash[p] = _hash(data)
        return []

    # -------------------------------------------------------- recarregamento
    def reload(self, paths: list[Path]) -> ReloadResult:
        """Aplica alterações externas aos ficheiros indicados.

        Cada ficheiro é validado isoladamente; um ficheiro inválido não
        substitui a última versão válida."""
        res = ReloadResult()
        with self._lock:
            # config.toml primeiro: os conjuntos são validados contra ele.
            ordered = sorted(set(paths), key=lambda p: (p != self.config_path, str(p)))
            for p in ordered:
                if p == self.config_path:
                    self._reload_settings(res)
                elif p.parent == self.sets_dir:
                    self._reload_set(p, res)
        return res

    def _reload_settings(self, res: ReloadResult) -> None:
        p = self.config_path
        if not p.exists():
            res.issues.append(Issue(self.rel(p), tr("store.config_removed")))
            return
        data = p.read_bytes()
        h = _hash(data)
        if self._known_hash.get(p) == h:
            return
        try:
            new = parse_settings(data.decode("utf-8-sig"), self.rel(p))
        except ConfigError as e:
            res.issues += e.issues
            return
        except UnicodeDecodeError:
            res.issues.append(Issue(self.rel(p), tr("store.not_utf8")))
            return
        # Conflitos da nova tecla de suspensão com os conjuntos existentes.
        conflicts: list[Issue] = []
        for ms in self.sets.values():
            conflicts += validate_macros(ms.clone(), new, self.rel(self.set_path(ms.id)))
        if conflicts:
            res.issues.append(Issue(self.rel(p), tr("store.rejected_conflict"),
                                    *locate_hotkey(data)))
            res.issues += conflicts
            return
        self.settings = new
        self._known_hash[p] = h
        res.changed = True
        res.messages.append(tr("store.reloaded", file=self.rel(p)))

    def _reload_set(self, p: Path, res: ReloadResult) -> None:
        if not p.exists():
            if p.stem in self.sets:
                del self.sets[p.stem]
                self._known_hash.pop(p, None)
                res.changed = True
                res.messages.append(tr("store.set_removed", file=self.rel(p)))
            return
        data = p.read_bytes()
        h = _hash(data)
        if self._known_hash.get(p) == h:
            return
        issues = self._load_set_file(p)
        if issues:
            res.issues += issues
            return
        res.changed = True
        res.messages.append(tr("store.reloaded", file=self.rel(p)))

    # -------------------------------------------------------------- gravação
    def _write(self, path: Path, text: str) -> None:
        data = atomic_write(path, text)
        self._known_hash[path] = _hash(data)

    def save_settings(self, s: Settings) -> list[Issue]:
        with self._lock:
            issues: list[Issue] = []
            for ms in self.sets.values():
                issues += validate_macros(ms.clone(), s, self.rel(self.set_path(ms.id)))
            if issues:
                return issues
            self.settings = s.clone()
            self._write(self.config_path, dump_settings(s))
            return []

    def save_set(self, ms: MacroSet) -> list[Issue]:
        with self._lock:
            ms = ms.clone()
            issues = validate_macros(ms, self.settings, self.rel(self.set_path(ms.id)))
            if not ms.nome.strip():
                issues.append(Issue(self.rel(self.set_path(ms.id)), tr("store.set_name_empty")))
            if ms.ambito.modo == "aplicacoes" and not ms.ambito.aplicacoes:
                issues.append(Issue(self.rel(self.set_path(ms.id)), tr("store.scope_need_app")))
            if issues:
                return issues
            self._write(self.set_path(ms.id), dump_set(ms))
            self.sets[ms.id] = ms
            return []

    def unique_id(self, name: str) -> str:
        base = slugify(name)
        cand, n = base, 2
        while cand in self.sets or self.set_path(cand).exists():
            cand = f"{base}-{n}"
            n += 1
        return cand

    def unique_name(self, name: str) -> str:
        names = {s.nome.lower() for s in self.sets.values()}
        cand, n = name, 2
        while cand.lower() in names:
            cand = f"{name} ({n})"
            n += 1
        return cand

    def create_set(self, name: str) -> MacroSet:
        with self._lock:
            name = self.unique_name(name.strip() or tr("store.new_set_name"))
            ms = MacroSet(self.unique_id(name), name, Scope(), [])
            self._write(self.set_path(ms.id), dump_set(ms))
            self.sets[ms.id] = ms
            return ms.clone()

    def duplicate_set(self, set_id: str) -> MacroSet:
        with self._lock:
            src = self.sets[set_id].clone()
            src.nome = self.unique_name(tr("store.copy_name", name=src.nome))
            src.id = self.unique_id(src.nome)
            self._write(self.set_path(src.id), dump_set(src))
            self.sets[src.id] = src
            return src.clone()

    def delete_set(self, set_id: str) -> None:
        with self._lock:
            p = self.set_path(set_id)
            self.sets.pop(set_id, None)
            self._known_hash.pop(p, None)
            try:
                p.unlink()
            except FileNotFoundError:
                pass

    def import_set(self, src: Path) -> MacroSet:
        """Importa um ficheiro de conjunto (valida antes de copiar)."""
        text = Path(src).read_bytes().decode("utf-8-sig")
        with self._lock:
            ms = parse_set(text, slugify(Path(src).stem), Path(src).name)
            issues = validate_macros(ms, self.settings, Path(src).name, text)
            if issues:
                raise ConfigError(issues)
            ms.nome = self.unique_name(ms.nome)
            ms.id = self.unique_id(ms.nome)
            self._write(self.set_path(ms.id), dump_set(ms))
            self.sets[ms.id] = ms
            return ms.clone()

    def export_set(self, set_id: str, dest: Path) -> None:
        with self._lock:
            atomic_write(Path(dest), dump_set(self.sets[set_id]))

    # ---------------------------------------------------------------- estado
    def load_state(self) -> State:
        st = State()
        try:
            data = tomllib.loads(self.state_path.read_text("utf-8"))
            st.suspenso = bool(data.get("suspenso", False))
            st.conjunto = str(data.get("conjunto", ""))
            st.painel_visivel = bool(data.get("painel_visivel", False))
            px, py = data.get("painel_x"), data.get("painel_y")
            if isinstance(px, int) and isinstance(py, int):
                st.painel_x, st.painel_y = px, py
            cont = data.get("contadores", {})
            if isinstance(cont, dict):
                st.contadores = {str(k): int(v) for k, v in cont.items()
                                 if isinstance(v, int) and not isinstance(v, bool)}
            mig = data.get("migracoes", [])
            if isinstance(mig, list):
                st.migracoes = [str(x) for x in mig]
        except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError, ValueError):
            pass
        return st

    def save_state(self, st: State) -> None:
        lines = ["# Estado da última sessão (gerido pelo Macropad; não é observado).",
                 f"suspenso = {'true' if st.suspenso else 'false'}",
                 f"conjunto = {toml_str(st.conjunto)}",
                 f"painel_visivel = {'true' if st.painel_visivel else 'false'}"]
        if st.painel_x is not None and st.painel_y is not None:
            lines += [f"painel_x = {int(st.painel_x)}", f"painel_y = {int(st.painel_y)}"]
        lines.append("migracoes = [" + ", ".join(toml_str(m) for m in st.migracoes) + "]")
        lines += ["", "[contadores]"]
        lines += [f"{toml_str(k)} = {int(v)}" for k, v in sorted(st.contadores.items())]
        try:
            atomic_write(self.state_path, "\n".join(lines) + "\n")
        except OSError:
            log.exception("não foi possível gravar o estado")

    # ------------------------------------------------------------ migrações
    MIGRATION_HOTKEY = "tecla_suspensao_v04"

    def migrate(self, st: State) -> list[str]:
        """Migrações únicas da configuração. Devolve mensagens a mostrar."""
        msgs: list[str] = []
        if self.MIGRATION_HOTKEY not in st.migracoes:
            if self.settings.tecla_suspensao == LEGACY_HOTKEY:
                new = self.settings.clone()
                new.tecla_suspensao = Settings().tecla_suspensao
                if not self.save_settings(new):
                    msgs.append(tr("store.migrated_hotkey", old=LEGACY_HOTKEY,
                                   new=new.tecla_suspensao))
            st.migracoes.append(self.MIGRATION_HOTKEY)
        return msgs


def locate_hotkey(data: bytes) -> tuple[Optional[int], Optional[int]]:
    from .configio import locate
    return locate(data.decode("utf-8", "replace"), "geral", "tecla_suspensao")
