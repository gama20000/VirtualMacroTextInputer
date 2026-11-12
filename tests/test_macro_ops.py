from macropad.core import macro_ops as ops
from macropad.core.configio import macro_from_clipboard, macro_to_clipboard
from macropad.core.model import (Macro, MacroSet, PanelSettings, Scope, apply_preset,
                                 matching_preset)


def mk(*macros):
    return MacroSet("x", "x", Scope(), list(macros))


def titles(ms):
    return [(m.titulo, m.arquivada) for m in ms.macros]


def test_duplicados_por_conteudo_e_nao_por_titulo_ou_tecla():
    ms = mk(Macro("A", "1", "ab{Enter}"), Macro("B", "2", "ab\n"),
            Macro("C", "3", "ab{enter}", arquivada=True), Macro("D", "4", "outro"),
            Macro("E", "", ""), Macro("F", "", ""))
    d = ops.duplicate_groups(ms.macros)
    assert d == {0: [1, 2], 1: [0, 2], 2: [0, 1]}     # vazios não contam


def test_mesma_tecla_nao_e_duplicado():
    ms = mk(Macro("A", "1", "x"), Macro("B", "1", "y"))
    assert ops.duplicate_groups(ms.macros) == {}


def test_arquivar_e_restaurar_sem_conflito():
    ms = mk(Macro("A", "1", "a"), Macro("B", "2", "b"), Macro("C", "3", "c"))
    i = ops.archive(ms, 0)
    assert titles(ms) == [("B", False), ("C", False), ("A", True)] and i == 2
    assert ops.key_conflict(ms, 2) is None
    j = ops.restore(ms, 2)
    assert titles(ms) == [("B", False), ("C", False), ("A", False)] and j == 2


def test_restaurar_com_conflito_substitui_no_lugar():
    ms = mk(Macro("A", "1", "a"), Macro("B", "2", "b"), Macro("Velha", "1", "v", arquivada=True),
            Macro("Z", "", "z", arquivada=True))
    assert ops.key_conflict(ms, 2) == 0
    k = ops.restore_replacing(ms, 2, 0)
    assert titles(ms) == [("Velha", False), ("B", False), ("A", True), ("Z", True)]
    assert k == 0


def test_pesquisa_no_arquivo():
    m = Macro("Codificação", "F5", "3E03305")
    assert ops.matches_query(m, "codif") and ops.matches_query(m, "3e03")
    assert ops.matches_query(m, "f5") and not ops.matches_query(m, "zzz")


def test_nova_macro_adiciona_so_uma_sem_tecla():
    ms = mk(*[Macro(str(n), str(n), "t") for n in range(1, 8)], Macro("Arq", "", "a", arquivada=True))
    i = ops.new_macro(ms, "Nova macro")
    assert len(ms.macros) == 9 and i == 7
    new = ms.macros[i]
    assert (new.titulo, new.tecla, new.texto, new.arquivada) == ("Nova macro", "", "", False)


def test_copiar_colar():
    ms = mk(Macro("A", "1", "a{Tab}"), Macro("B", "2", "b"))
    txt = macro_to_clipboard(ms.macros[0])
    m = macro_from_clipboard(txt)
    assert m == ms.macros[0]
    i = ops.insert_copy(ms, m, 0)
    assert i == 1 and ms.macros[1].texto == "a{Tab}" and ms.macros[1].tecla == ""   # tecla ocupada
    assert ops.duplicate_groups(ms.macros) == {0: [1], 1: [0]}
    assert macro_from_clipboard("texto qualquer") is None


def test_reordenar_grupo_e_mover():
    ms = mk(Macro("A"), Macro("B"), Macro("C", arquivada=True), Macro("D", arquivada=True))
    ops.reorder_group(ms, False, [1, 0])
    assert [m.titulo for m in ms.macros] == ["B", "A", "C", "D"]
    ops.reorder_group(ms, True, [3, 2])
    assert [m.titulo for m in ms.macros] == ["B", "A", "D", "C"]
    assert ops.move(ms, 1, 1) == 1            # não atravessa para o arquivo


def test_predefinicoes_do_painel():
    p = PanelSettings(colunas=6, opacidade=0.5)
    assert matching_preset(p) == "predefinido"
    neon = apply_preset(p, "neon")
    assert neon.colunas == 6 and neon.opacidade == 0.5 and neon.cor_texto == "#00e5ff"
    assert matching_preset(neon) == "neon"
    back = apply_preset(neon, "predefinido")
    assert back == PanelSettings(colunas=6, opacidade=0.5)


