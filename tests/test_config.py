import os
import time
from pathlib import Path

import pytest

from macropad.core.configio import (ConfigError, dump_set, dump_settings, parse_set,
                                    parse_settings, validate_macros)
from macropad.core.model import Macro, MacroSet, Scope, Settings
from macropad.core.store import ConfigStore, atomic_write
from macropad.core.watcher import FileWatcher

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "conjunto-exemplo.toml"


# ------------------------------------------------------------ leitura/escrita
def test_exemplo_comentado_e_valido():
    ms = parse_set(EXAMPLE.read_text("utf-8"), "exemplo")
    m1 = next(m for m in ms.macros if m.tecla == "1")
    assert m1.texto == "3E03305"


def test_roundtrip_set_e_settings():
    ms = MacroSet("x", "Codificação", Scope("aplicacoes", ["notepad.exe"]), [
        Macro('Aspas "e" \\barra', "Ctrl+F1", "linha1\nlinha2{Tab}ç", 3, 250),
        Macro("", "", "só painel"),
    ])
    back = parse_set(dump_set(ms), "x")
    assert back == ms
    from macropad.core.model import PanelSettings
    s = Settings(arrancar_com_windows=False, modo_texto="colar", modificadores="ignorar",
                 tecla_suspensao="Ctrl+Shift+F12", tecla_painel="", tema="automatico", idioma="en",
                 confirmar_eliminacao=False, avisar_conflito_tecla=False,
                 painel=PanelSettings(sempre_por_cima=False, opacidade=0.5, colunas=3,
                                      tamanho_botao=100, espacamento=12, arredondamento=50,
                                      borda=0, escala_texto=120, cor_fundo="#101010",
                                      cor_botao="#ffffff", cor_texto="#000000",
                                      cor_borda="#00e5ff", posicao_titulo="cima", posicao_tecla="centro",
                                      mostrar_tecla=False, mostrar_estado=False))
    assert parse_settings(dump_settings(s)) == s
    ms.macros[1].arquivada = True
    assert parse_set(dump_set(ms), "x") == ms


def test_erro_de_sintaxe_tem_linha_e_coluna():
    txt = 'versao_esquema = 1\nnome = "x"\n[[macros]]\ntitulo = "a\ntecla = "1"\n'
    with pytest.raises(ConfigError) as e:
        parse_set(txt, "x")
    iss = e.value.issues[0]
    assert iss.line == 4 and iss.column is not None
    assert "conjuntos/x.toml, linha 4" in str(iss)


def test_erros_semanticos_localizados():
    txt = """versao_esquema = 1
nome = "x"

[[macros]]
titulo = "a"
tecla = "1"
texto = "ok"

[[macros]]
titulo = "b"
tecla = "1"
texto = "a{Entr}"
repeticoes = 0
"""
    with pytest.raises(ConfigError) as e:
        parse_set(txt, "x")
    msgs = {(i.line, i.field): i.message for i in e.value.issues}
    assert any("já está atribuída" in m for (ln, f), m in msgs.items() if ln == 11)
    assert any("desconhecido" in m for (ln, f), m in msgs.items() if ln == 12)
    assert any("repetições" in m for (ln, f), m in msgs.items() if ln == 13)
    assert {i.macro_index for i in e.value.issues} == {0, 1}   # duplicado marcado nas duas
    assert any(ln == 6 and "macro 2" in m for (ln, f), m in msgs.items())


def test_campo_desconhecido_e_versao():
    with pytest.raises(ConfigError) as e:
        parse_set('versao_esquema = 9\nnome="x"\nrepeticoes = 1\n', "x")
    text = str(e.value)
    assert "mais recente" in text and "campo desconhecido «repeticoes»" in text


