# Independent review — Codex

*Portuguese version: [pt/revisao-codex.md](pt/revisao-codex.md).*

Reviews done by Codex in read-only mode, following the «Review guidelines» in
`AGENTS.md`. Codex did not change files or run the tests. Every finding was
confirmed in the code before being fixed. Test names are in Portuguese, as in
the code.

# First review (12-11-2026)

## Report (summary)

| Severity | File:line | Problem |
|---|---|---|
| P1 | `ui/config_window.py:874` | Reordering filtered Archive results can delete hidden archived macros |
| P2 | `core/engine.py:348` | A negative index in `Engine.trigger` can run the last macro |

### P1 — Reordering the Archive with the search active deletes the hidden macros

`_on_reordered` passed to `reorder_group` only the indices visible in the
Archive grid. With a search active, those indices are only the results.
`reorder_group` then rebuilt the group from those indices alone and dropped the
other archived macros.

Reported reproduction: archive several macros, search so that some are hidden,
drag a result to change the order and let it save. The hidden macros
disappear from the set and from the TOML file.

### P2 — `Engine.trigger(-1)` can run the last macro

`trigger` only validated the index inside the branch that checks for archived
or empty macros. `_start` did not reject negative indices, which Python reads
as positions counted from the end of the list.

## Confirmation

| Point | Classification | Evidence |
|---|---|---|
| P1 | **Confirmed** | `tests/test_macro_ops.py::test_reordenar_arquivo_filtrado_preserva_macros_ocultas` failed before the fix (5 macros became 3) |
| P2 | **Confirmed** | `tests/test_engine.py::test_trigger_com_indice_fora_do_intervalo_nao_executa` failed before the fix |

The P2 only shows if something calls `trigger` with an invalid index. The panel
always uses valid real indices, so the practical impact was low. It was fixed
anyway, because the fix is trivial and defensive.

No point was classified as a false positive, and none depends on a check on
Windows.

## Fixes

- **P1** — `core/macro_ops.py::reorder_group`: the visible macros swap
  positions among themselves, taking the positions they already had. Hidden
  ones stay where they are and no macro is dropped. An invalid order
  (repeated indices, out of range or from the other group) changes nothing.
  - Tests: `test_reordenar_arquivo_filtrado_preserva_macros_ocultas`,
    `test_reordenar_grupo_ignora_indices_do_outro_grupo` and, through the
    interface, `tests/test_ui_smoke.py::test_reordenar_arquivo_com_pesquisa_nao_perde_macros`.
- **P2** — `core/engine.py`: `trigger` rejects any index outside
  `0 <= index < len(macros)` up front, and `_start` also rejects negative
  indices.
  - Test: `test_trigger_com_indice_fora_do_intervalo_nao_executa`.

Validation: `pytest` with 110 tests passing and 1 skipped (the Win32 sizes
test, which only runs on Windows).

---

# Second review (version 0.4, 12-11-2026)

Codex confirmed that the two previous findings are fixed and reported four bugs
and one suspicion. The user added a problem found in use: a counter's key did
not count, but clicking the button did.

| Point | Classification | Evidence | Fix |
|---|---|---|---|
| Suspend hotkey migration recorded even when it fails | **Confirmed** | `test_config.py::test_migracao_falhada_nao_fica_marcada` | `store.migrate` only records the migration when saving succeeds; otherwise it keeps `Ctrl+Alt+P`, reports the conflict and retries at the next start |
| Restoring as a group two archived macros with the same key | **Confirmed** | `test_ui_smoke.py::test_restaurar_grupo_com_teclas_iguais` | only the first is restored; the others stay in the Archive, with a message; the change is saved |
| Panel counters outside the scope | **Confirmed** | `test_engine.py::test_contador_no_painel_respeita_o_ambito`, `test_ui_smoke.py::test_contador_do_painel_fora_do_ambito_desativado` | `Engine.counter_allowed` (suspend + scope) in `counter_press`; panel counter buttons are disabled outside the scope |
| Counter key counts after suspending | **Confirmed** | `test_engine.py::test_contador_revalida_ao_largar_a_tecla` | on release, suspend and scope are checked again; the counter `id` is stored instead of the index |
| `GlobalLock` failure not handled (suspicion) | **Confirmed by reading** (not reproducible without forcing the failure on Windows) | `platform/windows/__init__.py::_set_clipboard` | checks the pointer; if null, frees the block and raises; `GlobalUnlock` in a `finally` |
| Counter key does not count (user) | **Confirmed** | `test_ui_smoke.py::test_tecla_do_contador_com_a_configuracao_a_frente` | cause: with one of the program's windows in front, the hook lets every key through (the rule that avoids typing into its own windows). Counters type nothing, so the settings window counts them itself when the focus is not in a text field and the mouse is not over a button |

Validation: `pytest` with 142 tests passing and 1 skipped (Windows only).

---

# Third review (13-11-2026)

No P0. Codex confirmed that the findings of the previous reviews are fixed. All
new points were confirmed by reading the code and now have a test that
reproduces the scenario (races are reproduced by calling the intermediate step
directly).

