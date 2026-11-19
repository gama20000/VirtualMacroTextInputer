# Manual check on Windows

*Portuguese version, where results are recorded: [pt/VERIFICACAO-MANUAL.md](pt/VERIFICACAO-MANUAL.md).*

These points cannot be tested automatically: they depend on the real keyboard hook, window focus and the notification area. Check with `.\run-dev.ps1` (the console shows errors) and repeat with `dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe`.

OK column legend: ✅ checked · ◐ partial · ❌ failed · ☐ to check ·
👤 must be done by the user. The 12-11-2026 check was done by the agent (screen
control) with `tools\macropad-teste.cmd`, which uses a separate configuration
in `%TEMP%\MacropadTeste`. The results are recorded in the Portuguese version;
this table mirrors them.

How to start:

1. Close any running instance (icon next to the clock ▸ Quit), including the
   old «Macropad».
2. Double-click `tools\macropad-teste.cmd`. It opens the program with the test
   configuration, without touching your real macros.
3. Steps marked ✅ were checked on version 0.3; you can repeat them on 0.4.
   Steps 36 and 58 (panel title bar) must be repeated, because the panel now
   has its own bar.
4. In the test configuration, the «Exemplo» macro (key 4) has the text
   `a{Delay:5000}b` with 3 repetitions, from step 14. For step 5, set it back
   to `ABC{Tab}DEF{Delay:500}{Enter}` with 1 repetition.
5. Mark each line ✅, ◐ or ❌ (with a short note of what you saw).

Preparation: open Notepad and use the **Predefinido** set, where 1 → `3E03305`, 2 → `Z51.11{Enter}`, 3 → `C50.912` and 4 → `ABC{Tab}DEF{Delay:500}{Enter}`.

## Key suppression

| # | Action | Expected | OK |
|---|---|---|---|
| 1 | Macros active, in Notepad press `1` | `3E03305` appears, without the `1` | ✅ |
| 2 | Press `Numpad1` (NumLock on) | `1` appears (keypad not affected) | ☐ 👤 the agent cannot press Numpad1 |
| 3 | Hold `1` for 2 s | `3E03305` once, no `1111…` | ☐ |
| 4 | Press `2` | `Z51.11` and a new line | ✅ |
| 5 | Press `4` | `ABC`, tab, `DEF`, ~0.5 s pause, new line | ✅ |
| 6 | Write `ç é ã` as a macro title/text and trigger it | correct accents | ☐ |

## Modifiers

| # | Action | Expected | OK |
|---|---|---|---|
| 7 | `Shift+1` | `!` (normal behaviour) | ✅ |
| 8 | `Ctrl+1`, `Alt+1` | the application's normal behaviour | ☐ |
| 9 | Preferences ▸ Modifiers ▸ "Also trigger…"; `Shift+1` | `3E03305` | ☐ |
| 10 | Back to "Bare key only" | `Shift+1` gives `!` again | ☐ |

## Suspend

| # | Action | Expected | OK |
|---|---|---|---|
| 11 | Suspend hotkey (`Shift+Esc`; `Ctrl+Alt+P` in 0.3) | grey icon with pause; panel "Macros suspended" | ✅ |
| 12 | Press `1` | types `1` | ✅ |
| 13 | `Shift+Esc` | back to active | ✅ |
| 14 | Create a macro `a{Delay:5000}b` with 3 repetitions, trigger it and press `Shift+Esc` during the pause | only `a` appears; nothing else is typed | ✅ |
| 15 | Quit and reopen the program with macros suspended | starts suspended, with the same set | ☐ |

## Scope

| # | Action | Expected | OK |
|---|---|---|---|
| 16 | Scope ▸ Only `notepad.exe`; press `1` in Notepad | `3E03305` | ☐ |
| 17 | Press `1` in Explorer/browser | normal `1`; the panel shows "out of scope" | ☐ |
| 18 | Trigger `a{Delay:3000}b` and switch windows with Alt+Tab during the pause | `b` is not typed anywhere | ✅ |

## Panel and focus

| # | Action | Expected | OK |
|---|---|---|---|
| 19 | Icon ▸ Show panel. Click in Notepad, put the cursor in the middle of the text and click a panel button | the text goes in at the cursor; Notepad stays active (active title bar) | ✅ |
| 20 | Keep typing on the keyboard right after | keys keep going to Notepad | ✅ |
| 21 | Preferences: opacity 40 % and turn "always on top" off | the panel is translucent and can go behind other windows | ☐ |
| 22 | Close the panel with ✕ | the panel disappears and keys keep working | ☐ |

