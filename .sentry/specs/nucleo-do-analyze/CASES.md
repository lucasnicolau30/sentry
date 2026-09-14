# Núcleo do analyze

## Prompt

Cobrir o nucleo de `application/analyze.py` que nunca tinha spec: selecao de spec por
slug (`select_spec`), o modo `--spec all`, a politica de severidade declarada em
`sentry.toml`, o filtro `[analysis] exclude`, o suporte a projetos de outra stack (lcov e
JUnit declarados em vez de coverage.py/pytest), o registro de classes de equivalencia nao
aplicaveis como limitacao (nao como achado escondido), e a leitura do nome do projeto em
`[project] name` com fallback pro nome do diretorio. Esses comportamentos ja existiam e ja
tinham teste, so nunca ganharam `## Caso:` formal -- os testes tinham marcador de cenario
apontando pro nada.

## Campos

- **argumento_slug**: texto — o valor passado em `--spec` (ou `None`) que
  `select_spec` resolve contra `.sentry/specs/`.
- **quantidade_de_specs**: inteiro — quantas pastas com `CASES.md` existem sob
  `.sentry/specs/` quando nenhum slug foi passado.
- **valor_de_severidade**: texto — a string declarada em
  `[policy.severities]` no `sentry.toml`, que precisa bater com um valor do
  enum `Severity` pra sobrescrever a política padrão.
- **exclude_declarado**: booleano — se `[analysis] exclude` foi declarado no
  `sentry.toml` ou não.
- **stack_da_suite**: texto — se a suíte e a cobertura vêm de pytest/coverage.py
  (padrão) ou de um comando e um relatório lcov declarados (`[test] command`,
  `[coverage] path`), pra suportar projetos de outra linguagem.
- **nome_do_projeto**: texto — o valor de `[project] name` no `sentry.toml`.

## Caso: rejeita slug que escapa da pasta de specs

- **Requisito:** "`../..` no slug sairia de .sentry/specs e leria arquivo
  arbitrario"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** argumento_slug/caracteres-especiais
- **Dado:** um slug como `../../segredo`, apontando pra fora de `.sentry/specs/`
- **Quando:** `select_spec` resolve o caminho
- **Então:** levanta `ValueError` mencionando que o caminho aponta para fora
- **Entrada:** `argumento_slug = "../../segredo"`

## Caso: rejeita slug com caminho absoluto

- **Requisito:** "Caminho absoluto descartaria a base inteira no pathlib"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** argumento_slug/caracteres-especiais
- **Dado:** um slug que é um caminho absoluto do sistema de arquivos
- **Quando:** `select_spec` resolve o caminho
- **Então:** levanta `ValueError` mencionando que o caminho aponta para fora

## Caso: aceita slug valido

- **Requisito:** o caminho feliz da seleção por nome
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** argumento_slug/valido
- **Dado:** uma spec existente em `.sentry/specs/demo/CASES.md`
- **Quando:** `select_spec(root, "demo")` é chamado
- **Então:** devolve o caminho resolvido de `.sentry/specs/demo/CASES.md`
- **Entrada:** `argumento_slug = "demo"`

## Caso: sem slug e sem nenhuma spec, recusa com erro claro

- **Requisito:** sem slug e sem spec nenhuma, não há o que escolher
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** quantidade_de_specs/vazio
- **Dado:** `.sentry/specs/` existe mas está vazia
- **Quando:** `select_spec(root, None)` é chamado
- **Então:** levanta `ValueError` mencionando que nenhuma matriz de casos foi
  encontrada
- **Entrada:** `quantidade_de_specs = 0`

## Caso: sem slug e com mais de uma spec, pede para escolher com --spec

- **Requisito:** ambiguidade não pode ser resolvida em silêncio
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** quantidade_de_specs/valido
- **Dado:** duas specs (`demo-a`, `demo-b`) sob `.sentry/specs/`
- **Quando:** `select_spec(root, None)` é chamado
- **Então:** levanta `ValueError` mencionando que múltiplas specs foram
  encontradas
- **Entrada:** `quantidade_de_specs = 2`

