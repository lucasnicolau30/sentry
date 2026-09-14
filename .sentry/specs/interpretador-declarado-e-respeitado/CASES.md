# Interpretador declarado é respeitado

## Prompt

O interpretador declarado é descartado — local_tools.py:157. Declarei .venv/Scripts/python.exe -m pytest, arquivo que não existe, e ele rodou o Python global sem avisar. Regressão do commit novo: antes essa grafia caía no caminho genérico e rodava como declarado. Mata o uso em qualquer projeto com venv.

## Campos

- **comando**: texto — o comando de suíte declarado em `[test] command`. Quando ele
  nomeia um interpretador ou executável por caminho, esse caminho é a declaração do
  usuário sobre qual ambiente rodar, e o Sentry não pode substituí-lo pelo seu próprio.

## Caso: interpretador declarado por caminho e usado no lugar do global

- **Requisito:** "Declarei .venv/Scripts/python.exe -m pytest ... e ele rodou o Python global"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** comando/valido
- **Dado:** um projeto que declara a suíte pelo interpretador de um venv existente
- **Quando:** o Sentry monta e executa o comando
- **Então:** é o interpretador declarado que roda, ainda embrulhado em `coverage run -m pytest`
- **Entrada:** `comando = "<venv>/bin/python -m pytest"`

## Caso: interpretador declarado inexistente vira erro de infraestrutura

- **Requisito:** "arquivo que não existe, e ele rodou o Python global sem avisar"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** comando/caracteres-especiais
- **Dado:** um `[test] command` que aponta um venv ausente, na grafia do Windows com
  separadores `\` e sufixo `.exe`
- **Quando:** o Sentry executa a suíte
- **Então:** a execução sai como não executada, com erro de infraestrutura nomeando o
  caminho declarado, e nenhum outro interpretador é usado no lugar
- **Entrada:** `comando = ".venv\\Scripts\\python.exe -m pytest"`

## Caso: executavel pytest do venv roda no python do proprio venv

- **Requisito:** "mata o uso em qualquer projeto com venv" — a mesma declaração escrita
  como console script não pode cair no ambiente global
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** comando/valido
- **Dado:** um venv cujo diretório contém o executável `pytest` e o interpretador irmão
- **Quando:** o Sentry normaliza a invocação
- **Então:** o comando é montado com o interpretador irmão do venv, mantendo a cobertura
- **Entrada:** `comando = "<venv>/bin/pytest -x"`

## Caso: executavel pytest sem interpretador irmao roda como declarado

- **Requisito:** "antes essa grafia caía no caminho genérico e rodava como declarado" —
  sem como deduzir o ambiente, executar o que foi declarado é a única resposta honesta
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** comando/valido
- **Dado:** um executável `pytest` num diretório sem interpretador ao lado
- **Quando:** o Sentry normaliza a invocação
- **Então:** o comando declarado é executado literalmente, sem troca de interpretador, e
  nenhuma cobertura é reportada, mas ele segue reconhecido como pytest
- **Entrada:** `comando = "/opt/bin/pytest"`

## Caso: runner sem caminho continua no interpretador do Sentry

- **Requisito:** não regredir a forma mais comum, em que nenhum ambiente foi declarado
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** comando/valido
- **Dado:** um comando que nomeia o runner sem nenhum separador de caminho
- **Quando:** o Sentry normaliza a invocação
- **Então:** o interpretador do próprio Sentry é usado, com `coverage run -m pytest`
- **Entrada:** `comando = "pytest"`, `comando = "python -m pytest -q"`

## Classes não aplicáveis

- **comando/vazio**: já verificada na spec `execucao-fiel-da-suite-declarada`, que trata
  `[test] command` em branco; nada aqui muda esse caminho.
- **comando/tamanho-maximo-excedido**: o comprimento do comando é limite do sistema
  operacional, não regra do Sentry; não há corte próprio a verificar.
