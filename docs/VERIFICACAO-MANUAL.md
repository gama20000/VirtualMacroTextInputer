# Verificação manual no Windows

Estes pontos não podem ser testados automaticamente: dependem do hook de teclado real, do foco das janelas e da área de notificação. Faça a verificação com `.\run-dev.ps1` (a consola mostra erros) e repita com `dist\Macropad\Macropad.exe`.

Legenda da coluna OK: ✅ verificado · ◐ parcial · ❌ falhou · ☐ por verificar ·
👤 tem de ser feito pelo utilizador. Verificação de 12-11-2026 feita pelo agente
(controlo do ecrã) com `tools\macropad-teste.cmd`, que usa uma configuração
separada em `%TEMP%\MacropadTeste`.

Preparação: abra o Bloco de Notas e use o conjunto **Predefinido**, em que 1 → `3E03305`, 2 → `Z51.11{Enter}`, 3 → `C50.912` e 4 → `ABC{Tab}DEF{Delay:500}{Enter}`.

## Supressão de teclas

| # | Ação | Esperado | OK |
|---|---|---|---|
| 1 | Macros ativas, no Bloco de Notas prima `1` | aparece `3E03305`, sem o `1` | ✅ |
| 2 | Prima `Numpad1` (NumLock ligado) | aparece `1` (teclado numérico não é afetado) | ☐ 👤 o agente não consegue premir Numpad1 |
| 3 | Mantenha `1` premido 2 s | `3E03305` uma única vez, sem `1111…` | ☐ |
| 4 | Prima `2` | `Z51.11` e muda de linha | ✅ |
| 5 | Prima `4` | `ABC`, tabulação, `DEF`, pausa de ~0,5 s, nova linha | ✅ |
| 6 | Escreva `ç é ã` como título/texto de uma macro e dispare-a | acentos corretos | ☐ |

## Modificadores

| # | Ação | Esperado | OK |
|---|---|---|---|
| 7 | `Shift+1` | `!` (comportamento normal) | ✅ |
| 8 | `Ctrl+1`, `Alt+1` | comportamento normal da aplicação | ☐ |
| 9 | Preferências ▸ Modificadores ▸ "Disparar também…"; `Shift+1` | `3E03305` | ☐ |
| 10 | Volte a "Só a tecla isolada" | `Shift+1` volta a dar `!` | ☐ |

## Suspensão

| # | Ação | Esperado | OK |
|---|---|---|---|
| 11 | `Ctrl+Alt+P` | ícone cinzento com pausa; painel "Macros suspensas" | ✅ |
| 12 | Prima `1` | escreve `1` | ✅ |
| 13 | `Ctrl+Alt+P` | volta a ativo | ✅ |
| 14 | Crie uma macro `a{Delay:5000}b` com 3 repetições, dispare-a e prima `Ctrl+Alt+P` durante a pausa | só aparece `a`; nada mais é escrito | ✅ |
| 15 | Saia e volte a abrir o programa com as macros suspensas | arranca suspenso e com o mesmo conjunto | ☐ |

## Âmbito

| # | Ação | Esperado | OK |
|---|---|---|---|
| 16 | Âmbito ▸ Apenas `notepad.exe`; prima `1` no Bloco de Notas | `3E03305` | ☐ |
| 17 | Prima `1` no Explorador/browser | `1` normal; o painel indica "fora do âmbito" | ☐ |
| 18 | Dispare `a{Delay:3000}b` e mude de janela com Alt+Tab durante a pausa | `b` não é escrito em lado nenhum | ✅ |

## Painel e foco

| # | Ação | Esperado | OK |
|---|---|---|---|
| 19 | Ícone ▸ Mostrar painel. Clique no Bloco de Notas, coloque o cursor a meio do texto e clique num botão do painel | o texto entra no cursor; o Bloco de Notas continua ativo (barra de título ativa) | ✅ |
| 20 | Continue a escrever no teclado logo a seguir | as teclas continuam a ir para o Bloco de Notas | ✅ |
| 21 | Preferências: opacidade 40 % e desligar "sempre por cima" | o painel fica translúcido e pode ficar atrás de outras janelas | ☐ |
| 22 | Feche o painel no ✕ | o painel desaparece e as teclas continuam a funcionar | ☐ |

## Ícone e segundo plano

| # | Ação | Esperado | OK |
|---|---|---|---|
| 23 | Menu do ícone: Abrir configuração, Mostrar/ocultar painel, Conjunto ativo, Suspender/Reativar, Sair | todas as opções funcionam | ☐ 👤 botão direito na barra de tarefas bloqueado ao agente |
| 24 | Feche a janela de configuração | o programa continua (ícone presente, teclas ativas) | ☐ |
| 25 | Execute o programa uma segunda vez | não abre uma segunda instância; mostra a configuração existente | ☐ |
| 26 | Reinicie a sessão do Windows | arranca automaticamente; sem atalho no ambiente de trabalho | ☐ 👤 reinício da sessão |
| 27 | Desative "Arrancar com o Windows" e reinicie a sessão | não arranca | ☐ 👤 reinício da sessão |

## Ficheiros TOML

