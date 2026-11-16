# Exemplos

*English version: [EXAMPLES.md](../../EXAMPLES.md).*

Macros prontas a usar. Pode criar cada uma na janela de configuração, ou colar o TOML num ficheiro de conjunto em `%APPDATA%\VirtualMacroTextInputer\conjuntos\` (é recarregado assim que o gravar). A referência completa está em [ARQUITETURA.md](ARQUITETURA.md), e um conjunto completo e comentado está em [examples/conjunto-exemplo.toml](../../examples/conjunto-exemplo.toml).

## 1. Um código numa tecla

Premir **1** escreve o código; o próprio 1 não aparece.

```toml
[[macros]]
titulo = "3E03305"
tecla = "1"
texto = "3E03305"
```

## 2. Texto seguido de Enter

Uma quebra de linha no campo **Texto** equivale a `{Enter}`.

```toml
[[macros]]
titulo = "Z51.11 ⏎"
tecla = "2"
texto = "Z51.11{Enter}"
```

## 3. Preencher um formulário

Escreve o primeiro campo, passa ao seguinte com Tab, espera meio segundo pela aplicação e submete.

```toml
[[macros]]
titulo = "Formulário"
tecla = "3"
texto = "João Silva{Tab}joao@exemplo.pt{Delay:500}{Enter}"
```

Se premir Ctrl, Alt, Shift ou Win durante a execução, a macro espera que as largue (até 1,5 s), em vez de enviar o `{Enter}` como `Ctrl+Enter`.

## 4. Repetir uma linha

Executa a macro três vezes por cada pressão, com 250 ms entre execuções.

```toml
[[macros]]
titulo = "3× linha"
tecla = "Ctrl+F1"           # só dispara com exatamente Ctrl+F1
texto = "linha{Enter}"
repeticoes = 3
intervalo_ms = 250
```

## 5. Um botão só para o painel

Sem tecla, a macro só existe no painel; o teclado fica como está.

```toml
[[macros]]
titulo = "Assinatura"
tecla = ""
texto = "Com os melhores cumprimentos,{Enter}Alex"
```

## 6. Um painel de controlo multimédia

Os botões que pressionam teclas multimédia mostram um símbolo simples. No editor: **Multimédia ▸ O botão envia ▸ Reproduzir/Pausa** (uma macro nova passa a chamar-se «Play/Pausa» automaticamente).

```toml
[[macros]]
titulo = "Anterior"
tecla = ""
texto = "{MediaPrev}"

[[macros]]
titulo = "Play/Pausa"
tecla = ""
texto = "{MediaPlayPause}"

[[macros]]
titulo = "Seguinte"
tecla = ""
texto = "{MediaNext}"

[[macros]]
titulo = "Volume +"
tecla = ""
texto = "{VolumeUp}{VolumeUp}"   # dois passos por clique
```

Para usar antes uma tecla multimédia do teclado como gatilho de uma macro de texto, escolha **Multimédia ▸ A tecla do teclado ativa esta macro**.

## 7. Um contador

Uma pressão curta (clique ou **F9**) soma 1; manter premido 800 ms repõe a 0, com um sinal verde e o som de aviso do Windows. A contagem mantém-se entre sessões.

```toml
[[macros]]
tipo = "contador"
id = "chamadas"
titulo = "Chamadas"
tecla = "F9"
incremento = 1
reposicao = 0
pressao_longa_ms = 800
som_reposicao = "aviso"
```

## 8. Um conjunto que só funciona em algumas aplicações

As teclas deste conjunto só disparam no Bloco de Notas e no Word; nas outras aplicações escrevem normalmente.

```toml
versao_esquema = 1
nome = "Relatórios"

[ambito]
modo = "aplicacoes"
aplicacoes = ["notepad.exe", "WINWORD.EXE"]

[[macros]]
titulo = "Cabeçalho"
tecla = "F6"
texto = "RELATÓRIO{Enter}=========={Enter}"
```

## 9. Agrupar botões no painel

Os espaços vazios guardam uma célula livre, para agrupar botões por linha. Com 4 colunas, isto põe os dois códigos na primeira linha e os botões multimédia na segunda.

```toml
[[macros]]
titulo = "Código A"
tecla = "1"
texto = "3E03305"

[[macros]]
titulo = "Código B"
tecla = "2"
texto = "Z51.11"

[[macros]]
tipo = "espaco"

[[macros]]
tipo = "espaco"

[[macros]]
titulo = "Play/Pausa"
tecla = ""
texto = "{MediaPlayPause}"
```

## 10. Um painel compacto com páginas

No separador *Painel*: **Colunas** 3, **Linhas** 2, estilo **Compacto**. Com mais de seis botões, o painel mostra as setas ◀ 1 / 2 ▶; as teclas funcionam para os botões de todas as páginas. O mesmo no `config.toml`:

```toml
[painel]
colunas = 3
linhas = 2
tamanho_botao = 56            # o estilo Compacto
```

## 11. Aplicações que não aceitam escrita simulada

Algumas aplicações (ambientes de trabalho remotos, alguns formulários web) ignoram a escrita simulada. Mude Preferências ▸ **Modo de texto** para *Colar*: o texto passa pela área de transferência e Ctrl+V. No `config.toml`:

```toml
[geral]
modo_texto = "colar"
```
