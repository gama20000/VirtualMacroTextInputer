# Respostas

*English version: [ANSWERS.md](../../ANSWERS.md) (versão de referência).*

Decisões já tomadas. Os pedidos originais do utilizador estão no histórico da
conversa de 11-11-2026 e nos primeiros commits do histórico git.

## Q-001: Stack tecnológica

- **Resolvido:** 2026-11-11
- **Resposta:** Python 3.11+ com PySide6 (Qt 6), Win32 via `ctypes` e
  distribuição com PyInstaller.
- **Justificação:** Permite um núcleo em Python puro, testável sem Windows. O Qt
  funciona também em Linux (versão futura). O `ctypes` dá acesso direto ao hook
  `WH_KEYBOARD_LL`, a `SendInput` e a `WS_EX_NOACTIVATE`.
- **Evidência:** Proposta apresentada antes da implementação e aceite pelo
  utilizador ao continuar; `README.md`, secção Arquitetura.
- **Consequências:** O callback do hook tem de ser mínimo por causa do GIL e do
  LowLevelHooksTimeout. Não houve validação no Windows real durante o
  desenvolvimento (ver **Validação manual no Windows**).
- **Rever quando:** O hook em Python se mostrar pouco fiável no Windows real.

## Q-002: Valores predefinidos não fixados no pedido

- **Resolvido:** 2026-11-11
- **Resposta:**
  - Tecla de suspensão `Ctrl+Alt+P` (mudada depois, ver `Q-020`).
  - Macros podem não ter tecla (ficam só no painel).
  - Uma quebra de linha no texto equivale a `{Enter}` e uma tabulação a `{Tab}`.
  - As teclas premidas nas janelas do próprio Macropad nunca disparam macros.
  - A gravação pela interface reescreve o TOML no formato padrão; os
    comentários escritos à mão perdem-se.
- **Justificação:** São escolhas técnicas de rotina que o pedido delegava.
- **Evidência:** Resumo da entrega 0.1 ao utilizador; `README.md`.
- **Consequências:** Estão documentadas no README.
- **Rever quando:** O utilizador pedir outro comportamento.

## Q-003: Comportamento de «Nova macro» e macros sem texto

- **Resolvido:** 2026-11-11
- **Resposta:** «Nova macro» cria uma única macro, sem tecla e com texto vazio.
  Uma macro com texto vazio não é um erro: não faz nada até ter texto.
- **Justificação:** O utilizador pediu uma única macro, sem campos gerados a
  partir do número de macros existentes (a versão 0.1 atribuía uma tecla
  automaticamente). Permitir texto vazio deixa a nova macro gravar de imediato.
- **Evidência:** Pedido da ronda 0.2, ponto 6; `core/macro_ops.py::new_macro`;
  `tests/test_macro_ops.py`.
- **Consequências:** As macros com texto vazio não entram na deteção de
  duplicados.
- **Rever quando:** Nunca.

## Q-004: Confirmação ao eliminar várias macros

- **Resolvido:** 2026-11-11
- **Resposta:** Eliminar várias macros pede sempre confirmação com a
  quantidade, mesmo com «Não voltar a perguntar» ativo. Essa opção só se aplica
  a eliminações individuais.
- **Justificação:** É uma ação destrutiva em massa, e o pedido exige confirmação
  com a quantidade.
- **Evidência:** Pedido da ronda 0.3, ponto 3; `ui/config_window.py::_delete_macro`.
- **Consequências:** Nenhuma.
- **Rever quando:** O utilizador quiser que a opção se aplique a ambos os casos.

## Q-005: Cópia colada com tecla em uso

- **Resolvido:** 2026-11-11
- **Resposta:** A cópia colada fica sem tecla quando a tecla original já está
  atribuída a uma macro ativa.
- **Justificação:** Evita criar um conflito de tecla que bloquearia a gravação.
- **Evidência:** `core/macro_ops.py::insert_copy`; `tests/test_macro_ops.py`.
- **Consequências:** Nenhuma.
- **Rever quando:** Nunca.

## Q-006: Organização dos remotos git

- **Resolvido:** 2026-11-11
- **Resposta:** O repositório local terá um único remoto `origin` com dois
  endereços de envio (Forgejo e GitHub), em vez de o Forgejo espelhar
  automaticamente para o GitHub.
