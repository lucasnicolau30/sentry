# Docs consistentes

## Prompt

Consistencia entre os quatro documentos do Sentry (README.md, README.pt.md,
AGENT-SENTRY.md, frontend/src/components/DocsPage.tsx). Hoje eles divergem:
AGENT-SENTRY.md nunca menciona init/report/history/clear; DocsPage.tsx nunca menciona
review/watch/context e mostra um workflow de uma geracao atras
(init->new->check->run--run-tests->report->history); DocsPage.tsx tem um bug real no
exemplo de CASES.md (camada: unidade, que nao e valor valido de Layer, e sim de
TestType); README.md, README.pt.md e DocsPage.tsx listam so os 11 tipos escalares do
catalogo e omitem os 4 tipos de UI (formulario, navegacao, responsivo, acessibilidade);
AGENT-SENTRY.md lista Camada: backend | integracao sem frontend. A correcao inclui um
teste automatizado (tests/test_docs_consistency.py) que compara os quatro documentos
contra a fonte da verdade em codigo (cli.py build_parser() e o catalogo
FIELD_CLASSES/LAYERS), para a divergencia nao voltar em silencio depois da proxima
mudanca de CLI.

## Campos

- **comando_documentado**: texto — o nome de um subcomando real de `cli.py
  build_parser()` (`init, new, check, run, review, watch, status, context, report,
  history, clear`). Verificado por presença literal no texto de cada documento.
- **tipo_de_campo_documentado**: texto — uma chave do catálogo real
  (`FIELD_CLASSES`), incluindo os quatro tipos de UI. Verificado por presença literal
  na tabela de tipos de cada documento.
- **valor_de_camada_no_exemplo**: texto — o valor que segue `camada`/`layer` no
  snippet de exemplo de `CASES.md` mostrado no DocsPage.tsx. Só é válido quando é um
  dos três valores de `Layer`.

## Caso: todo comando do cli aparece no README.md

- **Requisito:** "o teste ... compara os quatro documentos contra a fonte da verdade
  em codigo"
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** comando_documentado/valido
- **Dado:** a lista de comandos de `cli.build_parser()`
- **Quando:** o teste de consistência lê `README.md`
- **Então:** todo comando aparece no texto do arquivo
- **Entrada:** `comando_documentado = "status"`

## Caso: todo comando do cli aparece no README.pt.md

- **Requisito:** mesma garantia na versão em português
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** comando_documentado/valido
- **Dado:** a lista de comandos de `cli.build_parser()`
- **Quando:** o teste de consistência lê `README.pt.md`
- **Então:** todo comando aparece no texto do arquivo
- **Entrada:** `comando_documentado = "status"`

## Caso: todo comando do cli aparece no AGENT-SENTRY.md

- **Requisito:** "AGENT-SENTRY.md nunca menciona init/report/history/clear"
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** crítica
- **Classe:** comando_documentado/valido
- **Dado:** a lista de comandos de `cli.build_parser()`
- **Quando:** o teste de consistência lê `AGENT-SENTRY.md` (o guia instalado em todo
  projeto por `sentry init`)
- **Então:** todo comando aparece no texto do arquivo
- **Entrada:** `comando_documentado = "init"`

## Caso: todo comando do cli aparece no DocsPage.tsx

- **Requisito:** "DocsPage.tsx nunca menciona review/watch/context e mostra um
  workflow de uma geracao atras"
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** crítica
- **Classe:** comando_documentado/valido
- **Dado:** a lista de comandos de `cli.build_parser()`
- **Quando:** o teste de consistência lê `frontend/src/components/DocsPage.tsx`
- **Então:** todo comando aparece no texto do arquivo
- **Entrada:** `comando_documentado = "review"`

## Caso: todo tipo de campo do catalogo aparece na tabela do README.md

- **Requisito:** "listam so os 11 tipos escalares do catalogo e omitem os 4 tipos de
  UI"
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** tipo_de_campo_documentado/valido
- **Dado:** as chaves de `FIELD_CLASSES`, incluindo `formulario`, `navegacao`,
  `responsivo`, `acessibilidade`
- **Quando:** o teste de consistência lê `README.md`
- **Então:** toda chave aparece no texto do arquivo
- **Entrada:** `tipo_de_campo_documentado = "acessibilidade"`

## Caso: todo tipo de campo do catalogo aparece na tabela do README.pt.md

- **Requisito:** mesma garantia na versão em português
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** tipo_de_campo_documentado/valido
- **Dado:** as chaves de `FIELD_CLASSES`
- **Quando:** o teste de consistência lê `README.pt.md`
- **Então:** toda chave aparece no texto do arquivo
- **Entrada:** `tipo_de_campo_documentado = "acessibilidade"`

## Caso: todo tipo de campo do catalogo aparece na tabela do DocsPage.tsx

- **Requisito:** mesma garantia na landing page
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** tipo_de_campo_documentado/valido
- **Dado:** as chaves de `FIELD_CLASSES`
- **Quando:** o teste de consistência lê `DocsPage.tsx`
- **Então:** toda chave aparece no texto do arquivo
- **Entrada:** `tipo_de_campo_documentado = "acessibilidade"`

## Caso: o valor de camada no exemplo do DocsPage.tsx e uma camada valida

- **Requisito:** "DocsPage.tsx tem um bug real no exemplo de CASES.md (camada:
  unidade, que nao e valor valido de Layer, e sim de TestType)"
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** crítica
- **Classe:** valor_de_camada_no_exemplo/valido
- **Dado:** o snippet de exemplo de `CASES.md` embutido em `DocsPage.tsx`
- **Quando:** o teste de consistência extrai o valor após `camada`/`layer` nesse
  snippet
- **Então:** o valor é um dos três valores de `Layer` (`backend`, `integração`,
  `frontend`)
- **Entrada:** `valor_de_camada_no_exemplo = "backend"`

## Classes não aplicáveis

- **comando_documentado/vazio**: a lista de comandos vem sempre de
  `cli.build_parser()`, que nunca está vazia — não existe Sentry sem nenhum
  subcomando.
- **comando_documentado/tamanho-maximo-excedido**: nome de subcomando é escolhido
  pelo código, não texto digitado com comprimento a limitar.
- **comando_documentado/caracteres-especiais**: idem — nomes de comando são
  identificadores simples, sem caractere especial possível.
- **tipo_de_campo_documentado/vazio**: `FIELD_CLASSES` nunca está vazio — é o
  catálogo embutido no pacote.
- **tipo_de_campo_documentado/tamanho-maximo-excedido**: idem
  `comando_documentado` — chave de catálogo, não texto digitado.
- **tipo_de_campo_documentado/caracteres-especiais**: idem — chaves são
  identificadores simples em minúsculas.
- **valor_de_camada_no_exemplo/vazio**: o snippet de exemplo sempre declara um
  valor para `camada`; um exemplo sem valor nenhum seria um defeito de outra
  natureza, não desta verificação.
- **valor_de_camada_no_exemplo/tamanho-maximo-excedido**: o valor é um de três
  enumerados, não texto livre com comprimento a limitar.
- **valor_de_camada_no_exemplo/caracteres-especiais**: idem — valor fechado do
  enum `Layer`.
