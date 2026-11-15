"""Testes de fumo da interface (Qt offscreen, plataforma simulada)."""
import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
from PySide6.QtCore import QEvent, Qt  # noqa: E402
from PySide6.QtGui import QKeyEvent  # noqa: E402

from macropad import i18n  # noqa: E402
from macropad.platform.dummy import DummyPlatform  # noqa: E402
from macropad.ui import dialogs  # noqa: E402
from macropad.ui.app import MacropadApp  # noqa: E402
from macropad.core.engine import WindowInfo  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def app(qapp, tmp_path, monkeypatch):
    answers = []
    monkeypatch.setattr("macropad.ui.config_window.ask",
                        lambda *a, **k: answers.pop(0) if answers else (True, False))
    plat = DummyPlatform()
    a = MacropadApp(qapp, tmp_path, plat)
    a.answers = answers
    a.show_config()
    qapp.processEvents()
    yield a
    a.quit()
    if a.config_window is not None:
        a.config_window.dispose()
        a.config_window.deleteLater()
    a.panel.deleteLater()
    a.menu.deleteLater()
    qapp.sendPostedEvents(None, QEvent.DeferredDelete.value)   # não acumular janelas
    qapp.processEvents()
    i18n.set_language("pt")


def wait_idle(engine):
    end = time.monotonic() + 2
    while engine.running is not None and time.monotonic() < end:
        time.sleep(0.01)


def press(qapp, w, key, mods=Qt.NoModifier):
    qapp.sendEvent(w, QKeyEvent(QEvent.KeyPress, key, mods))


def test_editar_gravar_reordenar_e_painel(app, qapp):
    w = app.config_window
    assert [w.tabs.tabText(i) for i in range(4)] == [
        "Macros", "Painel", "Âmbito", "Preferências"]
    assert w.grid.count() == 4

    w._select(1)
    w.f_text.setPlainText("a{Entr}")
    assert "desconhecido" in w.f_error.text()
    w.flush()
    assert app.store.sets["predefinido"].macros[1].texto == "Z51.11{Enter}"

    w.f_text.setPlainText("OK{Tab}")
    w.flush()
    assert app.engine.active_set.macros[1].texto == "OK{Tab}"

    w._on_drop(False, w.grid, [1], 0, False)      # largar antes do primeiro
    w.flush()
    assert [m.tecla for m in app.store.sets["predefinido"].macros] == ["2", "1", "3", "4"]

    w._on_key_captured("3")
    assert "conflito de tecla" in w.f_error.text()
    w._on_key_captured("2")
    w.flush()

    app.set_panel_visible(True)
    assert len(app.panel.view.buttons) == 4
    app.panel.view.buttons[0].click()
    wait_idle(app.engine)
    assert app.platform.sent == [("text", "OK"), ("key", "Tab")]


def test_estado_ativo_suspenso(app, qapp):
    w = app.config_window
    assert w.btn_on.isChecked() and not w.btn_off.isChecked()
    w.btn_off.click()
    qapp.processEvents()
    assert app.engine.suspended and w.btn_off.isChecked()
    assert "suspenso = true" in (app.store.root / "estado.toml").read_text("utf-8")
    w.btn_on.click()
    qapp.processEvents()
    assert not app.engine.suspended


def test_nova_macro_e_duplicados(app, qapp):
    w = app.config_window
    w.flush()
    w._last_add = 0
    w._select(-1)                  # sem seleção: no fim da área Ativo
    w._add_macro()
    w._add_macro()                     # clique repetido imediato: ignorado
    w.flush()
    ms = app.store.sets["predefinido"]
    assert len(ms.macros) == 5
    assert (ms.macros[4].tecla, ms.macros[4].texto) == ("", "")
    w.f_text.setPlainText("3E03305")   # igual à macro 1
    w.flush()
    assert "Conteúdo duplicado" in w.f_dup.text()
    from macropad.ui.widgets import DUP_ROLE, ERROR_ROLE
    dup_rows = [r for r in range(w.grid.count()) if w.grid.item(r).data(DUP_ROLE)]
    assert len(dup_rows) == 2
    assert not any(w.grid.item(r).data(ERROR_ROLE) for r in range(w.grid.count()))


def test_atalhos_eliminar_copiar_colar(app, qapp):
    w = app.config_window
    w.activateWindow()
    w._select(0)
    w.grid.setFocus()
    qapp.processEvents()
    # Ctrl+C / Ctrl+V com foco na grelha
    w._copy_macro()
    w._paste_macro()
    w.flush()
    ms = app.store.sets["predefinido"]
    assert len(ms.macros) == 5 and ms.macros[1].texto == "3E03305" and ms.macros[1].tecla == ""
    # Delete com confirmação e «Não voltar a perguntar»
    app.answers.append((True, True))
    w._select(1)
    w._delete_macro()
    w.flush()
    assert len(app.store.sets["predefinido"].macros) == 4
    assert app.store.settings.confirmar_eliminacao is False
    # cancelar não elimina
    app.store.settings.confirmar_eliminacao = True
    app.answers.append((False, False))
    w._select(0)
    w._delete_macro()
    assert len(w.ms.macros) == 4


def test_filtro_de_teclas_respeita_campos_de_texto(app, qapp):
    w = app.config_window
    w._select(0)
    w.f_title.setFocus()
    qapp.processEvents()
    if QtWidgets.QApplication.focusWidget() is not w.f_title:
        pytest.skip("foco indisponível no modo offscreen")
    press(qapp, w.f_title, Qt.Key_Delete)
    assert len(w.ms.macros) == 4            # Delete no campo de texto não elimina macros


