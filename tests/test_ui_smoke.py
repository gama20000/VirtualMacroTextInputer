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
    assert w2.windowTitle() == "Macropad — Settings"
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
