"""Modelo de dados da configuração (sem dependências de UI ou do SO)."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field, fields

SCHEMA_VERSION = 1

TEXT_MODES = ("escrever", "colar")          # SendInput Unicode | área de transferência
MODIFIER_MODES = ("exatos", "ignorar")
SCOPE_MODES = ("global", "aplicacoes")
THEMES = ("diurno", "noturno", "automatico")

MAX_REPEAT = 1000
MAX_INTERVAL_MS = 600_000


@dataclass
class Macro:
    titulo: str = ""
    tecla: str = ""            # associação canónica ("1", "Ctrl+F1") ou "" (só painel)
    texto: str = ""
    repeticoes: int = 1
    intervalo_ms: int = 0
    arquivada: bool = False    # fora da execução por tecla e do painel

    def display_title(self) -> str:
        if self.titulo.strip():
            return self.titulo
        t = self.texto.replace("\n", " ").strip()
        return t[:12] if t else "…"


@dataclass
class Scope:
    modo: str = "global"
    aplicacoes: list[str] = field(default_factory=list)


@dataclass
class MacroSet:
    id: str                    # nome do ficheiro sem extensão
    nome: str
    ambito: Scope = field(default_factory=Scope)
    macros: list[Macro] = field(default_factory=list)

    def clone(self) -> "MacroSet":
        return copy.deepcopy(self)

    def active_indices(self) -> list[int]:
        return [i for i, m in enumerate(self.macros) if not m.arquivada]

    def archived_indices(self) -> list[int]:
        return [i for i, m in enumerate(self.macros) if m.arquivada]


@dataclass
class PanelSettings:
    """Aparência e comportamento do painel. Os nomes coincidem com as chaves da
    tabela [painel] do config.toml. A predefinição é o aspeto original."""
    sempre_por_cima: bool = True
    opacidade: float = 0.92
    colunas: int = 4
    tamanho_botao: int = 78
    espacamento: int = 6
    arredondamento: int = 17      # % do lado (0 = quadrado, 50 = círculo)
    borda: int = 2                # px
    escala_texto: int = 100       # %
    cor_fundo: str = ""           # "" = segue o tema
    cor_botao: str = "#000000"
    cor_texto: str = "#ffffff"
    cor_borda: str = "#5a5a5a"
    mostrar_icone: bool = True
    mostrar_tecla: bool = True
    mostrar_estado: bool = True

    def clone(self) -> "PanelSettings":
        return copy.deepcopy(self)

    def style_fields(self) -> list[str]:
        """Campos de aparência (os que as predefinições de estilo alteram)."""
        return [f.name for f in fields(self)
                if f.name not in ("sempre_por_cima", "opacidade", "colunas")]


# (mínimo, máximo) dos campos numéricos do painel
PANEL_RANGES: dict[str, tuple[float, float]] = {
    "opacidade": (0.2, 1.0), "colunas": (1, 12), "tamanho_botao": (40, 160),
    "espacamento": (0, 30), "arredondamento": (0, 50), "borda": (0, 8),
    "escala_texto": (60, 180),
}
PANEL_COLORS = ("cor_fundo", "cor_botao", "cor_texto", "cor_borda")

# Estilos predefinidos do painel. "predefinido" repõe o aspeto original.
PANEL_PRESETS: dict[str, dict] = {
    "predefinido": {},
    "compacto": {"tamanho_botao": 56, "espacamento": 3, "arredondamento": 14,
                 "mostrar_icone": False, "escala_texto": 95},
    "grande": {"tamanho_botao": 112, "espacamento": 10, "arredondamento": 14,
               "escala_texto": 115},
    "claro": {"cor_fundo": "#e9e9ee", "cor_botao": "#ffffff", "cor_texto": "#1b1b1f",
              "cor_borda": "#c4c4cc", "arredondamento": 18},
    "neon": {"cor_fundo": "#070a14", "cor_botao": "#0b1020", "cor_texto": "#00e5ff",
             "cor_borda": "#00e5ff", "arredondamento": 26, "borda": 2},
    "redondo": {"arredondamento": 50, "espacamento": 8, "mostrar_tecla": False},
    "minimalista": {"borda": 0, "mostrar_icone": False, "cor_botao": "#2a2a2e",
                    "arredondamento": 8, "espacamento": 4},
}


def apply_preset(p: PanelSettings, preset: str) -> PanelSettings:
    """Aplica uma predefinição de estilo, mantendo colunas, opacidade e
    'sempre por cima'."""
    base = PanelSettings()
    out = p.clone()
    for name in out.style_fields():
        setattr(out, name, getattr(base, name))
    for k, v in PANEL_PRESETS.get(preset, {}).items():
        setattr(out, k, v)
    return out


def matching_preset(p: PanelSettings) -> str:
    """Nome da predefinição que coincide com o estilo atual ("" se nenhuma)."""
    for name in PANEL_PRESETS:
        q = apply_preset(p, name)
        if all(getattr(q, f) == getattr(p, f) for f in p.style_fields()):
            return name
    return ""


@dataclass
class Settings:
    arrancar_com_windows: bool = True
    modo_texto: str = "escrever"
    modificadores: str = "exatos"
    tecla_suspensao: str = "Ctrl+Alt+P"
    tema: str = "diurno"
    idioma: str = "pt"
    confirmar_eliminacao: bool = True
    painel: PanelSettings = field(default_factory=PanelSettings)

    def clone(self) -> "Settings":
        return copy.deepcopy(self)


@dataclass
class Config:
    settings: Settings
    sets: dict[str, MacroSet]          # por id

    def ordered_sets(self) -> list[MacroSet]:
        return sorted(self.sets.values(), key=lambda s: (s.nome.lower(), s.id))


@dataclass
class State:
    """Estado de sessão (não é configuração; não é observado)."""
    suspenso: bool = False
    conjunto: str = ""
    painel_visivel: bool = False


def app_matches(entry: str, exe_path: str) -> bool:
    """Compara uma entrada da lista de aplicações com o executável em primeiro
    plano. Entradas só com o nome (``notepad.exe``) comparam o nome do ficheiro;
    entradas com caminho comparam o caminho completo. Sem distinção de
    maiúsculas/minúsculas."""
    if not entry or not exe_path:
        return False
    e = entry.strip().replace("/", "\\").lower()
    p = exe_path.strip().replace("/", "\\").lower()
    if "\\" in e:
        return e == p
    return e == p.rsplit("\\", 1)[-1]


def scope_allows(scope: Scope, exe_path: str) -> bool:
    if scope.modo == "global":
        return True
    return any(app_matches(a, exe_path) for a in scope.aplicacoes)