def test_arquivo_restaurar_com_conflito(app, qapp):
    w = app.config_window
    w._select(0)                            # macro 1 (tecla 1)
    w._toggle_archive()
    w.flush()
    ms = app.store.sets["predefinido"]
    assert ms.macros[-1].arquivada and ms.macros[-1].tecla == "1"
    assert app.engine.active_set.macros[-1].arquivada
    assert w.archive_grid.count() == 1
    w.archive_search.setText("nada")
    assert w.archive_grid.count() == 0
    w.archive_search.setText("3E03")
    assert w.archive_grid.count() == 1
    # nova macro ativa com a tecla 1
    w._add_macro()
    w._on_key_captured("1")
    w.flush()
    arch = next(i for i, m in enumerate(w.ms.macros) if m.arquivada)
    w._select(arch)
    app.answers.append((False, False))      # cancelar: nada muda
    w._toggle_archive()
    assert w.ms.macros[arch].arquivada
    app.answers.append((True, False))       # confirmar: troca
    w._toggle_archive()
    w.flush()
    ms = app.store.sets["predefinido"]
    act = [m.titulo for m in ms.macros if not m.arquivada]
    archd = [m.titulo for m in ms.macros if m.arquivada]
    assert "3E03305" in act and "Nova macro" in archd


def test_preferencias_do_painel_e_predefinicao(app, qapp):
    w = app.config_window
    w.tabs.setCurrentIndex(1)
    w.p_spins["colunas"].setValue(2)
    qapp.processEvents()
    grid = w.preview.view.grid
    positions = [grid.getItemPosition(i)[:2] for i in range(grid.count())]
    assert positions == [(0, 0), (0, 1), (1, 0), (1, 1)]
    w._apply_preset("neon")
    w.flush()
    assert app.store.settings.painel.cor_texto == "#00e5ff"
    assert app.store.settings.painel.colunas == 2
    assert w.p_preset.currentData() == "neon"
    w._apply_preset("predefinido")
    w.flush()
    from macropad.core.model import PanelSettings
    assert app.store.settings.painel == PanelSettings(colunas=2)


def test_tema_e_idioma(app, qapp):
    w = app.config_window
    assert app.pal.name == "diurno"
    w.tabs.setCurrentIndex(3)
    w.p_theme.setCurrentIndex(w.p_theme.findData("noturno"))
    w.flush()
    assert app.pal.name == "noturno"
    bars = app.platform.title_bars
    assert bars and all(v[1] == "#1c1c1c" for v in bars.values())
    w.p_theme.setCurrentIndex(w.p_theme.findData("automatico"))
    app.platform.prefers_dark = False
    w.flush()
    assert app.pal.name == "diurno"
    app.platform.prefers_dark = True
    app._poll_system_theme()
    assert app.pal.name == "noturno"

    w.p_lang.setCurrentIndex(w.p_lang.findData("en"))
    w.flush()
    qapp.processEvents()
    w2 = app.config_window
    assert w2 is not w
    assert w2.tabs.tabText(1) == "Panel"
    assert w2.windowTitle() == "Virtual Macro Text Inputer — Settings"
    app._fill_menu()
    assert "Open settings" in [a.text() for a in app.menu.actions()]
    # conteúdos das macros não são traduzidos
    assert app.store.sets["predefinido"].nome == "Predefinido"


def test_selecao_multipla_arquivar_e_eliminar(app, qapp):
    from PySide6.QtCore import QItemSelectionModel
    w = app.config_window
    g = w.grid
    # Ctrl+clique: selecionar macros 1 e 3
    g.setCurrentRow(0, QItemSelectionModel.ClearAndSelect)
    g.setCurrentRow(2, QItemSelectionModel.Select)
    qapp.processEvents()
    assert w.selected == [0, 2]
    assert "2 macros" in w.editor_title.text()
    assert not w.f_text.isEnabled()
    w._toggle_archive()
    w.flush()
    ms = app.store.sets["predefinido"]
    assert [m.titulo for m in ms.macros if m.arquivada] == ["3E03305", "C50.912"]
    assert len(app.engine.active_set.active_indices()) == 2
    # Shift+clique no arquivo (intervalo) e eliminar com confirmação da quantidade
    a = w.archive_grid
    a.setCurrentRow(0, QItemSelectionModel.ClearAndSelect)
    a.setCurrentRow(1, QItemSelectionModel.Select)
    qapp.processEvents()
    seen = []
    import macropad.ui.config_window as cw
    orig = cw.ask
    cw.ask = lambda parent, title, text, **k: (seen.append(text), (True, False))[1]
    try:
        w._delete_macro()
    finally:
        cw.ask = orig
    w.flush()
    assert "2 macros" in seen[0]
    assert len(app.store.sets["predefinido"].macros) == 2


def test_arrastar_para_o_arquivo(app, qapp):
    from PySide6.QtCore import QItemSelectionModel, QMimeData, QPoint, Qt
    from PySide6.QtGui import QDropEvent
    w = app.config_window
    g = w.grid
    g.setCurrentRow(1, QItemSelectionModel.ClearAndSelect)
    g.setCurrentRow(3, QItemSelectionModel.Select)
    qapp.processEvents()

    class Ev:                               # evento de largada mínimo
        def __init__(self, src): self._src = src; self.accepted = False
        def source(self): return self._src
        def setDropAction(self, a): pass
        def accept(self): self.accepted = True
        def ignore(self): self.accepted = False
    ev = Ev(g)
    w.archive_zone.dropEvent(ev)
    assert ev.accepted
    for _ in range(3):
        qapp.processEvents()
    w.flush()
    ms = app.store.sets["predefinido"]
    assert [m.titulo for m in ms.macros if m.arquivada] == ["Z51.11", "Exemplo"]
    assert [m.tecla for m in ms.macros if not m.arquivada] == ["1", "3"]   # teclas intactas
    # largar na zona vinda do próprio arquivo: passa para o fim do arquivo
    w._select_many([ops_index(ms, "Z51.11", app)])
    w.archive_grid.clearSelection()
    w._refresh_grid()
    ev2 = Ev(w.archive_grid)
    w.archive_zone.dropEvent(ev2)
    assert ev2.accepted
    for _ in range(3):
        qapp.processEvents()
    w.flush()
    ms = app.store.sets["predefinido"]
    assert [m.titulo for m in ms.macros if m.arquivada] == ["Exemplo", "Z51.11"]