def test_conflito_com_tecla_de_suspensao():
    ms = MacroSet("x", "x", Scope(), [Macro("a", "shift+escape", "t")])
    issues = validate_macros(ms, Settings())
    assert issues and "suspensão" in issues[0].message
    ms2 = MacroSet("x", "x", Scope(), [Macro("a", "Escape", "t")])
    assert not validate_macros(ms2, Settings())
    assert validate_macros(ms2, Settings(modificadores="ignorar"))


def test_ambito_aplicacoes_vazio_invalido():
    with pytest.raises(ConfigError):
        parse_set('versao_esquema = 1\nnome="x"\n[ambito]\nmodo="aplicacoes"\n', "x")


# ------------------------------------------------------------------ store
@pytest.fixture
def store(tmp_path):
    s = ConfigStore(tmp_path)
    s.ensure_defaults()
    assert s.load_all() == []
    return s


def test_predefinicoes(store):
    ms = store.sets["predefinido"]
    assert [m.tecla for m in ms.macros] == ["1", "2", "3", "4"]
    assert ms.macros[0].texto == "3E03305"


def test_reload_valido_aplica(store):
    p = store.set_path("predefinido")
    txt = p.read_text("utf-8").replace('texto = "3E03305"', 'texto = "NOVO"')
    p.write_text(txt, "utf-8")
    r = store.reload([p])
    assert r.changed and not r.issues
    assert store.sets["predefinido"].macros[0].texto == "NOVO"


def test_reload_invalido_mantem_ultima_configuracao_valida(store):
    p = store.set_path("predefinido")
    p.write_text(p.read_text("utf-8").replace('texto = "3E03305"', 'texto = "a{Delay:x}"'), "utf-8")
    r = store.reload([p])
    assert not r.changed and r.issues
    assert "conjuntos/predefinido.toml, linha" in str(r.issues[0])
    assert store.sets["predefinido"].macros[0].texto == "3E03305"


def test_reload_settings_com_conflito_rejeitado(store):
    store.config_path.write_text(
        store.config_path.read_text("utf-8").replace('"Shift+Escape"', '"1"'), "utf-8")
    r = store.reload([store.config_path])
    assert not r.changed and r.issues
    assert store.settings.tecla_suspensao == "Shift+Escape"


def test_gravacao_propria_nao_recarrega(store):
    ms = store.sets["predefinido"].clone()
    ms.macros[0].texto = "UI"
    assert store.save_set(ms) == []
    r = store.reload([store.set_path("predefinido")])
    assert not r.changed and not r.issues


def test_gravacao_da_ui_rejeita_invalido(store):
    ms = store.sets["predefinido"].clone()
    ms.macros[1].tecla = "1"
    assert store.save_set(ms)
    assert store.sets["predefinido"].macros[1].tecla == "2"


def test_criar_duplicar_eliminar_importar_exportar(store, tmp_path):
    a = store.create_set("Faturação")
    assert a.id == "faturacao" and store.set_path(a.id).exists()
    b = store.duplicate_set("predefinido")
    assert b.nome == "Predefinido (cópia)" and b.macros == store.sets["predefinido"].macros
    out = tmp_path / "export.toml"
    store.export_set("predefinido", out)
    c = store.import_set(out)
    assert c.nome == "Predefinido (2)" or c.nome.startswith("Predefinido")
    assert c.id != "predefinido"
    store.delete_set(a.id)
    assert a.id not in store.sets and not store.set_path(a.id).exists()
    bad = tmp_path / "mau.toml"
    bad.write_text('versao_esquema = 1\nnome = "m"\n[[macros]]\ntecla="1"\ntexto="{X}"\n', "utf-8")
    with pytest.raises(ConfigError):
        store.import_set(bad)


def test_estado(store):
    from macropad.core.model import State
    store.save_state(State(True, "predefinido", True))
    assert store.load_state() == State(True, "predefinido", True)


# ---------------------------------------------------------------- watcher
class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _touch(p: Path, text: str, bump: int):
    p.write_text(text, "utf-8")
    st = p.stat()
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + bump * 1_000_000_000))


