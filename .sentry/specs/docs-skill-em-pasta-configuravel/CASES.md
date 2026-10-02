# docs: a skill vai para a pasta que o usuário declara, sem citar uma marca

## Prompt

Com a pasta da skill `sentry-cases` configurável (spec `init-skill-em-pasta-configuravel`), os documentos não podem mais dizer que ela é "do Claude Code" nem que fica sempre em `.claude/skills/`. Atualizar README, guia do agente e `DocsPage.tsx`.

Decisões do Lucas: uma skill é universal para agentes; o `.claude/skills` aparece só como o padrão, com o caminho real, porque é onde o `init` grava quando nada é declarado; o `AGENT-SENTRY.md` na raiz continua sendo o caminho universal. Aproveita-se a rodada para corrigir os READMEs, que ainda diziam que o projeto do brag fica em `brag-output/`, pasta que o `promo` deixa vazia.

## Campos

- **texto_do_documento**: booleano — se o texto do documento, em cada idioma, traz o conteúdo declarado.

## Caso: os documentos dizem que a skill vai para a pasta declarada e nao e de uma marca

- **Requisito:** "pensa que uma skill é universal para agentes" — descrição da skill
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** texto_do_documento/valido
- **Dado:** a descrição da skill `sentry-cases` em `README.md`, `README.pt.md` e na página Setup e Comandos de `DocsPage.tsx`
- **Quando:** o texto é lido em português e em inglês
- **Então:** diz que a skill vai para a pasta de `[init] skills_dirs` (padrão `.claude/skills`), que o agente que lê skills dessa pasta a carrega, e não atribui a skill a um agente ou empresa
- **Entrada:** `texto_do_documento = README.md, README.pt.md, DocsPage.tsx`

## Caso: as descricoes do init trazem a flag skills-dir

- **Requisito:** "com a flag --skills-dir"
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_do_documento/valido
- **Dado:** a descrição de `sentry init` em `README.md`, `README.pt.md`, `AGENT-SENTRY.md`, no guia de `skills.py` e em `DocsPage.tsx`
- **Quando:** o texto é lido
- **Então:** cita `--skills-dir` e que a escolha fica registrada em `[init] skills_dirs`
- **Entrada:** `texto_do_documento = README.md, README.pt.md, AGENT-SENTRY.md, guia do skills.py, DocsPage.tsx`

## Caso: o exemplo de sentry toml traz a secao init

- **Requisito:** a configuração nova precisa estar na referência do `sentry.toml`
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_do_documento/valido
- **Dado:** o exemplo de `sentry.toml` do `README.md`, do `README.pt.md` e da página Setup de `DocsPage.tsx`
- **Quando:** o texto é lido
- **Então:** cada um traz a seção `[init]` com `skills_dirs`, marcada como opcional e com `.claude/skills` como padrão
- **Entrada:** `texto_do_documento = README.md, README.pt.md, DocsPage.tsx`

## Caso: os readmes apontam o projeto do brag para a pasta de videos

- **Requisito:** depois do `promo`, `brag-output/` fica vazia e o projeto do brag está em `.sentry/video/`
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_do_documento/valido
- **Dado:** a descrição de `sentry promo` em `README.md` e `README.pt.md`
- **Quando:** o texto de "como alterar o vídeo" é lido
- **Então:** diz que o projeto do brag está em `.sentry/video/` e não em `brag-output/`
- **Entrada:** `texto_do_documento = README.md, README.pt.md`

## Classes não aplicáveis

- **texto_do_documento/vazio**: os documentos já existem e descrevem os comandos; um documento vazio é coberto pelos testes de consistência.
