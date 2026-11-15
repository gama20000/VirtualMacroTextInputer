# Revisão independente — Codex (12-11-2026)

*English version: [CODEX-REVIEW.md](../CODEX-REVIEW.md).*

Revisão feita pelo Codex em modo só de leitura, segundo as «Review guidelines»
do `AGENTS.md`, sobre o código da versão 0.3. O Codex não alterou ficheiros nem
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

---

# Segunda revisão do Codex (versão 0.4, 12-11-2026)

O Codex confirmou que os dois achados anteriores (P1 e P2) estão corrigidos e
reportou quatro bugs e uma suspeita. O utilizador acrescentou um problema
encontrado no uso: a tecla de um contador não contava, mas o clique no botão
sim.

| Ponto | Classificação | Evidência | Correção |
|---|---|---|---|
| Migração da tecla de suspensão marcada mesmo quando falha | **Confirmado** | `test_config.py::test_migracao_falhada_nao_fica_marcada` | `store.migrate` só regista a migração quando a gravação tem sucesso; senão mantém `Ctrl+Alt+P`, avisa com o conflito e volta a tentar no arranque seguinte |
| Restaurar em grupo duas arquivadas com a mesma tecla | **Confirmado** | `test_ui_smoke.py::test_restaurar_grupo_com_teclas_iguais` | só a primeira é restaurada; as outras ficam no Arquivo, com mensagem; a alteração é gravada |
| Contadores do painel fora do âmbito | **Confirmado** | `test_engine.py::test_contador_no_painel_respeita_o_ambito`, `test_ui_smoke.py::test_contador_do_painel_fora_do_ambito_desativado` | `Engine.counter_allowed` (suspensão + âmbito) em `counter_press`; os botões de contador do painel ficam desativados fora do âmbito |
| Tecla de contador conta depois de suspender | **Confirmado** | `test_engine.py::test_contador_revalida_ao_largar_a_tecla` | ao largar, revalida suspensão e âmbito; guarda o `id` do contador em vez do índice |
| Falha de `GlobalLock` não tratada (suspeita) | **Confirmado por leitura** (não reproduzível sem provocar a falha no Windows) | `platform/windows/__init__.py::_set_clipboard` | verifica o ponteiro; se for nulo liberta o bloco e dá erro; `GlobalUnlock` num `finally` |
| Tecla do contador não conta (utilizador) | **Confirmado** | `test_ui_smoke.py::test_tecla_do_contador_com_a_configuracao_a_frente` | causa: com uma janela do programa à frente, o hook deixa passar todas as teclas (regra para não escrever nas próprias janelas). Os contadores não escrevem, por isso a janela de configuração conta-os ela própria quando o foco não está num campo de texto nem o rato sobre um botão |

Validação: `pytest` com 142 testes a passar e 1 ignorado (só Windows).

---

# Terceira revisão do Codex (13-11-2026)

Sem P0. O Codex confirmou que os achados das revisões anteriores estão
corrigidos. Todos os pontos novos foram confirmados por leitura do código e têm
agora um teste que reproduz o cenário (as corridas são reproduzidas chamando
diretamente o passo intermédio).

| Ponto | Correção | Teste |
|---|---|---|
| P1 — Mudar o tema apaga edições pendentes | o tema só atualiza o aspeto (`ConfigWindow.set_palette`); `reload_from_store` grava primeiro as edições válidas e mantém as inválidas, exceto se o próprio ficheiro mudou por fora (aí avisa); fechar/recriar a janela (idioma) também grava | `test_mudar_tema_nao_apaga_edicoes_pendentes`, `test_edicao_invalida_sobrevive_a_recarregar_outro_ficheiro`, `test_mudar_idioma_grava_edicoes_pendentes` |
| P1 — Tecla executa macro de outro conjunto | `_start` recebe o retrato do conjunto usado no evento e recusa se o conjunto ativo mudou | `test_tecla_nao_executa_macro_de_outro_conjunto` |
| P2 — Macro começa depois da suspensão | `_start` volta a verificar a suspensão sob o lock | `test_suspensao_entre_verificacao_e_arranque` |
| P2 — Contador do conjunto errado | o keydown guarda o conjunto; se mudou, o keyup não conta; o evento leva `set_id` | `test_contador_premido_ao_mudar_de_conjunto_nao_conta` |
| P2 — Modificadores ainda premidos após 1,5 s | a execução é cancelada (nada é enviado) e aparece um aviso | `test_modificadores_premidos_alem_do_prazo_cancelam` |
| P2 — Falha de escrita deixa preferências em memória | `save_settings` grava antes de atualizar a memória; a interface mostra o erro de escrita | `test_falha_de_escrita_nao_altera_preferencias_em_memoria`, `test_falha_ao_gravar_preferencias_mostra_erro` |
| P2 — Pré-visualização com contadores ativos fora do âmbito | recebe o mesmo estado (suspensão e `counter_allowed`) que o painel real | `test_pre_visualizacao_desativa_contadores_fora_do_ambito` |
| P2 — Alternâncias simultâneas da suspensão | leitura e inversão sob o mesmo lock | `test_alternancias_simultaneas_da_suspensao` |
| P2 — `join()` numa thread por iniciar | `shutdown` só espera se a thread já arrancou | `test_encerrar_com_execucao_ainda_nao_iniciada` |