def test_watcher_agrupa_eventos_e_espera_estabilizar(store):
    clock = Clock()
    got = []
    w = FileWatcher(store.watched_files, got.append, settle=0.3, clock=clock)
    w.prime()
    p = store.set_path("predefinido")
    base = p.read_text("utf-8")
    _touch(p, base + "\n# 1\n", 1)
    assert w.poll() == []            # alteração detetada, ainda não estável
    clock.t = 0.1
    _touch(p, base + "\n# 1\n# 2\n", 2)   # escrita continua
    assert w.poll() == []
    clock.t = 0.25
    assert w.poll() == []
    clock.t = 0.5
    assert w.poll() == [p]           # um único evento agrupado
    clock.t = 1.0
    assert w.poll() == []
    assert got == [[p]]


def test_watcher_suporta_substituicao_do_ficheiro(store):
    clock = Clock()
    w = FileWatcher(store.watched_files, lambda _: None, settle=0.2, clock=clock)
    w.prime()
    p = store.set_path("predefinido")
    # editor que grava num temporário e renomeia por cima
    tmp = p.with_name("predefinido.toml.swp")
    tmp.write_text(p.read_text("utf-8").replace("3E03305", "SUBST"), "utf-8")
    os.replace(tmp, p)
    st = p.stat(); os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    w.poll()
    clock.t = 0.5
    ready = w.poll()
    assert ready == [p]
    r = store.reload(ready)
    assert r.changed and store.sets["predefinido"].macros[0].texto == "SUBST"


def test_watcher_ciclo_ui_sem_recarregamento(store):
    clock = Clock()
    w = FileWatcher(store.watched_files, lambda _: None, settle=0.1, clock=clock)
    w.prime()
    ms = store.sets["predefinido"].clone()
    ms.nome = "Gravado pela UI"
    store.save_set(ms)
    p = store.set_path("predefinido")
    st = p.stat(); os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    w.poll(); clock.t = 1
    ready = w.poll()
    assert ready == [p]
    r = store.reload(ready)
    assert not r.changed and not r.issues   # hash conhecido: sem ciclo


def test_watcher_detecta_novo_e_removido(store):
    clock = Clock()
    w = FileWatcher(store.watched_files, lambda _: None, settle=0.1, clock=clock)
    w.prime()
    novo = store.sets_dir / "novo.toml"
    novo.write_text('versao_esquema = 1\nnome = "Novo"\n', "utf-8")
    w.poll(); clock.t = 1
    ready = w.poll()
    assert novo in ready
    r = store.reload(ready)
    assert r.changed and "novo" in store.sets
    novo.unlink()
    clock.t = 2; w.poll(); clock.t = 3
    ready = w.poll()
    assert novo in ready
    store.reload(ready)
    assert "novo" not in store.sets


def test_atomic_write_nao_deixa_temporarios(tmp_path):
    p = tmp_path / "a.toml"
    atomic_write(p, "x = 1\n")
    atomic_write(p, "x = 2\n")
    assert p.read_text() == "x = 2\n"
    assert [f.name for f in tmp_path.iterdir()] == ["a.toml"]


def test_config_antiga_sem_campos_novos_continua_valida():
    old = """versao_esquema = 1
[geral]
arrancar_com_windows = true
modo_texto = "escrever"
modificadores = "exatos"
tecla_suspensao = "Ctrl+Alt+P"
[painel]
sempre_por_cima = true
opacidade = 0.92
colunas = 4
"""
    s = parse_settings(old)
    assert s.tema == "automatico" and s.idioma == "pt" and s.confirmar_eliminacao
    assert s.painel.tamanho_botao == 78 and s.painel.cor_fundo == ""


def test_validacao_preferencias_novas():
    bad = """versao_esquema = 1
[geral]
tema = "roxo"
idioma = "xx"
[painel]
cor_botao = "preto"
tamanho_botao = 500
"""
    with pytest.raises(ConfigError) as e:
        parse_settings(bad)
    txt = str(e.value)
    assert "tema" in txt and "idioma" in txt and "cor_botao" in txt and "tamanho_botao" in txt


