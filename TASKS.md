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
- [ ] Rewrite the history with the GitHub private e-mail (`Q-029`).
  - Acceptance criteria: no commit has the personal e-mail as author or
    committer; no file in any commit contains the Forgejo address or local
    user paths; local `user.email` is the GitHub private address.
  - Automated validation: `git log --format='%ae %ce' | sort -u`; `git grep`
    over all revisions.
  - Dependencies or blockers: the GitHub connection (`Q-011`) to learn the
    account id and username.
- [ ] Create the public `VirtualMacroTextInputer` repository on GitHub and push.
  - Acceptance criteria: GitHub shows the English README; `origin` has both
    push URLs.
  - Manual validation: the user runs `git push --force` to Forgejo, then a
    normal `git push`, and both remotes show the same commit.
  - Dependencies or blockers: the previous task.
- [ ] README: how to clone and push.
- [x] Licence: MIT (`Q-030`), `LICENSE` at the root.

## Paused: Phase 3 — Manual validation on Windows and distribution

Paused since 12-11-2026 at the user's request; resumes when the user
authorises it.

- [ ] Go through the checklist from source (`tools\macropad-teste.cmd`).
  - Scope: steps 1–89 of `docs/MANUAL-CHECKLIST.md`, except the 👤 ones; each
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