## Icon and background

| # | Action | Expected | OK |
|---|---|---|---|
| 23 | Icon menu: Open settings, Show/hide panel, Active set, Suspend/Resume, Quit | every option works | ☐ 👤 right-click on the taskbar blocked for the agent |
| 24 | Close the settings window | the program keeps running (icon present, keys active) | ☐ |
| 25 | Run the program a second time | no second instance; shows the existing settings | ☐ |
| 26 | Restart the Windows session | starts automatically; no desktop shortcut | ☐ 👤 session restart |
| 27 | Turn "Start with Windows" off and restart the session | does not start | ☐ 👤 session restart |

## TOML files

| # | Action | Expected | OK |
|---|---|---|---|
| 28 | Edit `conjuntos\predefinido.toml` (key 1 text → `TESTE`) and save | press `1` → `TESTE`, without restarting | ☐ |
| 29 | Write `texto = "a{Entr}"` and save | warning with file/line/column; `1` still types `TESTE` | ☐ |
| 30 | With the VS Code editor (saves by replacing), fix and save | reloads | ☐ |
| 31 | With macros suspended, save a valid change | they stay suspended | ☐ |

## Administrator (expected limitation)

| # | Action | Expected | OK |
|---|---|---|---|
| 32 | Open Notepad "as administrator" and press `1` | types `1` (Windows prevents interception) | ☐ 👤 UAC |
| 33 | Run the program as administrator and repeat | `3E03305` | ☐ 👤 UAC |

## Version 0.2 — interface

