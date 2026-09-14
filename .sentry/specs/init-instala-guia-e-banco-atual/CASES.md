# Init instala guia e banco na versão atual

## Prompt

Duas garantias do `sentry init` sem spec formal: (1) ele instala `AGENT-SENTRY.md` na
raiz do projeto (diferente da skill, que fica em `.claude/skills/` e só o Claude Code lê
— este arquivo é pra qualquer agente de IA capaz de rodar comandos de shell), mencionando
`sentry new` como próximo passo; (2) o banco `.sentry/sentry.db` sai do `init` já no
schema atual, com a tabela `runs` pronta (sem isso, `sentry history` antes de qualquer
`run` tocaria numa tabela inexistente), e um banco de versão anterior é migrado pra versão
atual sem perder dados existentes de outras tabelas.

## Campos

- **presenca_do_guia**: booleano — se `AGENT-SENTRY.md` existe na raiz do
  projeto depois do `init`.
- **versao_do_schema**: inteiro — o valor gravado em
  `schema_version.version` no `sentry.db`, comparado contra
  `CURRENT_SCHEMA_VERSION`.
- **dado_preexistente**: texto — conteúdo de uma tabela que já existia num
  banco de versão anterior, antes da migração.

## Caso: init instala o guia de agente na raiz do projeto

- **Requisito:** "Diferente da skill (.claude/skills, so Claude Code), este
  arquivo fica na raiz para qualquer agente de IA que consiga rodar
  comandos de shell ler"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** presenca_do_guia/valido
- **Dado:** um projeto novo, sem `AGENT-SENTRY.md`
- **Quando:** `sentry init` roda
- **Então:** `AGENT-SENTRY.md` é criado na raiz, mencionando `sentry new`, e
  aparece na lista do que foi criado; uma segunda execução não o recria
- **Entrada:** `presenca_do_guia = true`

## Caso: init cria o banco ja na versao atual, com a tabela runs pronta

- **Requisito:** "Sem isso, runs so era criada na primeira analise: sentry
  history antes de qualquer run tocaria numa tabela inexistente"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** versao_do_schema/valido
- **Dado:** um projeto novo, sem `sentry.db`
- **Quando:** `sentry init` roda
- **Então:** o banco criado já registra `CURRENT_SCHEMA_VERSION` em
  `schema_version`, e a tabela `runs` já existe (uma consulta contra ela
  não levanta `OperationalError`)

## Caso: banco de versao antiga e migrado sem perder dados existentes

- **Requisito:** "Simula um sentry.db criado por uma versao anterior, com
  schema_version mas sem a tabela runs: migrate precisa completar o schema
  sem apagar nada"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** dado_preexistente/valido
- **Dado:** um banco com `schema_version.version = 0` e uma tabela própria
  do usuário (`specs_marker`) com uma linha de dado
- **Quando:** `migrate(connection)` roda
- **Então:** `schema_version.version` passa a ser `CURRENT_SCHEMA_VERSION`,
  a tabela `runs` passa a existir, e a linha de `specs_marker` continua lá
  intacta
- **Entrada:** `dado_preexistente = "preserved"`

## Classes não aplicáveis

- **presenca_do_guia/vazio**: o `init` sempre escreve o arquivo com o
  mesmo conteúdo template; não existe um "guia vazio" a testar à parte.
- **versao_do_schema/vazio**: um banco recém-criado pelo `init` sempre
  grava uma versão; não existe banco sem linha em `schema_version` depois
  do `init` rodar.
- **versao_do_schema/nao-numerico**: a coluna é `INTEGER NOT NULL`; o
  próprio SQLite recusaria um valor não numérico.
- **versao_do_schema/negativo**: a versão só é incrementada pelo próprio
  código de migração, nunca decrementada nem escrita como negativa.
- **versao_do_schema/zero**: exercitada pelo `Dado` do caso de migração
  (banco criado com `schema_version.version = 0`), sem precisar de um caso
  isolado só pra esse valor.
- **versao_do_schema/limite-superior**: `CURRENT_SCHEMA_VERSION` é o próprio
  teto, incrementado pelo código conforme o schema evolui — não há valor
  acima dele a rejeitar.
- **dado_preexistente/vazio**: uma tabela vazia não perde nada na migração
  por definição — não há dado a verificar que sobreviveu.
- **dado_preexistente/caracteres-especiais**: o conteúdo é opaco pro
  Sentry (string qualquer gravada pelo usuário); `migrate` nunca inspeciona
  nem interpreta o valor, só preserva a tabela.
- **dado_preexistente/tamanho-maximo-excedido**: o conteúdo da tabela do
  usuário é opaco pro Sentry — `migrate` nunca lê nem limita seu conteúdo,
  só adiciona o que falta no schema.
