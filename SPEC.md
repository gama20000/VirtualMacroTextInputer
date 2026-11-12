# Especificação

## Destino

Uma aplicação de macro pad para Windows (Macropad) que transforma teclas
configuráveis do teclado habitual, e os botões de um painel flutuante opcional,
em ações de texto enviadas para a aplicação em primeiro plano. A tecla original
é suprimida quando a macro está ativa e dentro do âmbito configurado.

O projeto pára quando a versão Windows estiver revista, validada manualmente no
Windows (`docs/VERIFICACAO-MANUAL.md`), empacotada como executável e publicada
em dois remotos git (Forgejo próprio e GitHub). Uma versão Linux fica fora deste
destino, mas a arquitetura tem de a continuar a permitir.

## Problema

Quem escreve repetidamente os mesmos códigos e textos (ex.: `3E03305`,
`Z51.11{Enter}`) perde tempo e erra. Um Stream Deck físico ou virtual resolve
isto com botões; o Macropad usa as teclas que já existem no teclado e um painel
no ecrã, sem hardware adicional.

## Utilizadores

- Um utilizador principal, em Windows 10/11, que trabalha sobretudo noutras
  aplicações e quer o Macropad discreto, em segundo plano.
- Edita macros pela interface ou diretamente nos ficheiros TOML.
- Fala português europeu; a interface também tem de existir em inglês.

## Comportamento exigido

### Segundo plano e ciclo de vida

- Arranca com o Windows por omissão (desativável); sem atalho no ambiente de
  trabalho; ícone na área de notificação; funciona sem janelas visíveis.
- Fechar a configuração ou o painel não termina a aplicação; só «Sair» no menu
  do ícone.
- Menu do ícone: abrir configuração, mostrar/ocultar painel, escolher o conjunto
  ativo, suspender/reativar, sair.
- Recupera o estado ativo/suspenso, o conjunto ativo e a visibilidade do painel
  da sessão anterior. Uma única instância (a segunda abre a configuração da
  primeira).
- Ícones da área de notificação: contorno ciano (ativo) e cinzento com ponto
  vermelho (suspenso). Logótipo da aplicação: tecla «1» → cursor.

### Teclas e ativação

- Por omissão, teclas 1–4 da fila superior (distintas do teclado numérico);
  exemplo inicial: 1 → `3E03305`. Outras teclas e combinações configuráveis;
  uma macro pode não ter tecla (só painel).
- Modificadores: por omissão só a tecla isolada dispara (Ctrl+1, Alt+1, Shift+1
  mantêm o comportamento normal); configurável para «ignorar».
- Manter a tecla premida não volta a disparar; os eventos gerados pela
  aplicação nunca disparam macros; teclas nas janelas do próprio Macropad
  não disparam.
- Associações duplicadas e conflitos com a tecla de suspensão são erros.

### Suspensão global

- Tecla configurável (por omissão Ctrl+Alt+P) que alterna ativo/suspenso, também
  durante uma macro e durante `{Delay}`; cancela logo passos e repetições
  pendentes. Suspenso: todas as teclas com comportamento normal.
- Estado visível no ícone, no painel e na configuração; botões **Ativo** e
  **Suspenso** clicáveis na configuração e no painel, com estilos distintos e
  foco visível.

### Conjuntos e âmbito

- Criar, editar, duplicar, eliminar, mudar o nome, importar e exportar
  conjuntos; um conjunto ativo de cada vez, escolhido manualmente.
- Âmbito por conjunto: global ou lista de executáveis; fora do âmbito as teclas
  funcionam normalmente e o painel não envia. Mudar de janela durante uma
  execução interrompe os passos pendentes.

### Ações de texto e repetições

- Texto Unicode com `{Enter}`, `{Tab}` e `{Delay:ms}` (0–600000), executados
  pela ordem; quebras de linha equivalem a `{Enter}`; comandos mal formados são
  erros com posição. Modo «escrever» (SendInput Unicode) ou «colar»
  (área de transferência).
- Repetições (1–1000) com intervalo; sem loops infinitos; disparos durante uma
  execução são ignorados; a execução não bloqueia a interface.

### Interface de configuração

- Separadores, por esta ordem: **Macros**, **Painel**, **Âmbito**,
  **Preferências**.
- Macros: grelha reordenável por arrasto (a tecla não muda); editor de título,
  tecla, texto, repetições e intervalo; gravação automática quando válido;
  erros a vermelho (incluindo conflito de tecla); conteúdo duplicado (mesma
  sequência de texto e comandos) a amarelo, com explicação.
- «Nova macro» cria exatamente uma macro, sem tecla e com texto vazio.
- Seleção múltipla (Ctrl+clique, Shift+clique) para arquivar, restaurar,
  eliminar e copiar/colar.
- Fora de campos de edição: Delete/Backspace elimina (com confirmação e opção
  «Não voltar a perguntar», reativável nas preferências; várias macros pedem
  sempre confirmação com a quantidade), Ctrl+C copia, Ctrl+V cola. Dentro de
  campos de texto, comportamento normal.
