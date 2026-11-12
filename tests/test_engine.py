import threading
import time

from conftest import OTHER, TARGET, make_config, wait_idle

from macropad.core.engine import CANCEL_SUSPEND, CANCEL_WINDOW, Engine, KeyEvent, WindowInfo
from macropad.core.model import Macro, Scope, Settings

CTRL = frozenset({"Ctrl"})
HK = frozenset({"Ctrl", "Alt"})


def down(k, mods=frozenset(), ours=False):
    return KeyEvent(k, True, mods, ours)


def up(k, mods=frozenset()):
    return KeyEvent(k, False, mods)


# ---------------------------------------------------------------- supressão
def test_tecla_ativa_suprime_e_envia(engine, fake):
    assert engine.handle_key(down("1")) is True
    assert engine.handle_key(up("1")) is True
    wait_idle(engine)
    assert fake.typed() == "3E03305"


def test_suspenso_nao_suprime(engine, fake):
    engine.set_suspended(True)
    assert engine.handle_key(down("1")) is False
    assert engine.handle_key(up("1")) is False
    assert fake.log == []


def test_tecla_sem_macro_passa(engine, fake):
    assert engine.handle_key(down("5")) is False
    assert engine.handle_key(down("Numpad1")) is False


def test_modificadores_exatos_mantem_comportamento_normal(engine, fake):
    for mods in (CTRL, frozenset({"Alt"}), frozenset({"Shift"})):
        assert engine.handle_key(down("1", mods)) is False
        assert engine.handle_key(up("1", mods)) is False
    assert fake.log == []


def test_modo_ignorar_modificadores(fake):
    e = Engine(fake)
    s = Settings(modificadores="ignorar")
    e.set_config(make_config([Macro("A", "1", "x"), Macro("B", "Ctrl+1", "y")], settings=s))
    assert e.handle_key(down("1", frozenset({"Shift"}))) is True   # cai na tecla simples
    e.handle_key(up("1")); wait_idle(e)
    assert e.handle_key(down("1", CTRL)) is True                    # correspondência exata
    e.handle_key(up("1")); wait_idle(e)
    assert fake.typed() == "xy"


def test_combinacao_configurada(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "Ctrl+1", "x")]))
    assert e.handle_key(down("1")) is False
    e.handle_key(up("1"))
    assert e.handle_key(down("1", CTRL)) is True


def test_autorepeticao_nao_redispara(engine, fake):
    assert engine.handle_key(down("1"))
    wait_idle(engine)
    for _ in range(5):                      # auto-repetição do Windows
        assert engine.handle_key(down("1")) is True
    wait_idle(engine)
    assert fake.typed() == "3E03305"
    engine.handle_key(up("1"))
    engine.handle_key(down("1")); engine.handle_key(up("1"))
    wait_idle(engine)
    assert fake.typed() == "3E03305" * 2


def test_autorepeticao_de_tecla_que_passou_continua_a_passar(engine, fake):
    # 1 premido com Ctrl (passa); Ctrl libertado enquanto 1 continua premido.
    assert engine.handle_key(down("1", CTRL)) is False
    assert engine.handle_key(down("1")) is False
    assert engine.handle_key(up("1")) is False
    assert fake.log == []


def test_eventos_proprios_ignorados(engine, fake):
    assert engine.handle_key(down("1", ours=True)) is False
    assert fake.log == []


def test_proprio_processo_em_primeiro_plano_nao_dispara(engine, fake):
    fake.fg = WindowInfo(9, fake.own_pid(), "C:\\macropad.exe")
    assert engine.handle_key(down("1")) is False


# --------------------------------------------------------------- âmbito
def test_ambito_por_aplicacao(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "x")],
                             scope=Scope("aplicacoes", ["EDITOR.EXE"])))
    assert e.handle_key(down("1")) is True        # Editor.exe em primeiro plano
    e.handle_key(up("1")); wait_idle(e)
    fake.fg = OTHER
    assert e.handle_key(down("1")) is False       # fora do âmbito: comportamento normal
    assert e.handle_key(up("1")) is False
    ok, why = e.trigger(0)
    assert not ok and "fora do âmbito" in why     # o painel respeita o âmbito


def test_ambito_com_caminho_completo(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "x")],
                             scope=Scope("aplicacoes", ["c:/program files/app/editor.exe"])))
    assert e.handle_key(down("1")) is True


# ---------------------------------------------------- repetições / execução
def test_repeticoes_e_intervalo(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "ab{Enter}", repeticoes=3, intervalo_ms=30)]))
    t0 = time.monotonic()
    e.handle_key(down("1")); e.handle_key(up("1"))
    wait_idle(e)
    assert fake.typed() == "ab{Enter}" * 3
    assert time.monotonic() - t0 >= 0.055


