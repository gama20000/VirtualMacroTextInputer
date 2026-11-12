# Revisão independente — Codex (12-11-2026)

Revisão feita pelo Codex em modo só de leitura, segundo as «Review guidelines»
do `AGENTS.md`, sobre o commit `936fe38`. O Codex não alterou ficheiros nem
correu os testes.

## Relatório (resumo)

| Severidade | Ficheiro:linha | Problema |
|---|---|---|
| P1 | `ui/config_window.py:874` | Reordenar resultados filtrados do Arquivo pode eliminar macros arquivadas ocultas |
| P2 | `core/engine.py:348` | Índice negativo em `Engine.trigger` pode executar a última macro |

### P1 — Reordenar o Arquivo com a pesquisa ativa elimina as macros ocultas

`_on_reordered` passa a `reorder_group` só os índices visíveis na grelha do
Arquivo. Com uma pesquisa ativa, esses índices são apenas os resultados.
`reorder_group` reconstruía então o grupo apenas com esses índices e descartava
as restantes macros arquivadas.

Reprodução indicada: arquivar várias macros, pesquisar de modo a ocultar
algumas, arrastar um resultado para mudar a ordem e deixar gravar. As macros
ocultas desaparecem do conjunto e do ficheiro TOML.

### P2 — `Engine.trigger(-1)` pode executar a última macro

`trigger` só validava o índice dentro do ramo que verifica macros arquivadas ou
vazias. `_start` não rejeitava índices negativos, que o Python interpreta como
posições a contar do fim da lista.

## Confirmação

| Ponto | Classificação | Evidência |
|---|---|---|
| P1 | **Confirmado** | `tests/test_macro_ops.py::test_reordenar_arquivo_filtrado_preserva_macros_ocultas` falhava antes da correção (5 macros passavam a 3) |
| P2 | **Confirmado** | `tests/test_engine.py::test_trigger_com_indice_fora_do_intervalo_nao_executa` falhava antes da correção |

O P2 só se manifesta se alguém chamar `trigger` com um índice inválido. O painel
usa sempre índices reais válidos, por isso o impacto prático era baixo. Foi
corrigido na mesma, porque a correção é trivial e defensiva.

Nenhum ponto foi classificado como falso positivo, e nenhum fica dependente de
verificação no Windows.

## Correções

- **P1** — `core/macro_ops.py::reorder_group`: as macros visíveis trocam de
  posição entre si, ocupando as posições que já tinham. As ocultas ficam onde
  estão e nenhuma macro é descartada. Uma ordem inválida (índices repetidos, fora
  do intervalo ou do outro grupo) não altera nada.
  - Testes: `test_reordenar_arquivo_filtrado_preserva_macros_ocultas`,
    `test_reordenar_grupo_ignora_indices_do_outro_grupo` e, pela interface,
    `tests/test_ui_smoke.py::test_reordenar_arquivo_com_pesquisa_nao_perde_macros`.
- **P2** — `core/engine.py`: `trigger` rejeita logo qualquer índice fora de
  `0 <= index < len(macros)`, e `_start` também rejeita índices negativos.
  - Teste: `test_trigger_com_indice_fora_do_intervalo_nao_executa`.

Validação: `pytest` com 110 testes a passar e 1 ignorado (o teste de tamanhos
Win32, que só corre no Windows).
