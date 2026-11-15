# Tasks

*Portuguese version: [docs/pt/TASKS.md](docs/pt/TASKS.md).*

## Current phase: Phase 4 — Forgejo and publishing (in progress)

- [x] Private `VirtualMacroTextInputer` repository on the user's Forgejo
  (`Q-012`); history pushed by the user.
  - Validation: push done by the user. The agent cannot reach the server
    (Tailscale network), so it did not run `git ls-remote`.
- [x] Documentation in English at the root, Portuguese in `docs/pt/` (`Q-028`),
  without personal data (Forgejo address and username, local user paths).
  - Validation: links between documents checked by script; search for the
    private data in the files.
- [x] History rewritten (`Q-029`): author and committer
  `gama20000 <87977333+gama20000@users.noreply.github.com>` in every commit;
  Forgejo address, Forgejo username and local user paths removed from files
  and messages in every revision.
  - Validation: `git log --format='%an %ae %cn %ce' | sort -u` and `git grep`
    over all revisions found nothing personal.
- [x] GitHub repository `gama20000/VirtualMacroTextInputer` created by the user
  (public since 15-11-2026) and pushed; `origin` has both push URLs.
  - Validation: the user's `git push --force` updated Forgejo and the next
    `git push` created `main` on GitHub (15-11-2026).
- [x] README: how to clone and push.
- [x] GitHub repository made public by the user (15-11-2026).
- [x] Single-file build: `build.ps1 -OneFile` (`Q-034`).
- [ ] Release workflow (`.github/workflows/release.yml`): first run.
  - Acceptance criteria: pushing tag `v0.5.0` publishes a release with
    `VirtualMacroTextInputer.exe` and its `.sha256`; the downloaded file runs
    on the user's PC.
  - Manual validation: the user pushes the tag and opens the downloaded `.exe`.
  - Dependencies or blockers: the user pushes the commit and the tag; the
    workflow has not run yet (it can only run on GitHub).
- [x] Licence: MIT (`Q-030`), `LICENSE` at the root.

## Paused: Phase 3 — Manual validation on Windows and distribution

Paused since 12-11-2026 at the user's request; resumes when the user
authorises it.

- [ ] Go through the checklist from source (`tools\macropad-teste.cmd`).
  - Scope: steps 1–99 of `docs/MANUAL-CHECKLIST.md`, except the 👤 ones; each
    step's result is recorded there.
  - Acceptance criteria: every non-👤 step is ✅, or has a fix task or a
    limitation accepted in `ANSWERS.md`.
  - Progress: 16 steps ✅ (1, 4, 5, 7, 11–14, 18–20, 34, 39, 59–61), 3 partial
    (36, 40, 58). Steps 36 and 58 are repeated with the panel's own title bar.
- [ ] Steps the user has to do (👤): 2, 23, 26, 27, 32, 33, 84, 85, 89.
- [ ] Repeat the check with the executable (`build.ps1` →
  `dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe`): the acceptance
  criteria in [SPEC.md](SPEC.md#acceptance-criteria), plus icons and
  translations included.

## Completed

### Version 0.5 (15-11-2026)

- [x] Counter: progress along the panel button's border while held (mouse or
  key); reset at the long-press time, once, with a green flash; optional sound
  per counter (`Q-032`).
- [x] New macro, counter or empty space inserted right after the selected
  macro; with nothing selected, at the end of the Active area.
- [x] Panel rows, with pages and ◀ ▶ arrows when the buttons do not fit
  (`Q-031`); preview and real panel updated; saved in `config.toml`.
- [x] Media keys (Play/Pause, previous, next) from a «Media» menu, with the
  usual conflict checks; normal behaviour when suspended or outside the scope
  (`Q-033`).
- [x] Ctrl+Z / Ctrl+Y undo and redo deleting macros (same area, position,
  settings and key); text fields keep their own Ctrl+Z.
  - Validation: `pytest` 186 pass, 1 skipped; screenshots of the panel with
    pages, progress and flash checked. Residual risk: steps 90–99 on Windows
    (system sounds, media keys on the user's keyboard, real timing).

### New name: Virtual Macro Text Inputer (13-11-2026)

- [x] Visible name in windows, icon, executable, data folder and startup
  (`Q-026`); copy of the old folder; old startup entry removed; warning if the
  old version is running. `pytest`: 171 pass, 1 skipped. Residual risk: steps
  87–89 on Windows.

### Codex reviews 2 to 6 (12-11-2026 to 13-11-2026)

- [x] All findings confirmed and fixed, each with a regression test; details
  in `docs/CODEX-REVIEW.md`. Residual risk: paste mode is only confirmed by
  manual step 86 on Windows.

### Phase 2 — Version 0.4 (12-11-2026)

- [x] Core, engine, interface, panel, real Windows autostart, translations,
  README, checklist (steps 62–85) and version 0.4.0. `pytest`: 136 pass, 1
  skipped; offscreen screenshots (Day and Night) reviewed. Residual risk: real
  mouse dragging, the hook with capture over a button and the frameless title
  bar are only confirmed on Windows (Phase 3).

### Phase 1 — Independent review and fixes (12-11-2026)

- [x] Codex review run by the user and stored; P1 and P2 confirmed with
  failing tests and fixed (`Q-017`). `pytest`: 110 pass, 1 skipped.
