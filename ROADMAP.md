# Roteiro

## Destino

Ver [SPEC.md](SPEC.md#destino).

## Estado atual

O código está implementado até à versão 0.3. A Fase 1 (revisão independente)
está concluída: dois problemas confirmados e corrigidos, com 110 testes
automáticos a passar. Nada foi validado no Windows real: os passos 1–61 de
`docs/VERIFICACAO-MANUAL.md` estão por assinalar. Ainda não há remotos git.

## Decisões em aberto

### Fronteira

- [ ] **Visibilidade do repositório no GitHub** (`Q-010`): privado ou público.
  Define quem vê o código e se o README pode referir caminhos pessoais.
- [ ] **Acesso do agente ao GitHub** (`Q-011`): ligar a conta GitHub nas
  definições do claude.ai, ou o utilizador cria o repositório
  `virtual-visual-vext` vazio e envia ele próprio. Sem isto não é possível criar
  o repositório nem enviar.
- [ ] **Servidor para o Forgejo** (`Q-012`): que máquina (VPS, homelab, NAS) e
  com que sistema operativo.

### Bloqueado

- [ ] **Forma de acesso ao servidor do Forgejo** (`Q-014`): o agente executa
  os comandos através do PC ligado, ou prepara-os para o utilizador executar.
  Depende de **Servidor para o Forgejo** (`Q-012`).
- [ ] **Endereço e HTTPS do Forgejo** (`Q-015`): domínio (ex.:
  `git.dominio.pt`) e proxy inverso existente (Caddy, Nginx, Traefik) ou novo.
  Depende de **Servidor para o Forgejo** (`Q-012`).
- [ ] **Modo de instalação do Forgejo** (`Q-016`): Docker, Podman ou binário
  com systemd. Depende de **Servidor para o Forgejo** (`Q-012`).

### Nevoeiro

- Cópias de segurança do Forgejo (o que guardar, onde, com que frequência).
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

## Fase 2: Validação manual no Windows e distribuição

### Resultado

O Macropad está validado no Windows real, a partir do código e do executável.

### Trabalho incluído

- Percorrer os passos 1–61 de `docs/VERIFICACAO-MANUAL.md` com `run-dev.ps1`,
  e depois com `dist\Macropad\Macropad.exe` gerado por `build.ps1`.
- Corrigir as falhas encontradas, cada uma com o seu passo de verificação
  repetido.
- Acrescentar ao documento as verificações que a Fase 1 identificou como
  dependentes do Windows.

### Dependências e riscos

- Depende da Fase 1.
- Os passos que exigem controlo de teclado e rato podem ser feitos pelo
  utilizador ou pelo agente com controlo do computador, se o utilizador o
  autorizar.
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

## Fase 3: Forgejo e publicação

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

- Bloqueada por `Q-010`, `Q-011`, `Q-012`, `Q-014`, `Q-015` e `Q-016`.
- Ações em servidor (portas, firewall, certificados) são difíceis de reverter
  sem acesso. Antes de executar, gerar o plano exato de comandos e o
  procedimento para desinstalar.
- Credenciais: chaves SSH ou tokens nunca entram no repositório.

### Critérios de saída

- `git push` atualiza os dois remotos, e `git ls-remote` em ambos mostra o mesmo
  commit.
- O Forgejo responde por HTTPS e sobrevive a um reinício do servidor.

### Validação

- Manual: clonar a partir de cada remoto para uma pasta nova e correr `pytest`.
- Reiniciar o serviço Forgejo e confirmar que o repositório continua acessível.
