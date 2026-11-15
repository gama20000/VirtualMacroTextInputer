"""Mudança de nome para «Virtual Macro Text Inputer» (13-11-2026)."""
from __future__ import annotations

import sys

from macropad import branding
from macropad.__main__ import default_root, legacy_root, migrate_legacy_root


def test_nome_novo_e_pastas(monkeypatch, tmp_path):
    monkeypatch.delenv("MACROPAD_HOME", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert branding.APP_NAME == "Virtual Macro Text Inputer"
    new, old = default_root(), legacy_root()
    if sys.platform == "win32":
        assert new.name == "VirtualMacroTextInputer" and old.name == "Macropad"
    else:
        assert new.name == "virtual-macro-text-inputer" and old.name == "macropad"


def test_migracao_copia_e_mantem_a_pasta_antiga(tmp_path):
    old = tmp_path / "Macropad"
    (old / "conjuntos").mkdir(parents=True)
    (old / "config.toml").write_text("tema = 'noturno'\n", "utf-8")
    (old / "conjuntos" / "predefinido.toml").write_text("x = 1\n", "utf-8")
    new = tmp_path / "VirtualMacroTextInputer"
    assert migrate_legacy_root(new, old) is True
    assert (new / "config.toml").read_text("utf-8") == "tema = 'noturno'\n"
    assert (new / "conjuntos" / "predefinido.toml").exists()
    assert (old / "config.toml").exists()                 # a antiga fica intacta
    # segunda vez (a nova já existe): não volta a copiar nem sobrescreve
    (new / "config.toml").write_text("tema = 'diurno'\n", "utf-8")
    assert migrate_legacy_root(new, old) is False
    assert "diurno" in (new / "config.toml").read_text("utf-8")


def test_sem_pasta_antiga_nao_faz_nada(tmp_path):
    assert migrate_legacy_root(tmp_path / "novo", tmp_path / "nao-existe") is False
    assert not (tmp_path / "novo").exists()
