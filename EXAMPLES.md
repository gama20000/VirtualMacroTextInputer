# Examples

*Documentação em português: [docs/pt/EXEMPLOS.md](docs/pt/EXEMPLOS.md).*

Ready-to-use macros. You can build each one in the settings window, or paste the TOML into a set file in `%APPDATA%\VirtualMacroTextInputer\conjuntos\` (it is reloaded as soon as you save). Field names in the files are in Portuguese: `titulo` = title, `tecla` = key, `texto` = text, `repeticoes` = repetitions, `intervalo_ms` = interval. The full reference is in [ARCHITECTURE.md](ARCHITECTURE.md), and a complete commented set is in [examples/conjunto-exemplo.toml](examples/conjunto-exemplo.toml).

## 1. A code on a key

Pressing **1** types the code; the 1 itself does not appear.

```toml
[[macros]]
titulo = "3E03305"
tecla = "1"
texto = "3E03305"
```

## 2. Text followed by Enter

A line break in the **Text** field is the same as `{Enter}`.

```toml
[[macros]]
titulo = "Z51.11 ⏎"
tecla = "2"
texto = "Z51.11{Enter}"
```

## 3. Filling in a form

Types the first field, moves to the next one with Tab, waits half a second for the application, and submits.

```toml
[[macros]]
titulo = "Form"
tecla = "3"
texto = "John Smith{Tab}john@example.com{Delay:500}{Enter}"
```

If you press Ctrl, Alt, Shift or Win while a macro is running, it waits for you to release them (up to 1.5 s) instead of sending `{Enter}` as `Ctrl+Enter`.

## 4. Repeating a line

Runs the macro three times per press, with 250 ms between runs.

```toml
[[macros]]
titulo = "3× line"
tecla = "Ctrl+F1"           # only fires with exactly Ctrl+F1
texto = "line{Enter}"
repeticoes = 3
intervalo_ms = 250
```

## 5. A panel-only button

With no key, the macro is only on the panel; the keyboard is left alone.

```toml
[[macros]]
titulo = "Signature"
tecla = ""
texto = "Best regards,{Enter}Alex"
```

## 6. A media control panel

Buttons that press media keys show a simple symbol. In the editor: **Media ▸ The button sends ▸ Play/Pause** (a new macro is renamed to «Play/Pause» automatically).

```toml
[[macros]]
titulo = "Previous"
tecla = ""
texto = "{MediaPrev}"

[[macros]]
titulo = "Play/Pause"
tecla = ""
texto = "{MediaPlayPause}"

[[macros]]
titulo = "Next"
tecla = ""
texto = "{MediaNext}"

[[macros]]
titulo = "Volume +"
tecla = ""
texto = "{VolumeUp}{VolumeUp}"   # two steps per click
```

To use a keyboard media key as the trigger of a text macro instead, choose **Media ▸ The keyboard key triggers this macro**.

## 7. A tally counter

A short press (click or **F9**) adds 1; holding it for 800 ms resets to 0, with a green flash and the Windows warning sound. The count is kept between sessions.

```toml
[[macros]]
tipo = "contador"
id = "calls"
titulo = "Calls"
tecla = "F9"
incremento = 1
reposicao = 0
pressao_longa_ms = 800
som_reposicao = "aviso"
```

## 8. A set that only works in some applications

The keys of this set only fire in Notepad and Word; everywhere else they type normally.

```toml
versao_esquema = 1
nome = "Reports"

[ambito]
modo = "aplicacoes"
aplicacoes = ["notepad.exe", "WINWORD.EXE"]

[[macros]]
titulo = "Header"
tecla = "F6"
texto = "REPORT{Enter}======{Enter}"
```

## 9. Grouping buttons on the panel

Empty spaces keep a cell free, so you can group buttons by row. With 4 columns, this puts the two codes on the first row and the media buttons on the second.

```toml
[[macros]]
titulo = "Code A"
tecla = "1"
texto = "3E03305"

[[macros]]
titulo = "Code B"
tecla = "2"
texto = "Z51.11"

[[macros]]
tipo = "espaco"

[[macros]]
tipo = "espaco"

[[macros]]
titulo = "Play/Pause"
tecla = ""
texto = "{MediaPlayPause}"
```

## 10. A compact panel with pages

In the *Panel* tab: **Columns** 3, **Rows** 2, style **Compact**. With more than six buttons, the panel shows ◀ 1 / 2 ▶ arrows; the keys work for the buttons on every page. The same in `config.toml`:

```toml
[painel]
colunas = 3
linhas = 2
tamanho_botao = 56            # the Compact style
```

## 11. Applications that reject simulated typing

Some applications (remote desktops, some web forms) ignore simulated typing. Switch Preferences ▸ **Text mode** to *Paste*: the text goes through the clipboard and Ctrl+V. In `config.toml`:

```toml
[geral]
modo_texto = "colar"
```
