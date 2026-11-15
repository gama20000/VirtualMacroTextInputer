# Tarefas

*English version: [TASKS.md](../../TASKS.md) (versão de referência).*

## Fase atual: Fase 4 — Forgejo e publicação (em curso)

- [x] Repositório privado `VirtualMacroTextInputer` no Forgejo do utilizador
  (`Q-012`); histórico enviado pelo utilizador.
  - Validação: envio feito pelo utilizador. O agente não chega ao servidor
    (rede Tailscale), por isso não correu `git ls-remote`.
- [x] Documentação em inglês na raiz e em português em `docs/pt/` (`Q-028`),
  sem dados pessoais (endereço e utilizador do Forgejo, caminhos com o
  utilizador local).
  - Validação: ligações entre documentos verificadas por script; procura dos
    dados privados nos ficheiros.
- [ ] Reescrever o histórico com o email privado do GitHub (`Q-029`).
  - Critérios de aceitação: nenhum commit tem o email pessoal como autor ou
    committer; nenhum ficheiro de nenhum commit contém o endereço do Forgejo
    nem caminhos com o utilizador local; o `user.email` local é o endereço
    privado do GitHub.
  - Validação automática: `git log --format='%ae %ce' | sort -u`; `git grep`
    em todas as revisões.
  - Dependências ou bloqueios: a ligação ao GitHub (`Q-011`), para saber o id
    e o nome da conta.
- [ ] Criar o repositório público `VirtualMacroTextInputer` no GitHub e enviar.
  - Critérios de aceitação: o GitHub mostra o README em inglês; o `origin` tem
    os dois endereços de envio.
  - Validação manual: o utilizador corre `git push --force` para o Forgejo e
    depois um `git push` normal, e os dois remotos mostram o mesmo commit.
  - Dependências ou bloqueios: a tarefa anterior.
- [ ] README: como clonar e enviar.
- [x] Licença: MIT (`Q-030`), `LICENSE` na raiz.

## Em pausa: Fase 3 — Validação manual no Windows e distribuição

Em pausa desde 12-11-2026, a pedido do utilizador; retoma quando o utilizador
autorizar.

- [ ] Percorrer a lista de verificação com o código-fonte
  (`tools\macropad-teste.cmd`).
  - Âmbito: passos 1–89 de `docs/pt/VERIFICACAO-MANUAL.md`, exceto os 👤; o
    resultado de cada passo fica registado nesse documento.
  - Critérios de aceitação: todos os passos não 👤 estão ✅, ou têm uma tarefa
    de correção ou uma limitação aceite em `ANSWERS.md`.
  - Progresso: 16 passos ✅ (1, 4, 5, 7, 11–14, 18–20, 34, 39, 59–61), 3
    parciais (36, 40, 58). Os passos 36 e 58 repetem-se com a barra de título
    própria do painel.
- [ ] Passos que o utilizador tem de fazer (👤): 2, 23, 26, 27, 32, 33, 84, 85,
  89.
- [ ] Repetir a verificação com o executável (`build.ps1` →
  `dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe`): os critérios de
  aceitação de [SPEC.md](SPEC.md#critérios-de-aceitação), e confirmar que os
  ícones e as traduções foram incluídos.

## Concluídas

### Novo nome: Virtual Macro Text Inputer (13-11-2026)

- [x] Nome visível em janelas, ícone, executável, pasta de dados e arranque
  (`Q-026`); cópia da pasta antiga; limpeza da entrada de arranque antiga;
  aviso se a versão antiga estiver a correr. `pytest`: 171 passam, 1 ignorado.
  Risco residual: passos 87–89 no Windows.

### Revisões 2 a 6 do Codex (12-11-2026 a 13-11-2026)

- [x] Todos os achados confirmados e corrigidos, cada um com um teste de
  regressão; detalhe em `docs/pt/revisao-codex.md`. Risco residual: o modo
  «colar» só fica confirmado com o passo manual 86 no Windows.

### Fase 2 — Versão 0.4 (12-11-2026)

- [x] Núcleo, motor, interface, painel, arranque com o Windows de facto,
  traduções, README, lista de verificação (passos 62–85) e versão 0.4.0.
  `pytest`: 136 passam, 1 ignorado; capturas offscreen (Diurno e Noturno)
  revistas. Risco residual: o arrasto real com o rato, o hook com a captura por
  cima do botão e a barra de título sem moldura só se confirmam no Windows
  (Fase 3).

### Fase 1 — Revisão independente e correções (12-11-2026)

- [x] Revisão do Codex corrida pelo utilizador e guardada; P1 e P2 confirmados
  com testes que falhavam e corrigidos (`Q-017`). `pytest`: 110 passam, 1
  ignorado.
