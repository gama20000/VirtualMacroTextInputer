# Roadmap

*Portuguese version: [docs/pt/ROADMAP.md](docs/pt/ROADMAP.md).*

## Destination

See [SPEC.md](SPEC.md#destination).

## Current state

The code is at version 0.5 and the program is now called Virtual Macro Text
Inputer. Phase 1 (independent review) and Phase 2 (version 0.4, including the
panel's own title bar) are complete. Since then, six Codex reviews have been
addressed, and version 0.5 (counter progress and reset while held, insertion
after the selection, panel rows with pages, media keys, undoing a deletion)
is implemented; 187 automated tests pass (one skipped outside Windows). Manual validation on Windows is still
missing (Phase 3, paused since 12-11-2026, with 16 steps checked and 3
partial; steps 62–89 cover 0.4 and the rename, steps 90–99 cover 0.5). The
repository is on the user's Forgejo (private, through Tailscale) and public on
GitHub; releases with a single `.exe` are built by GitHub Actions (Phase 4).

## Open decisions

### Frontier

- [ ] **Rewrite in Rust** (`Q-024`): is it worth rewriting the program in Rust
  for a lighter executable with faster start-up? The decision should wait for
  the validation of the Python version (Phase 3), which fixes the behaviour to
  reproduce.

### Blocked

- (none)

### Fog

- Forgejo backups (what to keep, where, how often).
- HTTPS on Forgejo (`Q-025`): today access is only through the Tailscale
  network (already encrypted), over HTTP. Only needed if Forgejo must be
  reachable outside Tailscale.
- Versioning the distributed executable (git tags, zip name, release notes).
- Autostart with administrator privileges (Task Scheduler) for anyone who
  needs macros in elevated applications.

### Completed

- [x] [Technology stack](ANSWERS.md#q-001-technology-stack) (`Q-001`): Python + PySide6 + ctypes + PyInstaller.
- [x] [Defaults not fixed in the request](ANSWERS.md#q-002-defaults-not-fixed-in-the-request) (`Q-002`): macros without a key, line break = `{Enter}`.
- [x] [«New macro» behaviour and macros without text](ANSWERS.md#q-003-new-macro-behaviour-and-macros-without-text) (`Q-003`): one macro, no key, empty text allowed.
- [x] [Confirmation when deleting several macros](ANSWERS.md#q-004-confirmation-when-deleting-several-macros) (`Q-004`): always, with the count.
- [x] [Pasted copy with a key already in use](ANSWERS.md#q-005-pasted-copy-with-a-key-already-in-use) (`Q-005`): the copy gets no key.
- [x] [Git remote layout](ANSWERS.md#q-006-git-remote-layout) (`Q-006`): one `origin` with two push URLs.
- [x] [GitHub repository name](ANSWERS.md#q-007-github-repository-name) (`Q-007`): `VirtualMacroTextInputer`.
- [x] [Where Forgejo runs](ANSWERS.md#q-008-where-forgejo-runs) (`Q-008`): on a server.
- [x] [Independent review tool](ANSWERS.md#q-009-independent-review-tool) (`Q-009`): read-only Codex CLI with `AGENTS.md`.
- [x] [GitHub repository visibility](ANSWERS.md#q-010-github-repository-visibility) (`Q-010`): public.
- [x] [Agent access to GitHub](ANSWERS.md#q-011-agent-access-to-github) (`Q-011`): the user connects GitHub to Claude.
- [x] [Forgejo server](ANSWERS.md#q-012-forgejo-server) (`Q-012`): installed by the user, through Tailscale. Makes `Q-014`, `Q-015` and `Q-016` unnecessary.
- [x] [Codex CLI installation](ANSWERS.md#q-013-codex-cli-installation) (`Q-013`): the user ran the review on the PC.
- [x] [Handling the review findings](ANSWERS.md#q-017-handling-the-review-findings) (`Q-017`): P1 and P2 confirmed and fixed.
- [x] [Manual validation method](ANSWERS.md#q-018-manual-validation-method) (`Q-018`): screen control with a separate configuration; the user does the 👤 steps.
- [x] [Button icon and title/key position](ANSWERS.md#q-019-button-icon-and-titlekey-position) (`Q-019`): no icon; title and key at the top, centre or bottom.
- [x] [Default global keys](ANSWERS.md#q-020-default-global-keys) (`Q-020`): Shift+Escape suspends; Shift+F12 shows/hides the panel.
- [x] [How the counter works](ANSWERS.md#q-021-how-the-counter-works) (`Q-021`): panel and key, display only; holding resets.
- [x] [Assigning a key over a button and existing shortcuts](ANSWERS.md#q-022-assigning-a-key-over-a-button-and-existing-shortcuts) (`Q-022`): Delete, Backspace, Tab, Ctrl+C and Ctrl+V are kept.
- [x] [Panel title bar](ANSWERS.md#q-023-panel-title-bar) (`Q-023`): the panel draws its own bar.
- [x] [New program name](ANSWERS.md#q-026-new-program-name) (`Q-026`): Virtual Macro Text Inputer; data copied from the old folder.
- [x] [Repository location on the PC](ANSWERS.md#q-027-repository-location-on-the-pc) (`Q-027`): `%USERPROFILE%\source\VirtualMacroTextInputer`, outside Google Drive.
- [x] [Documentation language](ANSWERS.md#q-028-documentation-language) (`Q-028`): English at the root, Portuguese in `docs/pt/`.
- [x] [Licence](ANSWERS.md#q-030-licence) (`Q-030`): MIT.
- [x] [Panel rows and pages](ANSWERS.md#q-031-panel-rows-and-pages) (`Q-031`): pages with arrows; the panel shrinks with few buttons.
- [x] [Counter reset while held, and sound](ANSWERS.md#q-032-counter-reset-while-held-and-sound) (`Q-032`): resets at the long-press time; sound per counter, none by default.
- [x] [Media keys](ANSWERS.md#q-033-media-keys) (`Q-033`): assigned from a «Media» menu.
- [x] [Single-file release](ANSWERS.md#q-034-single-file-release) (`Q-034`): `build.ps1 -OneFile` locally; GitHub Actions on `vX.Y.Z` tags.
- [x] [E-mail in the commits](ANSWERS.md#q-029-e-mail-in-the-commits) (`Q-029`): GitHub private address; history rewritten.

## Phase 1: Independent review and fixes — complete (12-11-2026)

### Outcome

The code was reviewed by an independent agent, and the confirmed P0/P1
problems are fixed or accepted by a recorded decision.

### Included work

- Install or open Codex and run the full (read-only) review.
- Confirm each finding in the code; record false positives.
- Fix the confirmed problems, with a regression test whenever possible.

### Dependencies and risks

- Depended on **Codex CLI installation** (`Q-013`), now resolved.
- Risk: problems that only show on real Windows (hook, `SendInput`, focus)
  cannot be confirmed by reading the code alone. They move to Phase 3 as
  specific checks.
- Rollback: each fix in its own commit (`git revert`).

### Exit criteria

- The review report is stored (`docs/CODEX-REVIEW.md`), with the confirmation
  result of each point.
- No confirmed P0/P1 is left unresolved without a decision recorded in
  `ANSWERS.md`.

### Validation

- `pytest` with no failures.
- New regression tests for the fixed problems that are testable outside
  Windows.

## Phase 2: Version 0.4 — panel layout, shortcuts and preferences — complete (12-11-2026)

### Outcome

The 12 points of the 12-11-2026 request are implemented, together with the
panel title bar fix. The version becomes 0.4.

### Included work

- Empty spaces in the grid; counters; no icon; title and key position.
- Active/Archive areas with drag in both directions and insertion at the drop
  position; paste into the Archive; Active area with the panel's look,
  centred.
- Key assignment over a button, with conflict warnings that can be turned off.
- Global keys Shift+Escape (suspend, with migration) and Shift+F12 (panel,
  shown on the panel).
- Preferences that apply immediately: start with Windows (including the
  Windows startup approval) and delete confirmation (inverted wording), with
  an error indication.
- The panel's own title bar (`Q-023`), with its position saved.

### Dependencies and risks

- Old files (`mostrar_icone`, `Ctrl+Alt+P`) must remain valid.
- Dragging between grids in Qt (`QListWidget`) needs custom drop handling so
  that the source grid does not remove items.
- Rollback: one commit for the version; `git revert`.

### Exit criteria

- Each point has its behaviour covered by automated tests, or a manual check
  described in `docs/MANUAL-CHECKLIST.md`.
- `pytest` with no failures; interface screenshots (Day and Night) reviewed.

### Validation

- Automated: new core tests (spaces, counters, positional insertion, paste
  into the Archive, migration, global key conflicts) and interface tests (Qt
  offscreen).
- Manual: new steps added to the checklist, run in Phase 3.

## Phase 3: Manual validation on Windows and distribution — paused

### Outcome

The program is validated on real Windows, from source and from the executable.

### Included work

- Go through steps 1–99 of `docs/MANUAL-CHECKLIST.md` with `run-dev.ps1`, and
  then with `dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe` built by
  `build.ps1`.
- Fix the failures found, each with its check repeated.
- Add to the checklist the checks that Phase 1 identified as Windows-dependent.

### Dependencies and risks

- Depends on Phases 1 and 2.
- The steps are done by the agent through screen control (`Q-018`) or by the
  user. Steps 2, 23, 26, 27, 32, 33, 84, 85 and 89 are for the user.
- Risk: PyInstaller may leave out resources (`ui/assets`, `locales`). Check
  icons and translations in the executable.

### Exit criteria

- Every step of `docs/MANUAL-CHECKLIST.md` is marked OK or has a limitation
  accepted in `ANSWERS.md`.
- The acceptance criteria in [SPEC.md](SPEC.md#acceptance-criteria) are met
  with the executable.

### Validation

- Manual: the full checklist, in the Day and Night themes and in Portuguese
  and English.
- Automated: `pytest` with no failures, also run by `build.ps1`.

## Phase 4: Forgejo and publishing — in progress

### Outcome

The repository is published on Forgejo (private) and GitHub (public), and a
single `git push` updates both.

### Included work

- Forgejo installed by the user (`Q-012`); repository `VirtualMacroTextInputer`.
- Documentation in English at the root and Portuguese in `docs/pt/` (`Q-028`).
- History rewritten with the GitHub private e-mail (`Q-029`) and personal data
  removed from the published files.
- Create the public `VirtualMacroTextInputer` repository on GitHub and push.
- Configure `origin` with both push URLs; the user pushes the rewritten
  history to Forgejo with `--force`.
- Document in the README how to clone and push.

### Dependencies and risks

- Needs the GitHub connection (`Q-011`).
- Rewriting the history changes every commit identifier; old clones must be
  discarded.
- Credentials: SSH keys or tokens never go into the repository.

### Exit criteria

- `git push` updates both remotes, and `git ls-remote` on both shows the same
  commit.
- The public repository contains no personal e-mail, Forgejo address or local
  user paths (files and history).
- Forgejo answers (over HTTP through Tailscale; HTTPS only if `Q-025` requires
  it) and survives a server restart.

### Validation

- Manual: clone from each remote into a new folder and run `pytest`.
- Automated: search the published history for the personal e-mail and private
  addresses.
