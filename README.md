# Macropad

Macro pad para Windows. Usa teclas normais do teclado (por omissão, 1, 2, 3 e 4 da fila superior) e um painel flutuante opcional para escrever texto pré-definido na aplicação que está em primeiro plano. Quando uma macro dispara, a tecla original é suprimida. Premir **1** escreve `3E03305` e o 1 não aparece.

- Corre em segundo plano, com um ícone na área de notificação (junto ao relógio) e sem janelas visíveis.
- Fechar a configuração ou o painel não termina a aplicação. Para sair, use o menu do ícone ▸ **Sair**.
- Arranca com o Windows por omissão (pode desativar nas Preferências). Não cria atalhos no ambiente de trabalho.
- Só pode haver uma instância. Abrir o programa outra vez apenas mostra a configuração.

## Executar

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
.\build.ps1        # cria .venv, corre os testes e gera dist\Macropad\Macropad.exe
```

Copie a pasta `dist\Macropad` para onde quiser (por exemplo `%LOCALAPPDATA%\Programs\Macropad`) e execute `Macropad.exe`. O registo de arranque automático (`HKCU\...\Run`) aponta para o executável que estiver a correr. Se mudar a pasta de sítio, abra o programa uma vez a partir da nova localização e volte a ativar "Arrancar com o Windows".

### Testes

```powershell
.\.venv\Scripts\python -m pytest -q
```

Os testes cobrem a interpretação de comandos, as teclas e os modificadores, as repetições, o cancelamento (suspensão durante `{Delay}` e mudança de janela), o âmbito por aplicação, a validação e o recarregamento dos TOML (incluindo ficheiros inválidos, substituição atómica, agrupamento de eventos e ausência de ciclos), a camada Win32 simulada e um teste de fumo da interface. A supressão real de teclas e o foco do painel têm de ser verificados à mão: veja [docs/VERIFICACAO-MANUAL.md](docs/VERIFICACAO-MANUAL.md).

## Utilização

**Ícone junto ao relógio.** Clique para abrir a configuração. O botão direito dá acesso a: abrir a configuração, mostrar/ocultar o painel, escolher o conjunto ativo, suspender/reativar macros e sair. O ícone tem contorno ciano quando as macros estão **ativas** e fica cinzento com um ponto vermelho quando estão **suspensas**.

**Suspensão global.** A tecla de suspensão (por omissão `Ctrl+Alt+P`) alterna entre ativo e suspenso. Funciona mesmo a meio de uma macro, incluindo durante um `{Delay}`, e cancela logo os passos e as repetições pendentes. Com as macros suspensas, todas as teclas têm o comportamento normal. O estado e o conjunto selecionado são recuperados no arranque seguinte.

**Ativo / Suspenso.** No topo da configuração há dois botões, **Ativo** (verde quando selecionado) e **Suspenso** (vermelho quando selecionado). Fazem o mesmo que a tecla de suspensão e podem ser usados com o rato ou com o teclado (Tab até ao botão e Espaço). O botão com foco tem um contorno de foco visível.

**Configuração.** Tem quatro separadores, por esta ordem:
- *Macros*: grelha de botões das macros ativas e editor com título, tecla, texto, repetições e intervalo. Arraste os botões (ou use ◀ ▶) para mudar a ordem. A tecla atribuída não muda. Para mudar a tecla, clique no campo **Tecla** e prima a tecla ou a combinação pretendida. **Sem tecla** deixa a macro disponível só no painel. As alterações válidas são gravadas automaticamente.
  - **Nova macro** acrescenta uma única macro, sem tecla e com o texto vazio, e põe o cursor no campo **Texto**.
  - **Vermelho** (selo «!») indica um erro, incluindo um *conflito de tecla*, quando duas macros ativas têm a mesma tecla. Os erros não são gravados.
  - **Amarelo** (selo «=») indica *conteúdo duplicado*: macros com a mesma sequência de texto e comandos, mesmo que tenham títulos ou teclas diferentes (`{enter}`, `{Enter}` e uma quebra de linha contam como iguais). Passe o rato por cima do botão, ou veja a linha amarela no editor, para saber com que macros coincide. Os duplicados são apenas um aviso e são gravados.
- *Painel*: estilo, colunas, tamanho dos botões, espaçamento, arredondamento, borda, tamanho do texto, cores (botão, texto, borda, fundo), elementos visíveis (ícone, tecla, barra de estado, botões Ativo/Suspenso), «sempre por cima» e opacidade. A **pré-visualização**, centrada, usa o mesmo desenho do painel real (incluindo os botões Ativo/Suspenso) e atualiza-se a cada alteração, sem abrir o painel. Há estilos predefinidos (Predefinido, Compacto, Grande, Claro, Néon, Redondo, Minimalista). **Repor predefinição** volta ao aspeto original sem mexer nas colunas, na opacidade nem em «sempre por cima».
- *Âmbito*: o conjunto funciona em todas as aplicações ou só nas aplicações indicadas, identificadas pelo executável, por exemplo `notepad.exe`. Fora delas, as teclas funcionam normalmente e o painel não envia texto.
- *Preferências*: tema, idioma, arranque com o Windows, confirmação antes de eliminar, tecla de suspensão, modificadores e modo de texto.
- Menu **⋯**: novo, duplicar, mudar o nome, eliminar, importar e exportar conjuntos, e abrir a pasta de configuração.

**Seleção de várias macros.** Ctrl+clique acrescenta ou retira macros da seleção, e Shift+clique seleciona um intervalo. Com várias selecionadas, os botões **Arquivar (n)**/**Restaurar (n)** e 🗑 atuam em todas. Antes de eliminar várias, o programa pede sempre confirmação e indica a quantidade.

**Atalhos na grelha.** Com uma ou mais macros selecionadas e o foco fora de um campo de edição:

| Tecla | Ação |
|---|---|
| Delete ou Backspace | elimina a(s) macro(s) (pede confirmação) |
| Ctrl+C | copia a(s) macro(s) |
| Ctrl+V | cola cópias a seguir à seleção. Se a tecla já estiver em uso, a cópia fica sem tecla |

Com o foco num campo de texto, estes atalhos copiam, colam e apagam texto como habitualmente. A caixa de confirmação de eliminação tem a opção **Não voltar a perguntar**. Para voltar a ativar as confirmações, use Preferências ▸ «Pedir confirmação antes de eliminar macros».

**Arquivo.** Por baixo das macros ativas, a divisória **Arquivo** mostra as macros arquivadas, com uma caixa de pesquisa por título, texto ou tecla.
- **Arquivar** retira a macro das teclas e do painel sem a apagar. Fica no ficheiro do conjunto com `arquivada = true`. Também pode arrastar uma macro ativa, ou a seleção inteira, para a área abaixo da linha **Arquivo**: ao largar, fica arquivada imediatamente. Arrastar dentro da grelha só reordena e não altera as teclas.
- **Restaurar** volta a ativá-la. Se a tecla dela já estiver atribuída a uma macro ativa, o programa pede confirmação. Ao confirmar, a macro restaurada fica no lugar da ativa e essa passa para o arquivo. Ao cancelar, nada muda.
- Arquivar e restaurar não alteram ficheiros exportados anteriormente.

**Painel.** O painel mostra as macros ativas em grelha, com título e tecla, e um indicador de estado (ativo / suspenso / fora do âmbito / a executar). Clicar num botão não tira o foco à aplicação onde está a escrever, e o texto vai para lá. Fica sempre por cima por omissão. A aparência configura-se no separador *Painel*.
- Os botões **Ativo**/**Suspenso** do painel têm o mesmo estado e efeito dos da configuração e não tiram o foco à aplicação de destino.
- Com o ponteiro sobre o painel, a **roda do rato** ajusta a transparência em passos de 5 % (para cima fica mais opaco, para baixo mais transparente, entre 20 % e 100 %). O nível aparece brevemente no centro do painel e fica gravado. Só o painel é afetado.
- Se a roda não reagir enquanto o painel não está em foco, ative a definição do Windows «Deslocar janelas inativas ao pairar sobre elas».

**Tema.** Há três opções:
- **Diurno** (por omissão): interface clara com a barra de título preta.
- **Noturno**: interface e barra de título escuras.
- **Automático**: acompanha a definição do Windows (Definições ▸ Personalização ▸ Cores ▸ modo das aplicações).

A escolha aplica-se a todas as janelas, incluindo o painel e as caixas de diálogo. A cor da barra de título só pode ser definida no Windows 11. No Windows 10, a barra fica preta ou escura com o modo escuro do sistema.

**Idioma.** Português ou English (Preferências ▸ Idioma). A escolha aplica-se a toda a interface, mensagens, menus e caixas de confirmação. Os títulos e conteúdos das macros, os nomes dos conjuntos e os nomes dos campos nos ficheiros TOML não são traduzidos.

Para acrescentar um idioma, copie `src/macropad/locales/pt.toml` para `<código>.toml` (por exemplo `es.toml`), mude `nome` e traduza os valores. O novo idioma aparece logo na lista, e as chaves em falta usam o português. Os nomes entre chavetas (`{title}`) são preenchidos pelo programa. As chavetas literais escrevem-se `{{` e `}}`.

### Regras de disparo

- Por omissão (`modificadores = "exatos"`), só a tecla isolada dispara. `Ctrl+1`, `Alt+1` e `Shift+1` mantêm o comportamento normal. Também pode associar uma combinação a uma macro, por exemplo `Ctrl+F1`, que só dispara exatamente com essa combinação. Com `"ignorar"`, as teclas sem modificadores disparam também com Ctrl/Alt/Shift/Win premidos.
- As teclas 1 a 4 da fila superior são diferentes de `Numpad1` a `Numpad4`.
- Manter a tecla premida não volta a disparar a macro. É preciso largar e premir outra vez.
- Enquanto uma macro está a ser executada, novos disparos são ignorados (a tecla continua a ser suprimida).
- Se a macro tiver sido disparada com modificadores premidos, a execução espera que sejam largados (até 1,5 s). Assim, um `{Enter}` não é enviado como `Ctrl+Enter`.
- Se mudar de janela durante a execução, os passos pendentes são cancelados.
- O texto que o Macropad envia nunca dispara macros. As teclas premidas nas janelas do próprio Macropad também não.

## Comandos no texto

| Comando | Efeito |
|---|---|
| `{Enter}` | pressiona Enter |
| `{Tab}` | pressiona Tab |
| `{Delay:500}` | espera 500 ms (0 a 600000) |

Os comandos são executados pela ordem e na posição em que aparecem. Por exemplo, `ABC{Tab}DEF{Delay:500}{Enter}` escreve ABC, prime Tab, escreve DEF, espera 500 ms e prime Enter.

- Os nomes não distinguem maiúsculas de minúsculas (`{enter}` é igual a `{Enter}`). `{Enter}` e `{Tab}` são sempre comandos.
- Uma quebra de linha no texto equivale a `{Enter}` e uma tabulação equivale a `{Tab}`.
- Comandos mal formados (`{Entr}`, `{Delay:abc}`, `{Enter` sem fecho) são erros, com a indicação da posição. Outras chavetas que não formam um comando, como `{}` ou `{1}`, são texto literal.
- O texto pode ter qualquer carácter Unicode (acentos, €, emojis).

**Modo de texto** (Preferências):
- *Simular escrita* (por omissão) envia os caracteres como Unicode e não depende do layout do teclado.
- *Colar* copia o texto para a área de transferência e envia Ctrl+V. É útil em aplicações que não aceitam escrita simulada. O conteúdo anterior da área de transferência não é preservado.

## Ficheiros de configuração (TOML)

Ficam em `%APPDATA%\Macropad\`:

| Ficheiro | Conteúdo |
|---|---|
| `config.toml` | preferências gerais e do painel |
| `conjuntos\<id>.toml` | um ficheiro por conjunto. O nome do ficheiro é o identificador do conjunto |
| `estado.toml` | estado da sessão (ativo/suspenso, conjunto, painel visível). Gerido pelo programa e não é observado |
| `macropad.log` | registo de erros |

O exemplo comentado está em [examples/conjunto-exemplo.toml](examples/conjunto-exemplo.toml) e inclui a macro 1 → `3E03305`. Todos os ficheiros têm `versao_esquema = 1`. Os campos novos desta versão são opcionais, por isso os ficheiros antigos continuam válidos e mantêm o aspeto original.

`config.toml` (excerto):

```toml
[geral]
tema = "diurno"              # "diurno" | "noturno" | "automatico"
idioma = "pt"                # "pt" | "en" | outro ficheiro em locales/
confirmar_eliminacao = true

[painel]
colunas = 4
tamanho_botao = 78           # 40–160 px
espacamento = 6              # 0–30 px
arredondamento = 17          # 0 (quadrado) – 50 (redondo), % do lado
borda = 2                    # 0–8 px
escala_texto = 100           # 60–180 %
cor_fundo = ""               # "" segue o tema; ou "#RRGGBB"
cor_botao = "#000000"
cor_texto = "#ffffff"
cor_borda = "#5a5a5a"
mostrar_icone = true
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
```

**Recarregamento automático.** Ao guardar um destes ficheiros num editor, o Macropad deteta a alteração, espera que o ficheiro fique estável (o que agrupa gravações seguidas e evita ler ficheiros a meio da escrita), valida-o e aplica-o. Funciona também com editores que gravam substituindo o ficheiro.
- Se o ficheiro for **inválido**, mantém-se a última configuração válida e aparece um aviso com o ficheiro, a linha e a coluna, por exemplo `conjuntos/predefinido.toml, linha 12, coluna 9: macro 2: comando desconhecido {Entr}`.
- As alterações aplicam-se às execuções seguintes. Uma execução em curso termina com a configuração com que começou, a menos que seja suspensa ou que a janela mude.
- Um recarregamento nunca reativa macros suspensas.
- As gravações da interface são atómicas (ficheiro temporário + substituição) e não provocam recarregamentos em ciclo.
- Ao gravar a partir da interface, o ficheiro é reescrito no formato padrão, com os comentários de ajuda. Os comentários escritos à mão perdem-se.
- Campos desconhecidos são erros, para que um erro de escrita como `repeticao` não seja ignorado sem aviso.

**Importar/exportar.** Use o menu ⋯ da configuração. Exportar grava o conjunto num `.toml` à sua escolha. Importar valida o ficheiro antes de o copiar para `conjuntos\` e cria nomes únicos se houver colisões. Também pode copiar ficheiros diretamente para a pasta `conjuntos\`, que são detetados automaticamente.

**Nomes de teclas.** `0`–`9`, `A`–`Z`, `F1`–`F24`, `Numpad0`–`Numpad9`, `NumpadAdd`, `NumpadSubtract`, `NumpadMultiply`, `NumpadDivide`, `NumpadDecimal`, `Space`, `Tab`, `Enter`, `Backspace`, `Escape`, `Insert`, `Delete`, `Home`, `End`, `PageUp`, `PageDown`, `Up`, `Down`, `Left`, `Right`, `Pause`, `ScrollLock`, `CapsLock`, `NumLock`, `PrintScreen`, `Apps`, as teclas de pontuação `OEM1`…`OEM8`, `OEM102`, `OEMPlus`, `OEMComma`, `OEMMinus`, `OEMPeriod` (o carácter depende do layout; é mais fácil gravá-las no campo **Tecla**) e as teclas multimédia. Os modificadores são `Ctrl`, `Alt`, `Shift` e `Win`, por exemplo `Ctrl+Alt+F1`.

## Limitações

- **Aplicações executadas como administrador.** O Windows (UIPI) impede que um processo sem privilégios intercete teclas ou envie texto para janelas elevadas. Com uma dessas janelas em primeiro plano, as teclas funcionam normalmente e o painel não consegue escrever. Para usar macros nelas, execute o Macropad como administrador. Nesse caso, o arranque automático pelo registo `Run` não eleva o programa e terá de usar o Agendador de Tarefas com "Executar com privilégios mais elevados".
- O ecrã de UAC, o ecrã de bloqueio, o Ctrl+Alt+Del e alguns jogos com anti-cheat ou entrada "raw" não recebem nem deixam intercetar estes eventos.
- O Windows remove hooks de teclado que respondem devagar (LowLevelHooksTimeout). O callback do Macropad só consulta dados em memória, mas uma máquina muito sobrecarregada pode fazê-lo perder o hook. Nesse caso, reinicie o programa.
- No modo *Colar*, aplicações que leiam a área de transferência de forma muito lenta podem colar o texto anterior. O programa espera 80 ms depois de cada Ctrl+V.
- `AltGr` é tratado pelo Windows como `Ctrl+Alt`.
- A tecla de suspensão é global e intercetada mesmo nas janelas do Macropad, exceto enquanto um campo **Tecla** está a gravar.

## Arquitetura

```
src/macropad/
  core/                 # Python puro, sem Qt nem Win32 (testável em qualquer SO)
    commands.py         #   interpretação de {Enter} {Tab} {Delay:ms}
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
