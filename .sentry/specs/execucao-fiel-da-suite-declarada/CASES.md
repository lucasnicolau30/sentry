# Execução fiel da suíte declarada

## Prompt

Duas coisas que poderiam melhorar o tempo de analise de cada arquivo, que hoje nao acumula, deveria, e alguns casos de teste usando unittest ele injeta comandos que o unittest por padrao nao aceita. E eu colocaria o pytest junto com pytest-django com ele, porque ajuda bastante.

## Campos

- **comando**: texto — o comando de suíte declarado em `[test] command`. O Sentry só
  pode alterá-lo quando reconhece o runner; caso contrário executa literalmente.
- **junit_xml**: texto — caminho do relatório JUnit declarado em `[test] junit_xml`.
  Vazio significa que o projeto não gera relatório próprio.

## Caso: comando nao-pytest sem junit declarado nao recebe a flag do pytest

- **Requisito:** "usando unittest ele injeta comandos que o unittest por padrão não aceita"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** junit_xml/vazio
- **Dado:** um projeto com suíte `unittest` e nenhum `junit_xml` declarado
- **Quando:** o Sentry executa a suíte
- **Então:** o comando roda exatamente como declarado, sem `--junitxml`, e o erro de
  infraestrutura aponta a declaração que resolve
- **Entrada:** `comando = "python -m unittest discover"`, `junit_xml = ""`

## Caso: suite nao-pytest le o junit declarado sem injetar flag

- **Requisito:** com relatório próprio declarado, o Sentry apenas lê o arquivo
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** junit_xml/valido
- **Dado:** um projeto não-Python que gera o próprio JUnit XML
- **Quando:** o Sentry executa a suíte
- **Então:** a contagem vem do relatório, sem flag injetada e sem cobertura própria
- **Entrada:** `comando = "npx jest"`, `junit_xml = "reports/junit.xml"`

## Caso: pytest invocado como modulo e reconhecido

- **Requisito:** "eu colocaria o pytest junto com pytest-django" — forma usual em venv e Django
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** comando/valido
- **Dado:** um projeto que declara a suíte como módulo em vez do executável
- **Quando:** o Sentry executa a suíte
- **Então:** é reconhecido como pytest, embrulhado em `coverage run` e a cobertura é medida
- **Entrada:** `comando = "python -m pytest"`

## Caso: pytest invocado por caminho de executavel e reconhecido

- **Requisito:** o mesmo runner escrito com caminho não pode perder instrumentação
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** comando/caracteres-especiais
- **Dado:** um comando que aponta o executável do venv, com separadores e sufixo `.exe`
- **Quando:** o Sentry normaliza a invocação
- **Então:** é reconhecido como pytest e normalizado para `-m pytest`
- **Entrada:** `comando = ".venv/bin/pytest -x"`

## Caso: comando vazio vira erro de infraestrutura

- **Requisito:** configuração inválida não pode derrubar a análise
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** comando/vazio
- **Dado:** um `sentry.toml` com `[test] command` em branco
- **Quando:** o Sentry tenta executar a suíte
- **Então:** a execução sai como não executada com erro de infraestrutura, sem exceção
- **Entrada:** `comando = ""`

## Caso: comando de teste ausente vira erro de infraestrutura, nao reprovacao

- **Requisito:** "FileNotFoundError (comando configurado nao existe no PATH) precisa
  virar infrastructure_error, nunca ser tratado como suite reprovada"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** comando/valido
- **Dado:** `[test] command` apontando para um executável que não existe no PATH
- **Quando:** o Sentry tenta executar a suíte
- **Então:** a execução sai como não executada, com erro de infraestrutura, sem
  cobertura calculada

## Caso: fora do pytest, ausencia de teste contabilizado e infraestrutura

- **Requisito:** "Nao existe tabela confiavel de codigos de saida fora do pytest, entao
  o sinal e' a evidencia: sem nenhum teste contabilizado nao ha prova de que a suite
  rodou -- e' ambiente, e reprovar ali mentiria sobre o codigo. Com teste contabilizado,
  codigo de saida != 0 volta a ser reprovacao legitima"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** comando/valido
- **Dado:** uma suíte não-pytest (`npx jest`) que terminou sem contabilizar teste
  nenhum, e outra que terminou com pelo menos um teste contabilizado
- **Quando:** o Sentry classifica o código de saída
- **Então:** sem contagem, a ausência vira erro de infraestrutura nomeando o código de
  saída; com contagem, o código de saída não-zero continua sendo reprovação legítima

## Caso: junit.xml corrompido cai no fallback por regex sem quebrar

- **Requisito:** "XML invalido ou sem <testsuite> precisa devolver None -- e' o sinal
  para SuiteAdapter usar o fallback por regex na saida do pytest"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** junit_xml/invalido
- **Dado:** um `junit.xml` com conteúdo malformado, e outro sem elemento `<testsuite>`
- **Quando:** o Sentry tenta contar testes a partir do arquivo
- **Então:** a leitura devolve `None` para os dois, sem levantar exceção
- **Entrada:** `junit_xml = "isto nao e xml valido <<<"`

## Classes não aplicáveis

- **comando/tamanho-maximo-excedido**: o comprimento do comando é limite do sistema
  operacional, não regra do Sentry; não há corte próprio a verificar.
- **junit_xml/tamanho-maximo-excedido**: idem, o caminho é validado pelo sistema de arquivos.
- **junit_xml/caracteres-especiais**: o caminho é usado como `self.root / junit_xml` sem
  interpretação própria; não há classe de caractere que mude o comportamento do Sentry.
