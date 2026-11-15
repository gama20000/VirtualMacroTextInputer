# Answers

*Portuguese original: [docs/pt/ANSWERS.md](docs/pt/ANSWERS.md).*

Decisions already made. The user's original requests are in the conversation
of 11-11-2026 and in the first commits of the git history.

## Q-001: Technology stack

- **Resolved:** 2026-11-11
- **Answer:** Python 3.11+ with PySide6 (Qt 6), Win32 through `ctypes`, and
  distribution with PyInstaller.
- **Rationale:** Allows a pure-Python core, testable without Windows. Qt also
  works on Linux (future version). `ctypes` gives direct access to the
  `WH_KEYBOARD_LL` hook, `SendInput` and `WS_EX_NOACTIVATE`.
- **Evidence:** Proposal presented before implementation and accepted by the
  user by continuing; `README.md`, Architecture section.
- **Consequences:** The hook callback must be minimal because of the GIL and
  LowLevelHooksTimeout. There was no validation on real Windows during
  development (see **Manual validation method**).
- **Revisit when:** The Python hook proves unreliable on real Windows.

## Q-002: Defaults not fixed in the request

- **Resolved:** 2026-11-11
- **Answer:**
  - Suspend hotkey `Ctrl+Alt+P` (later changed, see `Q-020`).
  - Macros may have no key (panel only).
  - A line break in the text equals `{Enter}` and a tab equals `{Tab}`.
  - Keys pressed in the program's own windows never trigger macros.
  - Saving from the interface rewrites the TOML in the standard format;
    hand-written comments are lost.
- **Rationale:** Routine technical choices that the request delegated.
- **Evidence:** Summary of the 0.1 delivery to the user; `README.md`.
- **Consequences:** Documented in the README.
- **Revisit when:** The user asks for different behaviour.

## Q-003: «New macro» behaviour and macros without text

- **Resolved:** 2026-11-11
- **Answer:** «New macro» creates a single macro, with no key and empty text.
  A macro with empty text is not an error: it does nothing until it has text.
- **Rationale:** The user asked for a single macro, with no fields generated
  from the number of existing macros (version 0.1 assigned a key
  automatically). Allowing empty text lets the new macro save immediately.
- **Evidence:** Request of round 0.2, point 6; `core/macro_ops.py::new_macro`;
  `tests/test_macro_ops.py`.
- **Consequences:** Macros with empty text are not included in duplicate
  detection.
- **Revisit when:** Never.

## Q-004: Confirmation when deleting several macros

- **Resolved:** 2026-11-11
- **Answer:** Deleting several macros always asks for confirmation with the
  count, even with «Don't ask again» on. That option only applies to single
  deletions.
- **Rationale:** It is a bulk destructive action, and the request requires a
  confirmation with the count.
- **Evidence:** Request of round 0.3, point 3; `ui/config_window.py::_delete_macro`.
- **Consequences:** None.
- **Revisit when:** The user wants the option to apply to both cases.

## Q-005: Pasted copy with a key already in use

- **Resolved:** 2026-11-11
- **Answer:** A pasted copy gets no key when the original key is already
  assigned to an active macro.
- **Rationale:** Avoids creating a key conflict that would block saving.
- **Evidence:** `core/macro_ops.py::insert_copy`; `tests/test_macro_ops.py`.
- **Consequences:** None.
- **Revisit when:** Never.

## Q-006: Git remote layout

- **Resolved:** 2026-11-11
- **Answer:** The local repository has a single `origin` remote with two push
  URLs (Forgejo and GitHub), instead of Forgejo mirroring automatically to
  GitHub.
- **Rationale:** The user asked which option is more resilient. With two push
  URLs there is no single point of failure: if one server fails, the other
  still receives and git shows the error. A mirror depends on the Forgejo
  server and can stop working without anyone noticing.
- **Evidence:** The user's answer («Which of these is more resilient?») and the
  recommendation given.
- **Consequences:** Each `git push` sends to both; valid credentials are needed
  for both.
- **Revisit when:** There are more contributors, or CI depends on one of the
  remotes.

## Q-007: GitHub repository name

