# Virtual Macro Text Inputer

*Documentação em português: [docs/pt/README.md](docs/pt/README.md).*

> Vibe-coded with Claude and reviewed by Codex.
>
> This app lets me quickly enter short text snippets by clicking a button on a transparent on-screen panel or pressing a keyboard hotkey. I asked Claude to build it to meet a very specific need at work. It was strongly inspired by Virtual Stream Deck. One day, I forgot to bring my physical Stream Deck, so I asked Claude to recreate the concept in software. Claude built the core functionality in a single pass, with no errors that I noticed.

<p align="center">
  <img src="docs/images/settings.png" alt="Settings window: the Active area looks like the panel, with an empty space and a counter; the editor below" width="460">
  &nbsp;
  <img src="docs/images/panel.png" alt="Floating panel in the Night theme, with its own title bar" width="340">
</p>

A software macro pad for Windows. Ordinary keyboard keys (by default 1–4 on the top row) and an optional floating panel type predefined text into the application in the foreground. Pressing **1** types `Greetings`, and the 1 itself does not appear.

## Main features

- **Text on a key or a button.** Each macro has a title, a key (or none) and a text, which can include `{Enter}`, `{Tab}` and `{Delay:500}`.
- **Floating panel** that never steals the focus from the application you are typing in, with adjustable transparency, columns, rows and pages, and preset styles.
- **Counters**: buttons that count presses; holding one resets it, with the progress shown along its border.
- **Media buttons**: Play/Pause, previous/next track and volume, with simple icons.
- **Sets** of macros, each one global or limited to chosen applications, with an Archive for macros you are not using.
- **Comfortable editing**: drag and drop, assign a key by hovering a button and pressing it, copy/paste, undo a deletion, warnings for conflicts and duplicates.
- **Global suspend key** (`Shift+Escape`) and panel key (`Shift+F12`), working even in the middle of a macro.
- **Day, Night and Automatic themes**; Portuguese and English interface.
- **Plain TOML files** that you can edit by hand, reloaded automatically.

## Install

**Download.** The [Releases](https://github.com/gama20000/VirtualMacroTextInputer/releases) page has `VirtualMacroTextInputer.exe`, a single file that needs no installation and no Python. Put it wherever you like (for example `%LOCALAPPDATA%\Programs\VirtualMacroTextInputer`) and run it. It is not digitally signed, so on the first run Windows SmartScreen may say «Windows protected your PC»: **More info ▸ Run anyway**.

**From source** (Windows 10/11, Python 3.11 or later):

```powershell
git clone https://github.com/gama20000/VirtualMacroTextInputer.git
cd VirtualMacroTextInputer
.\run-dev.ps1              # run from source, with a console
.\build.ps1 -OneFile       # or build dist\VirtualMacroTextInputer.exe
```

## Quick start

1. Run the program. An icon appears next to the clock; click it to open the settings.
2. In the *Macros* tab, select a button, type its **Text**, and hover it and press a key to assign it.
3. Press that key in any application, or press `Shift+F12` and click the button on the panel.
4. `Shift+Escape` suspends and resumes all macros.

## Documentation

- [EXAMPLES.md](EXAMPLES.md): ready-to-use macros (forms, repetitions, counters, a media panel, per-application sets).
- [ARCHITECTURE.md](ARCHITECTURE.md): the full guide and reference: every setting, advanced options, commands, configuration files, limitations, code structure, building and tests.
- Project documents: [SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md), [TASKS.md](TASKS.md), [ANSWERS.md](ANSWERS.md), [docs/MANUAL-CHECKLIST.md](docs/MANUAL-CHECKLIST.md), [docs/CODEX-REVIEW.md](docs/CODEX-REVIEW.md). Portuguese versions in [docs/pt/](docs/pt/).

## About

Until version 0.4 it was called **Macropad**; settings from that version are moved over automatically on the first start ([details](ARCHITECTURE.md#migration-from-macropad)). Releases are built and tested by GitHub Actions on a clean Windows machine.

## Licence

MIT — see [LICENSE](LICENSE).