def test_arquivadas_podem_partilhar_tecla():
    ms = MacroSet("x", "x", Scope(), [Macro("a", "1", "a"), Macro("b", "1", "b", arquivada=True)])
    assert validate_macros(ms, Settings()) == []
    ms.macros[1].arquivada = False
    assert validate_macros(ms, Settings())


def test_texto_vazio_permitido():
    ms = MacroSet("x", "x", Scope(), [Macro("Nova macro", "", "")])
    assert validate_macros(ms, Settings()) == []


# ------------------------------------------------------------ versão 0.4
def test_tipos_espaco_e_contador_roundtrip():
    ms = MacroSet("x", "x", Scope(), [
        Macro("A", "1", "a"), Macro(tipo="espaco"),
        Macro("Conta", "F9", tipo="contador", id="abc", incremento=5, reposicao=10,
              pressao_longa_ms=1200)])
    back = parse_set(dump_set(ms), "x")
    assert back.macros[1].is_space and back.macros[1].tecla == ""
    c = back.macros[2]
    assert (c.tipo, c.id, c.incremento, c.reposicao, c.pressao_longa_ms) == (
        "contador", "abc", 5, 10, 1200)
    assert c.texto == ""


def test_validacao_espacos_e_contadores():
    bad = """versao_esquema = 1
nome = "x"
[[macros]]
tipo = "espaco"
arquivada = true
[[macros]]
tipo = "contador"
id = "c1"
incremento = 0
[[macros]]
tipo = "contador"
id = "c1"
pressao_longa_ms = 50
[[macros]]
tipo = "outro"
"""
    with pytest.raises(ConfigError) as e:
        parse_set(bad, "x")
    txt = str(e.value)
    assert "espaço" in txt and "incremento" in txt and "id" in txt and "tipo" in txt


def test_contador_sem_id_recebe_id_estavel():
    ms = parse_set('versao_esquema = 1\nnome="x"\n[[macros]]\ntipo="contador"\n', "x")
    assert ms.macros[0].id == "contador-1"


def test_mostrar_icone_antigo_aceite_e_ignorado():
    s = parse_settings('versao_esquema = 1\n[painel]\nmostrar_icone = false\n')
    assert s.painel.posicao_titulo == "centro"
    assert "mostrar_icone" not in dump_settings(s)


def test_teclas_globais_predefinidas_e_conflitos():
    s = Settings()
    assert (s.tecla_suspensao, s.tecla_painel) == ("Shift+Escape", "Shift+F12")
    ms = MacroSet("x", "x", Scope(), [Macro("a", "shift+f12", "t")])
    issues = validate_macros(ms, s)
    assert issues and "painel" in issues[0].message
    with pytest.raises(ConfigError):
        parse_settings('versao_esquema = 1\n[geral]\ntecla_suspensao = "F8"\ntecla_painel = "F8"\n')
    assert parse_settings('versao_esquema = 1\n[geral]\ntecla_painel = ""\n').tecla_painel == ""


def test_migracao_ctrl_alt_p_para_shift_escape(tmp_path):
    from macropad.core.model import State
    st = ConfigStore(tmp_path)
    st.ensure_defaults()
    st.config_path.write_text(st.config_path.read_text("utf-8").replace(
        '"Shift+Escape"', '"Ctrl+Alt+P"'), "utf-8")
    st.load_all()
    assert st.settings.tecla_suspensao == "Ctrl+Alt+P"
    state = State()
    msgs = st.migrate(state)
    assert msgs and st.settings.tecla_suspensao == "Shift+Escape"
    assert "Shift+Escape" in st.config_path.read_text("utf-8")
    # só uma vez: se o utilizador voltar a escolher Ctrl+Alt+P, mantém-se
    s = st.settings.clone(); s.tecla_suspensao = "Ctrl+Alt+P"; st.save_settings(s)
    assert st.migrate(state) == [] and st.settings.tecla_suspensao == "Ctrl+Alt+P"


