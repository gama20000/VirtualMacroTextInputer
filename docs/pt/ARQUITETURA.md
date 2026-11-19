# Arquitetura e referência

*English version: [ARCHITECTURE.md](../../ARCHITECTURE.md). Os comandos e caminhos abaixo são relativos à raiz do repositório.*

O guia completo: como funciona cada parte do programa, as opções avançadas, os ficheiros de configuração, os limites e a organização do código. Para uma visão rápida, veja o [README.md](README.md); para macros prontas a usar, veja [EXEMPLOS.md](EXEMPLOS.md).

- [Guia de utilização](#guia-de-utilização)
- [Regras de disparo](#regras-de-disparo)
- [Comandos no texto](#comandos-no-texto)
- [Ficheiros de configuração (TOML)](#ficheiros-de-configuração-toml)
- [Limitações](#limitações)
- [Estrutura do código](#estrutura-do-código)
- [Compilação, testes e releases](#compilação-testes-e-releases)
- [Migração a partir do Macropad](#migração-a-partir-do-macropad)

**Opções avançadas, num relance**

| Opção | Onde | O que faz |
|---|---|---|
| Modificadores: `exatos` / `ignorar` | Preferências, `modificadores` | se uma tecla sem modificadores também dispara com Ctrl/Alt/Shift/Win premidos ([regras de disparo](#regras-de-disparo)) |
| Modo de texto: *Simular escrita* / *Colar* | Preferências, `modo_texto` | escrita Unicode ou área de transferência + Ctrl+V ([modo de texto](#comandos-no-texto)) |
| Âmbito | separador *Âmbito*, `[ambito]` | o conjunto funciona em todo o lado ou só nos executáveis indicados |
| Repetições e intervalo | editor, `repeticoes`, `intervalo_ms` | executar uma macro várias vezes por pressão |
| Linhas e páginas | separador *Painel*, `linhas` | uma grelha fixa, com páginas ◀ ▶ quando os botões não cabem |
| Contadores | botão **Contador**, `tipo = "contador"` | botões de contagem com reposição por pressão longa e som opcional |
| Comandos multimédia | menu **Multimédia**, `{MediaPlayPause}`… | botões que controlam a música e o volume |
| Teclas de suspensão e do painel | Preferências | atalhos globais, também durante um `{Delay}` |

## Guia de utilização

O programa corre em segundo plano, com um ícone na área de notificação (junto ao relógio) e sem janelas visíveis. Fechar a configuração ou o painel não o termina; para sair, use o menu do ícone ▸ **Sair**. Só pode haver uma instância: abrir o programa outra vez apenas mostra a configuração. Arranca com o Windows por omissão (Preferências) e não cria atalhos no ambiente de trabalho.

**Ícone junto ao relógio.** Clique para abrir a configuração. O botão direito dá acesso a: abrir a configuração, mostrar/ocultar o painel, escolher o conjunto ativo, suspender/reativar macros e sair. O ícone tem contorno ciano quando as macros estão **ativas** e fica cinzento com um ponto vermelho quando estão **suspensas**.

**Suspensão global.** A tecla de suspensão (por omissão `Shift+Escape`; quem tinha `Ctrl+Alt+P`, a predefinição anterior, passa automaticamente para `Shift+Escape` uma única vez, com um aviso) alterna entre ativo e suspenso. Funciona mesmo a meio de uma macro, incluindo durante um `{Delay}`, e cancela logo os passos e as repetições pendentes. Com as macros suspensas, todas as teclas têm o comportamento normal. O estado e o conjunto selecionado são recuperados no arranque seguinte.

**Mostrar/ocultar o painel.** A tecla do painel (por omissão `Shift+F12`) mostra ou oculta o painel em qualquer aplicação, também com as macros suspensas. A tecla aparece na barra de título do painel e no menu do ícone. Pode mudá-la, ou deixá-la sem tecla, em Preferências ▸ «Tecla do painel».

**Ativo / Suspenso.** No topo da configuração há dois botões, **Ativo** (verde quando selecionado) e **Suspenso** (vermelho quando selecionado). Fazem o mesmo que a tecla de suspensão e podem ser usados com o rato ou com o teclado (Tab até ao botão e Espaço). O botão com foco tem um contorno de foco visível.

**Configuração.** Tem quatro separadores, por esta ordem:
- *Macros*: duas áreas, **Ativo** e **Arquivo**, e o editor do botão selecionado. A área **Ativo** está centrada e tem o mesmo aspeto do painel real (tamanho, cores, espaçamento, colunas, posição do título e da tecla); se for grande, a janela desloca-se. As alterações válidas são gravadas automaticamente.
  - **Arrastar**: largue um botão antes ou depois de outro para o pôr nessa posição (uma linha azul mostra onde fica), dentro da mesma área ou entre **Ativo** e **Arquivo**, nos dois sentidos. Largar no **centro** de outro botão troca os dois de lugar (também entre **Ativo** e **Arquivo**; se o que passa a ativo tiver uma tecla já em uso, é pedida confirmação como ao restaurar); um contorno tracejado mostra-o. Largar sobre um espaço vazio também os troca; junto à margem de um botão, insere antes ou depois dele. Com vários botões selecionados, largar insere sempre. Largar no título da área, ou numa zona vazia, põe o botão no fim. Tudo fica gravado logo. A tecla atribuída não muda. ◀ ▶ também mudam a ordem.
  - **Zoom**: −, + e **Ajustar**, junto ao título **Ativo** (ou Ctrl+roda do rato sobre uma grelha), aumentam ou reduzem a pré-visualização de **Ativo** e **Arquivo**, de 30 % a 200 %, sem mudar o painel real; clicar na percentagem volta a 100 %. **Ajustar** encaixa a grelha **Ativo** completa na área visível e continua a ajustá-la quando a janela muda de tamanho. Arraste o divisor por cima do editor para dar mais altura às grelhas.
  - **Tecla**: clique no campo **Tecla** e prima a tecla ou combinação; ou, mais rápido, ponha o rato sobre um botão (a etiqueta da tecla fica amarela, «Tecla…») e prima a tecla. Só é atribuída se não estiver em uso por outra macro ativa nem for a tecla de suspensão ou do painel; caso contrário aparece um aviso, com a opção **Não voltar a mostrar** (reative em Preferências ▸ «Avisar quando a tecla atribuída com o rato já está em uso»). Por cima de um botão, Delete/Backspace, Tab, Ctrl+C, Ctrl+V, Ctrl+Z e Ctrl+Y mantêm as suas funções e Esc cancela. **Sem tecla** deixa a macro disponível só no painel. **Multimédia** tem duas partes: *O botão envia* insere um comando multimédia no texto (a macro pressiona Reproduzir/Pausa, uma faixa ou o volume), e *A tecla do teclado ativa esta macro* atribui Reproduzir/Pausa, Faixa anterior ou Faixa seguinte como tecla da macro sem as premir (premi-las para gravar faria também reagir o leitor de música); aplicam-se as mesmas verificações de conflito. Suspenso ou fora do âmbito, as teclas multimédia funcionam como habitualmente.
  - **Nova macro** acrescenta uma única macro, sem tecla e com o texto vazio, e põe o cursor no campo **Texto**. **Nova macro**, **Contador** e **Espaço vazio** inserem o novo item logo a seguir à macro selecionada em **Ativo** (a seguir à última, se houver várias selecionadas); sem seleção, ou com uma macro arquivada selecionada, no fim de **Ativo**.
  - **Contador** acrescenta um botão que conta: um clique curto no painel (ou a sua tecla) soma o **incremento** (por omissão 1); enquanto o mantém premido, o botão do painel mostra o tempo decorrido numa linha ao longo da borda e, ao atingir a **pressão longa** (por omissão 800 ms), a contagem volta logo ao **valor de reposição** (por omissão 0), com um sinal verde, sem somar e sem esperar que largue (continuar premido não repete). **Som ao repor** toca um som do sistema do Windows na reposição (nenhum por omissão; **Testar** toca-o). O contador só mostra a contagem: não escreve nada. A contagem fica guardada em `estado.toml` e mantém-se entre sessões; **Repor agora** no editor repõe-na.
  - **Espaço vazio** ocupa uma posição da grelha sem botão. Na configuração aparece tracejado e pode ser arrastado; no painel é invisível e não faz nada, mas ocupa o lugar. Os espaços não vão para o Arquivo.
  - **Vermelho** (selo «!») indica um erro, incluindo um *conflito de tecla*, quando duas macros ativas têm a mesma tecla. Os erros não são gravados.
  - **Amarelo** (selo «=») indica *conteúdo duplicado*: macros com a mesma sequência de texto e comandos, mesmo que tenham títulos ou teclas diferentes (`{enter}`, `{Enter}` e uma quebra de linha contam como iguais). Passe o rato por cima do botão, ou veja a linha amarela no editor, para saber com que macros coincide. Os duplicados são apenas um aviso e são gravados.
- *Painel*: estilo, colunas, linhas (com mais botões do que linhas × colunas, o painel mostra páginas, com setas ◀ 1 / 2 ▶; com menos, só ocupa as linhas necessárias), tamanho dos botões, espaçamento, arredondamento, borda, tamanho do texto, cores (botão, texto, borda, fundo), posição do título e posição da tecla (em cima, ao centro, em baixo, independentes e sem se sobreporem), elementos visíveis (tecla, barra de estado, botões Ativo/Suspenso), «sempre por cima» e opacidade. A **pré-visualização**, centrada, usa o mesmo desenho do painel real (incluindo os botões Ativo/Suspenso) e atualiza-se a cada alteração, sem abrir o painel. Há estilos predefinidos (Predefinido, Compacto, Grande, Claro, Néon, Redondo, Minimalista, Título em cima). **Repor predefinição** volta ao aspeto original sem mexer nas colunas, na opacidade nem em «sempre por cima».
- *Âmbito*: o conjunto funciona em todas as aplicações ou só nas aplicações indicadas, identificadas pelo executável, por exemplo `notepad.exe`. Fora delas, as teclas funcionam normalmente e o painel não envia texto.
- *Preferências*: tema, idioma, arranque com o Windows, «Não pedir confirmação antes de eliminar macros», aviso de tecla em uso, tecla de suspensão, tecla do painel, modificadores e modo de texto. Cada alteração aplica-se logo. O arranque com o Windows é confirmado depois de aplicado (incluindo a aprovação em Gestor de Tarefas ▸ Aplicações de arranque); se não for possível, aparece um erro por baixo da opção.
- Menu **⋯**: novo, duplicar, mudar o nome, eliminar, importar e exportar conjuntos, e abrir a pasta de configuração.

**Seleção de várias macros.** Ctrl+clique acrescenta ou retira macros da seleção, e Shift+clique seleciona um intervalo. Com várias selecionadas, os botões **Arquivar (n)**/**Restaurar (n)** e 🗑 atuam em todas. Antes de eliminar várias, o programa pede sempre confirmação e indica a quantidade.

**Atalhos na grelha.** Com uma ou mais macros selecionadas e o foco fora de um campo de edição:

| Tecla | Ação |
|---|---|
| Delete ou Backspace | elimina a(s) macro(s) (pede confirmação) |
| Ctrl+C | copia a(s) macro(s) |
| Ctrl+V | cola cópias a seguir à seleção, na mesma área: a cópia de uma macro arquivada fica no Arquivo, logo a seguir à original. Se a tecla já estiver em uso, uma cópia ativa fica sem tecla |
| Ctrl+Z | anula a última eliminação: as macros voltam à mesma área e posição, com as mesmas definições e tecla (se a tecla entretanto foi atribuída a outra macro, a reposta fica sem tecla, com mensagem). Guardado por conjunto enquanto a janela estiver aberta |
| Ctrl+Y ou Ctrl+Shift+Z | volta a eliminá-las |

Com o foco num campo de texto, estes atalhos copiam, colam, apagam e desfazem texto como habitualmente. A caixa de confirmação de eliminação tem a opção **Não voltar a perguntar**. Para voltar a ativar as confirmações, desmarque Preferências ▸ «Não pedir confirmação antes de eliminar macros».

**Arquivo.** Por baixo das macros ativas, a divisória **Arquivo** mostra as macros arquivadas, com uma caixa de pesquisa por título, texto ou tecla.
- **Arquivar** retira a macro das teclas e do painel sem a apagar. Fica no ficheiro do conjunto com `arquivada = true`. Também pode arrastar uma macro ativa, ou a seleção inteira, para a área **Arquivo**: fica arquivada imediatamente, na posição largada.
- **Restaurar** (ou arrastá-la para **Ativo**) volta a ativá-la. Se a tecla dela já estiver atribuída a uma macro ativa, o programa pede confirmação. Ao confirmar, a macro restaurada fica no lugar da ativa e essa passa para o arquivo. Ao cancelar, nada muda. Se várias macros arquivadas com a mesma tecla forem restauradas juntas, só a primeira é restaurada e as outras ficam no Arquivo.
- Arquivar e restaurar não alteram ficheiros exportados anteriormente.

**Painel.** O painel mostra as macros ativas em grelha, com título e tecla, e um indicador de estado (ativo / suspenso / fora do âmbito / a executar). Tem uma barra de título própria, com as cores do tema, o nome do conjunto, a tecla do painel e ✕ para o ocultar; arraste-a para mover o painel (a posição fica gravada). Clicar num botão não tira o foco à aplicação onde está a escrever, e o texto vai para lá. Fica sempre por cima por omissão. A aparência configura-se no separador *Painel*.
- Os botões **Ativo**/**Suspenso** do painel têm o mesmo estado e efeito dos da configuração e não tiram o foco à aplicação de destino.
- Com o ponteiro sobre o painel, a **roda do rato** ajusta a transparência em passos de 5 % (para cima fica mais opaco, para baixo mais transparente, entre 20 % e 100 %). O nível aparece brevemente no centro do painel e fica gravado. Só o painel é afetado.
- Se a roda não reagir enquanto o painel não está em foco, ative a definição do Windows «Deslocar janelas inativas ao pairar sobre elas».

**Tema.** Há três opções:
- **Diurno**: interface clara com a barra de título preta.
- **Noturno**: interface e barra de título escuras.
- **Automático** (por omissão): acompanha a definição do Windows (Definições ▸ Personalização ▸ Cores ▸ modo das aplicações).

A escolha aplica-se a todas as janelas, incluindo o painel e as caixas de diálogo. A cor da barra de título só pode ser definida no Windows 11. No Windows 10, a barra fica preta ou escura com o modo escuro do sistema.

**Idioma.** Português ou English (Preferências ▸ Idioma). A escolha aplica-se a toda a interface, mensagens, menus e caixas de confirmação. Os títulos e conteúdos das macros, os nomes dos conjuntos e os nomes dos campos nos ficheiros TOML não são traduzidos.

Para acrescentar um idioma, copie `src/macropad/locales/pt.toml` para `<código>.toml` (por exemplo `es.toml`), mude `nome` e traduza os valores. O novo idioma aparece logo na lista, e as chaves em falta usam o português. Os nomes entre chavetas (`{title}`) são preenchidos pelo programa. As chavetas literais escrevem-se `{{` e `}}`.

## Regras de disparo

- Por omissão (`modificadores = "exatos"`), só a tecla isolada dispara. `Ctrl+1`, `Alt+1` e `Shift+1` mantêm o comportamento normal. Também pode associar uma combinação a uma macro, por exemplo `Ctrl+F1`, que só dispara exatamente com essa combinação. Com `"ignorar"`, as teclas sem modificadores disparam também com Ctrl/Alt/Shift/Win premidos.
- As teclas 1 a 4 da fila superior são diferentes de `Numpad1` a `Numpad4`.
- Manter a tecla premida não volta a disparar a macro. É preciso largar e premir outra vez.
- Enquanto uma macro está a ser executada, novos disparos são ignorados (a tecla continua a ser suprimida).
- Antes de enviar alguma coisa (no início e antes de cada bloco de texto ou tecla, por exemplo depois de um `{Delay}`), a execução espera que Ctrl, Alt, Shift e Win sejam largadas (até 1,5 s). Se continuarem premidas, a macro para aí e aparece um aviso. Assim, um `{Enter}` nunca é enviado como `Ctrl+Enter`, mesmo que prima Ctrl a meio de uma macro.
- Se mudar de janela durante a execução, os passos pendentes são cancelados. No modo *Colar*, a janela de destino é confirmada outra vez mesmo antes do Ctrl+V.
- O texto que o programa envia nunca dispara macros. As teclas premidas nas janelas do próprio programa também não (exceto as teclas dos contadores, que só contam).

## Comandos no texto

| Comando | Efeito |
|---|---|
| `{Enter}` | pressiona Enter |
| `{Tab}` | pressiona Tab |
| `{Delay:500}` | espera 500 ms (0 a 600000) |
| `{MediaPlayPause}`, `{MediaPrev}`, `{MediaNext}`, `{MediaStop}` | pressiona a tecla multimédia (Reproduzir/Pausa, faixa anterior, faixa seguinte, parar) |
| `{VolumeUp}`, `{VolumeDown}`, `{VolumeMute}` | pressiona a tecla de volume |

Uma macro cujo texto é só `{MediaPlayPause}` transforma o botão do painel num botão Reproduzir/Pausa, com um símbolo simples de Play/Pausa ao centro (cada comando multimédia tem o seu símbolo). Ao escolher uma ação multimédia numa macro que ainda tem o título predefinido («Nova macro»), o título passa a ser o nome curto da ação, no idioma atual (por exemplo «Play/Pausa» ou «Volume +»); um título escrito por si fica como está. **Multimédia ▸ O botão envia**, no editor, insere estes comandos na posição do cursor.

Os comandos são executados pela ordem e na posição em que aparecem. Por exemplo, `ABC{Tab}DEF{Delay:500}{Enter}` escreve ABC, prime Tab, escreve DEF, espera 500 ms e prime Enter.

- Os nomes não distinguem maiúsculas de minúsculas (`{enter}` é igual a `{Enter}`). `{Enter}`, `{Tab}` e as teclas multimédia são sempre comandos.
- Uma quebra de linha no texto equivale a `{Enter}` e uma tabulação equivale a `{Tab}`.
- Comandos mal formados (`{Entr}`, `{Delay:abc}`, `{Enter` sem fecho) são erros, com a indicação da posição. Outras chavetas que não formam um comando, como `{}` ou `{1}`, são texto literal.
- O texto pode ter qualquer carácter Unicode (acentos, €, emojis).

**Modo de texto** (Preferências):
- *Simular escrita* (por omissão) envia os caracteres como Unicode e não depende do layout do teclado.
- *Colar* copia o texto para a área de transferência e envia Ctrl+V. É útil em aplicações que não aceitam escrita simulada. O conteúdo anterior da área de transferência não é preservado.

## Ficheiros de configuração (TOML)

Ficam em `%APPDATA%\VirtualMacroTextInputer\`:

| Ficheiro | Conteúdo |
|---|---|
| `config.toml` | preferências gerais e do painel |
| `conjuntos\<id>.toml` | um ficheiro por conjunto. O nome do ficheiro é o identificador do conjunto |
| `estado.toml` | estado da sessão (ativo/suspenso, conjunto, painel visível e posição, contagens dos contadores, migrações feitas). Gerido pelo programa e não é observado |
| `macropad.log` | registo de erros |

O exemplo comentado está em [examples/conjunto-exemplo.toml](../../examples/conjunto-exemplo.toml) e inclui a macro 1 → `3E03305`. Todos os ficheiros têm `versao_esquema = 1`. Os campos novos desta versão são opcionais, por isso os ficheiros antigos continuam válidos e mantêm o aspeto original.

`config.toml` (excerto):

```toml
[geral]
tema = "automatico"          # "automatico" (por omissão) | "diurno" | "noturno"
idioma = "pt"                # "pt" | "en" | outro ficheiro em locales/
confirmar_eliminacao = true
tecla_suspensao = "Shift+Escape"
tecla_painel = "Shift+F12"   # "" = sem tecla
avisar_conflito_tecla = true

[painel]
colunas = 4
linhas = 0                   # 0 = todas; senão, páginas com setas ◀ ▶
tamanho_botao = 78           # 40–160 px
espacamento = 6              # 0–30 px
arredondamento = 17          # 0 (quadrado) – 50 (redondo), % do lado
borda = 2                    # 0–8 px
escala_texto = 100           # 60–180 %
cor_fundo = ""               # "" segue o tema; ou "#RRGGBB"
cor_botao = "#000000"
cor_texto = "#ffffff"
cor_borda = "#5a5a5a"
posicao_titulo = "centro"    # "cima" | "centro" | "baixo"
posicao_tecla = "baixo"
mostrar_tecla = true
mostrar_estado = true
mostrar_controlos = true     # botões Ativo/Suspenso no painel
```

```toml
versao_esquema = 1
nome = "Codificação"

[ambito]
modo = "global"            # ou "aplicacoes"
aplicacoes = ["notepad.exe"]

[[macros]]
titulo = "3E03305"
tecla = "1"
texto = "3E03305"
repeticoes = 1
intervalo_ms = 0

[[macros]]
tipo = "espaco"            # espaço vazio (sem outros campos)

[[macros]]
tipo = "contador"
id = "pecas"               # identifica a contagem em estado.toml
titulo = "Peças"
tecla = "F9"
incremento = 1
reposicao = 0
pressao_longa_ms = 800
som_reposicao = "aviso"    # opcional: "padrao", "aviso", "erro", "pergunta"
```

O campo `mostrar_icone` das versões anteriores é aceite e ignorado.

**Recarregamento automático.** Ao guardar um destes ficheiros num editor, o programa deteta a alteração, espera que o ficheiro fique estável (o que agrupa gravações seguidas e evita ler ficheiros a meio da escrita), valida-o e aplica-o. Funciona também com editores que gravam substituindo o ficheiro.
- Se o ficheiro for **inválido**, mantém-se a última configuração válida e aparece um aviso com o ficheiro, a linha e a coluna, por exemplo `conjuntos/predefinido.toml, linha 12, coluna 9: macro 2: comando desconhecido {Entr}`.
- Se o ficheiro que estava a editar na configuração for alterado por fora antes de a sua edição ser gravada, vale a versão do ficheiro e aparece um aviso.
- As alterações aplicam-se às execuções seguintes. Uma execução em curso termina com a configuração com que começou, a menos que seja suspensa ou que a janela mude.
- Um recarregamento nunca reativa macros suspensas.
- As gravações da interface são atómicas (ficheiro temporário + substituição) e não provocam recarregamentos em ciclo.
- Ao gravar a partir da interface, o ficheiro é reescrito no formato padrão, com os comentários de ajuda. Os comentários escritos à mão perdem-se.
- Campos desconhecidos são erros, para que um erro de escrita como `repeticao` não seja ignorado sem aviso.

**Importar/exportar.** Use o menu ⋯ da configuração. Exportar grava o conjunto num `.toml` à sua escolha; o nome sugerido para o ficheiro e o nome dentro do ficheiro são o nome atual do conjunto (depois de qualquer mudança de nome), e um ficheiro existente só é substituído depois de confirmar. Importar valida o ficheiro antes de o copiar para `conjuntos\` e cria nomes únicos se houver colisões. Também pode copiar ficheiros diretamente para a pasta `conjuntos\`, que são detetados automaticamente.

**Nomes de teclas.** `0`–`9`, `A`–`Z`, `F1`–`F24`, `Numpad0`–`Numpad9`, `NumpadAdd`, `NumpadSubtract`, `NumpadMultiply`, `NumpadDivide`, `NumpadDecimal`, `Space`, `Tab`, `Enter`, `Backspace`, `Escape`, `Insert`, `Delete`, `Home`, `End`, `PageUp`, `PageDown`, `Up`, `Down`, `Left`, `Right`, `Pause`, `ScrollLock`, `CapsLock`, `NumLock`, `PrintScreen`, `Apps`, as teclas de pontuação `OEM1`…`OEM8`, `OEM102`, `OEMPlus`, `OEMComma`, `OEMMinus`, `OEMPeriod` (o carácter depende do layout; é mais fácil gravá-las no campo **Tecla**) e as teclas multimédia. Os modificadores são `Ctrl`, `Alt`, `Shift` e `Win`, por exemplo `Ctrl+Alt+F1`.

## Limitações

- **Aplicações executadas como administrador.** O Windows (UIPI) impede que um processo sem privilégios intercete teclas ou envie texto para janelas elevadas. Com uma dessas janelas em primeiro plano, as teclas funcionam normalmente e o painel não consegue escrever. Para usar macros nelas, execute o programa como administrador. Nesse caso, o arranque automático pelo registo `Run` não eleva o programa e terá de usar o Agendador de Tarefas com "Executar com privilégios mais elevados".
- O ecrã de UAC, o ecrã de bloqueio, o Ctrl+Alt+Del e alguns jogos com anti-cheat ou entrada "raw" não recebem nem deixam intercetar estes eventos.
- O Windows remove hooks de teclado que respondem devagar (LowLevelHooksTimeout). O callback do programa só consulta dados em memória, mas uma máquina muito sobrecarregada pode fazê-lo perder o hook. Nesse caso, reinicie o programa.
- No modo *Colar*, aplicações que leiam a área de transferência de forma muito lenta podem colar o texto anterior. O programa espera 80 ms depois de cada Ctrl+V.
- `AltGr` é tratado pelo Windows como `Ctrl+Alt`.
- As teclas de suspensão e do painel são globais e intercetadas mesmo nas janelas do programa, exceto enquanto um campo **Tecla** está a gravar ou o rato está sobre um botão da configuração (com a janela ativa).
- O contador repõe quando o tempo da pressão longa é atingido, com a tecla ainda premida; um toque soma quando a tecla é largada. O Windows repete a tecla enquanto está premida; essas repetições são ignoradas.
- As teclas multimédia são vistas quando o teclado as envia como teclas (códigos virtuais). Os teclados cujas teclas multimédia só chegam às aplicações como «comandos de aplicação» (alguns utilitários de fabricante fazem isto) não as permitem atribuir.

## Estrutura do código

```
src/macropad/
  branding.py           # nome visível do programa (e o anterior, para a migração)
  core/                 # Python puro, sem Qt nem Win32 (testável em qualquer SO)
    commands.py         #   interpretação de {Enter} {Tab} {Delay:ms} e dos comandos multimédia
    keys.py             #   nomes de teclas e associações (Ctrl+Alt+P)
    model.py            #   modelo de dados, âmbito por executável
    configio.py         #   leitura/validação/escrita TOML com linha e coluna dos erros
    store.py            #   ficheiros, última versão válida, gravação atómica, hashes anti-ciclo
    watcher.py          #   observador por polling com agrupamento de eventos
    engine.py           #   decisão de supressão, execução numa thread, cancelamento
    macro_ops.py        #   arquivo/restauro, duplicados, copiar/colar, reordenação
  i18n.py, locales/     # traduções (pt, en) — também usadas pelas mensagens do núcleo
  platform/
    windows/            # hook WH_KEYBOARD_LL, SendInput Unicode, área de transferência,
                        # WS_EX_NOACTIVATE, cores da barra de título (DWM), tema do
                        # Windows, registo Run, mutex de instância única
    dummy.py            # plataforma simulada (desenvolvimento noutros SO)
  ui/                   # PySide6: ícone, configuração, painel, temas (assets/ = ícones)
```

Para uma versão Linux, basta criar `platform/linux` com a mesma interface (por exemplo evdev/uinput para intercetar e injetar, `_NET_ACTIVE_WINDOW` ou o compositor para a janela ativa) e escolhê-la em `platform/__init__.py`. O núcleo e a interface Qt não mudam.

## Compilação, testes e releases

Requisitos: Windows 10/11 e Python 3.11 ou superior. O Python é necessário apenas para executar a partir do código ou para gerar a distribuição.

```powershell
# a partir do código (com consola, útil para ver erros)
.\run-dev.ps1

# ou manualmente
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\pythonw -m macropad          # sem consola
```

### Gerar a distribuição Windows

```powershell
.\build.ps1        # cria .venv, corre os testes e gera dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe
```

Ou, num só ficheiro: `.\build.ps1 -OneFile` gera `dist\VirtualMacroTextInputer.exe` e o respetivo SHA-256.

Copie a pasta `dist\VirtualMacroTextInputer` para onde quiser (por exemplo `%LOCALAPPDATA%\Programs\VirtualMacroTextInputer`) e execute `VirtualMacroTextInputer.exe`. O registo de arranque automático (`HKCU\...\Run`) aponta para o executável que estiver a correr. Se mudar a pasta de sítio, abra o programa uma vez a partir da nova localização e volte a ativar "Arrancar com o Windows".

### Testes

```powershell
.\.venv\Scripts\python -m pytest -q
```

Os testes cobrem a interpretação de comandos, as teclas e os modificadores, as repetições, o cancelamento (suspensão durante `{Delay}` e mudança de janela), o âmbito por aplicação, a validação e o recarregamento dos TOML (incluindo ficheiros inválidos, substituição atómica, agrupamento de eventos e ausência de ciclos), a camada Win32 simulada e um teste de fumo da interface. A supressão real de teclas e o foco do painel têm de ser verificados à mão: veja [VERIFICACAO-MANUAL.md](VERIFICACAO-MANUAL.md).

### Releases e integração contínua

Cada pull request (incluindo os do Dependabot) e cada envio para `main` correm os testes no Windows (`.github/workflows/tests.yml`). As releases são geradas pelo GitHub Actions numa máquina Windows limpa (`.github/workflows/release.yml`): enviar uma etiqueta `vX.Y.Z` igual à versão do `pyproject.toml` corre os testes, gera o executável e publica a release.

O executável de ficheiro único descompacta-se para uma pasta temporária a cada arranque (1–3 s mais lento do que a versão em pasta) e não tem assinatura digital, por isso o SmartScreen avisa na primeira execução (**Mais informações ▸ Executar mesmo assim**). O ficheiro `.sha256` ao lado permite confirmar que a transferência está intacta (`Get-FileHash VirtualMacroTextInputer.exe`). Alguns antivírus desconfiam de programas que leem o teclado e escrevem texto; se o seu o bloquear, gere-o a partir do código.

### Obter o código

```powershell
git clone https://github.com/gama20000/VirtualMacroTextInputer.git
```

A cópia de trabalho do autor tem um único remoto `origin` com dois endereços de envio (um Forgejo privado e o GitHub), por isso um só `git push` atualiza os dois.

## Migração a partir do Macropad

Até à versão 0.4 o programa chamava-se **Macropad**. O pacote Python continua a chamar-se `macropad`, por isso os comandos `python -m macropad` mantêm-se.

**Mudança de nome.** No primeiro arranque com o nome novo, as macros e preferências de `%APPDATA%\Macropad` são copiadas para `%APPDATA%\VirtualMacroTextInputer` (a pasta antiga fica intacta, como cópia de segurança). A entrada antiga de arranque com o Windows («Macropad») é substituída pela nova. Se a versão antiga ainda estiver a correr, o programa pede para a fechar, para as macros não serem escritas duas vezes.