def test_arquivar_e_eliminar_varias():
    ms = mk(Macro("A"), Macro("B"), Macro("C"), Macro("D"), Macro("Z", arquivada=True))
    new = ops.archive_many(ms, [2, 0])
    assert titles(ms) == [("B", False), ("D", False), ("A", True), ("C", True), ("Z", True)]
    assert new == [2, 3]
    ops.delete_many(ms, [0, 3])
    assert [m.titulo for m in ms.macros] == ["D", "A", "Z"]


def test_copiar_varias():
    from macropad.core.configio import macros_from_clipboard, macros_to_clipboard
    ms = [Macro("A", "1", "a"), Macro("B", "", "b{Enter}", 2, 100)]
    assert macros_from_clipboard(macros_to_clipboard(ms)) == ms


def test_reordenar_arquivo_filtrado_preserva_macros_ocultas():
    # Revisão Codex P1: com a pesquisa ativa, a grelha do arquivo só mostra
    # parte das macros; reordenar não pode descartar as ocultas.
    ms = mk(Macro("A"), Macro("x1", arquivada=True), Macro("oculta", arquivada=True),
            Macro("x2", arquivada=True), Macro("oculta2", arquivada=True))
    ops.reorder_group(ms, True, [3, 1])        # só x1 e x2 visíveis; trocados
    assert len(ms.macros) == 5
    assert [m.titulo for m in ms.macros] == ["A", "x2", "oculta", "x1", "oculta2"]


def test_reordenar_grupo_ignora_indices_do_outro_grupo():
    ms = mk(Macro("A"), Macro("B"), Macro("Z", arquivada=True))
    ops.reorder_group(ms, False, [1, 0])
    assert [m.titulo for m in ms.macros] == ["B", "A", "Z"]


# ------------------------------------------------------------ versão 0.4
def test_mover_com_posicao_entre_areas():
    ms = mk(Macro("A"), Macro("B"), Macro("C"), Macro("X", arquivada=True),
            Macro("Y", arquivada=True))
    A, B, C, X, Y = ms.macros
    # Ativo -> Arquivo, antes de Y (não no fim)
    ops.move_items(ms, [B], True, anchor=Y, after=False)
    assert titles(ms) == [("A", False), ("C", False), ("X", True), ("B", True), ("Y", True)]
    # Arquivo -> Ativo, depois de A
    ops.move_items(ms, [Y], False, anchor=A, after=True)
    assert [m.titulo for m in ms.macros] == ["A", "Y", "C", "X", "B"]
    assert not Y.arquivada
    # reorganizar dentro da área, com inserção antes da âncora
    ops.move_items(ms, [C], False, anchor=A, after=False)
    assert [m.titulo for m in ms.macros] == ["C", "A", "Y", "X", "B"]
    # sem âncora: fim da área
    ops.move_items(ms, [C], True)
    assert [m.titulo for m in ms.macros] == ["A", "Y", "X", "B", "C"]


def test_espacos_nao_vao_para_o_arquivo():
    ms = mk(Macro("A"), Macro(tipo="espaco"), Macro("X", arquivada=True))
    sp = ms.macros[1]
    assert ops.move_items(ms, [sp], True) == []
    assert not sp.arquivada
    ops.archive_many(ms, [0, 1])
    assert [(m.titulo, m.tipo, m.arquivada) for m in ms.macros] == [
        ("", "espaco", False), ("A", "texto", True), ("X", "texto", True)]


def test_trocar_botao_com_espaco():
    ms = mk(Macro("A"), Macro(tipo="espaco"), Macro("B"))
    ops.swap(ms, 0, 1)
    assert [m.tipo for m in ms.macros] == ["espaco", "texto", "texto"]


def test_novos_espaco_e_contador():
    ms = mk(Macro("A"), Macro("Z", arquivada=True))
    i = ops.new_space(ms)
    j = ops.new_counter(ms, "Conta")
    assert (i, j) == (1, 2)
    c = ms.macros[2]
    assert c.is_counter and c.id and c.incremento == 1 and c.reposicao == 0
    assert ops.duplicate_groups(ms.macros + [Macro("B", tipo="contador", id="x")]) == {}


def test_colar_copia_de_arquivada_fica_no_arquivo_logo_a_seguir():
    ms = mk(Macro("A", "1", "a"), Macro("X", "2", "x", arquivada=True),
            Macro("Y", "", "y", arquivada=True))
    src = ms.macros[1]
    pos = ops.insert_copy(ms, src, 1)
    assert pos == 2
    assert [(m.titulo, m.arquivada) for m in ms.macros] == [
        ("A", False), ("X", True), ("X", True), ("Y", True)]
    assert ms.macros[1] is src and ms.macros[2].tecla == "2"   # no arquivo mantém a tecla


def test_copiar_contador_recebe_id_novo():
    ms = mk(Macro("C", tipo="contador", id="orig"))
    ops.insert_copy(ms, ms.macros[0], 0)
    assert ms.macros[1].id != "orig" and ms.macros[1].is_counter