def test_estado_com_contadores_posicao_e_migracoes(tmp_path):
    from macropad.core.model import State
    st = ConfigStore(tmp_path)
    s = State(True, "x", True, 120, -30, {"abc": 7, "d e": -2}, ["m1"])
    st.save_state(s)
    assert st.load_state() == s


def test_migracao_falhada_nao_fica_marcada(tmp_path):
    """Revisão Codex: se Shift+Escape já estiver numa macro, a migração não é
    registada, avisa e volta a ser tentada depois de resolvido o conflito."""
    from macropad.core.model import State
    st = ConfigStore(tmp_path)
    st.ensure_defaults()
    st.config_path.write_text(st.config_path.read_text("utf-8").replace(
        '"Shift+Escape"', '"Ctrl+Alt+P"'), "utf-8")
    st.load_all()
    ms = st.sets["predefinido"].clone()
    ms.macros[0].tecla = "Shift+Escape"
    assert st.save_set(ms) == []
    state = State()
    msgs = st.migrate(state)
    assert msgs and "Ctrl+Alt+P" in msgs[0] and st.settings.tecla_suspensao == "Ctrl+Alt+P"
    assert state.migracoes == []
    ms.macros[0].tecla = "1"
    assert st.save_set(ms) == []
    msgs = st.migrate(state)
    assert st.settings.tecla_suspensao == "Shift+Escape"
    assert state.migracoes == [ConfigStore.MIGRATION_HOTKEY]


def test_falha_de_escrita_nao_altera_preferencias_em_memoria(tmp_path, monkeypatch):
    st = ConfigStore(tmp_path)
    st.ensure_defaults()
    st.load_all()
    old = st.settings.tema
    s = st.settings.clone()
    s.tema = "noturno" if old != "noturno" else "diurno"

    def boom(*_a, **_k):
        raise OSError(13, "bloqueado")
    monkeypatch.setattr(st, "_write", boom)
    with pytest.raises(OSError):
        st.save_settings(s)
    assert st.settings.tema == old


def test_migracao_com_falha_de_escrita_nao_interrompe(tmp_path, monkeypatch):
    from macropad.core.model import State
    st = ConfigStore(tmp_path)
    st.ensure_defaults()
    st.config_path.write_text(st.config_path.read_text("utf-8").replace(
        '"Shift+Escape"', '"Ctrl+Alt+P"'), "utf-8")
    st.load_all()

    def boom(*_a, **_k):
        raise OSError(13, "Acesso negado")
    monkeypatch.setattr(st, "_write", boom)
    state = State()
    msgs = st.migrate(state)                       # não lança
    assert msgs and "Acesso negado" in msgs[0]
    assert st.settings.tecla_suspensao == "Ctrl+Alt+P"
    assert state.migracoes == []


def test_teclas_multimedia_e_conflitos():
    """Play/Pausa, faixa anterior e seguinte são teclas válidas; os conflitos
    com outras macros e com os atalhos globais são detetados como os outros."""
    from macropad.core.keys import display_binding, parse_binding
    assert str(parse_binding("mediaplaypause")) == "MediaPlayPause"
    ms = MacroSet("x", "x", Scope(), [Macro("a", "MediaNext", "t"),
                                      Macro("b", "MediaPrev", "u"),
                                      Macro("c", "MediaPlayPause", "v")])
    assert not validate_macros(ms, Settings())
    ms.macros[1].tecla = "MediaNext"
    assert validate_macros(ms, Settings())                       # duas macros, a mesma tecla
    ms.macros[1].tecla = "MediaPrev"
    assert validate_macros(ms, Settings(tecla_painel="MediaPlayPause"))   # tecla global
    assert display_binding("Ctrl+MediaNext") == "Ctrl+Faixa seguinte"
    assert display_binding("F5") == "F5"
