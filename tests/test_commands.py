import pytest

from macropad.core.commands import (CommandError, DelayStep, KeyStep, TextStep,
                                    parse_action)
from macropad.core.keys import KeyBindingError, normalize_binding, parse_binding


def test_exemplo_do_enunciado():
    assert parse_action("ABC{Tab}DEF{Delay:500}{Enter}") == [
        TextStep("ABC"), KeyStep("Tab"), TextStep("DEF"), DelayStep(500), KeyStep("Enter")]


def test_texto_simples_e_unicode():
    assert parse_action("3E03305") == [TextStep("3E03305")]
    assert parse_action("Ação çé ñ 😀") == [TextStep("Ação çé ñ 😀")]


def test_nomes_sem_distincao_de_maiusculas_e_espacos_no_delay():
    assert parse_action("{enter}{TAB}{delay: 20 }") == [
        KeyStep("Enter"), KeyStep("Tab"), DelayStep(20)]


def test_comandos_no_inicio_meio_fim_e_consecutivos():
    assert parse_action("{Enter}{Enter}a{Tab}") == [
        KeyStep("Enter"), KeyStep("Enter"), TextStep("a"), KeyStep("Tab")]


def test_quebras_de_linha_equivalem_a_enter():
    assert parse_action("a\nb\r\nc\td") == [
        TextStep("a"), KeyStep("Enter"), TextStep("b"), KeyStep("Enter"),
        TextStep("c"), KeyStep("Tab"), TextStep("d")]


@pytest.mark.parametrize("txt", ["{}", "{ x}", "{1}", "a{b c", "{", "x}"])
def test_chavetas_que_nao_sao_comandos_ficam_literais(txt):
    assert parse_action(txt) == [TextStep(txt)]


@pytest.mark.parametrize("txt,pos,frag", [
    ("ab{Entr}", 2, "desconhecido"),
    ("{Foo:1}", 0, "desconhecido"),
    ("x{Enter", 1, "não fechado"),
    ("{Tab:3}", 0, "não aceita"),
    ("{Delay}", 0, "precisa de um valor"),
    ("{Delay:}", 0, "inválido"),
    ("{Delay:abc}", 0, "inválido"),
    ("{Delay:-5}", 0, "inválido"),
    ("{Delay:1.5}", 0, "inválido"),
    ("{Delay:500", 0, "não fechado"),
    ("{Delay:999999999}", 0, "excede"),
])
def test_comandos_mal_formados(txt, pos, frag):
    with pytest.raises(CommandError) as e:
        parse_action(txt)
    assert e.value.position == pos
    assert frag in str(e.value)


def test_delay_zero_e_maximo():
    assert parse_action("{Delay:0}") == [DelayStep(0)]
    assert parse_action("{Delay:600000}") == [DelayStep(600000)]


def test_bindings():
    assert str(parse_binding("1")) == "1"
    assert str(parse_binding("shift+ctrl+f1")) == "Ctrl+Shift+F1"
    assert normalize_binding("alt+numpad1") == "Alt+Numpad1"
    assert parse_binding("1") != parse_binding("Numpad1")
    for bad in ["Ctrl", "Ctrl+", "Ctrl+Ctrl+1", "Hyper+1", "Foo", ""]:
        with pytest.raises(KeyBindingError):
            parse_binding(bad)