- **Justificação:** O utilizador perguntou qual das opções é mais resiliente.
  Com dois endereços de envio não há ponto único de falha: se um servidor
  falhar, o outro recebe na mesma e o git mostra o erro. Um espelho depende do
  servidor Forgejo e pode deixar de funcionar sem ninguém dar por isso.
- **Evidência:** Resposta do utilizador («Qual destas é mais resiliente?») e a
  recomendação dada.
- **Consequências:** Cada `git push` envia para os dois; é preciso ter
  credenciais válidas em ambos.
- **Rever quando:** Houver mais contribuidores ou CI a depender de um dos
  remotos.

## Q-007: Nome do repositório no GitHub

- **Resolvido:** 2026-11-11 (atualizado a 2026-11-15)
- **Resposta:** `VirtualMacroTextInputer`, o mesmo nome do repositório no
  Forgejo e do programa. A primeira proposta, `virtual-visual-vext` («Virtual &
  Visual Vext»), foi substituída quando o programa mudou de nome (`Q-026`).
- **Justificação:** Um só nome em todo o lado evita confusões entre o
  programa, o repositório do Forgejo e o do GitHub.
- **Evidência:** Respostas do utilizador de 11-11-2026 e 13-11-2026.
- **Consequências:** O GitHub redireciona o endereço antigo se o repositório
  mudar de nome mais tarde.
- **Rever quando:** O utilizador preferir outro nome.

## Q-008: Local do Forgejo

- **Resolvido:** 2026-11-11
- **Resposta:** O Forgejo será instalado num servidor, não no PC nem num
  serviço público como o Codeberg.
- **Justificação:** Escolha do utilizador.
- **Evidência:** Resposta do utilizador («Instalar num servidor»).
- **Consequências:** Ver `Q-012`.
- **Rever quando:** Não houver servidor disponível.

## Q-009: Ferramenta de revisão independente

- **Resolvido:** 2026-11-11
- **Resposta:** A revisão é feita pelo Codex CLI em modo só de leitura, guiado
  pelas «Review guidelines» do `AGENTS.md`. Os resultados são confirmados no
  código antes de qualquer correção.
- **Justificação:** É uma revisão por um agente que não escreveu o código. As
  revisões automáticas trazem falsos positivos, daí a confirmação.
- **Evidência:** `AGENTS.md`. O Codex CLI ainda não estava instalado no PC do
  utilizador nessa altura (o comando `codex` não foi encontrado).
- **Consequências:** A fase de revisão depende de o Codex estar instalado e com
  sessão iniciada.
- **Rever quando:** Não for possível instalar ou usar o Codex.

## Q-013: Instalação do Codex CLI

- **Resolvido:** 2026-11-12
- **Resposta:** O utilizador correu a revisão com o Codex no seu PC.
- **Justificação:** É o necessário para a revisão independente da Fase 1.
- **Evidência:** Relatório colado pelo utilizador a 12-11-2026, guardado em
  `docs/pt/revisao-codex.md`.
- **Consequências:** As próximas revisões (por exemplo `/review` sobre um
  commit) podem usar a mesma instalação.
- **Rever quando:** Nunca.

## Q-017: Tratamento dos resultados da revisão

- **Resolvido:** 2026-11-12
- **Resposta:** Os dois pontos (P1 e P2) foram confirmados com testes que
  falhavam e depois corrigidos. Não há pontos aceites sem correção nem falsos
  positivos.
- **Justificação:** O P1 causava perda de dados (macros arquivadas apagadas do
  TOML). O P2 tinha impacto baixo, mas a correção é defensiva e trivial.
- **Evidência:** `docs/pt/revisao-codex.md`; os testes de regressão lá indicados;
  `pytest` com 110 testes a passar.
- **Consequências:** A Fase 1 cumpre os critérios de saída.
- **Rever quando:** Uma nova revisão ou a validação manual encontrar problemas
  relacionados.

## Q-018: Método da validação manual

- **Resolvido:** 2026-11-12
- **Resposta:** O agente executa a lista de verificação no PC por controlo do
  ecrã. Usa o lançador `tools\macropad-teste.cmd`, que arranca a aplicação com
  `python.exe` (com consola) e com uma configuração separada em
  `%TEMP%\MacropadTeste`. O utilizador faz os passos que o agente não consegue
  fazer (👤 em `docs/pt/VERIFICACAO-MANUAL.md`). O utilizador também pode
  fazer a lista toda.
