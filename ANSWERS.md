# Respostas

Decisões já tomadas. Os pedidos originais do utilizador estão no histórico da
conversa de 11-11-2026 e nos commits `6da0f2f`, `5d330ce` e `936fe38`.

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
  - Tecla de suspensão `Ctrl+Alt+P`.
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

- **Resolvido:** 2026-11-11
- **Resposta:** Nome proposto `virtual-visual-vext`, com «Virtual & Visual Vext»
  na descrição.
- **Justificação:** O utilizador indicou «Virtual & Visual Vext», mas o GitHub
  não aceita espaços nem «&» em nomes de repositório.
- **Evidência:** Resposta do utilizador; regras de nomes do GitHub.
- **Consequências:** O nome do projeto (Macropad) e o nome do repositório são
  diferentes. A visibilidade continua por decidir (ver ROADMAP).
- **Rever quando:** O utilizador preferir outro nome.

## Q-008: Local do Forgejo

- **Resolvido:** 2026-11-11
- **Resposta:** O Forgejo será instalado num servidor, não no PC nem num
  serviço público como o Codeberg.
- **Justificação:** Escolha do utilizador.
- **Evidência:** Resposta do utilizador («Instalar num servidor»).
- **Consequências:** Faltam o servidor, a forma de acesso, o domínio e o modo de
  instalação (ver ROADMAP).
- **Rever quando:** Não houver servidor disponível.

## Q-009: Ferramenta de revisão independente

- **Resolvido:** 2026-11-11
- **Resposta:** A revisão é feita pelo Codex CLI em modo só de leitura, guiado
  pelas «Review guidelines» do `AGENTS.md`. Os resultados são confirmados no
  código antes de qualquer correção.
- **Justificação:** É uma revisão por um agente que não escreveu o código. As
  revisões automáticas trazem falsos positivos, daí a confirmação.
- **Evidência:** `AGENTS.md` (commit `936fe38`). O Codex CLI ainda não estava
  instalado no PC do utilizador (o comando `codex` não foi encontrado).
- **Consequências:** A fase de revisão depende de o Codex estar instalado e com
  sessão iniciada.
- **Rever quando:** Não for possível instalar ou usar o Codex.

## Q-013: Instalação do Codex CLI

- **Resolvido:** 2026-11-12
- **Resposta:** O utilizador correu a revisão com o Codex no seu PC.
- **Justificação:** É o necessário para a revisão independente da Fase 1.
- **Evidência:** Relatório colado pelo utilizador a 12-11-2026, guardado em
  `docs/revisao-codex.md`.
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
- **Evidência:** `docs/revisao-codex.md`; os testes de regressão lá indicados;
  `pytest` com 110 testes a passar.
- **Consequências:** A Fase 1 cumpre os critérios de saída. A seguir vem a
  Fase 2 (validação manual no Windows).
- **Rever quando:** Uma nova revisão ou a validação manual encontrar problemas
  relacionados.

## Q-018: Método da validação manual

- **Resolvido:** 2026-11-12
- **Resposta:** O agente executa a lista de verificação no PC por controlo do
  ecrã. Usa o lançador `tools\macropad-teste.cmd`, que arranca a aplicação com
  `python.exe` (com consola) e com uma configuração separada em
  `%TEMP%\MacropadTeste`. O utilizador faz os passos que o agente não consegue
  fazer (👤 em `docs/VERIFICACAO-MANUAL.md`).
- **Justificação:** O utilizador pediu que o agente fizesse os passos. Uma
  configuração separada protege as macros reais. O terminal só aceita cliques
  do agente, por isso a aplicação arranca a partir de um `.cmd` aberto no
  Explorador.
- **Evidência:** Pedido do utilizador de 12-11-2026; resultados registados em
  `docs/VERIFICACAO-MANUAL.md`.
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
  `estado.toml`).
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
- **Consequências:** Cada contador tem um `id` estável. A pressão longa decide-se
  pela duração entre premir e largar e nunca soma.
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
- **Evidência:** Passos 36 e 58 de `docs/VERIFICACAO-MANUAL.md` (parciais).
- **Consequências:** Mover o painel faz-se pela barra própria. A posição do
  painel passa a ser gravada.
- **Rever quando:** A barra própria der problemas de arrasto ou de foco.

## Q-012: Servidor para o Forgejo

- **Resolvido:** 2026-11-13
- **Resposta:** O utilizador instalou o Forgejo no seu próprio servidor e criou
  o repositório privado `VirtualMacroTextInputer`. É acessível pela rede Tailscale em
  `http://(endereço privado):3333/VirtualMacroTextInputer.git` (HTTP). O histórico foi
  enviado pelo utilizador a partir do PC.
- **Justificação:** O utilizador tratou da instalação; o agente não administra
  o servidor.
- **Evidência:** Mensagens do utilizador de 13-11-2026 («já criei o
  repositório privado do Forgejo», «Já consegui») e o endereço do repositório.
- **Consequências:** `Q-014`, `Q-015` e `Q-016` (forma de acesso, endereço e
  modo de instalação) deixam de ser decisões do projeto. O `origin` local
  aponta para este endereço e `main` segue `origin/main`. O agente não chega ao
  servidor a partir do seu ambiente (rede privada), por isso os envios são
  feitos pelo utilizador com `git push`. O acesso é só pela rede Tailscale, que
  já cifra o tráfego; HTTPS no próprio Forgejo fica por decidir (`Q-025`).
- **Atualização (2026-11-13):** a pedido do utilizador, o repositório passou a
  chamar-se «Virtual Macro Text Inputer» (`VirtualMacroTextInputer`);
  o anterior era `Macropad`. O programa continua a chamar-se Macropad.
- **Rever quando:** O servidor ou o endereço mudar, ou for preciso acesso fora
  do Tailscale.

