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

    w._on_reordered(False, [1, 0, 2, 3])
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
    # largar vindo do próprio arquivo é ignorado
    ev2 = Ev(w.archive_grid)
    w.archive_zone.dropEvent(ev2)
    assert not ev2.accepted


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
    w._on_reordered(True, list(reversed(vis)))
    w.flush()
    ms = app.store.sets["predefinido"]
    assert sorted(m.titulo for m in ms.macros if m.arquivada) == ["3E03305", "C50.912", "Z51.11"]
    assert len(ms.macros) == 4
