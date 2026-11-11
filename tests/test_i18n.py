import pytest

from macropad import i18n
from macropad.core.commands import CommandError, parse_action
from macropad.core.engine import Engine
from macropad.core.model import Macro


@pytest.fixture
def english():
    i18n.set_language("en")
    yield
    i18n.set_language("pt")


def test_idiomas_disponiveis_e_completos():
    langs = dict(i18n.available())
    assert langs["pt"] == "Português" and langs["en"] == "English"
    assert list(langs)[0] == "pt"
    base = i18n.keys("pt")
    for code in langs:
        assert i18n.keys(code) == base, f"{code}: chaves em falta/extra"


def test_mensagens_seguem_o_idioma(english):
    with pytest.raises(CommandError) as e:
        parse_action("a{Entr}")
    assert "unknown command {Entr}" in str(e.value) and "position 2" in str(e.value)


def test_idioma_desconhecido_volta_ao_portugues():
    i18n.set_language("xx")
    assert i18n.language() == "pt"


def test_titulos_e_conteudos_nao_sao_traduzidos(english, fake):
    from conftest import make_config, wait_idle
    e = Engine(fake)
    e.set_config(make_config([Macro("Olá Ação", "1", "Texto em português")]))
    assert e.active_set.macros[0].display_title() == "Olá Ação"
    e.trigger(0)
    wait_idle(e)
    assert fake.typed() == "Texto em português"
    assert e.status() == ("ativo", "Active")