## Caso: spec all junta casos de todas as pastas

- **Requisito:** "`--spec all` precisa somar os casos das duas pastas num
  veredito so, em vez de exigir escolher uma spec quando ha mais de uma"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** duas specs (`demo-a`, `demo-b`), cada uma com seu `CASES.md`
- **Quando:** `analyze(root, "all")` roda
- **Então:** o `Run` traz os casos das duas pastas somados, e `configuration.spec`
  lista as duas pelo nome

## Caso: spec all sem nenhuma pasta ainda recusa com erro claro

- **Requisito:** `--spec all` não inventa uma matriz vazia
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** quantidade_de_specs/vazio
- **Dado:** `.sentry/specs/` sem nenhuma pasta com `CASES.md`
- **Quando:** `analyze(root, "all")` roda
- **Então:** levanta `ValueError` mencionando que nenhuma matriz de casos foi
  encontrada

## Caso: severidade invalida no sentry.toml e ignorada, nao quebra a leitura

- **Requisito:** "Um valor de severidade que nao existe no enum nao pode
  derrubar a leitura do sentry.toml: a regra so fica sem sobrescrita, o resto
  da politica segue"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** valor_de_severidade/invalido
- **Dado:** `[policy.severities]` com uma chave valendo `"nivel-que-nao-existe"`
  e outra valendo `"baixa"`
- **Quando:** a política de severidade é lida
- **Então:** a entrada inválida some da política (sem sobrescrita), e a
  entrada válida é aplicada normalmente
- **Entrada:** `valor_de_severidade = "nivel-que-nao-existe"`

## Caso: arquivo em diretório excluído não entra no diff analisado

- **Requisito:** "frontend/ (ou outro diretorio fora do escopo) nao deve
  contar como codigo alterado: sem isso ele distorce impacto e cobertura do
  codigo alterado"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** exclude_declarado/valido
- **Dado:** `[analysis] exclude = ["frontend/"]` e um arquivo alterado dentro
  de `frontend/`
- **Quando:** `analyze(root)` roda
- **Então:** o arquivo excluído não aparece na lista de arquivos alterados do
  diff, enquanto arquivos fora do prefixo continuam aparecendo

## Caso: sem exclude declarado, nada é filtrado

- **Requisito:** "O padrao nao pode filtrar nada sem configuracao explicita:
  sem [analysis] exclude, ate um arquivo de outra stack continua no diff"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** exclude_declarado/vazio
- **Dado:** nenhum `[analysis] exclude` declarado, com arquivos alterados em
  mais de um diretório
- **Quando:** `analyze(root)` roda
- **Então:** todo arquivo alterado aparece no diff, sem nenhum ser removido

## Caso: projeto de outra stack mede cobertura pelo relatório que ele mesmo gera

- **Requisito:** "Um projeto Node/Go/Java gera lcov com a propria
  ferramenta; declarando [coverage] path, o Sentry mede cobertura alterada
  sem depender de coverage.py"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** stack_da_suite/valido
- **Dado:** `[coverage] path` apontando pra um `lcov.info` gerado fora do
  Sentry, com um arquivo `.js` alterado
- **Quando:** `analyze(root, run_tests=True)` roda
- **Então:** a cobertura do código alterado é calculada a partir do lcov
  declarado, sem erro e sem depender de coverage.py

## Caso: projeto de outra stack roda a propria suite e tem veredito real

- **Requisito:** "Fim a fim fora de Python: o projeto declara comando, junit
  e lcov; o Sentry executa, conta os testes e mede cobertura sem tocar em
  pytest"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** stack_da_suite/comando_declarado
- **Dado:** `[test] command` (um comando não-pytest), `junit_xml` e
  `[coverage] path` declarados
- **Quando:** `analyze(root, run_tests=True)` roda
- **Então:** os testes são contados a partir do JUnit gerado pelo comando
  declarado, a cobertura vem do lcov, sem erro de infraestrutura, e o
  veredito não sai inconclusivo

## Caso: classe nao aplicavel some dos achados e aparece como limitacao registrada