- **Resolved:** 2026-11-11 (updated 2026-11-15)
- **Answer:** `VirtualMacroTextInputer`, the same name as the Forgejo
  repository and the program. The first proposal, `virtual-visual-vext`
  («Virtual & Visual Vext»), was replaced when the program was renamed
  (`Q-026`).
- **Rationale:** One name everywhere avoids confusion between the program, the
  Forgejo repository and the GitHub repository.
- **Evidence:** The user's answers of 11-11-2026 and 13-11-2026.
- **Consequences:** GitHub redirects the old URL if the repository is renamed
  later.
- **Revisit when:** The user prefers another name.

## Q-008: Where Forgejo runs

- **Resolved:** 2026-11-11
- **Answer:** Forgejo is installed on a server, not on the PC nor on a public
  service such as Codeberg.
- **Rationale:** The user's choice.
- **Evidence:** The user's answer («Install on a server»).
- **Consequences:** See `Q-012`.
- **Revisit when:** No server is available.

## Q-009: Independent review tool

- **Resolved:** 2026-11-11
- **Answer:** The review is done by Codex CLI in read-only mode, guided by the
  «Review guidelines» in `AGENTS.md`. Findings are confirmed in the code before
  any fix.
- **Rationale:** A review by an agent that did not write the code. Automatic
  reviews bring false positives, hence the confirmation.
- **Evidence:** `AGENTS.md`. Codex CLI was not yet installed on the user's PC
  at the time (the `codex` command was not found).
- **Consequences:** The review phase depends on Codex being installed and
  signed in.
- **Revisit when:** Codex cannot be installed or used.

## Q-010: GitHub repository visibility

- **Resolved:** 2026-11-15
- **Answer:** Public.
- **Rationale:** The user's choice.
- **Evidence:** The user's answer of 15-11-2026.
- **Consequences:** Personal data is removed from the published files and
  history before the first push: the Forgejo address and username, local
  paths with the Windows user name, and the personal e-mail in commits
  (`Q-029`). A licence is still to be chosen (see ROADMAP, fog).
- **Revisit when:** The code should no longer be public.

## Q-011: Agent access to GitHub

- **Resolved:** 2026-11-15
- **Answer:** The user connects their GitHub account to Claude, and the agent
  creates the repository and pushes the history.
- **Rationale:** The user's choice.
- **Evidence:** The user's answer of 15-11-2026.
- **Consequences:** Later pushes from the PC go through the `origin` remote
  with both push URLs (`Q-006`) and need GitHub credentials on the PC (Git
  Credential Manager asks once).
- **Revisit when:** The GitHub connection is removed.

## Q-012: Forgejo server

- **Resolved:** 2026-11-13
- **Answer:** The user installed Forgejo on their own server and created the
  private repository `VirtualMacroTextInputer` there (first called
  `Macropad`). It is only reachable through the user's Tailscale network, over
  HTTP. The address is in the local git configuration, not in the repository.
  The user pushed the history from the PC.
- **Rationale:** The user handled the installation; the agent does not
  administer the server.
- **Evidence:** The user's messages of 13-11-2026 and the repository address.
- **Consequences:** `Q-014`, `Q-015` and `Q-016` (access method, address and
  installation method) are no longer project decisions. The agent cannot reach
  the server from its environment (private network), so pushes to Forgejo are
  done by the user with `git push`. Tailscale already encrypts the traffic;
  HTTPS on Forgejo itself is still open (`Q-025`).
- **Revisit when:** The server or address changes, or access outside
  Tailscale is needed.

## Q-013: Codex CLI installation

- **Resolved:** 2026-11-12
- **Answer:** The user ran the review with Codex on their PC.
- **Rationale:** What the independent review of Phase 1 needed.
- **Evidence:** Report pasted by the user on 12-11-2026, stored in
  `docs/CODEX-REVIEW.md`.
- **Consequences:** Later reviews (for example `/review` on a commit) can use
  the same installation.
- **Revisit when:** Never.

## Q-017: Handling the review findings

- **Resolved:** 2026-11-12
- **Answer:** Both points (P1 and P2) were confirmed with failing tests and
  then fixed. There are no points accepted without a fix and no false
  positives.
- **Rationale:** The P1 caused data loss (archived macros deleted from the
  TOML). The P2 had low impact, but the fix is defensive and trivial.
- **Evidence:** `docs/CODEX-REVIEW.md`; the regression tests listed there;
  `pytest` with 110 tests passing.
