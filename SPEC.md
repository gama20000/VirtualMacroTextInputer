# Especificação

## Destino

Uma aplicação de macro pad para Windows, **Virtual Macro Text Inputer**
(chamava-se Macropad até à versão 0.4; o pacote Python continua `macropad`), que transforma teclas
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
isto com botões; o programa usa as teclas que já existem no teclado e um painel
no ecrã, sem hardware adicional.

## Utilizadores

- Um utilizador principal, em Windows 10/11, que trabalha sobretudo noutras
  aplicações e quer o programa discreto, em segundo plano.
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
  aplicação nunca disparam macros; teclas nas janelas do próprio programa
  não disparam.
- Associações duplicadas e conflitos com a tecla de suspensão são erros.

### Suspensão global

- Tecla configurável (por omissão Shift+Escape; as configurações com o antigo
  Ctrl+Alt+P são migradas) que alterna ativo/suspenso, também
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
- Macros: duas áreas com títulos do mesmo estilo, **Ativo** e **Arquivo**. A
  área Ativo usa o mesmo aspeto do painel (dimensões, cores, posições do título
  e da tecla, espaçamento, número de colunas, espaços vazios) e fica centrada;
  se não couber, pode ser percorrida sem cortar macros.
- Arrastar reorganiza dentro de cada área e move entre Ativo e Arquivo nos dois
  sentidos. Ao largar, o item fica na posição indicada, antes ou depois do item
  sob o ponteiro, e não no fim. Largar sobre um espaço vazio troca o botão com
  o espaço. A interface atualiza-se e grava logo. A tecla nunca muda com a
  posição; restaurar por arrasto com a tecla ocupada pede a mesma confirmação.
- Editor de título, tecla, texto, repetições e intervalo; gravação automática
  quando válido; erros a vermelho (incluindo conflito de tecla); conteúdo
  duplicado (mesma sequência de texto e comandos) a amarelo, com explicação.
- «Nova macro» cria exatamente uma macro, sem tecla e com texto vazio.
- Espaços vazios: podem ser inseridos entre botões para compor a grelha. Não são
  macros, não executam, não vão para o Arquivo e só são visíveis (contorno
  tracejado) na configuração; no painel real ocupam a célula, invisíveis. A
  organização é gravada.
- Contadores: botão que mostra uma contagem. Um clique curto (ou um toque na
  tecla associada) soma o incremento (predefinição 1); manter premido durante o
  tempo de pressão longa repõe o valor configurado (predefinição 0) sem somar.
  Não escreve texto. A configuração e a contagem persistem entre sessões.
- Atribuir tecla por cima do botão: com o ponteiro sobre um botão da área de
  edição e o foco fora de campos de edição, premir uma tecla atribui-a (o botão
  mostra que está à espera). Delete, Backspace, Tab, Ctrl+C e Ctrl+V mantêm as
  suas funções. Se a tecla já estiver numa macro ativa, ou coincidir com uma
  tecla global (suspensão, painel), nada muda e aparece uma mensagem que
  identifica o conflito, com «Não voltar a mostrar» (reativável nas
  Preferências).
- Seleção múltipla (Ctrl+clique, Shift+clique) para arquivar, restaurar,
  eliminar e copiar/colar.
- Fora de campos de edição: Delete/Backspace elimina (com confirmação e opção
  «Não voltar a perguntar»; várias macros pedem sempre confirmação com a
  quantidade), Ctrl+C copia, Ctrl+V cola. Colar com uma macro arquivada
  selecionada cria a cópia no Arquivo, logo depois dela. Dentro de campos de
  texto, comportamento normal.
- Preferência «Não pedir confirmação antes de eliminar macros»: marcada elimina
  sem perguntar; aplica-se e grava-se logo ao mudar.
- Preferência «Arrancar automaticamente com o Windows»: ativa ou desativa de
  facto o arranque (incluindo a aprovação de arranque do Windows) e mostra uma
  indicação clara se não for possível aplicar a alteração.
- Arquivo: divisória «Arquivo» com as macros arquivadas e pesquisa (título,
  texto, tecla); arquivar por botão ou arrastando para essa área; arquivadas
  ficam fora das teclas e do painel; restaurar com tecla ocupada pede
  confirmação e troca as duas (cancelar não altera nada).
- Temas Diurno (predefinição, barra de título preta), Noturno e Automático
  (segue o Windows), aplicados a todas as janelas.
- Idiomas Português e Inglês para toda a interface, mensagens, menus e
  confirmações; títulos e conteúdos das macros nunca são traduzidos.

### Painel

- Tecla configurável para mostrar/ocultar o painel (por omissão Shift+F12),
  indicada no próprio painel.
- Grelha com título e tecla das macros ativas; executar com o rato sem roubar o
  foco à aplicação de destino; sempre por cima por omissão; transparência
  ajustável (também com a roda do rato sobre o painel, passos de 5 %, com
  indicação breve); respeita suspensão, âmbito e regras de execução.
- Aparência personalizável mantendo a grelha: colunas, tamanho, espaçamento,
  arredondamento, borda, tamanho do texto, cores, elementos visíveis, posição do
  título e da tecla (em cima, ao centro ou em baixo, de forma independente e sem
  sobreposição ilegível), estilos predefinidos e «Repor predefinição». Os
  botões não têm ícone.
- Pré-visualização centrada nas preferências, idêntica ao painel real
  (incluindo a barra de título com as cores do tema) e atualizada a cada
  alteração.

### Ficheiros TOML e recarregamento

- `config.toml` e `conjuntos/<id>.toml` em `%APPDATA%\VirtualMacroTextInputer\` (copiados de `%APPDATA%\Macropad\` no primeiro arranque com o nome novo), legíveis,
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
  como administrador, a menos que o programa também o seja.

## Restrições

- Primeira versão só com ações de texto (sem abrir programas nem scripts).
- Nomes dos campos TOML em português; não mudam sem nova `versao_esquema`.
- Nada específico do sistema operativo em `core/`.

## Fora do âmbito

- Versão Linux (a arquitetura permite-a, mas não faz parte deste destino).
- Outras categorias de ações (programas, scripts, atalhos de sistema).
- Sintaxe para escrever `{Enter}`/`{Tab}` literalmente.
- Preservar o conteúdo anterior da área de transferência.
- Instalador (o pacote é uma pasta com `VirtualMacroTextInputer.exe`).
- Ícones personalizados nos botões (removidos por agora).
- Reescrita noutra linguagem (ex.: Rust); ver ROADMAP.

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
- `build.ps1` gera `dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe` que arranca e passa os critérios
  acima.
- O repositório está publicado nos dois remotos acordados.
