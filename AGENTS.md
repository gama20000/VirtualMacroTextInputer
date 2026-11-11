# AGENTS.md — Macropad

Instruções para agentes de código (Codex, Claude Code, etc.) que trabalhem
neste repositório. Responde e escreve comentários em **português europeu**.

## O projeto

Macro pad para Windows (inspirado no Virtual Stream Deck). As teclas
configuráveis do teclado (por omissão 1–4 da fila superior) e um painel
flutuante enviam texto com os comandos `{Enter}`, `{Tab}` e `{Delay:ms}` para
a aplicação em primeiro plano, e a tecla original é suprimida.

- Python 3.11+, PySide6 (Qt 6), Win32 via `ctypes`; distribuição com PyInstaller.
- Configuração em TOML em `%APPDATA%\Macropad\` (`config.toml`,
  `conjuntos\*.toml`, `estado.toml`). Os nomes dos campos TOML são em
  português e fazem parte do formato: não os traduzas nem os renomeies sem
  aumentar `versao_esquema` e manter compatibilidade.
- Documentação de utilização: `README.md`. Verificação manual no Windows:
  `docs/VERIFICACAO-MANUAL.md`.

## Estrutura

```
src/macropad/
  core/        # Python puro, sem Qt nem Win32 — tem de continuar portável
    commands.py    interpretação de {Enter} {Tab} {Delay:ms}
    keys.py        nomes de teclas e associações (Ctrl+Alt+P)
    model.py       modelo de dados, predefinições do painel
    configio.py    leitura/validação/escrita TOML (erros com linha e coluna)
    store.py       ficheiros, última versão válida, gravação atómica, hashes anti-ciclo
    watcher.py     observador de ficheiros por polling com agrupamento
    engine.py      decisão de supressão, execução numa thread, cancelamento
    macro_ops.py   arquivo/restauro, duplicados, copiar/colar, reordenação
  i18n.py, locales/*.toml   traduções (pt = base, en)
  platform/
    windows/   hook WH_KEYBOARD_LL, SendInput, área de transferência, DWM, registo Run
    winkeys.py tabela VK -> nome (sem ctypes)
    dummy.py   plataforma simulada (testes e desenvolvimento noutros SO)
  ui/          PySide6: app (tray/tema/idioma), config_window, panel, widgets, theme
tests/         pytest (inclui testes de UI em Qt offscreen e Win32 simulado)
```

Regras de arquitetura:
- `core/` não pode importar Qt nem `ctypes.windll`. O código específico do
  sistema operativo fica em `platform/`.
- Todas as mensagens visíveis ao utilizador passam por `i18n.tr("chave")`.
  Uma chave nova tem de existir em **todos** os `locales/*.toml` (há um teste
  que o verifica). Chavetas literais escrevem-se `{{` e `}}`.
- Os títulos e conteúdos das macros nunca são traduzidos nem alterados.

## Comandos

```powershell
# ambiente (uma vez)
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"

# testes
.\.venv\Scripts\python -m pytest -q

# testes sem escrever no disco (modo só de leitura / sandbox)
$env:PYTHONDONTWRITEBYTECODE=1; .\.venv\Scripts\python -m pytest -q -p no:cacheprovider

# executar a partir do código
.\run-dev.ps1

# gerar a distribuição (dist\Macropad\Macropad.exe)
.\build.ps1
```

Em Linux/macOS os testes também correm: o Qt usa `QT_QPA_PLATFORM=offscreen`
e a plataforma é simulada (`DummyPlatform`).

Antes de dar uma tarefa por concluída: os testes passam, e as alterações de
comportamento estão refletidas no `README.md` e, se aplicável, em
`docs/VERIFICACAO-MANUAL.md`.

## Review guidelines

Numa revisão, **não alteres ficheiros**: analisa e reporta. Para cada problema
indica a severidade (**P0** crítico / **P1** importante / **P2** menor), o
`ficheiro:linha`, o que acontece, como reproduzir e a correção sugerida.
Distingue bugs confirmados de suspeitas e termina com uma tabela-resumo
ordenada por severidade.

Zonas de maior risco, por prioridade:

1. **Concorrência.** `Engine.handle_key` é chamado pela thread do hook de
   teclado, a execução de macros corre noutra thread e a UI recebe eventos
   por sinais Qt (`_Bridge`). Procura condições de corrida, estado partilhado
   sem lock, deadlocks e chamadas a widgets Qt fora da thread principal. O
   callback do hook tem de ser rápido: se exceder o LowLevelHooksTimeout
   (cerca de 1 s), o Windows remove o hook sem aviso.
2. **Win32/ctypes** (`platform/windows/`). Tamanhos e tipos das estruturas
   (`INPUT` = 40 bytes em x64, `KBDLLHOOKSTRUCT`), `argtypes`/`restype`,
   handles de 64 bits, área de transferência (`GlobalAlloc`/`SetClipboardData`),
   DWM e registo. São erros que só aparecem no Windows real.
3. **Supressão de teclas.** keydown/keyup desemparelhados, auto-repetição,
   modificadores (`exatos`/`ignorar`, AltGr = Ctrl+Alt), tecla de suspensão
   (também durante `{Delay}`), eventos injetados pelo próprio programa
   (`MAGIC_EXTRA_INFO`), teclas nas janelas do próprio Macropad e mudança de
   janela durante a execução.
4. **Configuração** (`core/store.py`, `core/watcher.py`, `core/configio.py`).
   Um ficheiro inválido nunca pode substituir a última configuração válida.
   Verifica também a gravação atómica, os ciclos UI↔ficheiro, os editores que
   gravam por substituição, a compatibilidade com ficheiros antigos (campos
   novos opcionais) e que um recarregamento nunca reative macros suspensas.
5. **Interface** (`ui/config_window.py`, `ui/widgets.py`, `ui/panel.py`).
   Índices reais das macros depois de reordenar, arquivar, restaurar
   (incluindo a substituição em caso de conflito de tecla) ou eliminar com
   seleção múltipla; arrastar para o Arquivo; atalhos Delete/Backspace,
   Ctrl+C e Ctrl+V, que só atuam fora de campos de edição; o painel nunca
   pode receber foco (`WS_EX_NOACTIVATE`); a pré-visualização tem de ser
   igual ao painel real.
6. **i18n.** Chaves em falta, `str.format` com chavetas, textos visíveis que
   não passam por `tr()`.

Não reportes como bugs: o estilo do código, os nomes em português, as
limitações já documentadas no README (aplicações executadas como
administrador, UIPI, cor da barra de título no Windows 10).