- **Consequences:** Phase 1 meets its exit criteria.
- **Revisit when:** A new review or the manual validation finds related
  problems.

## Q-018: Manual validation method

- **Resolved:** 2026-11-12
- **Answer:** The agent runs the checklist on the PC through screen control. It
  uses the `tools\macropad-teste.cmd` launcher, which starts the application
  with `python.exe` (with a console) and a separate configuration in
  `%TEMP%\MacropadTeste`. The user does the steps the agent cannot do (👤 in
  `docs/MANUAL-CHECKLIST.md`). The user may also run the whole checklist.
- **Rationale:** The user asked the agent to do the steps. A separate
  configuration protects the real macros. The terminal only accepts clicks
  from the agent, so the application starts from a `.cmd` opened in Explorer.
- **Evidence:** The user's request of 12-11-2026; results recorded in
  `docs/MANUAL-CHECKLIST.md`.
- **Consequences:**
  - The agent cannot right-click in the taskbar (icon menu), press keypad 1,
    restart the session or answer UAC: those steps are left to the user.
  - The single-instance mutex is shared: if an instance is already running
    (real or test), the launcher only opens its settings.
  - The program's windows belong to the Microsoft Store Python 3.12
    `pythonw`/`python` and are only visible to the agent after that process is
    authorised.
- **Revisit when:** The `.exe` built by PyInstaller has to be tested (a
  different process, which needs a new authorisation).

## Q-019: Button icon and title/key position

- **Resolved:** 2026-11-12
- **Answer:** Buttons no longer have the «[T]» icon, and the «Show icon»
  option is gone. The title and the key can each be at the top, centre or
  bottom of the button.
- **Rationale:** The 0.4 request removes icons «for now» (point 10) and asks
  for title and key positions (point 7). Without an icon, positions are
  relative to the button.
- **Evidence:** The user's answer of 12-11-2026.
- **Consequences:** The `mostrar_icone` option in old files is still accepted
  but ignored. Preset styles no longer use it.
- **Revisit when:** Icons on the buttons are requested again.

## Q-020: Default global keys

- **Resolved:** 2026-11-12
- **Answer:** Suspend/resume with **Shift+Escape**; show/hide the panel with
  **Shift+F12**. Configurations that still have the old `Ctrl+Alt+P` are
  migrated to Shift+Escape once (recorded in `estado.toml`). If the migration
  cannot be saved (conflict or write error), it is retried at the next start.
- **Rationale:** The user asked for Shift+Escape for both functions. Since a
  combination can only have one function, they chose this split and asked for
  the current configuration to be migrated.
- **Evidence:** The user's answers of 12-11-2026.
- **Consequences:** Macros cannot use either global key, and the two must
  differ.
- **Revisit when:** The user changes the keys in Preferences (their choice).

## Q-021: How the counter works

- **Resolved:** 2026-11-12
- **Answer:** The counter works on the panel and with an assigned key, and only
  shows the value (it types no text). A tap adds; holding resets. Scope and
  suspend apply to the key as they do to macros. The count is saved in
  `estado.toml` (per set and counter) and the configuration in the set file.
- **Rationale:** The user's answer. Saving the count outside the set's TOML
  avoids rewriting that file, and reloading it, on every click.
