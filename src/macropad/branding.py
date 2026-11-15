"""Nome do programa, num só sítio.

O pacote Python continua a chamar-se ``macropad`` (nome interno); o que o
utilizador vê — janelas, ícone junto ao relógio, executável, pasta de dados e
entrada de arranque com o Windows — usa o nome abaixo."""
from __future__ import annotations

APP_NAME = "Virtual Macro Text Inputer"
EXE_NAME = "VirtualMacroTextInputer"          # executável, pasta de dados, registo
LINUX_DIR_NAME = "virtual-macro-text-inputer"

# Nome anterior (até à versão 0.4): para migrar a pasta de dados, limpar a
# entrada antiga de arranque e não deixar correr as duas versões ao mesmo tempo.
LEGACY_NAME = "Macropad"
LEGACY_LINUX_DIR_NAME = "macropad"