Validação: `pytest` com 154 testes a passar e 1 ignorado (só Windows).

---

# Quarta revisão do Codex (13-11-2026)

| Ponto | Classificação | Correção | Teste |
|---|---|---|---|
| P1 — Recarregamento externo apagado por uma edição pendente | **Confirmado**: `reload_from_store` gravava a cópia local antes de olhar para os caminhos alterados | os caminhos alterados são vistos primeiro; uma edição pendente cujo ficheiro mudou por fora é descartada sem ser gravada e aparece um aviso | `test_alteracao_externa_nao_e_sobrescrita_por_edicao_pendente` |
| P1 — Modo «colar» falha (`OpenClipboard(NULL)`) | **Confirmado pela documentação da Microsoft** (`EmptyClipboard` com dono NULL faz `SetClipboardData` falhar); ainda por confirmar no Windows real | janela própria «só de mensagens» como dona; dados preparados antes de esvaziar a área; resultados de `EmptyClipboard`/`SetClipboardData` verificados; memória libertada em falha | `test_windows_layer.py::test_area_de_transferencia_*` (API simulada) |
| P2 — Contador no conjunto errado (tecla na janela de configuração) | **Confirmado** | guarda o conjunto ao premir; se mudou ao largar, não conta | `test_tecla_do_contador_na_janela_ao_mudar_de_conjunto` |
| P2 — Hover com índice antigo | **Confirmado** | no momento de atribuir, consulta o item que está sob o cursor; a grelha recalcula o hover ao ser reconstruída | `test_hover_usa_o_item_atual_sob_o_cursor` |
| P2 (suspeita) — Reconstrução com o lock do hook | **Confirmado por leitura** | o retrato do conjunto é construído fora do lock e publicado numa secção curta (`set_config`, `set_active_set`) | `test_reconstrucao_do_conjunto_fora_do_lock` |

Validação: `pytest` com 161 testes a passar e 1 ignorado (só Windows). O modo
«colar» precisa do passo manual 86 no Windows.

---

# Quinta revisão do Codex (13-11-2026)

O Codex confirmou as correções da quarta revisão e reportou três problemas.

| Ponto | Correção | Teste |
|---|---|---|
| P1 — «Colar» noutra janela depois da espera pela área de transferência | `send_text(..., still_ok=...)`: depois de preparar a área de transferência e mesmo antes do Ctrl+V, a janela-alvo é confirmada outra vez; se mudou, não cola e a execução é cancelada | `test_colar_revalida_a_janela_antes_do_ctrl_v` |
| P2 — Corrida no estado do hook | a decisão de suprimir e o arranque da macro são feitos com o mesmo retrato, sob o lock (só consultas rápidas; os planos continuam a ser construídos fora); se o arranque for recusado, a tecla passa para a aplicação; os contadores usam `counter_press_id`, que verifica o conjunto e aplica a operação sob o lock | `test_tecla_nao_se_perde_se_o_retrato_mudar`, `test_decisao_e_arranque_sob_o_mesmo_lock`, `test_contador_por_id_so_no_mesmo_conjunto` |
| P2 — Falhas de escrita não tratadas | migração (o arranque continua com a tecla antiga e avisa), transparência do painel (aviso no ícone), «Não voltar a perguntar» (elimina, avisa e não marca a preferência como gravada) | `test_migracao_com_falha_de_escrita_nao_interrompe`, `test_falhas_ao_gravar_opacidade_e_nao_perguntar` |

Validação: `pytest` com 167 testes a passar e 1 ignorado (só Windows).

---

# Sexta revisão do Codex (13-11-2026)

O Codex confirmou as correções da quinta revisão e reportou um ponto.

| Ponto | Correção | Teste |
|---|---|---|
| P2 — `PlatformAPI` sem o parâmetro `still_ok` | o `Protocol` declara `still_ok: Optional[Callable[[], bool]] = None`, com a descrição do contrato | `test_backends_seguem_o_contrato_da_plataforma` (compara a assinatura do `Protocol` com a de cada backend: simulado, de testes e, no Windows, o real) |

Validação: `pytest` com 168 testes a passar e 1 ignorado (só Windows).
