# Fase 3 — caber no loop

## Prompt

Fase 3: caber no loop. (a) Dois modos por desenho: um modo instantaneo que nao executa
teste nenhum -- estrutura, rastreabilidade, marcador orfao, diff e a cobertura da ultima
execucao completa -- para o loop de digitacao; e o modo completo, sob demanda e no
pre-commit. A cobertura reaproveitada precisa ser declarada como vinda da execucao
anterior, nunca como medida agora. (b) Cache por hash de conteudo: se o diff, os arquivos
de teste e as specs nao mudaram, reusar a ultima execucao completa em vez de repetir a
suite. (c) sentry watch: reavalia ao salvar no modo instantaneo, e escala para o completo
quando o arquivo salvo e um teste. (d) sentry context --json: o payload denso do que nao
tem evidencia -- faixas de linha descobertas, caminhos de erro que nenhum teste executou,
testes falhando com nome, cenarios sem teste, classes de equivalencia ausentes e
marcadores orfaos -- para o agente trabalhar sobre o recorte em vez do codigo inteiro.
(e) Bloco de Custo no relatorio: os tokens que o Sentry gastou (zero, porque nao chama
modelo) e o tamanho do que ele resumiu.

## Campos

- **modo_de_execucao**: texto — `instantâneo` (não executa teste, reaproveita a cobertura
  da última execução completa) ou `completo` (executa a suíte). É ele que decide o que o
  relatório pode afirmar sobre cobertura.
- **hash_da_entrada**: texto — a impressão do conteúdo que decide se a execução completa
  anterior ainda serve: diff, arquivos de teste e specs.
- **lacuna**: texto — um item sem evidência no payload de `sentry context --json`. O que
  se cobra é o payload trazer todas as espécies de lacuna, e nada além delas.

## Caso: modo instantaneo nao executa a suite

- **Requisito:** "um modo instantaneo que nao executa teste nenhum ... para o loop de
  digitacao"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** modo_de_execucao/valido
- **Dado:** um projeto com suíte declarada
- **Quando:** a análise roda no modo instantâneo
- **Então:** nenhum processo de teste é iniciado e a execução termina sem contagem de
  testes desta rodada
- **Entrada:** `modo_de_execucao = "instantâneo"`

## Caso: modo instantaneo reusa a cobertura da ultima execucao completa

- **Requisito:** "estrutura, rastreabilidade, marcador orfao, diff e a cobertura da ultima
  execucao completa"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** modo_de_execucao/valido
- **Dado:** uma execução completa anterior que mediu cobertura
- **Quando:** a análise roda no modo instantâneo
- **Então:** o relatório traz a cobertura global e do alterado vindas daquela execução
- **Entrada:** `modo_de_execucao = "instantâneo"`

## Caso: cobertura reusada e declarada como da execucao anterior

- **Requisito:** "A cobertura reaproveitada precisa ser declarada como vinda da execucao
  anterior, nunca como medida agora"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** modo_de_execucao/caracteres-especiais
- **Dado:** uma análise instantânea que reaproveitou cobertura
- **Quando:** o relatório é gerado
- **Então:** a cobertura aparece marcada como vinda de execução anterior, com o instante
  daquela execução, e não como medição desta
- **Entrada:** `modo_de_execucao = "instantâneo"`

## Caso: sem execucao completa anterior a cobertura sai indisponivel

- **Requisito:** reaproveitar o que não existe seria inventar medição; a ausência é
  limitação declarada, como em toda outra parte do produto
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** modo_de_execucao/vazio
- **Dado:** um projeto sem nenhuma execução completa registrada
- **Quando:** a análise roda no modo instantâneo
- **Então:** a cobertura sai indisponível e nenhum número é afirmado
- **Entrada:** `modo_de_execucao = "instantâneo"`

## Caso: modo instantaneo entrega estrutura rastreabilidade e diff

- **Requisito:** "estrutura, rastreabilidade, marcador orfao, diff"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** um projeto com spec válida e uma mudança na árvore
- **Quando:** a análise roda no modo instantâneo
- **Então:** o relatório traz os arquivos alterados, os cenários da spec com teste
  associado e os achados que não dependem de execução
- **Entrada:** `modo_de_execucao = "instantâneo"`

## Caso: segunda execucao completa sem mudanca volta do cache

- **Requisito:** "se o diff, os arquivos de teste e as specs nao mudaram, reusar a ultima
  execucao completa em vez de repetir a suite"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** hash_da_entrada/valido
- **Dado:** uma execução completa recém-terminada e nada alterado desde então
- **Quando:** a análise completa roda de novo
- **Então:** a suíte não é executada outra vez e o veredito é o mesmo da execução anterior
- **Entrada:** `hash_da_entrada = "inalterado"`

## Caso: mudanca em arquivo de codigo invalida o cache

- **Requisito:** "se o diff ... nao mudaram" — mudou o diff, a execução anterior não
  descreve mais o código
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** hash_da_entrada/caracteres-especiais
- **Dado:** uma execução completa anterior e um arquivo de código editado depois dela
- **Quando:** o hash da entrada é calculado
- **Então:** o hash difere do gravado e a suíte é executada de novo
- **Entrada:** `hash_da_entrada = "codigo alterado"`

## Caso: mudanca em arquivo de teste invalida o cache

- **Requisito:** "os arquivos de teste ... nao mudaram"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** hash_da_entrada/valido
- **Dado:** uma execução completa anterior e um arquivo de teste editado depois dela
- **Quando:** o hash da entrada é calculado
- **Então:** o hash difere do gravado e a suíte é executada de novo
- **Entrada:** `hash_da_entrada = "teste alterado"`