- **Evidence:** The user's answer of 12-11-2026.
- **Consequences:** Each counter has a stable `id`. A long press never adds.
  A counter key pressed with the settings window in front is counted the same
  way. Since 15-11-2026 the reset happens when the long-press time is reached,
  not on release ([Q-032](#q-032-counter-reset-while-held-and-sound)).
- **Revisit when:** The counter is asked to type its value.

## Q-022: Assigning a key over a button and existing shortcuts

- **Resolved:** 2026-11-12
- **Answer:** With the pointer over a button, Delete, Backspace, Tab, Ctrl+C
  and Ctrl+V keep their functions (delete, navigate, copy, paste). Other keys
  and combinations are assigned. While the pointer is over a button (with the
  settings window active), global keys are not intercepted, so that the
  conflict can be explained. Assignment only happens with the focus outside
  edit fields.
- **Rationale:** Avoids deleting or assigning keys by mistake while typing in a
  field with the mouse resting on a button, and keeps the shortcuts already
  requested.
- **Evidence:** Points 6 (version 0.2) and 9 (version 0.4) of the requests.
- **Consequences:** To assign Delete or Backspace to a macro, use the «Key»
  field in the editor.
- **Revisit when:** The user wants to assign those keys over a button.

## Q-023: Panel title bar

- **Resolved:** 2026-11-12
- **Answer:** The panel no longer has a Windows frame. It draws its own title
  bar (the same as the preview), in the theme colours, with drag-to-move and a
  close button.
- **Rationale:** On real Windows, the panel's native title bar (a tool window
  without focus) did not follow the theme, and the request requires the panel
  to match the preview. A custom bar is identical in both.
- **Evidence:** Steps 36 and 58 of `docs/MANUAL-CHECKLIST.md` (partial).
- **Consequences:** The panel is moved with its own bar. Its position is now
  saved.
- **Revisit when:** The custom bar has drag or focus problems.

## Q-026: New program name

- **Resolved:** 2026-11-13
- **Answer:** The program is now called **Virtual Macro Text Inputer** (windows,
  icon next to the clock, `VirtualMacroTextInputer.exe`, data folder
  `%APPDATA%\VirtualMacroTextInputer`, startup entry `VirtualMacroTextInputer`).
  The Python package and source files are still `macropad`.
- **Rationale:** The user's request, after renaming the repository. Renaming
  the Python package too would mean renaming all the code and tests with no
  visible benefit.
- **Evidence:** The user's message of 13-11-2026.
- **Consequences:** On the first start, `%APPDATA%\Macropad` is copied to the
  new folder (the old one stays as a backup). The «Macropad» startup entry is
  deleted when the new one is written. If the old version is running, the new
  program warns and does not start (two hooks would type macros twice). The
  visible name lives in `src/macropad/branding.py`. Manual steps 87–89.
- **Revisit when:** The name changes again, or the Python package should be
  renamed too.

## Q-027: Repository location on the PC

- **Resolved:** 2026-11-15
- **Answer:** The repository now lives in
  `%USERPROFILE%\source\VirtualMacroTextInputer`, outside Google Drive. It was
  created with a local `git clone` of the old folder (full history), with
  `origin` pointing to Forgejo and the same author settings.
- **Rationale:** The user does not want the repository inside the folder
  synchronised by Google Drive. `Documents` was ruled out because it shows
  signs of being synchronised too (`.tmp.drivedownload`).
- **Evidence:** The user's messages of 15-11-2026 and the choice «source
  folder».
- **Consequences:** The `.venv` environment is not copied (it is not
  portable): it is recreated with `run-dev.ps1`. The old folder in Google
  Drive stays until the user decides to delete it.
- **Revisit when:** The repository moves again.

## Q-028: Documentation language

- **Resolved:** 2026-11-15
- **Answer:** English at the repository root and in `docs/` (README, SPEC,
  ROADMAP, TASKS, ANSWERS, AGENTS, `docs/MANUAL-CHECKLIST.md`,
  `docs/CODEX-REVIEW.md`); the Portuguese versions in `docs/pt/`. The English
  files are the reference; both are updated together. `AGENTS.md` asks agents
  to answer the maintainer in European Portuguese. Code comments, TOML field
  names and the Portuguese UI strings are unchanged.
- **Rationale:** The user's choice when publishing on GitHub: an English front
  page for a public repository, while keeping the documentation in
  Portuguese.
- **Evidence:** The user's answer of 15-11-2026 («English at the root, PT in a
  folder»).
- **Consequences:** Two copies of each document to keep in sync; links in
  `docs/pt/` are relative to that folder.
- **Revisit when:** Keeping both languages becomes a burden.

## Q-029: E-mail in the commits

- **Resolved:** 2026-11-15
- **Answer:** Before the first public push, the history is rewritten so that
  author and committer use the GitHub private e-mail
  (`<id>+<user>@users.noreply.github.com`) instead of the personal e-mail. The
  local `user.email` is changed to the same address.
- **Rationale:** In a public repository the commit e-mail is visible to
  anyone. The user chose the GitHub private address.
- **Evidence:** The user's answer of 15-11-2026.
- **Consequences:** Commit identifiers change; Forgejo has to receive the
  rewritten history with `git push --force` (done by the user). Clones of the
  old history must be discarded.
