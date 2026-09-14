# Impacto respeita os diretórios de teste declarados

## Prompt

[tests] paths é ignorado pela análise de impacto — impact.py:55 hardcoda root/"tests". O mesmo relatório disse "nenhum arquivo de teste encontrado" e "Testes impactados: 0" enquanto associava users/test_serializers.py na matriz.

## Campos

- **test_paths**: texto — os diretórios de teste declarados em `[tests] paths` no
  `sentry.toml`. Sem declaração vale o padrão (`tests`, `test`, `spec`, `__tests__`).

## Caso: impacto encontra testes no diretorio declarado

- **Requisito:** "[tests] paths é ignorado pela análise de impacto"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** test_paths/valido
- **Dado:** um projeto com o teste ao lado do código, declarando `[tests] paths = ["users"]`
  e sem nenhum diretório `tests/`
- **Quando:** o Sentry calcula o impacto de uma alteração em `users/serializers.py`
- **Então:** `users/test_serializers.py` entra como teste impactado e nenhuma limitação
  de "nenhum arquivo de teste encontrado" é emitida
- **Entrada:** `test_paths = "users"`

## Caso: impacto e matriz enxergam o mesmo conjunto de arquivos

- **Requisito:** "o mesmo relatório disse 'nenhum arquivo de teste encontrado' ... enquanto
  associava users/test_serializers.py na matriz"
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** crítica
- **Classe:** test_paths/valido
- **Dado:** o mesmo projeto com teste ao lado do código
- **Quando:** impacto e rastreabilidade coletam os arquivos de teste
- **Então:** todo arquivo de teste que a matriz pode associar é visível para o impacto,
  sem um afirmar a ausência do que o outro associou
- **Entrada:** `test_paths = "users"`

## Caso: padrao cobre os quatro diretorios convencionais

- **Requisito:** sem declaração, impacto e matriz precisam ter o mesmo padrão; o impacto
  só olhava `tests/`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** test_paths/vazio
- **Dado:** um projeto sem `[tests] paths` e com os testes em `spec/`
- **Quando:** o Sentry calcula o impacto
- **Então:** os testes em `spec/` são encontrados
- **Entrada:** `test_paths = ""`

## Caso: diretorio declarado inexistente vira limitacao e nao silencio

- **Requisito:** o relatório precisa dizer que não olhou, em vez de reportar zero
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** test_paths/caracteres-especiais
- **Dado:** um `[tests] paths` apontando um diretório que não existe, escrito com
  separadores e subdiretório
- **Quando:** o Sentry calcula o impacto de uma alteração em código fonte
- **Então:** a limitação "nenhum arquivo de teste encontrado" é registrada, nomeando o
  caminho declarado
- **Entrada:** `test_paths = "backend/testes"`

## Caso: dependencia de terceiros nao entra como teste do projeto

- **Requisito:** o conjunto de arquivos precisa ser o mesmo da matriz, que já ignora
  diretórios de dependência
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** test_paths/valido
- **Dado:** um diretório declarado que contém `node_modules` com arquivos de teste
- **Quando:** o Sentry coleta os arquivos de teste
- **Então:** os arquivos de dependência ficam de fora
- **Entrada:** `test_paths = "frontend"`

## Caso: teste com erro de sintaxe vira limitacao, nao quebra a analise

- **Requisito:** "Um arquivo de teste com sintaxe invalida nao pode derrubar a analise
  dos demais: SyntaxError ao parsear os imports precisa virar limitacao registrada"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** um arquivo de teste com sintaxe Python inválida, dentro do diretório de
  testes analisado
- **Quando:** o Sentry calcula o impacto de uma alteração em código fonte
- **Então:** a análise não levanta exceção; o arquivo quebrado não entra como impactado,
  e a limitação é registrada em vez de silenciar o defeito

## Classes não aplicáveis

- **test_paths/tamanho-maximo-excedido**: o comprimento do caminho é limite do sistema de
  arquivos, não regra do Sentry; um caminho longo demais apenas não existe.