- **Justificação:** O utilizador pediu que o agente fizesse os passos. Uma
  configuração separada protege as macros reais. O terminal só aceita cliques
  do agente, por isso a aplicação arranca a partir de um `.cmd` aberto no
  Explorador.
- **Evidência:** Pedido do utilizador de 12-11-2026; resultados registados em
  `docs/pt/VERIFICACAO-MANUAL.md`.
- **Consequências:**
  - O agente não consegue usar o botão direito na barra de tarefas (menu do
    ícone), premir a tecla 1 do teclado numérico, reiniciar a sessão nem
    responder ao UAC: esses passos ficam para o utilizador.
  - O mutex de instância única é partilhado: se uma instância já estiver a
    correr (real ou de teste), o lançador limita-se a abrir a configuração
    dela.
  - As janelas do Macropad pertencem ao `pythonw`/`python` do Python 3.12
    da Microsoft Store e só ficam visíveis ao agente depois de esse processo
    ser autorizado.
- **Rever quando:** For preciso testar o `.exe` gerado pelo PyInstaller
  (processo diferente, exige nova autorização).

## Q-019: Ícone dos botões e posição do título e da tecla

- **Resolvido:** 2026-11-12
- **Resposta:** Os botões deixam de ter o ícone «[T]», e a opção «Mostrar ícone»
  desaparece. O título e a tecla podem ficar, cada um, em cima, ao centro ou em
  baixo do botão.
- **Justificação:** O pedido 0.4 remove os ícones «para já» (ponto 10) e pede
  posições para o título e a tecla (ponto 7). Sem ícone, as posições passam a
  ser relativas ao botão.
- **Evidência:** Resposta do utilizador a 12-11-2026.
- **Consequências:** A opção `mostrar_icone` dos ficheiros antigos continua a
  ser aceite, mas é ignorada. Os estilos predefinidos deixam de a usar.
- **Rever quando:** Voltarem a ser pedidos ícones nos botões.

## Q-020: Teclas globais predefinidas

- **Resolvido:** 2026-11-12
- **Resposta:** Suspender/reativar com **Shift+Escape**; mostrar/ocultar o
  painel com **Shift+F12**. As configurações que ainda tenham o antigo
  `Ctrl+Alt+P` são migradas para Shift+Escape uma única vez (registado em
  `estado.toml`). Se a migração não puder ser gravada (conflito ou erro de
  escrita), volta a ser tentada no arranque seguinte.
- **Justificação:** O utilizador pediu Shift+Escape para as duas funções. Como
  uma combinação só pode ter uma função, escolheu esta distribuição e pediu a
  migração da configuração atual.
- **Evidência:** Respostas do utilizador a 12-11-2026.
- **Consequências:** As macros não podem usar nenhuma das duas teclas globais,
  e as duas têm de ser diferentes entre si.
- **Rever quando:** O utilizador mudar as teclas nas Preferências (fica a
  escolha dele).

## Q-021: Funcionamento do contador

- **Resolvido:** 2026-11-12
- **Resposta:** O contador funciona no painel e com uma tecla associada, e só
  mostra o valor (não escreve texto). Um toque soma; manter premido repõe. O
  âmbito e a suspensão aplicam-se à tecla como às macros. A contagem é gravada
  em `estado.toml` e a configuração no ficheiro do conjunto.
- **Justificação:** Resposta do utilizador. Gravar a contagem fora do TOML do
  conjunto evita reescrever esse ficheiro, e recarregá-lo, a cada clique.