- **Requisito:** "Sem justificativa aceita, o Sentry cobraria 4 classes de
  'exclude' que nao fazem sentido para um parametro de configuracao. A
  justificativa remove o achado sem escondê-lo: ele fica registrado nas
  limitações do relatório"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Dado:** um `CASES.md` que declara `exclude/tamanho-maximo-excedido` e
  `exclude/caracteres-especiais` em "Classes não aplicáveis", mas não
  justifica `exclude/vazio`
- **Quando:** `analyze(root)` roda
- **Então:** as classes justificadas não geram achado `missing-equivalence-class`
  e aparecem em `configuration.justified_classes`; a classe não justificada
  (`vazio`) continua sendo cobrada como achado

## Caso: nome do projeto vem do toml, com o diretorio como fallback

- **Requisito:** "A chave [project] name existia no template do init mas
  nunca era lida: o relatorio sempre mostrava o nome do diretorio"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** nome_do_projeto/valido
- **Dado:** `[project] name = "cobranca-api"` declarado no `sentry.toml`
- **Quando:** `analyze(root)` roda
- **Então:** `run.project` é `"cobranca-api"`, não o nome do diretório
- **Entrada:** `nome_do_projeto = "cobranca-api"`

## Classes não aplicáveis

- **argumento_slug/vazio**: `None` é o próprio caminho de "nenhum slug
  passado", já coberto pelos casos de quantidade de specs — não é uma classe
  de erro à parte.
- **argumento_slug/tamanho-maximo-excedido**: o slug vem de um diretório
  real sob `.sentry/specs/`, cujo comprimento é limite do sistema de
  arquivos, não do Sentry.
- **quantidade_de_specs/negativo**: contagem de diretórios nunca é negativa.
- **quantidade_de_specs/nao-numerico**: é sempre `len()` de uma lista.
- **quantidade_de_specs/zero**: mesma contagem que a classe `vazio` (nenhuma
  spec sob `.sentry/specs/`) — já exercitada pelo caso "sem slug e sem
  nenhuma spec"; não é um valor numérico distinto a isolar.
- **quantidade_de_specs/limite-superior**: contagem de diretórios não tem
  teto próprio imposto pelo Sentry; quem limita é o sistema de arquivos.
- **valor_de_severidade/vazio**: uma chave sem valor não é TOML válido — o
  parser já recusaria antes de chegar na política.
- **valor_de_severidade/tamanho-maximo-excedido**: um de quatro valores
  fixos do enum `Severity`, não texto digitado com comprimento a limitar.
- **valor_de_severidade/caracteres-especiais**: idem — valor fechado do enum.
- **valor_de_severidade/valido**: o caminho de uma severidade reconhecida
  não é o que esta spec cobra — o comportamento em questão é justamente a
  entrada inválida ser ignorada; o caminho válido já é o padrão testado em
  todo o resto da suíte de `sentry.toml`.
- **exclude_declarado/caracteres-especiais**: os prefixos são comparados por
  `startswith` contra caminhos já normalizados pelo Git; não há caractere
  que mude o resultado.
- **stack_da_suite/vazio**: sem `[test] command` nem `[coverage] path`
  declarados, o Sentry usa o padrão pytest/coverage.py — já é o caminho
  feliz coberto noutras specs, não uma classe de erro aqui.
- **stack_da_suite/tamanho-maximo-excedido**: o valor é um comando de shell
  declarado pelo usuário no `sentry.toml`, sem limite próprio do Sentry.
- **stack_da_suite/caracteres-especiais**: idem — o comando é executado
  literalmente via subprocess, sem parsing que dependa de caractere
  específico.
- **nome_do_projeto/vazio**: testado no caso de fallback (nome do
  diretório), que é o caminho feliz da ausência, não uma classe de erro.
- **nome_do_projeto/tamanho-maximo-excedido**: o nome é texto livre do
  `sentry.toml`, sem limite próprio imposto pelo Sentry — quem limita é o
  próprio TOML/sistema de arquivos.
- **nome_do_projeto/caracteres-especiais**: idem — passa direto para o
  relatório como string, sem parsing adicional.
