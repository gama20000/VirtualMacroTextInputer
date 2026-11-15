# Roteiro

*English version: [ROADMAP.md](../../ROADMAP.md) (versão de referência).*

## Destino

Ver [SPEC.md](SPEC.md#destino).

## Estado atual

O código está na versão 0.5 e o programa chama-se agora Virtual Macro Text
Inputer. A Fase 1 (revisão independente) e a Fase 2 (versão 0.4, incluindo a
barra de título própria do painel) estão concluídas. Depois disso, seis
revisões do Codex foram corrigidas e a versão 0.5 (progresso e reposição do
contador com a tecla premida, inserção a seguir à seleção, linhas do painel
com páginas, teclas multimédia, anular a eliminação) está implementada; 187
testes automáticos passam (um ignorado fora do Windows). Falta a
validação manual no Windows (Fase 3, em pausa desde 12-11-2026, com 16 passos
verificados e 3 parciais; os passos 62–89 cobrem a 0.4 e a mudança de nome,
os passos 90–99 cobrem a 0.5). O
repositório está no Forgejo do utilizador (privado, pelo Tailscale) e é
público no GitHub; as releases com um só `.exe` são geradas pelo GitHub
Actions (Fase 4).

## Decisões em aberto

### Fronteira

- [ ] **Reescrita em Rust** (`Q-024`): vale a pena reescrever o programa em
  Rust para ter um executável mais leve e com arranque mais rápido? A decisão
  deve esperar pela validação da versão Python (Fase 3), que fixa o
  comportamento a reproduzir.

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
- [x] [Valores predefinidos não fixados no pedido](ANSWERS.md#q-002-valores-predefinidos-não-fixados-no-pedido) (`Q-002`): macros sem tecla, quebra de linha = `{Enter}`.
- [x] [Comportamento de «Nova macro» e macros sem texto](ANSWERS.md#q-003-comportamento-de-nova-macro-e-macros-sem-texto) (`Q-003`): uma macro, sem tecla, texto vazio permitido.
- [x] [Confirmação ao eliminar várias macros](ANSWERS.md#q-004-confirmação-ao-eliminar-várias-macros) (`Q-004`): sempre, com a quantidade.
- [x] [Cópia colada com tecla em uso](ANSWERS.md#q-005-cópia-colada-com-tecla-em-uso) (`Q-005`): a cópia fica sem tecla.
- [x] [Organização dos remotos git](ANSWERS.md#q-006-organização-dos-remotos-git) (`Q-006`): um `origin` com dois endereços de envio.
- [x] [Nome do repositório no GitHub](ANSWERS.md#q-007-nome-do-repositório-no-github) (`Q-007`): `VirtualMacroTextInputer`.
- [x] [Local do Forgejo](ANSWERS.md#q-008-local-do-forgejo) (`Q-008`): num servidor.
- [x] [Ferramenta de revisão independente](ANSWERS.md#q-009-ferramenta-de-revisão-independente) (`Q-009`): Codex CLI só de leitura com o `AGENTS.md`.
- [x] [Visibilidade do repositório no GitHub](ANSWERS.md#q-010-visibilidade-do-repositório-no-github) (`Q-010`): público.
- [x] [Acesso do agente ao GitHub](ANSWERS.md#q-011-acesso-do-agente-ao-github) (`Q-011`): o utilizador liga o GitHub ao Claude.
- [x] [Servidor para o Forgejo](ANSWERS.md#q-012-servidor-para-o-forgejo) (`Q-012`): instalado pelo utilizador, pelo Tailscale. Torna `Q-014`, `Q-015` e `Q-016` desnecessárias.
- [x] [Instalação do Codex CLI](ANSWERS.md#q-013-instalação-do-codex-cli) (`Q-013`): o utilizador correu a revisão no PC.
- [x] [Tratamento dos resultados da revisão](ANSWERS.md#q-017-tratamento-dos-resultados-da-revisão) (`Q-017`): P1 e P2 confirmados e corrigidos.
- [x] [Método da validação manual](ANSWERS.md#q-018-método-da-validação-manual) (`Q-018`): controlo do ecrã com uma configuração separada; o utilizador faz os passos 👤.
- [x] [Ícone dos botões e posição do título e da tecla](ANSWERS.md#q-019-ícone-dos-botões-e-posição-do-título-e-da-tecla) (`Q-019`): sem ícone; título e tecla em cima, ao centro ou em baixo.
- [x] [Teclas globais predefinidas](ANSWERS.md#q-020-teclas-globais-predefinidas) (`Q-020`): Shift+Escape suspende; Shift+F12 mostra/oculta o painel.
- [x] [Funcionamento do contador](ANSWERS.md#q-021-funcionamento-do-contador) (`Q-021`): painel e tecla, só mostra; manter premido repõe.
- [x] [Atribuição de tecla por cima do botão e atalhos existentes](ANSWERS.md#q-022-atribuição-de-tecla-por-cima-do-botão-e-atalhos-existentes) (`Q-022`): Delete, Backspace, Tab, Ctrl+C e Ctrl+V mantêm-se.
- [x] [Barra de título do painel](ANSWERS.md#q-023-barra-de-título-do-painel) (`Q-023`): o painel desenha a sua própria barra.
- [x] [Novo nome do programa](ANSWERS.md#q-026-novo-nome-do-programa) (`Q-026`): Virtual Macro Text Inputer; dados copiados da pasta antiga.
- [x] [Localização do repositório no PC](ANSWERS.md#q-027-localização-do-repositório-no-pc) (`Q-027`): `%USERPROFILE%\source\VirtualMacroTextInputer`, fora do Google Drive.
- [x] [Idioma da documentação](ANSWERS.md#q-028-idioma-da-documentação) (`Q-028`): inglês na raiz, português em `docs/pt/`.
- [x] [Licença](ANSWERS.md#q-030-licença) (`Q-030`): MIT.
- [x] [Linhas e páginas do painel](ANSWERS.md#q-031-linhas-e-páginas-do-painel) (`Q-031`): páginas com setas; o painel encolhe com poucos botões.
- [x] [Reposição do contador com a tecla premida, e som](ANSWERS.md#q-032-reposição-do-contador-com-a-tecla-premida-e-som) (`Q-032`): repõe ao atingir o tempo; som por contador, nenhum por omissão.
- [x] [Teclas multimédia](ANSWERS.md#q-033-teclas-multimédia) (`Q-033`): atribuídas num menu «Multimédia».
- [x] [Release num só ficheiro](ANSWERS.md#q-034-release-num-só-ficheiro) (`Q-034`): `build.ps1 -OneFile` no PC; GitHub Actions com etiquetas `vX.Y.Z`.
- [x] [Email nos commits](ANSWERS.md#q-029-email-nos-commits) (`Q-029`): endereço privado do GitHub; histórico reescrito.

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
  foco) não são confirmáveis só pela leitura do código. Passam para a Fase 3
  como verificações específicas.
- Rollback: cada correção num commit próprio (`git revert`).

### Critérios de saída

- O relatório da revisão está guardado (`docs/pt/revisao-codex.md`), com o
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
  manual descrita em `docs/pt/VERIFICACAO-MANUAL.md`.
- `pytest` sem falhas; capturas da interface (Diurno e Noturno) revistas.

### Validação

- Automática: testes novos do núcleo (espaços, contadores, inserção
  posicional, colar no Arquivo, migração, conflitos de teclas globais) e da
  interface (Qt offscreen).
- Manual: passos novos acrescentados à lista, executados na Fase 3.

## Fase 3: Validação manual no Windows e distribuição — em pausa

### Resultado

O programa está validado no Windows real, a partir do código e do executável.

### Trabalho incluído

- Percorrer os passos 1–99 de `docs/pt/VERIFICACAO-MANUAL.md` com
  `run-dev.ps1`, e depois com
  `dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe` gerado por
  `build.ps1`.
- Corrigir as falhas encontradas, cada uma com o seu passo de verificação
  repetido.
- Acrescentar ao documento as verificações que a Fase 1 identificou como
  dependentes do Windows.

### Dependências e riscos

- Depende das Fases 1 e 2.
- Os passos são feitos pelo agente por controlo do ecrã (`Q-018`) ou pelo
  utilizador. Os passos 2, 23, 26, 27, 32, 33, 84, 85 e 89 ficam para o
  utilizador.
- Risco: o PyInstaller pode não incluir os recursos (`ui/assets`, `locales`).
  Verificar os ícones e as traduções no executável.

### Critérios de saída

- Todos os passos de `docs/pt/VERIFICACAO-MANUAL.md` estão assinalados como OK
  ou têm uma limitação aceite em `ANSWERS.md`.
- Os critérios de aceitação de [SPEC.md](SPEC.md#critérios-de-aceitação)
  cumprem-se com o executável.

### Validação

- Manual: a lista completa, nos temas Diurno e Noturno e em português e inglês.
- Automática: `pytest` sem falhas, executado também por `build.ps1`.

## Fase 4: Forgejo e publicação — em curso

### Resultado

O repositório está publicado no Forgejo (privado) e no GitHub (público), e um
único `git push` atualiza os dois.

### Trabalho incluído

- Forgejo instalado pelo utilizador (`Q-012`); repositório
  `VirtualMacroTextInputer`.
- Documentação em inglês na raiz e em português em `docs/pt/` (`Q-028`).
- Histórico reescrito com o email privado do GitHub (`Q-029`) e dados pessoais
  retirados dos ficheiros publicados.
- Criar o repositório público `VirtualMacroTextInputer` no GitHub e enviar.
- Configurar o `origin` com os dois endereços de envio; o utilizador envia o
  histórico reescrito para o Forgejo com `--force`.
- Documentar no README como clonar e enviar.

### Dependências e riscos

- Precisa da ligação ao GitHub (`Q-011`).
- Reescrever o histórico muda todos os identificadores dos commits; clones
  antigos têm de ser descartados.
- Credenciais: chaves SSH ou tokens nunca entram no repositório.

### Critérios de saída

- `git push` atualiza os dois remotos, e `git ls-remote` em ambos mostra o mesmo
  commit.
- O repositório público não contém o email pessoal, o endereço do Forgejo nem
  caminhos com o utilizador local (ficheiros e histórico).
- O Forgejo responde (em HTTP pelo Tailscale; HTTPS só se `Q-025` o exigir) e
  sobrevive a um reinício do servidor.

### Validação

- Manual: clonar a partir de cada remoto para uma pasta nova e correr `pytest`.
- Automática: procurar no histórico publicado o email pessoal e os endereços
  privados.
