# Roteiro

## Destino

Ver [SPEC.md](SPEC.md#destino).

## Estado atual

O código está na versão 0.4. A Fase 1 (revisão independente) e a Fase 2
(versão 0.4, incluindo a barra de título própria do painel) estão concluídas.
Depois disso, seis revisões do Codex foram corrigidas; 168 testes automáticos
passam. Falta a validação manual no Windows (Fase 3, em pausa desde
12-11-2026, com 16 passos verificados e 3 parciais; os passos 62–86 cobrem a
0.4). O repositório está no Forgejo do utilizador (privado, pelo Tailscale);
falta o GitHub (Fase 4).

## Decisões em aberto

### Fronteira

- [ ] **Visibilidade do repositório no GitHub** (`Q-010`): privado ou público.
  Define quem vê o código e se o README pode referir caminhos pessoais.
- [ ] **Acesso do agente ao GitHub** (`Q-011`): ligar a conta GitHub nas
  definições do claude.ai, ou o utilizador cria o repositório
  `virtual-visual-vext` vazio e envia ele próprio. Sem isto não é possível criar
  o repositório nem enviar.

- [ ] **Reescrita em Rust** (`Q-024`): vale a pena reescrever o Macropad em
  Rust para ter um executável mais leve e com arranque mais rápido? A decisão
  deve esperar pela validação da versão Python (Fase 3), que fixa o
  comportamento a reproduzir. Nada da Fase 2 depende disto.

### Bloqueado

- (nenhuma)

### Nevoeiro

- Cópias de segurança do Forgejo (o que guardar, onde, com que frequência).
- HTTPS no Forgejo (`Q-025`): hoje o acesso é só pela rede Tailscale (já
  cifrada), em HTTP. Só é preciso se o Forgejo tiver de ser acessível fora do
  Tailscale.
- Dar versões ao executável distribuído (etiquetas git, nome do zip, notas de
  versão).
- Arranque automático com privilégios de administrador (Agendador de Tarefas)
  para quem precisar de macros em aplicações elevadas.

### Concluídas

- [x] [Stack tecnológica](ANSWERS.md#q-001-stack-tecnológica) (`Q-001`): Python + PySide6 + ctypes + PyInstaller.
- [x] [Valores predefinidos não fixados no pedido](ANSWERS.md#q-002-valores-predefinidos-não-fixados-no-pedido) (`Q-002`): Ctrl+Alt+P, macros sem tecla, quebra de linha = `{Enter}`.
- [x] [Comportamento de «Nova macro» e macros sem texto](ANSWERS.md#q-003-comportamento-de-nova-macro-e-macros-sem-texto) (`Q-003`): uma macro, sem tecla, texto vazio permitido.
- [x] [Confirmação ao eliminar várias macros](ANSWERS.md#q-004-confirmação-ao-eliminar-várias-macros) (`Q-004`): sempre, com a quantidade.
- [x] [Cópia colada com tecla em uso](ANSWERS.md#q-005-cópia-colada-com-tecla-em-uso) (`Q-005`): a cópia fica sem tecla.
- [x] [Organização dos remotos git](ANSWERS.md#q-006-organização-dos-remotos-git) (`Q-006`): um `origin` com dois endereços de envio.
- [x] [Nome do repositório no GitHub](ANSWERS.md#q-007-nome-do-repositório-no-github) (`Q-007`): `virtual-visual-vext`.
- [x] [Local do Forgejo](ANSWERS.md#q-008-local-do-forgejo) (`Q-008`): num servidor.
- [x] [Ferramenta de revisão independente](ANSWERS.md#q-009-ferramenta-de-revisão-independente) (`Q-009`): Codex CLI só de leitura com o `AGENTS.md`.
- [x] [Instalação do Codex CLI](ANSWERS.md#q-013-instalação-do-codex-cli) (`Q-013`): o utilizador correu a revisão no PC.
- [x] [Método da validação manual](ANSWERS.md#q-018-método-da-validação-manual) (`Q-018`): o agente controla o ecrã, com uma configuração separada; o utilizador faz os passos 👤.
- [x] [Ícone dos botões e posição do título e da tecla](ANSWERS.md#q-019-ícone-dos-botões-e-posição-do-título-e-da-tecla) (`Q-019`): sem ícone; título e tecla em cima, ao centro ou em baixo.
- [x] [Teclas globais predefinidas](ANSWERS.md#q-020-teclas-globais-predefinidas) (`Q-020`): Shift+Escape suspende; Shift+F12 mostra/oculta o painel.
- [x] [Funcionamento do contador](ANSWERS.md#q-021-funcionamento-do-contador) (`Q-021`): painel e tecla, só mostra; manter premido repõe.
- [x] [Atribuição de tecla por cima do botão e atalhos existentes](ANSWERS.md#q-022-atribuição-de-tecla-por-cima-do-botão-e-atalhos-existentes) (`Q-022`): Delete, Backspace, Tab, Ctrl+C e Ctrl+V mantêm-se.
- [x] [Barra de título do painel](ANSWERS.md#q-023-barra-de-título-do-painel) (`Q-023`): o painel desenha a sua própria barra.
- [x] [Servidor para o Forgejo](ANSWERS.md#q-012-servidor-para-o-forgejo) (`Q-012`): instalado pelo utilizador; `VirtualMacroTextInputer` pelo Tailscale. Torna `Q-014`, `Q-015` e `Q-016` desnecessárias.
- [x] [Tratamento dos resultados da revisão](ANSWERS.md#q-017-tratamento-dos-resultados-da-revisão) (`Q-017`): P1 e P2 confirmados e corrigidos.

## Fase 1: Revisão independente e correções — concluída (12-11-2026)

### Resultado

O código foi revisto por um agente independente, e os problemas confirmados
P0/P1 estão corrigidos ou aceites por decisão registada.

### Trabalho incluído

- Instalar ou abrir o Codex e correr a revisão completa (só de leitura).
- Confirmar cada achado no código; registar os falsos positivos.
- Corrigir os problemas confirmados, com um teste de regressão sempre que
  possível.

### Dependências e riscos

- Dependia de **Instalação do Codex CLI** (`Q-013`), já resolvida.
- Risco: problemas que só se manifestam no Windows real (hook, `SendInput`,
  foco) não são confirmáveis só pela leitura do código. Passam para a Fase 2
  como verificações específicas.
- Rollback: cada correção num commit próprio (`git revert`).

### Critérios de saída

- O relatório da revisão está guardado (`docs/revisao-codex.md`), com o
  resultado da confirmação de cada ponto.
- Não há P0/P1 confirmados por resolver sem decisão registada em `ANSWERS.md`.

### Validação

- `pytest` sem falhas.
- Novos testes de regressão para os problemas corrigidos que sejam testáveis
  fora do Windows.

## Fase 2: Versão 0.4 — organização do painel, atalhos e preferências — concluída (12-11-2026)

### Resultado

Os 12 pontos do pedido de 12-11-2026 estão implementados, juntamente com a
correção da barra de título do painel. A versão passa a 0.4.

### Trabalho incluído

- Espaços vazios na grelha; contadores; sem ícone; posição do título e da tecla.
- Áreas Ativo/Arquivo com arrasto nos dois sentidos e inserção na posição
  largada; colar no Arquivo; área Ativo com o mesmo aspeto do painel, centrada.
- Atribuição de tecla por cima do botão, com avisos de conflito desativáveis.
- Teclas globais Shift+Escape (suspender, com migração) e Shift+F12 (painel,
  indicada no painel).
- Preferências que se aplicam logo: arranque com o Windows (incluindo a
  aprovação de arranque do Windows) e confirmação de eliminação (texto
  invertido), com indicação de erro.
- Barra de título própria do painel (`Q-023`), com a posição gravada.

### Dependências e riscos

- Ficheiros antigos (`mostrar_icone`, `Ctrl+Alt+P`) têm de continuar válidos.
- O arrasto entre grelhas no Qt (`QListWidget`) exige tratamento próprio da
  largada, para que a grelha de origem não remova itens.
- Rollback: um commit da versão; `git revert`.

### Critérios de saída

- Cada ponto tem comportamento coberto por testes automáticos, ou verificação
  manual descrita em `docs/VERIFICACAO-MANUAL.md`.
- `pytest` sem falhas; capturas da interface (Diurno e Noturno) revistas.

### Validação

- Automática: testes novos do núcleo (espaços, contadores, inserção
  posicional, colar no Arquivo, migração, conflitos de teclas globais) e da
  interface (Qt offscreen).
- Manual: passos novos acrescentados à lista, executados na Fase 3.

## Fase 3: Validação manual no Windows e distribuição — em pausa

### Resultado

O Macropad está validado no Windows real, a partir do código e do executável.

### Trabalho incluído

- Percorrer os passos 1–85 de `docs/VERIFICACAO-MANUAL.md` com `run-dev.ps1`,
  e depois com `dist\Macropad\Macropad.exe` gerado por `build.ps1`.
- Corrigir as falhas encontradas, cada uma com o seu passo de verificação
  repetido.
- Acrescentar ao documento as verificações que a Fase 1 identificou como
  dependentes do Windows.

### Dependências e riscos

- Depende das Fases 1 e 2.
- Os passos são feitos pelo agente por controlo do ecrã (`Q-018`). Os
  passos 2, 23, 26, 27, 32 e 33 ficam para o utilizador.
- Problema encontrado: a barra de título do painel real não segue o tema
  (tarefa em `TASKS.md`).
- Risco: o PyInstaller pode não incluir os recursos (`ui/assets`, `locales`).
  Verificar os ícones e as traduções no executável.

### Critérios de saída

- Todos os passos de `docs/VERIFICACAO-MANUAL.md` estão assinalados como OK ou
  têm uma limitação aceite em `ANSWERS.md`.
- Os critérios de aceitação de [SPEC.md](SPEC.md#critérios-de-aceitação)
  cumprem-se com o executável.

### Validação

- Manual: a lista completa, nos temas Diurno e Noturno e em português e inglês.
- Automática: `pytest` sem falhas, executado também por `build.ps1`.

## Fase 4: Forgejo e publicação

### Resultado

O Forgejo está a correr no servidor, por HTTPS, e o repositório está publicado
no Forgejo e no GitHub com um único `git push`.

### Trabalho incluído

- Instalar e configurar o Forgejo (administrador, registo fechado, HTTPS).
- Criar o repositório no Forgejo e `virtual-visual-vext` no GitHub.
- Configurar o `origin` com os dois endereços de envio e enviar o histórico
  completo.
- Documentar no README como clonar e enviar.

### Dependências e riscos

- Forgejo feito pelo utilizador a 13-11-2026 (`Q-012`): repositório privado
  `VirtualMacroTextInputer`, acessível pelo Tailscale em HTTP; o `origin` aponta
  para lá e `main` segue `origin/main`.
- Falta o GitHub: bloqueado por `Q-010` e `Q-011`. Depois, acrescentar o
  GitHub como segundo endereço de envio do `origin`.
- Ações em servidor (portas, firewall, certificados) são difíceis de reverter
  sem acesso. Antes de executar, gerar o plano exato de comandos e o
  procedimento para desinstalar.
- Credenciais: chaves SSH ou tokens nunca entram no repositório.

### Critérios de saída

- `git push` atualiza os dois remotos, e `git ls-remote` em ambos mostra o mesmo
  commit.
- O Forgejo responde (hoje em HTTP pelo Tailscale; HTTPS só se `Q-025` o
  exigir) e sobrevive a um reinício do servidor.

### Validação

- Manual: clonar a partir de cada remoto para uma pasta nova e correr `pytest`.
- Reiniciar o serviço Forgejo e confirmar que o repositório continua acessível.