- **Evidência:** Resposta do utilizador a 12-11-2026.
- **Consequências:** Cada contador tem um `id` estável. A pressão longa nunca
  soma. A tecla de um contador premida com a janela de configuração à frente
  conta da mesma forma. Desde 15-11-2026 a reposição acontece quando o tempo da
  pressão longa é atingido, e não ao largar
  ([Q-032](#q-032-reposição-do-contador-com-a-tecla-premida-e-som)).
- **Rever quando:** For pedido que o contador escreva o valor.

## Q-022: Atribuição de tecla por cima do botão e atalhos existentes

- **Resolvido:** 2026-11-12
- **Resposta:** Com o ponteiro sobre um botão, Delete, Backspace, Tab, Ctrl+C e
  Ctrl+V mantêm as suas funções (eliminar, navegar, copiar, colar). As
  restantes teclas e combinações são atribuídas. Enquanto o ponteiro está sobre
  um botão, as teclas globais deixam de ser intercetadas, para que o conflito
  possa ser explicado. A atribuição só acontece com o foco fora de campos de
  edição.
- **Justificação:** Evita apagar ou atribuir teclas por engano ao escrever num
  campo com o rato parado sobre um botão, e mantém os atalhos já pedidos.
- **Evidência:** Pontos 6 (versão 0.2) e 9 (versão 0.4) dos pedidos.
- **Consequências:** Para atribuir Delete ou Backspace a uma macro usa-se o
  campo «Tecla» do editor.
- **Rever quando:** O utilizador quiser atribuir essas teclas por cima do botão.

## Q-023: Barra de título do painel

- **Resolvido:** 2026-11-12
- **Resposta:** O painel passa a não ter moldura do Windows. Desenha a sua
  própria barra de título (a mesma da pré-visualização), com as cores do tema,
  arrasto para mover e botão de fechar.
- **Justificação:** No Windows real, a barra de título nativa do painel (janela
  de ferramenta sem foco) não seguia o tema, e o pedido exige que o painel seja
  igual à pré-visualização. Uma barra própria é idêntica nas duas.
- **Evidência:** Passos 36 e 58 de `docs/pt/VERIFICACAO-MANUAL.md` (parciais).
- **Consequências:** Mover o painel faz-se pela barra própria. A posição do
  painel passa a ser gravada.
- **Rever quando:** A barra própria der problemas de arrasto ou de foco.

## Q-012: Servidor para o Forgejo

- **Resolvido:** 2026-11-13
- **Resposta:** O utilizador instalou o Forgejo no seu próprio servidor e criou
  lá o repositório privado `VirtualMacroTextInputer` (a princípio chamado
  `Macropad`). Só é acessível pela rede Tailscale do utilizador, em HTTP. O
  endereço está na configuração git local, não no repositório. O histórico foi
  enviado pelo utilizador a partir do PC.
- **Justificação:** O utilizador tratou da instalação; o agente não administra
  o servidor.
- **Evidência:** Mensagens do utilizador de 13-11-2026 e o endereço do
  repositório.
- **Consequências:** `Q-014`, `Q-015` e `Q-016` (forma de acesso, endereço e
  modo de instalação) deixam de ser decisões do projeto. O agente não chega ao
  servidor a partir do seu ambiente (rede privada), por isso os envios para o
  Forgejo são feitos pelo utilizador com `git push`. O Tailscale já cifra o
  tráfego; HTTPS no próprio Forgejo fica por decidir (`Q-025`).
- **Rever quando:** O servidor ou o endereço mudar, ou for preciso acesso fora
  do Tailscale.

## Q-026: Novo nome do programa

- **Resolvido:** 2026-11-13
- **Resposta:** O programa passa a chamar-se **Virtual Macro Text Inputer**
  (janelas, ícone junto ao relógio, executável `VirtualMacroTextInputer.exe`,
  pasta de dados `%APPDATA%\VirtualMacroTextInputer`, entrada de arranque
  `VirtualMacroTextInputer`). O pacote Python e os ficheiros do código
  continuam `macropad`.
- **Justificação:** Pedido do utilizador, a seguir à mudança de nome do
  repositório. Mudar também o pacote Python obrigaria a renomear todo o código
  e os testes sem ganho visível.
- **Evidência:** Mensagem do utilizador de 13-11-2026.
- **Consequências:** No primeiro arranque, a pasta `%APPDATA%\Macropad` é
  copiada para a nova (a antiga fica como cópia de segurança). A entrada de
  arranque «Macropad» é apagada quando a nova é escrita. Se a versão antiga
  estiver a correr, o programa novo avisa e não arranca (dois hooks
  escreveriam as macros duas vezes). Nome visível centralizado em
  `src/macropad/branding.py`. Passos manuais 87–89.
- **Rever quando:** O nome mudar outra vez, ou se quiser renomear também o
  pacote Python.

## Q-027: Localização do repositório no PC

- **Resolvido:** 2026-11-15
- **Resposta:** O repositório passa a estar em
  `%USERPROFILE%\source\VirtualMacroTextInputer`, fora do Google Drive. Foi
  criado com `git clone` local a partir da pasta antiga (todo o histórico), com
  o `origin` a apontar para o Forgejo e as mesmas definições de autor.
- **Justificação:** O utilizador não quer o repositório dentro da pasta
  sincronizada pelo Google Drive. `Documents` foi posto de parte porque mostra
  sinais de também ser sincronizada (`.tmp.drivedownload`).
- **Evidência:** Mensagens do utilizador de 15-11-2026 e a escolha «Pasta
  source».
- **Consequências:** O ambiente `.venv` não é copiado (não é portável):
  recria-se com `run-dev.ps1`. A pasta antiga no Google Drive fica até o
  utilizador decidir apagá-la.
- **Rever quando:** O repositório mudar outra vez de sítio.

## Q-010: Visibilidade do repositório no GitHub

- **Resolvido:** 2026-11-15
- **Resposta:** Público.
- **Justificação:** Escolha do utilizador.
- **Evidência:** Resposta do utilizador de 15-11-2026.
- **Consequências:** Antes do primeiro envio, saem dos ficheiros publicados e
  do histórico os dados pessoais: o endereço e o utilizador do Forgejo, os
  caminhos locais com o nome do utilizador do Windows e o email pessoal nos
  commits (`Q-029`). Falta escolher uma licença (ver ROADMAP, nevoeiro).
- **Rever quando:** O código deixar de dever ser público.

## Q-011: Acesso do agente ao GitHub

- **Resolvido:** 2026-11-15
- **Resposta:** O utilizador liga a conta GitHub ao Claude e o agente cria o
  repositório e envia o histórico.
- **Justificação:** Escolha do utilizador.
- **Evidência:** Resposta do utilizador de 15-11-2026.
- **Consequências:** Os envios seguintes a partir do PC vão pelo remoto
  `origin` com os dois endereços (`Q-006`) e precisam de credenciais do GitHub
  no PC (o Git Credential Manager pede-as uma vez).
- **Rever quando:** A ligação ao GitHub for removida.

## Q-028: Idioma da documentação

- **Resolvido:** 2026-11-15
- **Resposta:** Inglês na raiz do repositório e em `docs/` (README, SPEC,
  ROADMAP, TASKS, ANSWERS, AGENTS, `docs/MANUAL-CHECKLIST.md`,
  `docs/CODEX-REVIEW.md`); as versões em português em `docs/pt/`. Os ficheiros
  em inglês são a referência; os dois são atualizados em conjunto. O
  `AGENTS.md` pede aos agentes que respondam ao responsável em português
  europeu. Os comentários do código, os nomes dos campos TOML e os textos
  portugueses da interface não mudam.
- **Justificação:** Escolha do utilizador ao publicar no GitHub: página
  principal em inglês num repositório público, mantendo a documentação em
  português.
- **Evidência:** Resposta do utilizador de 15-11-2026 («Inglês na raiz, PT em
  pasta»).
- **Consequências:** Duas cópias de cada documento para manter iguais; as
  ligações em `docs/pt/` são relativas a essa pasta.
- **Rever quando:** Manter as duas línguas se tornar um peso.

## Q-029: Email nos commits

- **Resolvido:** 2026-11-15
- **Resposta:** Antes do primeiro envio público, o histórico é reescrito para
  o autor e o committer usarem o email privado do GitHub
  (`<id>+<utilizador>@users.noreply.github.com`) em vez do email pessoal. O
  `user.email` local passa a ser o mesmo endereço.
- **Justificação:** Num repositório público, o email dos commits fica visível
  para qualquer pessoa. O utilizador escolheu o endereço privado do GitHub.
- **Evidência:** Resposta do utilizador de 15-11-2026.
- **Consequências:** Os identificadores dos commits mudam; o Forgejo tem de
  receber o histórico reescrito com `git push --force` (feito pelo
  utilizador). Cópias do histórico antigo devem ser descartadas.
- **Rever quando:** Nunca.

## Q-030: Licença

- **Resolvido:** 2026-11-15
- **Resposta:** MIT. `LICENSE` na raiz, direitos de autor em nome de
  «gama20000» (o nome da conta GitHub, não um nome pessoal).
- **Justificação:** Escolha do utilizador. A MIT é a licença comum mais
  permissiva: qualquer pessoa pode reutilizar o código, mantendo o aviso.
- **Evidência:** Mensagem do utilizador de 15-11-2026.
- **Consequências:** O `pyproject.toml` declara `license = { text = "MIT" }`.
- **Rever quando:** O utilizador quiser uma licença copyleft.

## Q-031: Linhas e páginas do painel

- **Resolvido:** 2026-11-15
- **Resposta:** O painel tem um número de linhas além das colunas («Todas» por
  omissão, `linhas = 0`). Com mais células do que linhas × colunas, mostra
  páginas com setas ◀ ▶, e todas as páginas têm o tamanho completo. Com menos,
  o painel encolhe para as linhas necessárias.
- **Justificação:** Escolha do utilizador entre páginas, deslocamento ou
  esconder o excesso. As páginas são como funciona um Stream Deck; o tamanho
  fixo entre páginas mantém os botões no sítio ao mudar de página.
- **Evidência:** Respostas do utilizador de 15-11-2026.
- **Consequências:** `[painel] linhas` no `config.toml` (0–12). Os estilos
  predefinidos mantêm as linhas, tal como as colunas. As teclas executam as
  macros de qualquer página. A área Ativo da configuração continua a mostrar
  todas as macros.
- **Rever quando:** O utilizador quiser que o painel mantenha o tamanho fixo
  mesmo com poucos botões.

## Q-032: Reposição do contador com a tecla premida, e som

- **Resolvido:** 2026-11-15
- **Resposta:** Enquanto um contador está premido (rato ou tecla), o botão do
  painel mostra o progresso ao longo da borda; ao atingir o tempo da pressão
  longa, a contagem é reposta logo, uma vez, com um sinal verde. O som da
  reposição configura-se por contador: nenhum por omissão, ou um som do sistema
  do Windows (`som_reposicao`).
- **Justificação:** Pedido e resposta do utilizador (som por contador).
- **Evidência:** Mensagens do utilizador de 15-11-2026.
- **Consequências:** O motor inicia um temporizador quando a tecla é premida;
  largar só soma se a reposição ainda não aconteceu. A janela de configuração
  usa a mesma lógica do motor. O progresso aparece no painel; a área Ativo da
  configuração não tem animação.
- **Rever quando:** Um contador precisar de um ficheiro de som próprio.

## Q-033: Teclas multimédia

- **Resolvido:** 2026-11-15
- **Resposta:** Reproduzir/Pausa, faixa anterior e faixa seguinte atribuem-se
  num menu «Multimédia» junto ao campo da tecla, com as mesmas verificações de
  conflito da atribuição com o rato. As teclas aparecem com nomes legíveis; o
  ficheiro guarda os nomes canónicos (`MediaPlayPause`, `MediaPrev`,
  `MediaNext`).
- **Justificação:** Premir uma tecla multimédia para a gravar também chega ao
  leitor de música, porque o hook deixa passar as teclas durante a gravação.
- **Evidência:** Pedido do utilizador de 15-11-2026; o `platform/winkeys.py`
  já tinha os códigos virtuais.
- **Consequências:** Suspensas ou fora do âmbito, as teclas seguem para o
  Windows. Os teclados cujas teclas multimédia só enviam `WM_APPCOMMAND` (sem
  código virtual) não são vistos pelo hook de teclado; a confirmar no teclado
  do utilizador.
- **Rever quando:** As teclas multimédia de um teclado não chegarem ao hook.

## Q-034: Release num só ficheiro

- **Resolvido:** 2026-11-15
- **Resposta:** As releases são um único `VirtualMacroTextInputer.exe`
  (PyInstaller `--onefile`) com o respetivo SHA-256, gerado pelo GitHub
  Actions em `windows-latest` quando se envia uma etiqueta `vX.Y.Z`. O
  `build.ps1 -OneFile` gera o mesmo ficheiro no PC do utilizador; o
  `build.ps1` sem essa opção mantém a versão em pasta.
- **Justificação:** O ambiente do agente é Linux e o PyInstaller não compila
  para outro sistema, por isso a compilação tem de ser feita no Windows. Uma
  máquina de CI limpa dá sempre o mesmo resultado e publica a release
  sozinha; a compilação local continua disponível para testes rápidos. O
  repositório é público, por isso os minutos do Actions são gratuitos.
- **Evidência:** Perguntas do utilizador e indicação de que o repositório é
  público (15-11-2026).
- **Consequências:** O executável não tem assinatura (aviso do SmartScreen na
  primeira execução). Um só ficheiro arranca 1–3 s mais devagar (descompacta-se
  para uma pasta temporária) e tem mais probabilidade de alertar os antivírus
  do que a versão em pasta. O workflow recusa uma etiqueta diferente da versão
  do `pyproject.toml`.
- **Rever quando:** Houver um certificado de assinatura de código, ou depois
  de uma reescrita (Rust, `Q-024`) que gere um executável nativo pequeno.