def test_disparos_durante_execucao_sao_ignorados(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "a{Delay:150}b"), Macro("B", "2", "zz")]))
    e.handle_key(down("1")); e.handle_key(up("1"))
    time.sleep(0.03)
    assert e.handle_key(down("2")) is True        # suprimida, mas ignorada
    e.handle_key(up("2"))
    assert e.trigger(1)[0] is False
    wait_idle(e)
    assert fake.typed() == "ab"


def test_suspensao_interrompe_durante_delay(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "a{Delay:5000}b", repeticoes=3)]))
    e.handle_key(down("1")); e.handle_key(up("1"))
    time.sleep(0.05)
    run = e.running
    t0 = time.monotonic()
    assert e.handle_key(down("P", HK)) is True    # hotkey Ctrl+Alt+P durante o Delay
    e.handle_key(up("P", HK))
    wait_idle(e, 1.0)
    assert time.monotonic() - t0 < 0.5
    assert run.cancel_reason == CANCEL_SUSPEND
    assert fake.typed() == "a"
    assert e.suspended
    # com macros suspensas a tecla volta ao normal
    assert e.handle_key(down("1")) is False


def test_suspensao_interrompe_intervalo_entre_repeticoes(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "a", repeticoes=5, intervalo_ms=3000)]))
    e.handle_key(down("1"))
    time.sleep(0.05)
    e.set_suspended(True)
    wait_idle(e, 1.0)
    assert fake.typed() == "a"


def test_hotkey_reativa_e_nao_reativa_por_si(engine):
    engine.handle_key(down("P", HK)); engine.handle_key(up("P", HK))
    assert engine.suspended
    engine.handle_key(down("P", HK)); engine.handle_key(up("P", HK))
    assert not engine.suspended


def test_mudanca_de_janela_interrompe(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "a{Delay:3000}b")]))
    e.handle_key(down("1"))
    time.sleep(0.05)
    fake.fg = OTHER
    wait_idle(e, 1.0)
    assert e is not None and fake.typed() == "a"


def test_mudanca_de_janela_entre_passos(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "a{Enter}b{Tab}c")]))

    def switch(ev):
        if ev == ("key", "Enter"):
            fake.fg = OTHER
    fake.on_send = switch
    finished = []
    e.add_listener(lambda ev, p: finished.append(p) if ev == "finished" else None)
    e.handle_key(down("1"))
    wait_idle(e)
    assert fake.typed() == "a{Enter}"
    assert finished[-1]["cancelled"] == CANCEL_WINDOW


def test_recarregamento_nao_altera_execucao_em_curso(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "a{Delay:100}b")]))
    e.handle_key(down("1"))
    time.sleep(0.03)
    e.set_config(make_config([Macro("A", "1", "XYZ")]))
    wait_idle(e)
    assert fake.typed() == "ab"
    e.handle_key(up("1"))
    e.handle_key(down("1")); wait_idle(e)
    assert fake.typed() == "abXYZ"


def test_recarregamento_nao_ativa_macros(engine):
    engine.set_suspended(True)
    engine.set_config(make_config([Macro("A", "1", "x")]))
    assert engine.suspended


def test_espera_libertacao_de_modificadores(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "Ctrl+1", "x{Enter}")]))
    fake.mods = CTRL
    e.handle_key(down("1", CTRL))
    time.sleep(0.1)
    assert fake.log == []           # aguarda que o utilizador largue o Ctrl
    fake.mods = frozenset()
    wait_idle(e)
    assert fake.typed() == "x{Enter}"


def test_painel_dispara_na_janela_em_primeiro_plano(engine, fake):
    ok, _ = engine.trigger(1)
    assert ok
    wait_idle(engine)
    assert fake.typed() == "X{Enter}"
    engine.set_suspended(True)
    assert engine.trigger(0) == (False, "macros suspensas")


def test_hotkey_durante_captura_nao_e_intercetada(engine):
    engine.capture_mode = True
    assert engine.handle_key(down("P", HK)) is False
    assert not engine.suspended


def test_macros_arquivadas_fora_das_teclas_e_do_painel(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("A", "1", "a", arquivada=True), Macro("B", "2", "b")]))
    assert e.handle_key(down("1")) is False           # tecla normal
    e.handle_key(up("1"))
    ok, why = e.trigger(0)
    assert not ok and "arquivada" in why
    assert fake.log == []


def test_macro_sem_texto_nao_suprime_tecla(fake):
    e = Engine(fake)
    e.set_config(make_config([Macro("Nova", "1", "")]))
    assert e.handle_key(down("1")) is False
    assert e.trigger(0)[0] is False


def test_trigger_com_indice_fora_do_intervalo_nao_executa(engine, fake):
    # Revisão Codex P2: índices negativos não podem apontar para o fim da lista.
    for idx in (-1, -2, 2, 99):
        ok, _ = engine.trigger(idx)
        assert ok is False
    time.sleep(0.05)
    assert fake.log == []