## Caso: mudanca na spec invalida o cache

- **Requisito:** "e as specs nao mudaram"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** hash_da_entrada/valido
- **Dado:** uma execução completa anterior e um `CASES.md` editado depois dela
- **Quando:** o hash da entrada é calculado
- **Então:** o hash difere do gravado e a análise é refeita
- **Entrada:** `hash_da_entrada = "spec alterada"`

## Caso: sem execucao anterior nao ha cache a reusar

- **Requisito:** o cache é reuso de evidência existente; sem execução anterior não há o
  que reusar, e inventar acerto seria pior que repetir a suíte
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** hash_da_entrada/vazio
- **Dado:** um projeto sem nenhuma execução completa registrada
- **Quando:** a decisão de reuso é tomada
- **Então:** o cache não acerta e a suíte é executada
- **Entrada:** `hash_da_entrada = ""`

## Caso: execucao vinda do cache e declarada no relatorio

- **Requisito:** reusar sem dizer transformaria evidência velha em afirmação nova — a
  mesma armadilha do relatório que envelhece sem avisar
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Dado:** uma análise que reaproveitou a execução anterior
- **Quando:** o relatório é gerado
- **Então:** o relatório diz que a execução veio do cache e de quando ela é
- **Entrada:** `hash_da_entrada = "inalterado"`

## Caso: watch no arquivo de codigo roda o modo instantaneo

- **Requisito:** "sentry watch: reavalia ao salvar no modo instantaneo"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** modo_de_execucao/valido
- **Dado:** um arquivo de código-fonte salvo
- **Quando:** o watch decide o que fazer
- **Então:** escolhe o modo instantâneo
- **Entrada:** `modo_de_execucao = "instantâneo"`

## Caso: watch no arquivo de teste escala para o modo completo

- **Requisito:** "escala para o completo quando o arquivo salvo e um teste"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** modo_de_execucao/valido
- **Dado:** um arquivo de teste salvo
- **Quando:** o watch decide o que fazer
- **Então:** escolhe o modo completo, porque só executando é que a mudança no teste vira
  evidência
- **Entrada:** `modo_de_execucao = "completo"`

## Caso: context emite as faixas de linha sem cobertura

- **Requisito:** "o payload denso do que nao tem evidencia -- faixas de linha descobertas"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** lacuna/valido
- **Dado:** uma execução com linhas alteradas que nenhum teste executou
- **Quando:** o payload de contexto é montado
- **Então:** ele traz, por arquivo, as faixas de linha descobertas
- **Entrada:** `lacuna = "linhas descobertas"`

## Caso: context emite cenarios classes caminhos de erro e marcadores orfaos

- **Requisito:** "caminhos de erro que nenhum teste executou ... cenarios sem teste,
  classes de equivalencia ausentes e marcadores orfaos"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** lacuna/valido
- **Dado:** uma execução com cenário sem teste, classe de equivalência ausente, caminho de
  erro descoberto e marcador órfão
- **Quando:** o payload de contexto é montado
- **Então:** cada uma das quatro espécies aparece na sua própria chave
- **Entrada:** `lacuna = "cenario sem teste"`

## Caso: context emite os testes falhando com nome

- **Requisito:** "testes falhando com nome"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** lacuna/caracteres-especiais
- **Dado:** uma execução com testes falhando
- **Quando:** o payload de contexto é montado
- **Então:** os nomes dos testes falhos aparecem no payload
- **Entrada:** `lacuna = "teste falhando"`

## Caso: sem lacuna nenhuma o payload sai vazio e nao omitido

- **Requisito:** o agente precisa distinguir "nada a fazer" de "o Sentry não olhou"; chave
  ausente é ambígua onde lista vazia é conclusiva
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** lacuna/vazio
- **Dado:** uma execução aprovada, sem lacuna nenhuma
- **Quando:** o payload de contexto é montado
- **Então:** todas as chaves existem, todas vazias
- **Entrada:** `lacuna = ""`

## Caso: relatorio traz o bloco de custo com zero token gasto

- **Requisito:** "os tokens que o Sentry gastou (zero, porque nao chama modelo)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** qualquer análise concluída
- **Quando:** o relatório em Markdown é gerado
- **Então:** existe um bloco de custo declarando zero token gasto pelo Sentry
- **Entrada:** `modo_de_execucao = "completo"`

## Caso: bloco de custo mede o tamanho do que o relatorio resumiu

- **Requisito:** "e o tamanho do que ele resumiu" — o argumento do produto precisa de um
  número que ele mesmo emita, não de uma estimativa em slide
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Dado:** uma análise sobre um diff de tamanho conhecido
- **Quando:** o relatório é gerado
- **Então:** o bloco de custo traz o tamanho do diff resumido e o do próprio relatório,
  declarando que a conversão em tokens é estimativa
- **Entrada:** `modo_de_execucao = "completo"`

## Classes não aplicáveis

- **modo_de_execucao/tamanho-maximo-excedido**: o modo é um de dois valores fechados
  escolhidos pela linha de comando, não texto digitado com comprimento a limitar.
- **hash_da_entrada/tamanho-maximo-excedido**: o hash tem comprimento fixo por
  construção — é a saída de uma função de resumo, não entrada do usuário.
- **lacuna/tamanho-maximo-excedido**: a espécie de lacuna vem de um conjunto fechado de
  chaves do payload; o comprimento do conteúdo de cada uma não participa da decisão.
