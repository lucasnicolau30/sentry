Cobrir o nucleo de `application/analyze.py` que nunca tinha spec: selecao de spec por
slug (`select_spec`), o modo `--spec all`, a politica de severidade declarada em
`sentry.toml`, o filtro `[analysis] exclude`, o suporte a projetos de outra stack (lcov e
JUnit declarados em vez de coverage.py/pytest), o registro de classes de equivalencia nao
aplicaveis como limitacao (nao como achado escondido), e a leitura do nome do projeto em
`[project] name` com fallback pro nome do diretorio. Esses comportamentos ja existiam e ja
tinham teste, so nunca ganharam `## Caso:` formal -- os testes tinham marcador de cenario
apontando pro nada.