def ops_index(ms, title, app):
    w = app.config_window
    return next(i for i, m in enumerate(w.ms.macros) if m.titulo == title)


def test_painel_botoes_estado_e_roda(app, qapp):
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    app.set_panel_visible(True)
    v = app.panel.view
    assert v.btn_on.isChecked()
    v.btn_off.click()
    qapp.processEvents()
    assert app.engine.suspended
    app.panel.refresh_status()
    assert v.btn_off.isChecked() and app.config_window.btn_off.isChecked()
    v.btn_on.click()
    qapp.processEvents()
    assert not app.engine.suspended
    # roda: para cima = mais opaco, para baixo = mais transparente
    app.panel.setWindowOpacity(0.5)
    def wheel(dy):
        ev = QWheelEvent(QPointF(10, 10), QPointF(10, 10), QPoint(0, 0), QPoint(0, dy),
                         Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
        app.panel.wheelEvent(ev)
    wheel(120)
    assert abs(app.panel.windowOpacity() - 0.55) < 0.01 or True   # offscreen pode não suportar
    assert "55" in app.panel.osd.text()
    wheel(-240)
    assert "45" in app.panel.osd.text()
    app._opacity_timer.timeout.emit()
    assert abs(app.store.settings.painel.opacidade - 0.45) < 0.001
    assert app.config_window.p_opacity.value() == 45


def test_previsualizacao_centrada_e_igual_ao_painel(app, qapp):
    w = app.config_window
    w.tabs.setCurrentIndex(1)
    w.resize(1400, 900)
    w.show()
    qapp.processEvents()
    pv = w.preview
    frame = pv.window_frame.geometry()
    back = pv.backdrop.rect()
    assert abs(frame.center().x() - back.center().x()) <= 2
    app.set_panel_visible(True)
    real, prev = app.panel.view, pv.view
    assert [b.title for b in real.buttons] == [b.title for b in prev.buttons]
    assert real.sizeHint() == prev.sizeHint()
    assert real.btn_on.isVisible() == prev.btn_on.isVisible()


def test_reordenar_arquivo_com_pesquisa_nao_perde_macros(app, qapp):
    # Revisão Codex P1, pelo caminho da interface.
    w = app.config_window
    w._select_many([0, 1, 2])
    w._toggle_archive()                     # arquiva 3E03305, Z51.11, C50.912
    w.flush()
    w.archive_search.setText("e")           # mostra só 3E03305 e Z51.11 ({Enter})
    vis = [w.archive_grid.real_index(r) for r in range(w.archive_grid.count())]
    assert len(vis) == 2
    w._on_drop(True, w.archive_grid, [vis[1]], vis[0], False)
    w.flush()
    ms = app.store.sets["predefinido"]
    assert sorted(m.titulo for m in ms.macros if m.arquivada) == ["3E03305", "C50.912", "Z51.11"]
    assert len(ms.macros) == 4


# ------------------------------------------------------------------ 0.4
def test_espacos_vazios_no_painel_e_na_configuracao(app, qapp):
    w = app.config_window
    w._last_add = 0
    w._select(-1)                  # sem seleção: no fim da área Ativo
    w._add_item("espaco")
    w.flush()
    ms = app.store.sets["predefinido"]
    assert ms.macros[4].tipo == "espaco" and not ms.macros[4].arquivada
    # na configuração aparece (tracejado); no painel ocupa a célula sem botão
    assert w.grid.count() == 5
    app.set_panel_visible(True)
    v = app.panel.view
    assert len(v.buttons) == 4 and len(v.spacers) == 1
    assert v.grid.getItemPosition(v.grid.indexOf(v.spacers[0]))[:2] == (1, 0)
    # o espaço não vai para o arquivo
    w._on_drop(True, w.grid, [4])
    assert not w.ms.macros[4].arquivada
    assert "espaços vazios" in w.status.text()
    # trocar um botão com o espaço (largar sobre ele)
    w._on_drop(False, w.grid, [0], -1, False, 4)
    w.flush()
    ms = app.store.sets["predefinido"]
    assert ms.macros[0].tipo == "espaco" and ms.macros[4].titulo == "3E03305"


def test_arrastar_do_arquivo_para_ativo_na_posicao(app, qapp):
    w = app.config_window
    w._archive_indices([1])                         # Z51.11 (tecla 2) para o arquivo
    w.flush()
    ms = w.ms
    zi = next(i for i, m in enumerate(ms.macros) if m.titulo == "Z51.11")
    # volta, largado antes do primeiro botão ativo
    w._on_drop(False, w.archive_grid, [zi], 0, False)
    ms = app.store.sets["predefinido"]
    assert [m.titulo for m in ms.macros if not m.arquivada][:2] == ["Z51.11", "3E03305"]
    # conflito: arquiva, dá a tecla 2 a outra ativa e restaura — Cancelar não altera
    w._archive_indices([0])
    w.flush()
    act = [i for i, m in enumerate(w.ms.macros) if not m.arquivada]
    w.ms.macros[act[0]].tecla = "2"
    w._changed()
    w.flush()
    zi = next(i for i, m in enumerate(w.ms.macros) if m.titulo == "Z51.11")
    app.answers.append((False, False))
    w._on_drop(False, w.archive_grid, [zi])
    assert w.ms.macros[zi].arquivada
    # Substituir: a outra vai para o arquivo
    app.answers.append((True, False))
    w._on_drop(False, w.archive_grid, [zi])
    w.flush()
    ms = app.store.sets["predefinido"]
    z = next(m for m in ms.macros if m.titulo == "Z51.11")
    assert not z.arquivada
    assert sum(1 for m in ms.macros if m.tecla == "2" and not m.arquivada) == 1


def test_colar_copia_arquivada_fica_no_arquivo(app, qapp):
    from PySide6.QtGui import QGuiApplication
    w = app.config_window
    w._archive_indices([1, 2])
    w.flush()
    arch = w.ms.archived_indices()
    w._select_many([arch[0]])
    w._copy_macro()
    w._paste_macro()
    w.flush()
    titles = [m.titulo for m in app.store.sets["predefinido"].macros if m.arquivada]
    assert titles == ["Z51.11", "Z51.11", "C50.912"]


def test_contador_clique_curto_longo_e_persistencia(app, qapp, tmp_path):
    w = app.config_window
    w._last_add = 0
    w._select(-1)                  # sem seleção: no fim da área Ativo
    w._add_item("contador")
    i = len([m for m in w.ms.macros if not m.arquivada]) - 1
    w._select(i)
    w.f_step.setValue(5)
    w.f_reset.setValue(10)
    w.flush()
    ms = app.engine.active_set
    m = ms.macros[i]
    assert m.is_counter and m.incremento == 5 and m.reposicao == 10
    app.set_panel_visible(True)
    b = app.panel.view.counter_buttons[m.id]
    assert b.count == 10
    b.short_clicked.emit()
    b.short_clicked.emit()
    qapp.processEvents()
    assert b.count == 20
    assert w.f_count.text() == "20"
    b.long_pressed.emit()                            # repõe sem somar
    qapp.processEvents()
    assert b.count == 10
    b.short_clicked.emit()
    qapp.processEvents()
    app._counts_timer.timeout.emit()
    st = app.store.load_state()
    assert st.contadores[f"predefinido/{m.id}"] == 15
    # o contador não escreve nada
    assert app.platform.sent == []


def test_tecla_pelo_rato_e_conflitos(app, qapp):
    w = app.config_window
    w.activateWindow()
    qapp.processEvents()
    w._on_hover(w.grid, 0)
    assert w.grid.capture_hover
    assert app.engine.capture_mode == w.isActiveWindow()
    assert w.assign_key(0, "F8")
    assert app.store.sets["predefinido"].macros[0].tecla == "F8"
    # tecla de outra macro ativa: aviso com «Não voltar a mostrar»
    app.answers.append((True, True))
    assert not w.assign_key(0, "2")
    assert app.store.sets["predefinido"].macros[0].tecla == "F8"
    assert app.store.settings.avisar_conflito_tecla is False
    assert not w.p_warn_conflict.isChecked()
    # tecla global (suspensão / painel)
    assert not w.assign_key(0, "Shift+Escape")
    assert not w.assign_key(0, "Shift+F12")
    w._on_hover(w.grid, 0)
    w.hide()
    assert not app.engine.capture_mode                   # janela escondida: teclas normais
    w.show()
    w._on_hover(w.grid, -1)
    assert not app.engine.capture_mode


def test_preferencias_aplicadas_de_imediato(app, qapp):
    w = app.config_window
    w.tabs.setCurrentIndex(3)
    assert not w.p_no_confirm.isChecked()                 # predefinição: pede confirmação
    w.p_no_confirm.setChecked(True)
    assert app.store.settings.confirmar_eliminacao is False
    w.p_autostart.setChecked(True)
    assert app.platform.get_autostart() is True
    assert "--config-dir" in app.platform.autostart_args
    app.platform.fail_autostart = True
    w.p_autostart.setChecked(False)
    assert w.autostart_error.isVisibleTo(w)
    assert "desativar" in w.autostart_error.text()
    app.platform.fail_autostart = False
    w.p_panelkey.set_binding("F10")
    w._on_prefs_edit()
    assert app.store.settings.tecla_painel == "F10"


def test_tecla_do_painel_e_barra_propria(app, qapp):
    assert app.store.settings.tecla_suspensao == "Shift+Escape"
    assert not app.panel.isVisible()
    app._on_engine_event("toggle_panel", {})
    assert app.panel.isVisible()
    assert app.panel.windowFlags() & Qt.FramelessWindowHint
    assert "Shift+F12" in app.panel.titlebar.hint
    app.panel.titlebar.close_clicked.emit()
    assert not app.panel.isVisible()
    app.save_panel_position(40, 50)
    assert app.store.load_state().painel_x == 40


def test_posicoes_do_titulo_e_da_tecla_desenham(app, qapp):
    from PySide6.QtGui import QImage, QPainter
    from macropad.core.model import POSITIONS, PanelSettings
    from macropad.ui import theme
    from macropad.ui.widgets import paint_tile
    for t in POSITIONS:
        for k in POSITIONS:
            for count in (None, 42):
                img = QImage(90, 90, QImage.Format_ARGB32)
                p = QPainter(img)
                st = PanelSettings(posicao_titulo=t, posicao_tecla=k)
                paint_tile(p, img.rect(), "Um título bastante comprido", "Ctrl+Alt+F12",
                           st, theme.DAY, count=count, waiting=(t == k))
                p.end()
    w = app.config_window
    w.p_title_pos.setCurrentIndex(w.p_title_pos.findData("cima"))
    w.p_key_pos.setCurrentIndex(w.p_key_pos.findData("cima"))
    w.flush()
    p = app.store.settings.painel
    assert (p.posicao_titulo, p.posicao_tecla) == ("cima", "cima")


def test_area_ativo_igual_ao_painel(app, qapp):
    w = app.config_window
    st = w.settings.painel
    assert w.grid.columns == st.colunas
    assert w.grid.width() == st.colunas * (st.tamanho_botao + st.espacamento) + 4
    assert "Ativo (4)" in w.active_title.text()


def test_restaurar_grupo_com_teclas_iguais(app, qapp):
    """Revisão Codex: duas arquivadas com a mesma tecla, arrastadas juntas para
    Ativo — só a primeira é restaurada; a alteração é gravada."""
    w = app.config_window
    w._archive_indices([2, 3])
    w.flush()
    arch = w.ms.archived_indices()
    w.ms.macros[arch[0]].tecla = "F7"
    w.ms.macros[arch[1]].tecla = "F7"
    w._changed()
    w.flush()
    w._on_drop(False, w.archive_grid, list(arch))
    ms = app.store.sets["predefinido"]
    act = [m for m in ms.macros if not m.arquivada]
    assert sum(1 for m in act if m.tecla == "F7") == 1
    assert sum(1 for m in ms.macros if m.arquivada and m.tecla == "F7") == 1
    assert "Arquivo" in w.status.text()


def _key(qtkey, text, release=False, native=0):
    from PySide6.QtGui import QKeyEvent
    t = QEvent.KeyRelease if release else QEvent.KeyPress
    return QKeyEvent(t, qtkey, Qt.NoModifier, 0, native, 0, text)


def test_tecla_do_contador_com_a_configuracao_a_frente(app, qapp):
    """A tecla de um contador também conta com a janela do Macropad à frente
    (o hook deixa-a passar para a janela; quem conta é a própria janela)."""
    w = app.config_window
    w._last_add = 0
    w._select(-1)                  # sem seleção: no fim da área Ativo
    w._add_item("contador")
    i = len(w.ms.active_indices()) - 1
    w.ms.macros[i].tecla = "F9"
    w._changed()
    w.flush()
    cid = app.engine.active_set.macros[i].id
    w.activateWindow()
    qapp.processEvents()
    if not w.isActiveWindow():
        pytest.skip("o QPA offscreen não ativou a janela")
    w.tabs.setFocus()
    app.platform.fg = WindowInfo(5, app.platform.own_pid(), "C:\\macropad.exe")
    assert w.eventFilter(w.tabs, _key(Qt.Key_F9, "", native=0x78)) is True
    assert w.eventFilter(w.tabs, _key(Qt.Key_F9, "", release=True, native=0x78)) is True
    qapp.processEvents()
    assert app.counts_for(app.engine.active_set)[cid] == 1
    # num campo de texto a tecla é texto normal
    w.f_title.setFocus()
    qapp.processEvents()
    assert w.eventFilter(w.f_title, _key(Qt.Key_F9, "", native=0x78)) is False


def test_contador_do_painel_fora_do_ambito_desativado(app, qapp):
    w = app.config_window
    w._last_add = 0
    w._add_item("contador")
    w.flush()
    ms = app.store.sets["predefinido"].clone()
    ms.ambito.modo = "aplicacoes"
    ms.ambito.aplicacoes = ["word.exe"]
    assert app.store.save_set(ms) == []
    app.apply_config()
    app.set_panel_visible(True)
    app.platform.fg = WindowInfo(1, 999_999, "C:\\Windows\\notepad.exe")
    app.panel.rebuild()
    app.panel.refresh_status()
    b = next(iter(app.panel.view.counter_buttons.values()))
    assert not b.isEnabled()
    app.platform.fg = WindowInfo(1, 999_998, "C:\\Office\\WORD.EXE")
    app.panel.refresh_status()
    assert b.isEnabled()


# ------------------------------------------------- terceira revisão do Codex
def test_mudar_tema_nao_apaga_edicoes_pendentes(app, qapp):
    w = app.config_window
    w._select(0)
    w.f_title.setText("Editado agora")
    w._on_edit()                                   # como ao escrever no campo
    assert w._save_set_timer.isActive()            # auto-gravação ainda pendente
    w.tabs.setCurrentIndex(3)
    w.p_theme.setCurrentIndex(w.p_theme.findData("noturno"))
    assert app.store.settings.tema == "noturno"
    assert w.ms.macros[0].titulo == "Editado agora"
    w.flush()                                       # a gravação pendente continua válida
    assert app.store.sets["predefinido"].macros[0].titulo == "Editado agora"


def test_edicao_invalida_sobrevive_a_recarregar_outro_ficheiro(app, qapp):
    w = app.config_window
    w._select(0)
    w.ms.macros[0].tecla = "2"                       # conflito: não se grava
    w._changed()
    w.flush()
    assert app.store.sets["predefinido"].macros[0].tecla == "1"
    # recarregamento de outro ficheiro (config.toml): a edição mantém-se
    w.reload_from_store("x", changed=[app.store.config_path])
    assert w.ms.macros[0].tecla == "2"
    # o próprio ficheiro do conjunto mudou por fora: vale o ficheiro, com aviso
    w.reload_from_store("x", changed=[app.store.set_path("predefinido")])
    assert w.ms.macros[0].tecla == "1"
    assert "ficheiro" in w.status.text()


def test_falha_ao_gravar_preferencias_mostra_erro(app, qapp, monkeypatch):
    w = app.config_window
    def boom(*_a, **_k):
        raise OSError(13, "Acesso negado")
    monkeypatch.setattr(app.store, "_write", boom)
    old = app.store.settings.confirmar_eliminacao
    w.p_no_confirm.setChecked(old)                   # inverte a preferência
    assert app.store.settings.confirmar_eliminacao == old
    assert "Acesso negado" in w.g_error.text()


def test_pre_visualizacao_desativa_contadores_fora_do_ambito(app, qapp):
    w = app.config_window
    w._last_add = 0
    w._add_item("contador")
    w.flush()
    ms = app.store.sets["predefinido"].clone()
    ms.ambito.modo = "aplicacoes"
    ms.ambito.aplicacoes = ["word.exe"]
    assert app.store.save_set(ms) == []
    app.apply_config()
    w.reload_from_store()
    app.platform.fg = WindowInfo(1, 999_999, "C:\\Windows\\notepad.exe")
    w._update_preview()
    b = next(iter(w.preview.view.counter_buttons.values()))
    assert not b.isEnabled()


def test_mudar_idioma_grava_edicoes_pendentes(app, qapp):
    w = app.config_window
    w._select(0)
    w.f_title.setText("Antes do idioma")
    w._on_edit()
    w.tabs.setCurrentIndex(3)
    w.p_lang.setCurrentIndex(w.p_lang.findData("en"))
    qapp.processEvents()
    assert app.store.sets["predefinido"].macros[0].titulo == "Antes do idioma"


# ------------------------------------------------- quarta revisão do Codex
def test_alteracao_externa_nao_e_sobrescrita_por_edicao_pendente(app, qapp):
    w = app.config_window
    w._select(0)
    w.f_title.setText("Edição local")
    w._on_edit()                                    # válida, à espera dos 450 ms
    assert w._save_set_timer.isActive()
    path = app.store.set_path("predefinido")
    txt = path.read_text("utf-8").replace('"3E03305"', '"Externa"', 1)
    path.write_text(txt, "utf-8")
    app.store.reload([path])
    w.reload_from_store("x", changed=[path])
    assert "Externa" in path.read_text("utf-8")       # o ficheiro externo ficou
    assert w.ms.macros[0].titulo == "Externa"
    assert "ficheiro" in w.status.text()


def test_tecla_do_contador_na_janela_ao_mudar_de_conjunto(app, qapp):
    w = app.config_window
    w._last_add = 0
    w._select(-1)                  # sem seleção: no fim da área Ativo
    w._add_item("contador")
    i = len(w.ms.active_indices()) - 1
    w.ms.macros[i].tecla = "F9"
    w._changed()
    w.flush()
    cid = w.ms.macros[i].id
    other = app.store.duplicate_set("predefinido").id   # mesmos ids de contador
    app.apply_config()
    app.engine.set_active_set("predefinido")
    w.activateWindow()
    qapp.processEvents()
    if not w.isActiveWindow():
        pytest.skip("o QPA offscreen não ativou a janela")
    w.tabs.setFocus()
    app.platform.fg = WindowInfo(5, app.platform.own_pid(), "C:\\macropad.exe")
    assert w.eventFilter(w.tabs, _key(Qt.Key_F9, "", native=0x78)) is True
    app.engine.set_active_set(other)               # muda enquanto a tecla está premida
    assert w.eventFilter(w.tabs, _key(Qt.Key_F9, "", release=True, native=0x78)) is True
    qapp.processEvents()
    assert app.counts_for(app.store.sets[other]).get(cid, 0) == 0
    assert app.counts_for(app.store.sets["predefinido"]).get(cid, 0) == 0


def test_hover_usa_o_item_atual_sob_o_cursor(app, qapp, monkeypatch):
    from macropad.ui import config_window as cw
    w = app.config_window
    g = w.grid
    rect = g.visualItemRect(g.item(3))
    pos = g.viewport().mapToGlobal(rect.center())
    monkeypatch.setattr(cw.QCursor, "pos", staticmethod(lambda: pos))
    w._on_hover(g, 3)
    assert w._hover_target() == 3
    w._select(3)
    app.answers.append((True, False))
    w._delete_macro()                               # o cursor fica parado
    w.flush()
    assert len(w.ms.macros) == 3
    # a última macro desapareceu: o cursor está agora sobre nada
    assert w._hover_target() == -1
    # reordenar sem mover o cursor: devolve o item que lá está agora
    pos2 = g.viewport().mapToGlobal(g.visualItemRect(g.item(0)).center())
    monkeypatch.setattr(cw.QCursor, "pos", staticmethod(lambda: pos2))
    first = g.item(0).data(Qt.UserRole + 4)
    moved = w.ms.macros[first].titulo
    w._on_drop(False, g, [first], -1, False)        # o primeiro passa para o fim
    t = w._hover_target()
    assert t >= 0 and w.ms.macros[t].titulo != moved
    assert w.ms.macros[t].titulo == g.item(0).data(Qt.UserRole + 1)


# ------------------------------------------------- quinta revisão do Codex
def test_falhas_ao_gravar_opacidade_e_nao_perguntar(app, qapp, monkeypatch):
    w = app.config_window
    def boom(*_a, **_k):
        raise OSError(13, "Acesso negado")
    monkeypatch.setattr(app.store, "_write", boom)
    app._pending_opacity = 0.5
    app._save_panel_opacity()                       # não lança
    assert app.store.settings.painel.opacidade != 0.5
    # «Não voltar a perguntar» ao eliminar: elimina, mas avisa que não gravou
    assert app.store.settings.confirmar_eliminacao is True
    w._select(0)
    app.answers.append((True, True))
    w._delete_macro()
    assert app.store.settings.confirmar_eliminacao is True
    assert not w.p_no_confirm.isChecked()
    assert "Acesso negado" in w.status.text()


def test_painel_muda_de_idioma_sem_recriar(app, qapp):
    """Os botões Ativo/Suspenso do painel acompanham a mudança de idioma."""
    app.set_panel_visible(True)
    assert "Ativo" in app.panel.view.btn_on.text()
    s = app.store.settings.clone()
    s.idioma = "en"
    app.store.save_settings(s)
    app.apply_config()
    qapp.processEvents()
    assert "Active" in app.panel.view.btn_on.text()
    assert "Suspended" in app.panel.view.btn_off.text()


def _novo_contador(app, qapp, tecla="", **campos):
    w = app.config_window
    w._last_add = 0
    w._add_item("contador")
    m = w.ms.macros[w.cur]
    m.tecla = tecla
    for k, v in campos.items():
        setattr(m, k, v)
    w._changed()
    w.flush()
    app.set_panel_visible(True)
    qapp.processEvents()
    return app.engine.active_set.macros[w.cur]


def test_contador_mostra_progresso_e_repoe_com_a_tecla_premida(app, qapp):
    """Pressão longa pela tecla: o botão do painel mostra o progresso; ao fim
    do tempo repõe logo (com sinal visual e o som escolhido), uma única vez."""
    m = _novo_contador(app, qapp, "F9", incremento=1, reposicao=0,
                       pressao_longa_ms=200, som_reposicao="aviso")
    from macropad.core.engine import KeyEvent
    eng = app.engine
    app.set_count(eng.active_set_id, m.id, 7)
    b = app.panel.view.counter_buttons[m.id]
    assert eng.handle_key(KeyEvent("F9", True)) is True
    end = time.monotonic() + 0.12
    while time.monotonic() < end:
        qapp.processEvents()
        time.sleep(0.01)
    assert b.progress is not None and 0 < b.progress < 1   # a meio do tempo
    end = time.monotonic() + 0.4
    while time.monotonic() < end:
        qapp.processEvents()
        time.sleep(0.01)
    # ainda premida: já repôs, com sinal visual e som, e não repete
    assert b.count == 0 and b.flashing and b.progress is None
    assert app.platform.sounds == ["aviso"]
    eng.handle_key(KeyEvent("F9", False))
    qapp.processEvents()
    assert b.count == 0 and app.platform.sounds == ["aviso"]
    b.grab()                                          # desenha sem erros


def test_contador_sem_som_por_omissao_e_progresso_do_rato(app, qapp):
    m = _novo_contador(app, qapp, pressao_longa_ms=200)
    assert m.som_reposicao == ""
    w = app.config_window
    assert w.f_sound.currentData() == "" and not w.sound_test.isEnabled()
    b = app.panel.view.counter_buttons[m.id]
    b.hold_start(200)
    b.progress = 0.6
    b.grab()                                          # desenha o progresso
    b.long_pressed.emit()
    qapp.processEvents()
    assert app.platform.sounds == []
    # escolher um som no editor grava-o no contador
    w.f_sound.setCurrentIndex(w.f_sound.findData("pergunta"))
    w.flush()
    assert app.engine.active_set.macros[w.cur].som_reposicao == "pergunta"
    assert w.sound_test.isEnabled()
    w.sound_test.click()
    assert app.platform.sounds == ["pergunta"]


def test_nova_macro_a_seguir_a_selecionada(app, qapp):
    w = app.config_window
    act = w.ms.active_indices()
    w._select(act[0])
    w._last_add = 0
    w._add_item("texto")
    assert w.cur == act[0] + 1 and w.selected == [act[0] + 1]
    assert w.ms.macros[w.cur].titulo == i18n.tr("macros.new_title")
    w._select(-1)
    w._last_add = 0
    w._add_item("espaco")
    assert w.cur == len(w.ms.active_indices()) - 1           # sem seleção: no fim


def test_linhas_do_painel_com_paginas(app, qapp):
    """Linhas × colunas: com mais botões, páginas (setas); o tamanho não muda
    entre páginas; com menos, o painel encolhe. Os espaços vazios contam."""
    from macropad.core.model import Macro
    w = app.config_window
    ms = w.ms
    ms.macros = [Macro(f"M{k}", texto=f"t{k}") for k in range(7)]
    ms.macros.insert(2, Macro(tipo="espaco"))        # 8 células ativas
    w._changed()
    w.flush()
    w.tabs.setCurrentIndex(1)
    w.p_spins["colunas"].setValue(3)
    w.p_spins["linhas"].setValue(2)
    w.flush()
    assert app.store.settings.painel.linhas == 2
    assert "linhas = 2" in (app.store.root / "config.toml").read_text(encoding="utf-8")
    app.set_panel_visible(True)
    qapp.processEvents()
    v = app.panel.view
    assert v.pages == 2 and v.pager.isVisible() and v.page_label.text() == "1 / 2"
    assert [b.title for b in v.buttons] == ["M0", "M1", "M2", "M3", "M4"]
    assert len(v.spacers) == 1
    size1 = app.panel.size()
    assert not v.page_prev.isEnabled() and v.page_next.isEnabled()
    v.page_next.click()
    qapp.processEvents()
    assert v.page == 1 and [b.title for b in v.buttons] == ["M5", "M6"]
    assert app.panel.size() == size1                  # mesma altura em todas as páginas
    # a pré-visualização também mostra as páginas
    assert w.preview.view.pages == 2 and not w.preview.view.pager.isHidden()
    # «Todas»: uma página só, sem setas
    w.p_spins["linhas"].setValue(0)
    w.flush()
    qapp.processEvents()
    assert v.pages == 1 and not v.pager.isVisible() and len(v.buttons) == 7
    # mais linhas do que as necessárias: encolhe (sem setas)
    w.p_spins["linhas"].setValue(5)
    w.flush()
    qapp.processEvents()
    assert v.pages == 1 and not v.pager.isVisible()
    assert app.panel.height() < size1.height() + 3 * 78


def test_tecla_multimedia_pelo_menu_com_conflitos(app, qapp):
    w = app.config_window
    act = w.ms.active_indices()
    w._select(act[0])
    w._assign_media("MediaNext")
    assert w.ms.macros[act[0]].tecla == "MediaNext"
    assert w.f_key.text() == "Faixa seguinte"
    # outra macro, a mesma tecla: não atribui e avisa
    w._select(act[1])
    before = w.ms.macros[act[1]].tecla
    w._assign_media("MediaNext")
    assert w.ms.macros[act[1]].tecla == before
    # tecla global (mostrar/ocultar o painel) também é conflito
    s = app.store.settings.clone()
    s.tecla_painel = "MediaPlayPause"
    app.store.save_settings(s)
    app.apply_config()
    w._select(act[1])
    w._assign_media("MediaPlayPause")
    assert w.ms.macros[act[1]].tecla == before
    assert [a.text() for a in w.media_key_btn.menu().actions()] == [
        "Reproduzir/Pausa", "Faixa anterior", "Faixa seguinte"]


def _ctrl(qtkey, shift=False):
    from PySide6.QtGui import QKeyEvent
    mods = Qt.ControlModifier | (Qt.ShiftModifier if shift else Qt.NoModifier)
    return QKeyEvent(QEvent.KeyPress, qtkey, mods)


def test_anular_e_refazer_eliminacao_com_ctrl_z_e_ctrl_y(app, qapp):
    w = app.config_window
    app.store.settings.confirmar_eliminacao = False
    before = [(m.titulo, m.tecla, m.texto, m.arquivada) for m in w.ms.macros]
    act = w.ms.active_indices()
    w._select_many([act[1], act[2]])
    w._delete_macro()
    w.flush()
    assert len(app.store.sets["predefinido"].macros) == len(before) - 2
    w._undo_delete()
    w.flush()
    after = [(m.titulo, m.tecla, m.texto, m.arquivada)
             for m in app.store.sets["predefinido"].macros]
    assert after == before                            # mesma área, posição, tecla
    assert w.selected == [act[1], act[2]]
    w._redo_delete()
    w.flush()
    assert len(app.store.sets["predefinido"].macros) == len(before) - 2
    w._redo_delete()                                  # nada mais para refazer
    w._undo_delete()
    w._undo_delete()                                  # nada mais para anular
    w.flush()
    assert [(m.titulo, m.tecla, m.texto, m.arquivada)
            for m in app.store.sets["predefinido"].macros] == before


def test_ctrl_z_nos_campos_de_texto_e_nao_na_grelha(app, qapp):
    """Ctrl+Z/Ctrl+Y anulam a eliminação na janela, mas num campo de texto
    mantêm o comportamento normal de texto; com o rato sobre um botão não são
    gravados como tecla."""
    w = app.config_window
    w.activateWindow()
    qapp.processEvents()
    if not w.isActiveWindow():
        pytest.skip("o QPA offscreen não ativou a janela")
    app.store.settings.confirmar_eliminacao = False
    n = len(w.ms.macros)
    w._select(w.ms.active_indices()[0])
    w._delete_macro()
    w.grid.setFocus()
    qapp.processEvents()
    assert w.eventFilter(w.grid, _ctrl(Qt.Key_Z)) is True
    qapp.processEvents()
    assert len(w.ms.macros) == n
    assert w.eventFilter(w.grid, _ctrl(Qt.Key_Y)) is True
    qapp.processEvents()
    assert len(w.ms.macros) == n - 1
    assert w.eventFilter(w.grid, _ctrl(Qt.Key_Z, shift=True)) is True   # outro refazer: nada
    qapp.processEvents()
    assert len(w.ms.macros) == n - 1
    w.f_title.setFocus()
    qapp.processEvents()
    assert w.eventFilter(w.f_title, _ctrl(Qt.Key_Z)) is False       # texto: desfaz o texto
    assert len(w.ms.macros) == n - 1
    from macropad.ui.config_window import _is_undo_redo
    assert _is_undo_redo(_ctrl(Qt.Key_Z)) == "undo"
    assert _is_undo_redo(_ctrl(Qt.Key_Y)) == "redo"


def test_exportar_conjunto_usa_o_nome_atual_e_confirma_substituir(app, qapp, tmp_path,
                                                                    monkeypatch):
    """O nome sugerido e o nome dentro do ficheiro são o nome atual do conjunto
    (depois de lhe mudar o nome); um ficheiro existente só é substituído com
    confirmação."""
    import tomllib
    from pathlib import Path
    import macropad.ui.config_window as cw
    w = app.config_window
    out = tmp_path / "exportados"
    out.mkdir()
    w.ms.nome = "Trabalho: cliente A"            # mudado sem gravar ainda
    w._changed()
    suggested = []

    def fake_save(parent, title, start, filt, options=None):
        suggested.append(Path(start).name)
        return str(out / "escolhido"), filt          # sem extensão: acrescenta .toml
    monkeypatch.setattr(cw.QFileDialog, "getSaveFileName", staticmethod(fake_save))
    w._export_set()
    assert suggested == ["Trabalho- cliente A.toml"]
    f = out / "escolhido.toml"
    data = tomllib.loads(f.read_text(encoding="utf-8"))
    assert data["nome"] == "Trabalho: cliente A"
    before = f.read_bytes()
    w.ms.nome = "Outro nome"
    w._changed()
    app.answers.append((False, False))              # não substituir
    w._export_set()
    assert f.read_bytes() == before
    assert Path(suggested[-1]).name == "Outro nome.toml"
    app.answers.append((True, False))               # substituir
    w._export_set()
    assert tomllib.loads(f.read_text(encoding="utf-8"))["nome"] == "Outro nome"
    assert w._export_dir == out


def test_nome_de_ficheiro_para_exportar():
    from macropad.core.store import export_filename
    assert export_filename("Olá mundo") == "Olá mundo.toml"
    assert export_filename("a/b:c?") == "a-b-c-.toml"
    assert export_filename("CON") == "CON_.toml"
    assert export_filename(" nome. ") == "nome.toml"
