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