| Point | Fix | Test |
|---|---|---|
| P1 — Changing the theme loses pending edits | the theme only updates the look (`ConfigWindow.set_palette`); `reload_from_store` first saves valid edits and keeps invalid ones, unless that very file changed externally (then it warns); closing/recreating the window (language) also saves | `test_mudar_tema_nao_apaga_edicoes_pendentes`, `test_edicao_invalida_sobrevive_a_recarregar_outro_ficheiro`, `test_mudar_idioma_grava_edicoes_pendentes` |
| P1 — A key runs a macro from another set | `_start` receives the set snapshot used for the event and refuses if the active set changed | `test_tecla_nao_executa_macro_de_outro_conjunto` |
| P2 — A macro starts after suspending | `_start` checks the suspend state again under the lock | `test_suspensao_entre_verificacao_e_arranque` |
| P2 — Counter of the wrong set | the keydown stores the set; if it changed, the keyup does not count; the event carries `set_id` | `test_contador_premido_ao_mudar_de_conjunto_nao_conta` |
| P2 — Modifiers still held after 1.5 s | the execution is cancelled (nothing is sent) and a warning appears | `test_modificadores_premidos_alem_do_prazo_cancelam` |
| P2 — A write failure leaves preferences changed in memory | `save_settings` writes before updating memory; the interface shows the write error | `test_falha_de_escrita_nao_altera_preferencias_em_memoria`, `test_falha_ao_gravar_preferencias_mostra_erro` |
| P2 — Preview with counters enabled outside the scope | receives the same state (suspend and `counter_allowed`) as the real panel | `test_pre_visualizacao_desativa_contadores_fora_do_ambito` |
| P2 — Simultaneous suspend toggles | read and flip under the same lock | `test_alternancias_simultaneas_da_suspensao` |
| P2 — `join()` on a thread not yet started | `shutdown` only waits if the thread has started | `test_encerrar_com_execucao_ainda_nao_iniciada` |

Validation: `pytest` with 154 tests passing and 1 skipped (Windows only).

---

# Fourth review (13-11-2026)

| Point | Classification | Fix | Test |
|---|---|---|---|
| P1 — External reload overwritten by a pending edit | **Confirmed**: `reload_from_store` saved the local copy before looking at the changed paths | the changed paths are checked first; a pending edit whose file changed externally is discarded without being saved and a warning appears | `test_alteracao_externa_nao_e_sobrescrita_por_edicao_pendente` |
| P1 — Paste mode fails (`OpenClipboard(NULL)`) | **Confirmed by the Microsoft documentation** (`EmptyClipboard` with a NULL owner makes `SetClipboardData` fail); still to be confirmed on real Windows | a message-only window as owner; data prepared before emptying the clipboard; results of `EmptyClipboard`/`SetClipboardData` checked; memory freed on failure | `test_windows_layer.py::test_area_de_transferencia_*` (simulated API) |
| P2 — Counter in the wrong set (key in the settings window) | **Confirmed** | stores the set on press; if it changed on release, it does not count | `test_tecla_do_contador_na_janela_ao_mudar_de_conjunto` |
| P2 — Hover with a stale index | **Confirmed** | when assigning, looks up the item currently under the cursor; the grid recomputes the hover when rebuilt | `test_hover_usa_o_item_atual_sob_o_cursor` |
| P2 (suspicion) — Rebuild holding the hook's lock | **Confirmed by reading** | the set snapshot is built outside the lock and published in a short critical section (`set_config`, `set_active_set`) | `test_reconstrucao_do_conjunto_fora_do_lock` |

Validation: `pytest` with 161 tests passing and 1 skipped (Windows only). Paste
mode needs manual step 86 on Windows.

---

# Fifth review (13-11-2026)

Codex confirmed the fourth review's fixes and reported three problems.

| Point | Fix | Test |
|---|---|---|
| P1 — «Paste» into another window after waiting for the clipboard | `send_text(..., still_ok=...)`: after preparing the clipboard and right before Ctrl+V, the target window is checked again; if it changed, nothing is pasted and the execution is cancelled | `test_colar_revalida_a_janela_antes_do_ctrl_v` |
| P2 — Race in the hook state | the suppression decision and the macro start use the same snapshot, under the lock (only quick lookups; plans are still built outside); if the start is refused, the key goes to the application; counters use `counter_press_id`, which checks the set and applies the operation under the lock | `test_tecla_nao_se_perde_se_o_retrato_mudar`, `test_decisao_e_arranque_sob_o_mesmo_lock`, `test_contador_por_id_so_no_mesmo_conjunto` |
| P2 — Unhandled write failures | migration (start continues with the old key and warns), panel transparency (warning on the icon), «Don't ask again» (deletes, warns and does not mark the preference as saved) | `test_migracao_com_falha_de_escrita_nao_interrompe`, `test_falhas_ao_gravar_opacidade_e_nao_perguntar` |

Validation: `pytest` with 167 tests passing and 1 skipped (Windows only).

---

# Sixth review (13-11-2026)

Codex confirmed the fifth review's fixes and reported one point.

| Point | Fix | Test |
|---|---|---|
| P2 — `PlatformAPI` without the `still_ok` parameter | the `Protocol` declares `still_ok: Optional[Callable[[], bool]] = None`, with the contract description | `test_backends_seguem_o_contrato_da_plataforma` (compares the `Protocol` signature with each backend's: simulated, test and, on Windows, the real one) |

Validation: `pytest` with 168 tests passing and 1 skipped (Windows only).
