"""Leitura, validação e escrita dos ficheiros TOML.

Ficheiros:

* ``config.toml``            – preferências gerais e do painel
* ``conjuntos/<id>.toml``    – um ficheiro por conjunto de macros

A leitura usa ``tomllib`` (biblioteca padrão). A escrita é feita aqui, com um
formato estável e comentado, para que os ficheiros continuem fáceis de editar
à mão. Os nomes dos campos TOML ficam sempre em português (são o formato do
ficheiro); as mensagens de erro seguem o idioma da interface.
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, fields
from typing import Any, Optional

from ..i18n import available as available_languages
from ..i18n import tr
from .commands import CommandError, parse_action
from .keys import KeyBindingError, parse_binding
from .model import (ITEM_TYPES, MAX_INTERVAL_MS, MAX_REPEAT, MODIFIER_MODES, PANEL_COLORS,
                    PANEL_ENUMS, PANEL_OBSOLETE, PANEL_RANGES, RESET_SOUNDS, SCHEMA_VERSION,
                    SCOPE_MODES, TEXT_MODES, THEMES, Macro, MacroSet, PanelSettings, Scope,
                    Settings)

_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass
class Issue:
    file: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    macro_index: Optional[int] = None      # índice (0-based) da macro, se aplicável
    field: Optional[str] = None

    def location(self) -> str:
        loc = self.file
        if self.line is not None:
            loc += tr("loc.line", n=self.line)
            if self.column is not None:
                loc += tr("loc.column", n=self.column)
        return loc

    def __str__(self) -> str:
        return f"{self.location()}: {self.message}" if self.file else self.message


class ConfigError(Exception):
    def __init__(self, issues: list[Issue]):
        super().__init__("\n".join(str(i) for i in issues))
        self.issues = issues


# --------------------------------------------------------------------------
# Localização aproximada de campos no texto (para mensagens de erro)
# --------------------------------------------------------------------------
_ARRAY_HDR = re.compile(r"^\s*\[\[\s*([A-Za-z0-9_.]+)\s*\]\]")
_TABLE_HDR = re.compile(r"^\s*\[\s*([A-Za-z0-9_.]+)\s*\]")


def locate(text: str, section: Optional[str], field: Optional[str] = None,
           index: Optional[int] = None) -> tuple[Optional[int], Optional[int]]:
    """Linha/coluna (1-based) de ``field`` na secção indicada.

    ``section`` None = nível superior; ``index`` para [[arrays]]."""
    cur: Optional[str] = None
    counts: dict[str, int] = {}
    cur_idx: Optional[int] = None
    header_line: Optional[int] = None
    for ln, line in enumerate(text.splitlines(), start=1):
        m = _ARRAY_HDR.match(line)
        if m:
            cur = m.group(1)
            cur_idx = counts.get(cur, 0)
            counts[cur] = cur_idx + 1
            if cur == section and cur_idx == index:
                header_line = ln
            continue
        m = _TABLE_HDR.match(line)
        if m:
            cur, cur_idx = m.group(1), None
            if cur == section and index is None:
                header_line = ln
            continue
        if cur == section and (index is None or cur_idx == index) and field:
            fm = re.match(rf"^(\s*){re.escape(field)}\s*=\s*", line)
            if fm:
                return ln, fm.end() + 1
    return header_line, None


def _toml_error_location(err: tomllib.TOMLDecodeError) -> tuple[Optional[int], Optional[int], str]:
    line = getattr(err, "lineno", None)
    col = getattr(err, "colno", None)
    msg = getattr(err, "msg", None) or str(err)
    m = re.search(r"\(at line (\d+), column (\d+)\)", str(err))
    if m:
        line = line or int(m.group(1))
        col = col or int(m.group(2))
        msg = re.sub(r"\s*\(at line \d+, column \d+\)", "", msg)
    elif "(at end of document)" in str(err):
        msg = msg.replace(" (at end of document)", "") + tr("toml.end_of_document")
    return line, col, msg


def parse_toml(text: str, file: str) -> dict[str, Any]:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        line, col, msg = _toml_error_location(e)
        raise ConfigError([Issue(file, tr("toml.invalid", msg=msg), line, col)])


# --------------------------------------------------------------------------
# Helpers de validação
# --------------------------------------------------------------------------
class _Ctx:
    def __init__(self, file: str, text: str):
        self.file = file
        self.text = text
        self.issues: list[Issue] = []

    def add(self, msg: str, section: Optional[str] = None, field: Optional[str] = None,
            index: Optional[int] = None) -> None:
        line, col = locate(self.text, section, field, index)
        self.issues.append(Issue(self.file, msg, line, col,
                                 macro_index=index if section == "macros" else None,
                                 field=field))


def _type_name(typ) -> str:
    if isinstance(typ, tuple):
        return tr("type.number")
    return {str: tr("type.text"), bool: tr("type.bool"), int: tr("type.int"),
            list: tr("type.list")}.get(typ, tr("type.number"))


def _check_unknown(ctx: _Ctx, table: dict, allowed: set[str], section: Optional[str],
                   index: Optional[int] = None, where: str = "") -> None:
    for k in table:
        if k not in allowed:
            ctx.add(tr("cfg.unknown_field", key=k, where=where,
                       allowed=", ".join(sorted(allowed))), section, k, index)


def _get(ctx: _Ctx, table: dict, key: str, typ, default, section, index=None, where=""):
    if key not in table:
        return default
    v = table[key]
    ok = isinstance(v, typ) and not (typ in (int, (int, float)) and isinstance(v, bool))
    if not ok:
        ctx.add(tr("cfg.wrong_type", key=key, where=where, type=_type_name(typ)),
                section, key, index)
        return default
    return v


def _enum(ctx: _Ctx, value: str, options, field: str, section: str) -> bool:
    if value in options:
        return True
    opts = tr("word.or").join(repr(o) for o in options)
    ctx.add(tr("cfg.bad_option", field=field, value=value, options=opts), section, field)
    return False


def _check_schema(ctx: _Ctx, data: dict) -> None:
    v = data.get("versao_esquema")
    if v is None:
        ctx.add(tr("cfg.schema_missing"), None, None)
    elif not isinstance(v, int) or isinstance(v, bool):
        ctx.add(tr("cfg.schema_type"), None, "versao_esquema")
    elif v > SCHEMA_VERSION:
        ctx.add(tr("cfg.schema_newer", v=v, max=SCHEMA_VERSION), None, "versao_esquema")
    elif v < 1:
        ctx.add(tr("cfg.schema_invalid"), None, "versao_esquema")


# --------------------------------------------------------------------------
# config.toml
# --------------------------------------------------------------------------
_GERAL_FIELDS = {"arrancar_com_windows", "modo_texto", "modificadores", "tecla_suspensao",
                 "tecla_painel", "tema", "idioma", "confirmar_eliminacao",
                 "avisar_conflito_tecla"}


def parse_settings(text: str, file: str = "config.toml") -> Settings:
    data = parse_toml(text, file)
    ctx = _Ctx(file, text)
    _check_schema(ctx, data)
    _check_unknown(ctx, data, {"versao_esquema", "geral", "painel"}, None)
    s = Settings()
    geral = data.get("geral", {})
    painel = data.get("painel", {})
    if not isinstance(geral, dict):
        ctx.add(tr("cfg.not_table", name="geral"), None, "geral"); geral = {}
    if not isinstance(painel, dict):
        ctx.add(tr("cfg.not_table", name="painel"), None, "painel"); painel = {}

    _check_unknown(ctx, geral, _GERAL_FIELDS, "geral")
    s.arrancar_com_windows = _get(ctx, geral, "arrancar_com_windows", bool,
                                  s.arrancar_com_windows, "geral")
    s.confirmar_eliminacao = _get(ctx, geral, "confirmar_eliminacao", bool,
                                  s.confirmar_eliminacao, "geral")
    s.avisar_conflito_tecla = _get(ctx, geral, "avisar_conflito_tecla", bool,
                                   s.avisar_conflito_tecla, "geral")
    s.modo_texto = _get(ctx, geral, "modo_texto", str, s.modo_texto, "geral")
    _enum(ctx, s.modo_texto, TEXT_MODES, "modo_texto", "geral")
    s.modificadores = _get(ctx, geral, "modificadores", str, s.modificadores, "geral")
    _enum(ctx, s.modificadores, MODIFIER_MODES, "modificadores", "geral")
    s.tema = _get(ctx, geral, "tema", str, s.tema, "geral")
    _enum(ctx, s.tema, THEMES, "tema", "geral")
    s.idioma = _get(ctx, geral, "idioma", str, s.idioma, "geral")
    _enum(ctx, s.idioma, [c for c, _ in available_languages()], "idioma", "geral")
    hk = _get(ctx, geral, "tecla_suspensao", str, s.tecla_suspensao, "geral")
    try:
        s.tecla_suspensao = str(parse_binding(hk))
    except KeyBindingError as e:
        ctx.add(tr("cfg.hotkey_error", err=e), "geral", "tecla_suspensao")
    pk = _get(ctx, geral, "tecla_painel", str, s.tecla_painel, "geral")
    if pk.strip():
        try:
            s.tecla_painel = str(parse_binding(pk))
        except KeyBindingError as e:
            ctx.add(tr("cfg.panel_key_error", err=e), "geral", "tecla_painel")
    else:
        s.tecla_painel = ""
    if s.tecla_painel and s.tecla_painel == s.tecla_suspensao:
        ctx.add(tr("cfg.hotkeys_equal", key=s.tecla_painel), "geral", "tecla_painel")

    s.painel = _parse_panel(ctx, painel)
    if ctx.issues:
        raise ConfigError(ctx.issues)
    return s


def _parse_panel(ctx: _Ctx, painel: dict) -> PanelSettings:
    p = PanelSettings()
    allowed = {f.name for f in fields(PanelSettings)} | set(PANEL_OBSOLETE)
    _check_unknown(ctx, painel, allowed, "painel")
    for f in fields(PanelSettings):
        cur = getattr(p, f.name)
        if f.name in PANEL_ENUMS:
            v = _get(ctx, painel, f.name, str, cur, "painel")
            if _enum(ctx, v, PANEL_ENUMS[f.name], f.name, "painel"):
                setattr(p, f.name, v)
        elif isinstance(cur, bool):
            setattr(p, f.name, _get(ctx, painel, f.name, bool, cur, "painel"))
        elif isinstance(cur, float):
            v = _get(ctx, painel, f.name, (int, float), cur, "painel")
            lo, hi = PANEL_RANGES[f.name]
            if not (lo <= float(v) <= hi):
                ctx.add(tr("cfg.range", field=f.name, min=lo, max=hi), "painel", f.name)
            else:
                setattr(p, f.name, float(v))
        elif isinstance(cur, int):
            v = _get(ctx, painel, f.name, int, cur, "painel")
            lo, hi = PANEL_RANGES[f.name]
            if not (lo <= v <= hi):
                ctx.add(tr("cfg.range", field=f.name, min=int(lo), max=int(hi)), "painel", f.name)
            else:
                setattr(p, f.name, v)
        else:   # cor
            v = _get(ctx, painel, f.name, str, cur, "painel")
            if v == "" and f.name == "cor_fundo":
                setattr(p, f.name, "")
            elif not _COLOR_RE.match(v):
                ctx.add(tr("cfg.color", field=f.name), "painel", f.name)
            else:
                setattr(p, f.name, v.lower())
    return p


# --------------------------------------------------------------------------
# conjuntos/<id>.toml
# --------------------------------------------------------------------------
_MACRO_FIELDS = {"titulo", "tecla", "texto", "repeticoes", "intervalo_ms", "arquivada",
                 "tipo", "id", "incremento", "reposicao", "pressao_longa_ms",
                 "som_reposicao"}


def parse_set(text: str, set_id: str, file: Optional[str] = None) -> MacroSet:
    file = file or f"conjuntos/{set_id}.toml"
    data = parse_toml(text, file)
    ctx = _Ctx(file, text)
    _check_schema(ctx, data)
    _check_unknown(ctx, data, {"versao_esquema", "nome", "ambito", "macros"}, None)

    nome = _get(ctx, data, "nome", str, set_id, None)
    if not nome.strip():
        ctx.add(tr("set.name_empty"), None, "nome")

    scope = Scope()
    amb = data.get("ambito", {})
    if not isinstance(amb, dict):
        ctx.add(tr("cfg.not_table", name="ambito"), None, "ambito"); amb = {}
    _check_unknown(ctx, amb, {"modo", "aplicacoes"}, "ambito")
    scope.modo = _get(ctx, amb, "modo", str, "global", "ambito")
    _enum(ctx, scope.modo, SCOPE_MODES, "modo", "ambito")
    apps = _get(ctx, amb, "aplicacoes", list, [], "ambito")
    for a in apps:
        if not isinstance(a, str) or not a.strip():
            ctx.add(tr("set.app_entry"), "ambito", "aplicacoes")
            break
    else:
        scope.aplicacoes = [a.strip() for a in apps]
    if scope.modo == "aplicacoes" and not scope.aplicacoes:
        ctx.add(tr("set.apps_empty"), "ambito", "aplicacoes")

    macros: list[Macro] = []
    raw_macros = data.get("macros", [])
    if not isinstance(raw_macros, list):
        ctx.add(tr("set.macros_not_list"), None, "macros")
        raw_macros = []
    for i, m in enumerate(raw_macros):
        where = tr("cfg.where_macro", n=i + 1)
        if not isinstance(m, dict):
            ctx.add(tr("set.macro_invalid", n=i + 1), "macros", None, i)
            continue
        _check_unknown(ctx, m, _MACRO_FIELDS, "macros", i, where)
        mac = Macro()
        mac.titulo = _get(ctx, m, "titulo", str, "", "macros", i, where)
        mac.tecla = _get(ctx, m, "tecla", str, "", "macros", i, where)
        mac.texto = _get(ctx, m, "texto", str, "", "macros", i, where)
        mac.repeticoes = _get(ctx, m, "repeticoes", int, 1, "macros", i, where)
        mac.intervalo_ms = _get(ctx, m, "intervalo_ms", int, 0, "macros", i, where)
        mac.arquivada = _get(ctx, m, "arquivada", bool, False, "macros", i, where)
        mac.tipo = _get(ctx, m, "tipo", str, "texto", "macros", i, where)
        if mac.tipo not in ITEM_TYPES:
            ctx.add(tr("cfg.bad_option", field="tipo", value=mac.tipo,
                       options=tr("word.or").join(repr(t) for t in ITEM_TYPES)),
                    "macros", "tipo", i)
            mac.tipo = "texto"
        mac.id = _get(ctx, m, "id", str, "", "macros", i, where)
        mac.incremento = _get(ctx, m, "incremento", int, 1, "macros", i, where)
        mac.reposicao = _get(ctx, m, "reposicao", int, 0, "macros", i, where)
        mac.pressao_longa_ms = _get(ctx, m, "pressao_longa_ms", int, 800, "macros", i, where)
        mac.som_reposicao = _get(ctx, m, "som_reposicao", str, "", "macros", i, where)
        if mac.som_reposicao not in RESET_SOUNDS:
            ctx.add(tr("cfg.bad_option", field="som_reposicao", value=mac.som_reposicao,
                       options=tr("word.or").join(repr(t) for t in RESET_SOUNDS)),
                    "macros", "som_reposicao", i)
            mac.som_reposicao = ""
        if mac.is_counter and not mac.id.strip():
            # contador escrito à mão sem id: id estável a partir da posição
            mac.id = f"contador-{i + 1}"
        macros.append(mac)

    ms = MacroSet(set_id, nome, scope, macros)
    for iss in validate_macros(ms, file=file, text=text):
        ctx.issues.append(iss)
    if ctx.issues:
        raise ConfigError(ctx.issues)
    return ms


def macro_label(i: int, m: Macro) -> str:
    if m.titulo:
        return tr("mac.label_title", n=i + 1, title=m.titulo)
    return tr("mac.label", n=i + 1)


def validate_macros(ms: MacroSet, settings: Optional[Settings] = None,
                    file: Optional[str] = None, text: str = "") -> list[Issue]:
    """Validação semântica de um conjunto (também usada pela interface).

    Os conflitos de tecla só se verificam entre macros ativas; as arquivadas
    podem partilhar a tecla de uma ativa (o conflito é tratado ao restaurar).
    Normaliza ``tecla`` para a forma canónica quando válida."""
    file = file or f"conjuntos/{ms.id}.toml"
    ctx = _Ctx(file, text)
    seen: dict[str, int] = {}
    hotkey = panel_key = None
    if settings is not None:
        try:
            hotkey = parse_binding(settings.tecla_suspensao)
        except KeyBindingError:
            hotkey = None
        try:
            panel_key = parse_binding(settings.tecla_painel) if settings.tecla_painel else None
        except KeyBindingError:
            panel_key = None
    ids: dict[str, int] = {}
    ignore_mods = settings is not None and settings.modificadores == "ignorar"

    for i, m in enumerate(ms.macros):
        label = macro_label(i, m)
        if m.is_space:
            m.tecla = ""
            if m.arquivada:
                ctx.add(tr("mac.space_archived", label=label), "macros", "arquivada", i)
            continue
        if m.is_counter:
            if m.id in ids:
                ctx.add(tr("mac.counter_id_dup", label=label, other=ids[m.id] + 1),
                        "macros", "id", i)
            ids.setdefault(m.id, i)
            if m.incremento == 0 or not (-1_000_000 <= m.incremento <= 1_000_000):
                ctx.add(tr("mac.counter_step", label=label), "macros", "incremento", i)
            if not (200 <= m.pressao_longa_ms <= 10_000):
                ctx.add(tr("mac.counter_long", label=label), "macros", "pressao_longa_ms", i)
        if len(m.titulo) > 40:
            ctx.add(tr("mac.title_long", label=label), "macros", "titulo", i)
        if m.texto and not m.is_counter:
            try:
                parse_action(m.texto)
            except CommandError as e:
                ctx.add(f"{label}: {e}", "macros", "texto", i)
        if not (1 <= m.repeticoes <= MAX_REPEAT):
            ctx.add(tr("mac.repeat_range", label=label, max=MAX_REPEAT),
                    "macros", "repeticoes", i)
        if not (0 <= m.intervalo_ms <= MAX_INTERVAL_MS):
            ctx.add(tr("mac.interval_range", label=label, max=MAX_INTERVAL_MS),
                    "macros", "intervalo_ms", i)
        if not m.tecla.strip():
            m.tecla = ""
            continue
        try:
            b = parse_binding(m.tecla)
        except KeyBindingError as e:
            ctx.add(f"{label}: {e}", "macros", "tecla", i)
            continue
        m.tecla = key = str(b)
        if m.arquivada:
            continue
        if key in seen:
            j = seen[key]
            ctx.add(tr("mac.key_dup", label=label, key=key, other=j + 1), "macros", "tecla", i)
            if not any(x.macro_index == j and x.field == "tecla" for x in ctx.issues):
                ctx.add(tr("mac.key_dup", label=macro_label(j, ms.macros[j]), key=key,
                           other=i + 1), "macros", "tecla", j)
        else:
            seen[key] = i
        if hotkey is not None:
            if b == hotkey:
                ctx.add(tr("mac.key_is_hotkey", label=label, key=key), "macros", "tecla", i)
            elif ignore_mods and not b.mods and b.key == hotkey.key:
                ctx.add(tr("mac.key_hotkey_ignore", label=label, key=key, hotkey=hotkey),
                        "macros", "tecla", i)
        if panel_key is not None:
            if b == panel_key:
                ctx.add(tr("mac.key_is_panel_key", label=label, key=key), "macros", "tecla", i)
            elif ignore_mods and not b.mods and b.key == panel_key.key:
                ctx.add(tr("mac.key_hotkey_ignore", label=label, key=key, hotkey=panel_key),
                        "macros", "tecla", i)
    return ctx.issues


# --------------------------------------------------------------------------
# Escrita
# --------------------------------------------------------------------------
def toml_str(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif o < 0x20 or o == 0x7F:
            out.append(f"\\u{o:04X}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _bool(b: bool) -> str:
    return "true" if b else "false"


def _val(v) -> str:
    if isinstance(v, bool):
        return _bool(v)
    if isinstance(v, float):
        return repr(round(v, 2))
    if isinstance(v, int):
        return str(v)
    return toml_str(str(v))


SETTINGS_HEADER = """\
# Macropad — preferências gerais
# Este ficheiro é recarregado automaticamente quando é guardado.
# Se tiver erros, o Macropad mantém a última configuração válida e mostra o erro.
# Nota: ao gravar a partir da interface, este ficheiro é reescrito neste formato
# (comentários acrescentados à mão não são preservados).
"""

_PANEL_COMMENTS = {
    "opacidade": "# 0.2 (quase transparente) a 1.0 (opaco)",
    "tamanho_botao": "# Aparência (a predefinição corresponde ao aspeto original)\n"
                     "# tamanho_botao: 40–160 px; espacamento: 0–30 px",
    "arredondamento": "# arredondamento: 0 (quadrado) a 50 (redondo), em % do lado; borda: 0–8 px",
    "escala_texto": "# escala_texto: 60–180 %",
    "cor_fundo": "# Cores #RRGGBB. cor_fundo = \"\" segue o tema (Diurno/Noturno).",
    "posicao_titulo": "# Posição do título e da tecla no botão: \"cima\", \"centro\" ou \"baixo\".",
}


def dump_settings(s: Settings) -> str:
    lines = [
        SETTINGS_HEADER,
        f"versao_esquema = {SCHEMA_VERSION}",
        "",
        "[geral]",
        "# Arrancar automaticamente com o Windows.",
        f"arrancar_com_windows = {_bool(s.arrancar_com_windows)}",
        "# \"escrever\" = simula a escrita (Unicode); \"colar\" = área de transferência + Ctrl+V.",
        f"modo_texto = {toml_str(s.modo_texto)}",
        "# \"exatos\" = a tecla só dispara com exatamente os modificadores indicados",
        "#   (\"1\" não dispara com Ctrl+1, que mantém o comportamento normal).",
        "# \"ignorar\" = teclas sem modificadores disparam também com Ctrl/Alt/Shift/Win premidos.",
        f"modificadores = {toml_str(s.modificadores)}",
        "# Alterna entre macros ativas e suspensas (funciona mesmo durante um {Delay}).",
        f"tecla_suspensao = {toml_str(s.tecla_suspensao)}",
        "# Mostra/oculta o painel (\"\" = sem tecla).",
        f"tecla_painel = {toml_str(s.tecla_painel)}",
        "# Tema: \"diurno\", \"noturno\" ou \"automatico\" (segue o Windows).",
        f"tema = {toml_str(s.tema)}",
        "# Idioma da interface (código de um ficheiro em locales/, ex.: \"pt\", \"en\").",
        f"idioma = {toml_str(s.idioma)}",
        "# Pedir confirmação antes de eliminar macros.",
        f"confirmar_eliminacao = {_bool(s.confirmar_eliminacao)}",
        "# Avisar quando se tenta atribuir uma tecla que já está em uso.",
        f"avisar_conflito_tecla = {_bool(s.avisar_conflito_tecla)}",
        "",
        "[painel]",
    ]
    for f in fields(PanelSettings):
        if f.name in _PANEL_COMMENTS:
            lines.append(_PANEL_COMMENTS[f.name])
        lines.append(f"{f.name} = {_val(getattr(s.painel, f.name))}")
    return "\n".join(lines) + "\n"


SET_HEADER = """\
# Macropad — conjunto de macros
#
# Texto das macros: texto literal com comandos intercalados:
#   {Enter}       pressiona Enter
#   {Tab}         pressiona Tab
#   {Delay:500}   espera 500 ms (0 a 600000)
# Exemplo: "ABC{Tab}DEF{Delay:500}{Enter}"
#
# tecla: "1", "F13", "Numpad5", "Ctrl+Alt+F1"... ou "" (só disponível no painel).
# As teclas 1–4 da fila superior são distintas de Numpad1–Numpad4.
# A ordem das secções [[macros]] é a ordem dos botões; não depende da tecla.
# arquivada = true: a macro fica no arquivo (fora das teclas e do painel).
# tipo = "espaco": célula vazia na grelha. tipo = "contador": botão que conta
#   (id, incremento, reposicao, pressao_longa_ms; som_reposicao opcional:
#   "padrao", "aviso", "erro" ou "pergunta"); a contagem fica em estado.toml.
#
# Este ficheiro é recarregado automaticamente quando é guardado.
"""


def dump_macro(m: Macro) -> list[str]:
    if m.is_space:
        return ["[[macros]]", 'tipo = "espaco"']
    lines = ["[[macros]]"]
    if m.is_counter:
        lines += ['tipo = "contador"',
                  f"id = {toml_str(m.id)}",
                  f"titulo = {toml_str(m.titulo)}",
                  f"tecla = {toml_str(m.tecla)}",
                  f"incremento = {m.incremento}",
                  f"reposicao = {m.reposicao}",
                  f"pressao_longa_ms = {m.pressao_longa_ms}"]
        if m.som_reposicao:
            lines.append(f"som_reposicao = {toml_str(m.som_reposicao)}")
    else:
        lines += [f"titulo = {toml_str(m.titulo)}",
                  f"tecla = {toml_str(m.tecla)}",
                  f"texto = {toml_str(m.texto)}",
                  f"repeticoes = {m.repeticoes}",
                  f"intervalo_ms = {m.intervalo_ms}"]
    if m.arquivada:
        lines.append("arquivada = true")
    return lines


def dump_set(ms: MacroSet) -> str:
    lines = [SET_HEADER, f"versao_esquema = {SCHEMA_VERSION}",
             f"nome = {toml_str(ms.nome)}", "",
             "[ambito]",
             "# \"global\" = em todas as aplicações; \"aplicacoes\" = só nas indicadas abaixo.",
             f"modo = {toml_str(ms.ambito.modo)}",
             "aplicacoes = [" + ", ".join(toml_str(a) for a in ms.ambito.aplicacoes) + "]"]
    for m in ms.macros:
        lines.append("")
        lines += dump_macro(m)
    return "\n".join(lines) + "\n"


def macros_to_clipboard(macros: list[Macro]) -> str:
    """Representação TOML de uma ou mais macros (área de transferência)."""
    body = "\n\n".join("\n".join(dump_macro(m)) for m in macros)
    return f"versao_esquema = {SCHEMA_VERSION}\nnome = \"copia\"\n\n{body}\n"


def macros_from_clipboard(text: str) -> list[Macro]:
    try:
        ms = parse_set(text, "copia", "clipboard")
    except ConfigError:
        return []
    return ms.macros


def macro_to_clipboard(m: Macro) -> str:
    return macros_to_clipboard([m])


def macro_from_clipboard(text: str) -> Optional[Macro]:
    ms = macros_from_clipboard(text)
    return ms[0] if len(ms) == 1 else None
