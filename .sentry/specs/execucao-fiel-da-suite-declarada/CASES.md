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

## Classes não aplicáveis

- **comando/tamanho-maximo-excedido**: o comprimento do comando é limite do sistema
  operacional, não regra do Sentry; não há corte próprio a verificar.
- **junit_xml/tamanho-maximo-excedido**: idem, o caminho é validado pelo sistema de arquivos.
- **junit_xml/caracteres-especiais**: o caminho é usado como `self.root / junit_xml` sem
  interpretação própria; não há classe de caractere que mude o comportamento do Sentry.