- Arquivo: divisória «Arquivo» com as macros arquivadas e pesquisa (título,
  texto, tecla); arquivar por botão ou arrastando para essa área; arquivadas
  ficam fora das teclas e do painel; restaurar com tecla ocupada pede
  confirmação e troca as duas (cancelar não altera nada).
- Temas Diurno (predefinição, barra de título preta), Noturno e Automático
  (segue o Windows), aplicados a todas as janelas.
- Idiomas Português e Inglês para toda a interface, mensagens, menus e
  confirmações; títulos e conteúdos das macros nunca são traduzidos.

### Painel

- Grelha com título e tecla das macros ativas; executar com o rato sem roubar o
  foco à aplicação de destino; sempre por cima por omissão; transparência
  ajustável (também com a roda do rato sobre o painel, passos de 5 %, com
  indicação breve); respeita suspensão, âmbito e regras de execução.
- Aparência personalizável mantendo a grelha: colunas, tamanho, espaçamento,
  arredondamento, borda, tamanho do texto, cores, elementos visíveis, estilos
  predefinidos e «Repor predefinição» (aspeto original).
- Pré-visualização centrada nas preferências, idêntica ao painel real e
  atualizada a cada alteração.

### Ficheiros TOML e recarregamento

- `config.toml` e `conjuntos/<id>.toml` em `%APPDATA%\Macropad\`, legíveis,
  com `versao_esquema`; campos novos são opcionais (ficheiros antigos válidos).
- Recarregamento automático ao guardar, incluindo editores que substituem o
  ficheiro; eventos agrupados; validação antes de aplicar; um ficheiro inválido
  mantém a última configuração válida e mostra ficheiro, linha e coluna.
- Gravação atómica pela interface, sem ciclos com o observador; alterações
  aplicam-se a execuções futuras; um recarregamento nunca reativa macros.

## Arquitetura e fluxo de dados

- `src/macropad/core/`: Python puro (comandos, teclas, modelo, TOML, ficheiros,
  observador, motor, operações sobre macros). Sem Qt nem Win32.
- `src/macropad/platform/`: camada do sistema operativo (Windows: hook
  `WH_KEYBOARD_LL`, `SendInput`, área de transferência, `WS_EX_NOACTIVATE`,
  DWM, registo `Run`, mutex). `dummy.py` para testes e desenvolvimento.
- `src/macropad/ui/`: PySide6 (ícone, configuração, painel, temas).
- `src/macropad/i18n.py` + `locales/*.toml`: traduções, usadas também pelo núcleo.
- Threads: hook de teclado → `Engine.handle_key` (rápido, sem bloquear);
  execução numa thread própria; a UI recebe eventos por sinais Qt.

## Segurança e privacidade

- Sem rede. Os textos das macros ficam em ficheiros locais do utilizador.
- O modo «colar» substitui a área de transferência sem preservar o conteúdo
  anterior (aceite).

## Desempenho e compatibilidade

- Windows 10 (build 19041+) e Windows 11, Python 3.11+.
- O callback do hook tem de responder bem abaixo do LowLevelHooksTimeout
  (~1 s).
- Limitação documentada: sem interceção nem envio para aplicações executadas
  como administrador, a menos que o Macropad também o seja.

## Restrições

- Primeira versão só com ações de texto (sem abrir programas nem scripts).
- Nomes dos campos TOML em português; não mudam sem nova `versao_esquema`.
- Nada específico do sistema operativo em `core/`.

## Fora do âmbito

- Versão Linux (a arquitetura permite-a, mas não faz parte deste destino).
- Outras categorias de ações (programas, scripts, atalhos de sistema).
- Sintaxe para escrever `{Enter}`/`{Tab}` literalmente.
- Preservar o conteúdo anterior da área de transferência.
- Instalador (o pacote é uma pasta com `Macropad.exe`).

## Critérios de aceitação

- Com macros ativas, premir 1 envia `3E03305` sem inserir o 1 original.
- Com macros suspensas, premir 1 escreve 1 normalmente.
- Fora do âmbito configurado, a tecla mantém o comportamento normal.
- A tecla de suspensão interrompe uma sequência mesmo durante um `{Delay}`.
- Guardar um TOML válido atualiza automaticamente a configuração; um TOML
  inválido não substitui a configuração válida.
- Clicar no painel envia a macro para a aplicação de destino sem roubar o foco.
- Os comportamentos de interface acima (arquivo, seleção múltipla, atalhos,
  temas, idiomas, painel personalizável) funcionam como descrito.
- Validação automática: `pytest` sem falhas.
- Validação manual: todos os passos de `docs/VERIFICACAO-MANUAL.md` assinalados
  no Windows real.
- Revisão independente concluída, com os problemas P0/P1 corrigidos ou
  aceites por decisão registada.
- `build.ps1` gera `dist\Macropad\Macropad.exe` que arranca e passa os critérios
  acima.
- O repositório está publicado nos dois remotos acordados.
