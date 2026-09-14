# Dimensão de exceções não afirma o falso

## Prompt

A dimensão de exceções afirma o falso — dimensions.py:57. Sem cobertura, saiu "não aplicável — nenhum caminho de erro nas linhas alteradas" enquanto as Limitações diziam "1 caminho de erro alterado sem dados de cobertura".

## Campos

- **caminhos_de_erro**: inteiro — quantos `raise`/`except`/`throw` existem nas linhas
  alteradas. Zero significa que a dimensão não existe nesta mudança; mais que zero
  significa que existe, independentemente de ter sido possível medi-la.
- **cobertura**: texto — os dados de execução por linha. Vazio significa que a suíte não
  rodou ou não produziu cobertura, e nada pode ser afirmado sobre execução.

## Caso: sem dados de cobertura a dimensao sai como nao verificada

- **Requisito:** "saiu 'não aplicável — nenhum caminho de erro nas linhas alteradas'
  enquanto as Limitações diziam '1 caminho de erro alterado sem dados de cobertura'"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** cobertura/vazio
- **Dado:** uma mudança que altera um `raise` e uma análise sem dados de cobertura
- **Quando:** o Sentry avalia a dimensão de exceções
- **Então:** o status não é "não aplicável" nem "coberta", e a evidência informa quantos
  caminhos de erro existem e que não foi possível medi-los
- **Entrada:** `caminhos_de_erro = 1`, `cobertura = ""`

## Caso: ausencia real de caminho de erro continua nao aplicavel

- **Requisito:** "não aplicável" precisa continuar significando que a dimensão não existe
  nesta mudança
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** caminhos_de_erro/zero
- **Dado:** uma mudança sem nenhum caminho de erro nas linhas alteradas, com ou sem cobertura
- **Quando:** o Sentry avalia a dimensão de exceções
- **Então:** o status é "não aplicável", com a evidência de que não há caminho de erro
- **Entrada:** `caminhos_de_erro = 0`

## Caso: com cobertura o veredito de execucao permanece

- **Requisito:** o conserto só pode alcançar o caso sem medição
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** cobertura/valido
- **Dado:** uma mudança com dois caminhos de erro alterados e dados de cobertura
- **Quando:** um deles foi executado por algum teste e o outro não
- **Então:** o status é "parcial", e com todos executados é "coberta", com nenhum é "não coberta"
- **Entrada:** `caminhos_de_erro = 2`, `cobertura = "1 executado, 1 nao executado"`

## Caso: caminho de erro excluido da medicao nao vira ausencia de caminho

- **Requisito:** o mesmo defeito de fundo — a dimensão dizendo que não há o que medir
  quando as Limitações dizem que há
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** caminhos_de_erro/valido
- **Dado:** uma mudança cujo único caminho de erro alterado está marcado `# pragma: no cover`
- **Quando:** o Sentry avalia a dimensão de exceções
- **Então:** a evidência declara a exclusão em vez de afirmar que não há caminho de erro
- **Entrada:** `caminhos_de_erro = 1`, `cobertura = "excluido pelo projeto"`

## Caso: dimensao nao verificada aparece no relatorio como ausencia de evidencia

- **Requisito:** o relatório precisa ser lido sem contradição entre a tabela e as Limitações
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** cobertura/vazio
- **Dado:** uma análise sem execução de testes sobre uma mudança que altera um `raise`
- **Quando:** o relatório é montado
- **Então:** a linha da dimensão de exceções e a seção de Limitações concordam: ambas
  dizem que existe caminho de erro e que ele não pôde ser medido
- **Entrada:** `caminhos_de_erro = 1`, `cobertura = ""`

## Classes não aplicáveis

- **caminhos_de_erro/vazio**: a quantidade é o tamanho das listas produzidas por
  `select_error_paths`; listas sempre existem, ainda que vazias — e vazia é a classe zero.
- **caminhos_de_erro/nao-numerico**: idem, é um comprimento de lista, nunca texto.
- **caminhos_de_erro/negativo**: idem, um comprimento de lista nunca é negativo.
- **caminhos_de_erro/limite-superior**: a dimensão agrega por contagem, sem teto próprio;
  mais caminhos apenas mudam os números da evidência.
- **cobertura/tamanho-maximo-excedido**: a cobertura chega como mapa de arquivo para
  números de linha, não como texto; não há comprimento a limitar.
- **cobertura/caracteres-especiais**: idem, os valores já vêm validados pelo leitor de
  cobertura; não há texto livre a interpretar nesta dimensão.
