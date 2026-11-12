# Tarefas

## Fase atual: Fase 2 — Validação manual no Windows e distribuição

Estado: **por iniciar.** Aguarda autorização. As tarefas detalhadas serão
escritas quando a fase começar (ver [ROADMAP.md](ROADMAP.md#fase-2-validação-manual-no-windows-e-distribuição)).

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

Risco residual: as versões 0.1–0.3 continuam sem validação manual no Windows.
É o âmbito da Fase 2.
