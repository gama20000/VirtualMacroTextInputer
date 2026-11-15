# AGENTS.md — Virtual Macro Text Inputer

Instructions for coding agents (Codex, Claude Code, etc.) working in this
repository. **Answer the maintainer, and write code comments, in European
Portuguese.** Documentation is kept in English (root and `docs/`) with
Portuguese translations in `docs/pt/` (see «Documentation» below).

## The project

A macro pad for Windows (inspired by Virtual Stream Deck). It was called
Macropad until version 0.4; the visible name comes from
`src/macropad/branding.py` and the Python package is still `macropad`.
Configurable keyboard keys (by default 1–4 on the top row) and a floating
panel send text with the `{Enter}`, `{Tab}` and `{Delay:ms}` commands to the
application in the foreground, and the original key is suppressed.

- Python 3.11+, PySide6 (Qt 6), Win32 through `ctypes`; distribution with
  PyInstaller.
- TOML configuration in `%APPDATA%\VirtualMacroTextInputer\` (`config.toml`,
  `conjuntos\*.toml`, `estado.toml`). TOML field names are in Portuguese and
  are part of the format: do not translate or rename them without raising
  `versao_esquema` and keeping compatibility.
- User documentation: `README.md`. Manual check on Windows:
  `docs/MANUAL-CHECKLIST.md` (results recorded in
  `docs/pt/VERIFICACAO-MANUAL.md`).

## Planning

Work is planned with four documents at the root (wayfinder skill): `SPEC.md`
(destination and acceptance criteria), `ROADMAP.md` (open decisions and
phases), `TASKS.md` (current phase tasks) and `ANSWERS.md` (decision record).
Read them before starting. Do not implement a phase without authorisation and
do not mark tasks as done without the required validation.

## Documentation

- English at the root and in `docs/` is the reference; `docs/pt/` holds the
  Portuguese versions (`README.md`, `SPEC.md`, `ROADMAP.md`, `TASKS.md`,
  `ANSWERS.md`, `VERIFICACAO-MANUAL.md`, `revisao-codex.md`).
- When a document changes, update both languages in the same commit.
- Links inside `docs/pt/` are relative to that folder.
- Do not put personal data in the repository (it is public on GitHub): no
  e-mails, private server addresses or local paths with user names.

## Structure

```
src/macropad/
  branding.py  # visible program name (and the previous one, for migration)
  core/        # pure Python, no Qt or Win32 — must stay portable
    commands.py    parsing of {Enter} {Tab} {Delay:ms}
    keys.py        key names and bindings (Ctrl+Alt+P)
    model.py       data model, panel defaults
    configio.py    TOML read/validate/write (errors with line and column)
    store.py       files, last valid version, atomic writes, anti-loop hashes
    watcher.py     polling file watcher with coalescing
    engine.py      suppression decision, execution thread, cancellation
    macro_ops.py   archive/restore, duplicates, copy/paste, reordering
  i18n.py, locales/*.toml   translations (pt = base, en)
  platform/
    windows/   WH_KEYBOARD_LL hook, SendInput, clipboard, DWM, Run registry key
    winkeys.py VK -> name table (no ctypes)
    dummy.py   simulated platform (tests and development on other OSes)
  ui/          PySide6: app (tray/theme/language), config_window, panel, widgets, theme
tests/         pytest (includes UI tests on Qt offscreen and simulated Win32)
```

Architecture rules:
- `core/` must not import Qt or `ctypes.windll`. OS-specific code lives in
  `platform/`.
- Every user-visible message goes through `i18n.tr("key")`. A new key must
  exist in **every** `locales/*.toml` (a test checks this). Literal braces are
  written `{{` and `}}`.
- Macro titles and contents are never translated or changed.

## Commands

```powershell
# environment (once)
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"

# tests
.\.venv\Scripts\python -m pytest -q

# tests without writing to disk (read-only mode / sandbox)
$env:PYTHONDONTWRITEBYTECODE=1; .\.venv\Scripts\python -m pytest -q -p no:cacheprovider

# run from source
.\run-dev.ps1

# build the distribution (dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe)
.\build.ps1
```

On Linux/macOS the tests also run: Qt uses `QT_QPA_PLATFORM=offscreen` and the
platform is simulated (`DummyPlatform`).

Before calling a task done: the tests pass, and behaviour changes are
reflected in `README.md` (both languages) and, where relevant, in the manual
checklist.

## Review guidelines

In a review, **do not change files**: analyse and report. For each problem
give the severity (**P0** critical / **P1** important / **P2** minor), the
`file:line`, what happens, how to reproduce it and the suggested fix.
Distinguish confirmed bugs from suspicions and end with a summary table
ordered by severity.

Highest-risk areas, by priority:

1. **Concurrency.** `Engine.handle_key` is called by the keyboard hook thread,
   macros run in another thread and the UI receives events through Qt signals
   (`_Bridge`). Look for race conditions, shared state without a lock,
   deadlocks and calls to Qt widgets outside the main thread. The hook
   callback must be fast: if it exceeds LowLevelHooksTimeout (about 1 s),
   Windows removes the hook silently.
2. **Win32/ctypes** (`platform/windows/`). Structure sizes and types (`INPUT` =
   40 bytes on x64, `KBDLLHOOKSTRUCT`), `argtypes`/`restype`, 64-bit handles,
   clipboard (`GlobalAlloc`/`SetClipboardData`), DWM and registry. These are
   errors that only show on real Windows.
3. **Key suppression.** Unpaired keydown/keyup, auto-repeat, modifiers
   (`exatos`/`ignorar`, AltGr = Ctrl+Alt), the suspend hotkey (also during
   `{Delay}`), events injected by the program itself (`MAGIC_EXTRA_INFO`), keys
   in the program's own windows and window changes during execution.
4. **Configuration** (`core/store.py`, `core/watcher.py`, `core/configio.py`).
   An invalid file must never replace the last valid configuration. Also check
   atomic writes, UI↔file loops, editors that save by replacing, compatibility
   with old files (new fields optional) and that a reload never reactivates
   suspended macros.
5. **Interface** (`ui/config_window.py`, `ui/widgets.py`, `ui/panel.py`). Real
   macro indices after reordering, archiving, restoring (including replacement
   on a key conflict) or deleting with multiple selection; dragging to the
   Archive; Delete/Backspace, Ctrl+C and Ctrl+V shortcuts, which only act
   outside edit fields; the panel must never receive focus
   (`WS_EX_NOACTIVATE`); the preview must match the real panel.
6. **i18n.** Missing keys, `str.format` with braces, visible text that does not
   go through `tr()`.

Do not report as bugs: code style, Portuguese names, limitations already
documented in the README (applications run as administrator, UIPI, title bar
colour on Windows 10).