| # | Action | Expected | OK |
|---|---|---|---|
| 34 | Icon next to the clock with macros active / suspended | cyan outline / grey with a red dot | ✅ |
| 35 | Icon of the windows, the taskbar and the `.exe` | logo (key «1» → cursor) | ☐ |
| 36 | Preferences ▸ Theme ▸ Day | light interface; black title bar with readable text and buttons (settings, panel and dialogs) | ◐ settings window black; **panel not** (fixed in 0.4, repeat) |
| 37 | Theme ▸ Night | dark interface and title bar | ☐ |
| 38 | Theme ▸ Automatic; change the Windows app mode (light/dark) | the program follows within a few seconds | ☐ |
| 39 | Tabs | Macros · Panel · Scope · Preferences | ✅ |
| 40 | **Active**/**Suspended** buttons: click and use Tab + Space | change the state; visible focus; distinct colours | ◐ click OK; keyboard (Tab + Space) to test |
| 41 | Panel preferences: change columns, size, colours, styles | the preview changes immediately; the real panel (if open) too | ☐ |
| 42 | **Restore default** | back to the original look | ☐ |
| 43 | **New macro** (one click) | exactly one macro appears, with no key, cursor in the text | ☐ |
| 44 | Give two macros the same text | both with a yellow outline/«=» badge and an explanation in the editor | ☐ |
| 45 | Give two macros the same key | red «!» badge and a «key conflict» message | ☐ |
| 46 | Select a macro (click in the grid) and press Delete | asks for confirmation; «Don't ask again» turns off the next ones | ☐ |
| 47 | In the Text field, press Delete/Ctrl+C/Ctrl+V | normal text editing; no macro is deleted/copied | ☐ |
| 48 | With the grid focused: Ctrl+C and Ctrl+V | a copy appears (without a key if the key is taken) | ☐ |
| 49 | Archive a macro and press its key | the key works normally; the macro is not on the panel | ☐ |
| 50 | Search the archive by title, text and key | filters the archived macros | ☐ |
| 51 | Restore a macro whose key is taken: Cancel / Replace | Cancel changes nothing; Replace swaps the two (the active one goes to the archive) | ☐ |
| 52 | Preferences ▸ Language ▸ English | the whole interface, icon menu and dialogs in English; macro titles unchanged | ☐ |
| 53 | Close and reopen the program | theme, language and panel style are kept | ☐ |

## Version 0.3 — panel and selection

| # | Action | Expected | OK |
|---|---|---|---|
| 54 | Drag an active macro into the «Archive» area and drop it | dashed outline while hovering; archived immediately; other macros' keys unchanged | ☐ |
| 55 | Ctrl+click 3 macros, then Shift+click another | individual / range selection; the editor shows «n macros selected» | ☐ |
| 56 | With several selected: drag to «Archive» | all archived | ☐ |
| 57 | With several selected: Delete | confirmation with the count; Cancel does not delete | ☐ |
| 58 | «Panel» tab with the window maximised | preview centred and identical to the real panel | ◐ centred OK; real panel title bar differed (fixed in 0.4, repeat) |
| 59 | Active/Suspended buttons on the panel (with the cursor in Notepad) | change the state; Notepad keeps the focus; settings and icon follow | ✅ |
| 60 | Mouse wheel over the panel | up more opaque, down more transparent; shows «Opacity n %»; other windows unchanged | ✅ |
| 61 | Check boxes and spin-box arrows (folder with accents/spaces) | visible and in the correct state | ✅ |

## Version 0.4 — layout, shortcuts and preferences

Before starting: in the test configuration, the previous suspend hotkey
(`Ctrl+Alt+P`) should have become `Shift+Escape`, with a notice on the icon.

| # | Action | Expected | OK |
|---|---|---|---|
| 62 | First 0.4 start with a configuration that had `Ctrl+Alt+P` | migration notice; Preferences shows `Shift+Escape`; no notice at the next start | ☐ |
| 63 | Shift+Esc in Notepad | suspends/resumes; Esc alone stays normal | ☐ |
| 64 | Shift+F12 in Notepad (also with macros suspended) | shows/hides the panel; Notepad keeps the focus | ☐ |
| 65 | Panel: title bar | theme colours (black in Day, dark in Night); shows the set and «Shift+F12 shows/hides»; ✕ hides the panel | ☐ |
| 66 | Drag the panel's title bar, close and reopen the program | the panel moves without taking the focus; reopens at the same position | ☐ |
| 67 | Macros tab: «Active» area | centred, with the panel's size, colours, columns and spacing; the «Active (n)» title has the «Archive (n)» style | ☐ |
| 68 | **Empty space**, then drag it among the buttons | dashed in the settings; on the panel the cell is empty and does not react to clicks | ☐ |
| 69 | Drag a button onto an empty space | they swap; saved immediately | ☐ |
| 70 | Drag a button between two others (Active) and between two archived ones | blue line at the position; lands exactly there; keys unchanged | ☐ |
| 71 | Drag an archived one to «Active», between two buttons | restored at that position; a key conflict asks for confirmation (Cancel changes nothing) | ☐ |
| 72 | Drag an empty space to «Archive» | not archived; message in the status bar | ☐ |
| 73 | Select an archived macro, Ctrl+C, Ctrl+V | the copy appears in the Archive, right after the original | ☐ |
| 74 | Mouse over a button (window active), press F8 | yellow «Key…» label while the mouse is over it; F8 assigned and saved | ☐ |
| 75 | Mouse over a button, press another active macro's key | «already assigned» warning; tick «Don't show again»; afterwards it only shows in the status bar; Preferences shows the option unticked | ☐ |
| 76 | Mouse over a button, press Shift+Esc and Shift+F12 | does not suspend or show the panel; global key warning | ☐ |
| 77 | Mouse over a button, switch to Notepad with Alt+Tab and press 1 | macro 1 works in Notepad (capture only applies with the settings window active) | ☐ |
| 78 | Mouse over a button: Delete, Ctrl+C, Ctrl+V, Tab, Esc | keep their functions (Esc cancels without assigning) | ☐ |
| 79 | **Counter**: on the panel, 3 short clicks; then hold for 1 s | 1, 2, 3; holding goes back to 0 without adding | ☐ |
| 80 | Counter with step 5, reset 10, long press 500 ms; assign F9; in Notepad tap F9 and hold F9 | adds 5; holding resets to 10; nothing is typed in Notepad | ☐ |
| 80a | With the settings window in front (focus outside text fields, mouse off the buttons), tap and hold F9 | counts and resets, as in Notepad; in a text field F9 does not count | ☐ |
| 80b | Counter in a set scoped to `notepad.exe` only; with Explorer in front, click the panel counter and press F9 | button disabled and F9 normal; with Notepad in front it counts again | ☐ |
| 80c | Press and hold F9, suspend with the mouse (panel's Suspended button) and release F9 | the count does not change | ☐ |
| 81 | Close and reopen the program | the count and the counter configuration are kept | ☐ |
| 82 | Panel tab: title/key position in every combination | preview and real panel identical; title and key never overlap | ☐ |
| 83 | Preferences: tick «Don't ask for confirmation…» and delete a macro | deletes without asking; unticking asks again (no restart) | ☐ |
| 84 | Preferences: untick and tick «Start automatically with Windows»; check Task Manager ▸ Startup apps | applied immediately; the program shows «Enabled»; disabled in Task Manager and ticked again → back to «Enabled» | 👤 |
| 85 | Restart the Windows session with autostart on | the program starts by itself with the same configuration folder | 👤 |
| 86 | Preferences ▸ Text mode «Paste»; copy «old» to the clipboard; in Notepad press the key of a macro with `Olá{Enter}mundo` | types «Olá», new line, «mundo» (with accents); the clipboard holds the macro text; no error | ☐ |

## New name — Virtual Macro Text Inputer

| # | Action | Expected | OK |
|---|---|---|---|
| 87 | With the old Macropad running, open the new program (`run-dev.ps1`) | warning to close the old Macropad; the new one does not start | ☐ |
| 88 | Close the old one and open the new one | windows, icon and menus show «Virtual Macro Text Inputer»; your macros and preferences are there (copied from `%APPDATA%\Macropad`, which still exists) | ☐ |
| 89 | With «Start with Windows» on, check Task Manager ▸ Startup apps | only the new entry, enabled; «Macropad» is gone | 👤 |

## Version 0.5

| # | Action | Expected | OK |
|---|---|---|---|
| 90 | Panel counter with long press 1500 ms: hold it with the mouse | a green line runs along the border from the top; at 1.5 s the count resets at once with a green flash, still held; keeping it held does not reset again; releasing does not add | ☐ |
| 91 | Same counter with F9 in Notepad: hold F9 with the panel visible | same progress and reset on the panel button while F9 is still held; nothing typed | ☐ |
| 92 | Editor of the counter: «Sound on reset» ▸ «Warning», click «Test», then reset by holding | the Windows warning sound plays on «Test» and on the reset; with «None» there is no sound | ☐ |
| 93 | Select the 2nd macro and click «New macro»; then «Counter»; click an empty area of the grid (no selection) and «Empty space» | the macro goes right after the 2nd, the counter right after the new macro; the space goes to the end of Active; the new item is selected | ☐ |
| 94 | Panel tab: 3 columns and 2 rows, with 8 buttons | preview and real panel show 6 cells and ◀ 1 / 2 ▶; ▶ shows the rest in a panel of the same size; clicking the arrows does not take the focus from Notepad; the setting is kept after restarting | ☐ |
| 95 | Rows «All», then 5 rows with 8 buttons and 3 columns | no arrows; the panel only takes the rows it needs | ☐ |
| 96 | Editor ▸ «Media» ▸ «Next track» on a macro; in Notepad press the keyboard's ⏭ key | the macro runs; the music player does not skip track | ☐ |
| 97 | Suspend (Shift+Esc) and press ⏭; then, active but with a window outside the scope, press ⏭ | the music player skips track in both cases | ☐ |
| 98 | Assign «Next track» to a second macro | «already assigned» warning; nothing changes | ☐ |
| 99 | Delete two macros (one active, one archived), Ctrl+Z, Ctrl+Y, Ctrl+Z; then in the Title field type text and press Ctrl+Z | they come back in the same places with the same keys; Ctrl+Y deletes them again; in the field Ctrl+Z only undoes the text | ☐ |

## Preview zoom and swapping

| # | Action | Expected | OK |
|---|---|---|---|
| 100 | *Macros*: −, +, click the percentage; Ctrl+mouse wheel over the grid | the Active and Archive previews shrink and grow (30–200 %); the percentage goes back to 100 %; the real panel keeps its size | ☐ |
| 101 | With many macros, drag the divider above the editor up, then click **Fit** and resize the window | the whole Active grid fits in the visible area and keeps fitting while resizing; −/+ turn Fit off | ☐ |
| 102 | At 50 % and at 150 %: drag a macro to the centre of another, near its edge, and onto an empty space | centre: dashed frame and the two swap; edge: blue line and it is inserted; empty space: they swap | ☐ |
| 103 | Drag an active macro to the centre of an archived one with the same key as another active macro | confirmation as in «Restore»; Cancel changes nothing; Replace swaps them and sends the conflicting one to the Archive | ☐ |