| # | Ação | Esperado | OK |
|---|---|---|---|
| 28 | Edite `conjuntos\predefinido.toml` (texto da tecla 1 → `TESTE`) e guarde | prima `1` → `TESTE`, sem reiniciar | ☐ |
| 29 | Escreva `texto = "a{Entr}"` e guarde | aviso com ficheiro/linha/coluna; `1` continua a escrever `TESTE` | ☐ |
| 30 | Com o editor do VS Code (grava por substituição), corrija e guarde | recarrega | ☐ |
| 31 | Com as macros suspensas, guarde uma alteração válida | continuam suspensas | ☐ |

## Administrador (limitação esperada)

| # | Ação | Esperado | OK |
|---|---|---|---|
| 32 | Abra o Bloco de Notas "como administrador" e prima `1` | escreve `1` (o Windows impede a interceção) | ☐ 👤 UAC |
| 33 | Execute o Macropad como administrador e repita | `3E03305` | ☐ 👤 UAC |

## Versão 0.2 — interface

| # | Ação | Esperado | OK |
|---|---|---|---|
| 34 | Ícone junto ao relógio com macros ativas / suspensas | contorno ciano / cinzento com ponto vermelho | ✅ |
| 35 | Ícone das janelas, da barra de tarefas e do `Macropad.exe` | logótipo (tecla «1» → cursor) | ☐ |
| 36 | Preferências ▸ Tema ▸ Diurno | interface clara; barra de título preta com texto e botões legíveis (configuração, painel e caixas de diálogo) | ◐ janela de configuração preta; **painel não** (ver ROADMAP) |
| 37 | Tema ▸ Noturno | interface e barra de título escuras | ☐ |
| 38 | Tema ▸ Automático; mude o modo das aplicações no Windows (claro/escuro) | o Macropad acompanha em poucos segundos | ☐ |
| 39 | Separadores | Macros · Painel · Âmbito · Preferências | ✅ |
| 40 | Botões **Ativo**/**Suspenso**: clique e use Tab + Espaço | mudam o estado; foco visível; cores distintas | ◐ clique OK; teclado (Tab + Espaço) por testar |
| 41 | Preferências do painel: mude colunas, tamanho, cores, estilos | a pré-visualização muda logo; o painel real (se aberto) também | ☐ |
| 42 | **Repor predefinição** | volta ao aspeto original | ☐ |
| 43 | **Nova macro** (um clique) | aparece exatamente uma macro, sem tecla, cursor no texto | ☐ |
| 44 | Dê a duas macros o mesmo texto | ambas com contorno/selo amarelo «=» e explicação no editor | ☐ |
| 45 | Dê a duas macros a mesma tecla | selo vermelho «!» e mensagem «conflito de tecla» | ☐ |
| 46 | Selecione uma macro (clique na grelha) e prima Delete | pede confirmação; «Não voltar a perguntar» desativa as próximas | ☐ |
| 47 | No campo Texto, prima Delete/Ctrl+C/Ctrl+V | edição normal de texto; nenhuma macro é eliminada/copiada | ☐ |
| 48 | Com a grelha em foco: Ctrl+C e Ctrl+V | aparece uma cópia (sem tecla se a tecla estiver ocupada) | ☐ |
| 49 | Arquivar uma macro e premir a sua tecla | a tecla funciona normalmente; a macro não aparece no painel | ☐ |
| 50 | Pesquisar no arquivo por título, texto e tecla | filtra as macros arquivadas | ☐ |
| 51 | Restaurar uma macro cuja tecla está ocupada: Cancelar / Substituir | Cancelar não muda nada; Substituir troca as duas (a ativa vai para o arquivo) | ☐ |
| 52 | Preferências ▸ Idioma ▸ English | toda a interface, menu do ícone e diálogos em inglês; títulos das macros inalterados | ☐ |
| 53 | Feche e reabra o programa | tema, idioma e estilo do painel mantêm-se | ☐ |

## Versão 0.3 — painel e seleção

| # | Ação | Esperado | OK |
|---|---|---|---|
| 54 | Arraste uma macro ativa para baixo da linha «Arquivo» e largue | contorno tracejado ao passar; arquivada logo; teclas das outras não mudam | ☐ |
| 55 | Ctrl+clique em 3 macros, depois Shift+clique noutra | seleção individual / intervalo; editor indica «n macros selecionadas» | ☐ |
| 56 | Com várias selecionadas: arrastar para «Arquivo» | todas arquivadas | ☐ |
| 57 | Com várias selecionadas: Delete | confirmação com a quantidade; Cancelar não apaga | ☐ |
| 58 | Separador «Painel» com a janela maximizada | pré-visualização centrada e igual ao painel real | ◐ centrada OK; barra de título do painel real difere |
| 59 | Botões Ativo/Suspenso no painel (com o cursor no Bloco de Notas) | mudam o estado; o Bloco de Notas mantém o foco; configuração e ícone acompanham | ✅ |
| 60 | Roda do rato sobre o painel | para cima mais opaco, para baixo mais transparente; mostra «Opacidade n %»; outras janelas inalteradas | ✅ |
| 61 | Caixas de verificação e setas dos campos numéricos (pasta com acentos/espaços) | visíveis e com o estado correto | ✅ |
