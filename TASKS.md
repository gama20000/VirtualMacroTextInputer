# Tarefas

## Fase 2 — Versão 0.4 (concluída a 12-11-2026)

Decisões: `Q-019` a `Q-023`. Validação automática: `pytest` — 136 passam, 1
ignorado (só Windows). Capturas offscreen (Diurno e Noturno) revistas:
configuração com áreas Ativo/Arquivo, espaço vazio, contador, indicação
«Tecla…», editor do contador, separador Painel, Preferências e painel com a
barra de título própria. A validação manual no Windows dos passos 62–85 faz
parte da Fase 3.

- [x] Núcleo: modelo, TOML e operações (espaços, contadores, posições,
  `mostrar_icone` obsoleto, `tecla_painel`, `avisar_conflito_tecla`, migração
  Ctrl+Alt+P → Shift+Escape, inserção posicional, colar no Arquivo, conflitos
  com as teclas globais). Testes em `test_config.py` e `test_macro_ops.py`.
- [x] Motor: tecla do painel e contadores por tecla (decisão no keyup,
  repetições ignoradas). Testes em `test_engine.py`.
- [x] Interface: áreas Ativo/Arquivo com arrasto posicional nos dois sentidos
  e troca com espaços; botões Contador e Espaço vazio; editor por tipo;
  atribuição de tecla com o rato por cima do botão (só com a janela ativa),
  avisos de conflito com «Não voltar a mostrar»; preferências aplicadas de
  imediato com erro do arranque automático; posições do título e da tecla;
  área Ativo igual ao painel e centrada. Testes de UI offscreen em
  `test_ui_smoke.py`.
- [x] Painel: barra de título própria (cores do tema, conjunto, tecla do
  painel, ✕, arrastar para mover, posição gravada), espaços invisíveis,
  contadores com clique curto e pressão longa, contagens em `estado.toml`.
- [x] Arranque com o Windows de facto: `StartupApproved\Run`, verificação
  depois de aplicar, mensagem de erro, `--config-dir` quando a pasta não é a
  habitual. Validação manual: passos 84–85 (👤).
- [x] Traduções (pt/en), README, lista de verificação (passos 62–85),
  planeamento e versão 0.4.0.
  - Risco residual: o arrasto real com o rato, o comportamento do hook com a
    captura por cima do botão e a barra de título sem moldura só se confirmam
    no Windows (Fase 3).

## Fase atual: Fase 3 — Validação manual no Windows e distribuição (em pausa)


Estado: **em pausa** desde 12-11-2026 às 18:48, a pedido do utilizador;
retoma quando o utilizador autorizar (a Fase 2 já está concluída). Autorizada a 12-11-2026, com o agente a executar os passos por
controlo do ecrã ([Q-018](ANSWERS.md#q-018-método-da-validação-manual)).

Estado deixado no PC: a instância de teste do Macropad e o painel estão
abertos, e o Bloco de notas tem texto de teste por gravar. Na configuração de
teste, a macro «Exemplo» tem o texto `a{Delay:5000}b` com 3 repetições. A
última ação foi interrompida a meio: pode ter rodado a roda do rato sobre o
painel e escrito algumas teclas no Bloco de notas.

- [ ] Percorrer a lista de verificação com o código-fonte (`tools\macropad-teste.cmd`).
  - Âmbito: passos 1–85 de `docs/VERIFICACAO-MANUAL.md`, exceto os marcados
    👤; o resultado de cada passo fica registado nesse documento.
  - Critérios de aceitação: todos os passos não 👤 estão ✅, ou têm uma tarefa
    de correção ou uma limitação aceite em `ANSWERS.md`.
  - Validação automática: nenhuma.
  - Validação manual: registada em `docs/VERIFICACAO-MANUAL.md`.
  - Progresso: 16 passos ✅ (1, 4, 5, 7, 11–14, 18–20, 34, 39, 59–61), 3
    parciais (36, 40, 58). Por fazer: 3, 6, 8–10, 15–17, 21, 22, 24, 25,
    28–31, 35, 37, 38, 41–57, 62–85 (novos da 0.4). Os passos 36 e 58
    repetem-se com a barra de título própria do painel.
  - Dependências ou bloqueios: retomar quando o utilizador autorizar.

- [ ] ~~Corrigir a barra de título do painel no tema Diurno.~~ Passou para a
  Fase 2 (`Q-023`).
  - Âmbito: a janela real do painel mostra a barra de título cinzenta clara.
    A janela de configuração e a pré-visualização mostram-na preta.
    Investigar a ordem entre `make_window_noactivate` (que muda
    `GWL_EXSTYLE` para `WS_EX_TOOLWINDOW`/`WS_EX_NOACTIVATE`), a recriação da
    janela por `setWindowFlags` e as chamadas DWM em `style_window`.
  - Critérios de aceitação: no Windows, a barra de título do painel tem as
    cores do tema (preta no Diurno, escura no Noturno), tal como a
    pré-visualização; os passos 36 e 58 ficam ✅.
  - Validação automática: `pytest` sem falhas; um teste com a plataforma
    simulada que verifique que o painel é estilizado depois de mudar as flags.
  - Validação manual: repetir os passos 36 e 58 no Windows.
  - Dependências ou bloqueios: precisa de autorização para implementar.

- [ ] Passos que o utilizador tem de fazer (👤).
  - Âmbito: 2 (tecla 1 do teclado numérico), 23 (menu do ícone junto ao
    relógio), 26–27 (reiniciar a sessão), 32–33 (aplicação como
    administrador, UAC).
  - Critérios de aceitação: resultado registado em `docs/VERIFICACAO-MANUAL.md`.
  - Validação manual: feita pelo utilizador.
  - Dependências ou bloqueios: disponibilidade do utilizador.

- [ ] Repetir a verificação com o executável.
  - Âmbito: `build.ps1` → `dist\Macropad\Macropad.exe`; repetir os critérios
    de aceitação de [SPEC.md](SPEC.md#critérios-de-aceitação) e confirmar que
    os ícones e as traduções foram incluídos.
  - Critérios de aceitação: os critérios de aceitação cumprem-se com o `.exe`.
  - Validação automática: `pytest`, executado por `build.ps1`.
  - Validação manual: os passos essenciais (1, 7, 12, 14, 19, 28, 29) com o
    `.exe`.
  - Dependências ou bloqueios: as tarefas anteriores.

## Concluídas

### Fase 1 — Revisão independente e correções (12-11-2026)

- [x] Preparar o Codex no PC.
  - Validação: o utilizador correu a revisão com o Codex (`Q-013`).
- [x] Correr a revisão completa e guardar o relatório.
  - Validação: relatório guardado em `docs/revisao-codex.md`. O Codex declarou
    que não alterou ficheiros, e o `git status` no PC estava limpo antes das
    correções.
- [x] Confirmar cada achado no código.
  - Validação: P1 e P2 confirmados com testes que falhavam antes da correção.
    Não houve falsos positivos (`Q-017`).
- [x] Corrigir os problemas confirmados.
  - Validação: `pytest` com 110 testes a passar e 1 ignorado (só corre no
    Windows); três testes de regressão novos e um teste de interface.
  - Validação manual: nenhum ponto depende do Windows real.
