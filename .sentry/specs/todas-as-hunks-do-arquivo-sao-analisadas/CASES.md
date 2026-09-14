# Todas as hunks do arquivo são analisadas

## Prompt

Só a última hunk de cada arquivo é analisada — local_tools.py:62, sobrescreve em vez de acumular. Fiz 2 hunks com raise (linhas 50 e 370); ele reportou apenas users/serializers.py:370. O caminho de erro do validate_telefone ficou invisível.

## Campos

- **hunks**: inteiro — quantidade de blocos `@@` que o diff traz para o mesmo arquivo.
  Cada um descreve linhas alteradas, e todas juntas são o que a análise deve enxergar.
- **diff**: texto — a saída bruta de `git diff --unified=0`, de onde os arquivos e as
  linhas alteradas são lidos.

## Caso: duas hunks no mesmo arquivo acumulam em vez de sobrescrever

- **Requisito:** "Fiz 2 hunks com raise (linhas 50 e 370); ele reportou apenas ...:370"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** hunks/valido
- **Dado:** um diff com dois blocos alterados no mesmo arquivo, distantes entre si
- **Quando:** o Sentry lê as linhas alteradas
- **Então:** as linhas das duas hunks aparecem, em ordem crescente e sem repetição
- **Entrada:** `hunks = 2` (linhas 50 e 370 do mesmo arquivo)

## Caso: hunk que so remove linhas nao apaga as demais do arquivo

- **Requisito:** acumular não pode quebrar quando uma das hunks não adiciona linha
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** hunks/zero
- **Dado:** um arquivo com uma hunk de adição e outra de remoção pura (`+N,0`)
- **Quando:** o Sentry lê as linhas alteradas
- **Então:** a remoção não contribui linha alguma e as linhas adicionadas permanecem
- **Entrada:** `hunks = 2`, uma delas com contagem `0`

## Caso: hunk sem contagem explicita vale uma linha

- **Requisito:** o Git omite a contagem quando ela é 1; ignorar essa forma perderia hunks
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** hunks/vazio
- **Dado:** um diff cujo cabeçalho traz `@@ -10 +10 @@`, sem vírgula
- **Quando:** o Sentry lê as linhas alteradas
- **Então:** exatamente a linha indicada é registrada
- **Entrada:** `hunks = 1` com contagem omitida

## Caso: muitas hunks no mesmo arquivo e nenhuma e perdida

- **Requisito:** "o caminho de erro ficou invisível" — nenhum bloco pode sumir, por mais
  que sejam
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** hunks/limite-superior
- **Dado:** um arquivo com dezenas de blocos alterados
- **Quando:** o Sentry lê as linhas alteradas
- **Então:** todas as linhas de todos os blocos estão presentes
- **Entrada:** `hunks = 60`

## Caso: hunk de arquivo removido nao e atribuida ao arquivo anterior

- **Requisito:** acumular torna a atribuição errada permanente, em vez de sobrescrita
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** diff/caracteres-especiais
- **Dado:** um diff em que um arquivo alterado é seguido de um arquivo removido, cujo
  cabeçalho é `+++ /dev/null`
- **Quando:** o Sentry lê as linhas alteradas
- **Então:** as hunks do arquivo removido não entram nas linhas do arquivo anterior
- **Entrada:** `diff = "... +++ b/a.py ... +++ /dev/null ..."`

## Caso: linhas alteradas alimentam a analise de cobertura de todas as hunks

- **Requisito:** o efeito visível do defeito era o caminho de erro da primeira hunk sair
  do relatório
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** diff/valido
- **Dado:** um repositório Git com um arquivo alterado em dois pontos distantes
- **Quando:** o Sentry monta o contexto da mudança
- **Então:** os dois pontos aparecem entre as linhas alteradas do arquivo
- **Entrada:** `diff = <saida real de git diff --unified=0>`

## Classes não aplicáveis

- **hunks/negativo**: a quantidade de blocos é a contagem de cabeçalhos `@@` presentes
  no diff; nunca é negativa.
- **hunks/nao-numerico**: o cabeçalho é casado por expressão regular numérica, então o
  que não for número simplesmente não é reconhecido como hunk.
- **diff/vazio**: diff vazio significa nenhum arquivo alterado, caminho já verificado
  pelo contexto Git existente; não há hunk a acumular.
- **diff/tamanho-maximo-excedido**: a saída é lida inteira do `git diff`, sem corte
  próprio do Sentry; não há limite a verificar.