- **Revisit when:** Never.

## Q-030: Licence

- **Resolved:** 2026-11-15
- **Answer:** MIT. `LICENSE` at the root, copyright «gama20000» (the GitHub
  account name, not a personal name).
- **Rationale:** The user's choice. MIT is the most permissive common licence:
  anyone may reuse the code, keeping the notice.
- **Evidence:** The user's message of 15-11-2026.
- **Consequences:** `pyproject.toml` declares `license = "MIT"` (SPDX) and `license-files = ["LICENSE"]`.
- **Revisit when:** The user wants a copyleft licence.

## Q-031: Panel rows and pages

- **Resolved:** 2026-11-15
- **Answer:** The panel has a number of rows besides the columns («All» by
  default, `linhas = 0`). With more cells than rows × columns, it shows pages
  with ◀ ▶ arrows, and every page has the full size. With fewer, the panel
  shrinks to the rows it needs.
- **Rationale:** The user's choice among pages, scrolling or hiding the
  surplus. Pages are how a Stream Deck works; a fixed size across pages keeps
  the buttons in place when changing page.
- **Evidence:** The user's answers of 15-11-2026.
- **Consequences:** `[painel] linhas` in `config.toml` (0–12). Style presets
  keep the rows, as they keep the columns. Keys run macros on any page. The
  settings Active area keeps showing every macro.
- **Revisit when:** The user wants the panel to keep a fixed size even with
  few buttons.

## Q-032: Counter reset while held, and sound

- **Resolved:** 2026-11-15
- **Answer:** While a counter is held (mouse or key), its panel button shows
  the progress along its border; at the long-press time the count resets
  immediately, once, with a green flash. The reset sound is configured per
  counter: none by default, or a Windows system sound (`som_reposicao`).
- **Rationale:** The user's request and answer (sound per counter).
- **Evidence:** The user's messages of 15-11-2026.
- **Consequences:** The engine starts a timer when the key goes down; release
  only adds if the reset has not happened. The settings window uses the same
  engine logic. The progress shows on the panel; the settings Active area does
  not animate.
- **Revisit when:** A counter needs its own custom sound file.

## Q-033: Media keys

- **Resolved:** 2026-11-15
- **Answer:** Play/Pause, previous track and next track are assigned from a
  «Media» menu next to the key field, with the same conflict checks as a key
  assigned with the mouse. The keys are shown with readable names; the file
  keeps the canonical names (`MediaPlayPause`, `MediaPrev`, `MediaNext`).
- **Rationale:** Pressing a media key to record it also reaches the music
  player, because the hook lets keys through while recording.
- **Evidence:** The user's request of 15-11-2026; `platform/winkeys.py`
  already mapped the virtual-key codes.
- **Consequences:** Suspended or outside the scope, the keys pass to Windows.
  Keyboards whose media keys only send `WM_APPCOMMAND` (no virtual-key code)
  are not seen by the keyboard hook; to be confirmed on the user's keyboard.
- **Revisit when:** A keyboard's media keys do not reach the hook.

## Q-034: Single-file release

- **Resolved:** 2026-11-15
- **Answer:** Releases are a single `VirtualMacroTextInputer.exe` (PyInstaller
  `--onefile`) with its SHA-256, built by GitHub Actions on `windows-latest`
  when a `vX.Y.Z` tag is pushed. `build.ps1 -OneFile` builds the same file on
  the user's PC; `build.ps1` without it keeps the folder build.
- **Rationale:** The agent's environment is Linux and PyInstaller does not
  cross-compile, so the build must run on Windows. A clean CI machine gives
  the same result every time and publishes the release by itself; the local
  build stays available for quick tests. The repository is public, so the
  Actions minutes are free.
- **Evidence:** The user's questions and the note that the repository is
  public (15-11-2026).
- **Consequences:** The executable is unsigned (SmartScreen warning on first
  run). A single file starts 1–3 s slower (it unpacks to a temporary folder)
  and is more likely to trigger antivirus heuristics than the folder build.
  The workflow refuses a tag that does not match `pyproject.toml`.
- **Revisit when:** A code-signing certificate is available, or after a
  rewrite (Rust, `Q-024`) that produces a small native executable.

