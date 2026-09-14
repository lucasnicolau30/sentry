# Caminho relativo declarado executa em qualquer grafia

## Prompt

No Windows, caminho relativo com barra normal não executa. .venv/Scripts/python.exe -m pytest é reconhecido mas o CreateProcess não resolve. Testei as quatro variantes: só relativo+/ quebra. O código normaliza \→/ para reconhecer (local_tools.py:230) mas passa args[0] cru para executar (:241).

## Campos

- **caminho_do_executavel**: texto — o caminho declarado em `[test] command`. Pode ser
  absoluto ou relativo, com barra normal ou invertida, ou um nome puro a resolver no PATH.

## Caso: caminho relativo com barra normal executa

- **Requisito:** "No Windows, caminho relativo com barra normal não executa ... só relativo+/ quebra"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** caminho_do_executavel/caracteres-especiais
- **Dado:** um venv real declarado com barra normal e caminho relativo à raiz do projeto
- **Quando:** o Sentry executa a suíte
- **Então:** o processo roda, sem erro de infraestrutura
- **Entrada:** `caminho_do_executavel = "venv/Scripts/python.exe"`

## Caso: as quatro grafias do mesmo executavel sao equivalentes

- **Requisito:** "Testei as quatro variantes" — absoluto/relativo × barra normal/invertida
  descrevem o mesmo arquivo e não podem divergir no resultado
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** caminho_do_executavel/valido
- **Dado:** o mesmo interpretador escrito nas quatro grafias
- **Quando:** o Sentry monta e executa o comando
- **Então:** as quatro chegam ao mesmo arquivo e produzem o mesmo resultado
- **Entrada:** `caminho_do_executavel = "venv\\Scripts\\python.exe"` e as demais grafias

## Caso: caminho relativo e resolvido contra a raiz do projeto

- **Requisito:** o executável relativo descreve um arquivo do projeto, não do diretório de
  onde a CLI foi chamada
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** caminho_do_executavel/valido
- **Dado:** um projeto com venv na raiz e o Sentry invocado de outro diretório
- **Quando:** o Sentry executa a suíte
- **Então:** o interpretador do projeto é encontrado e executado
- **Entrada:** `caminho_do_executavel = "venv/Scripts/python.exe"`

## Caso: nome puro continua resolvido pelo PATH

- **Requisito:** não regredir a forma mais comum, em que nenhum caminho foi declarado
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** caminho_do_executavel/valido
- **Dado:** um comando que nomeia o runner sem nenhum separador
- **Quando:** o Sentry monta o comando
- **Então:** o nome segue intocado, para o sistema operacional resolver no PATH
- **Entrada:** `caminho_do_executavel = "pytest"`

## Caso: caminho declarado inexistente nomeia onde foi procurado

- **Requisito:** resolver contra a raiz não pode transformar erro de configuração em
  mensagem mais obscura
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** caminho_do_executavel/valido
- **Dado:** um `[test] command` apontando um venv que não existe no projeto
- **Quando:** o Sentry executa a suíte
- **Então:** o erro de infraestrutura mostra o caminho já resolvido contra a raiz, dizendo
  onde se procurou
- **Entrada:** `caminho_do_executavel = ".venv/Scripts/python.exe"`

## Caso: suite nao-pytest com caminho relativo tambem e resolvida

- **Requisito:** o defeito é da execução, não do reconhecimento do pytest; qualquer runner
  declarado por caminho relativo sofre o mesmo
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** caminho_do_executavel/caracteres-especiais
- **Dado:** uma suíte não-pytest declarada por caminho relativo com barra normal
- **Quando:** o Sentry executa a suíte
- **Então:** o processo roda, sem erro de infraestrutura
- **Entrada:** `caminho_do_executavel = "ferramentas/runner.exe"`

## Classes não aplicáveis

- **caminho_do_executavel/vazio**: `[test] command` em branco já é verificado na spec
  `execucao-fiel-da-suite-declarada`; nada aqui muda esse caminho.
- **caminho_do_executavel/tamanho-maximo-excedido**: o comprimento do caminho é limite do
  sistema de arquivos, não regra do Sentry; um caminho longo demais apenas não existe e cai
  no caso de caminho inexistente.
