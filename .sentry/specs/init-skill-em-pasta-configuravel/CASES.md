# init: a pasta da skill sentry-cases é configurável

## Prompt

O `sentry init` grava a skill `sentry-cases` só em `.claude/skills/`, com o caminho escrito fixo no código, e os textos a apresentam como "(Claude Code)". Uma skill (`SKILL.md`) é universal para agentes, mas cada agente lê a sua pasta. O Sentry não deve decidir por quem usa: a pasta passa a ser declarada pelo usuário, com `.claude/skills` só como padrão.

Decisões do Lucas: a opção recomendada, com a pasta no `sentry.toml` (`[init] skills_dirs`) mais a flag `--skills-dir`; a lista aceita mais de uma pasta; o `AGENT-SENTRY.md` na raiz continua sendo o caminho universal e não muda.

Decisões de desenho: sem declaração vale `.claude/skills`, para quem usa o Claude não ver mudança nenhuma; a flag `--skills-dir` (repetível) grava a escolha no `sentry.toml`, senão a próxima execução do `init` (o `sentry run` também o roda) recriaria `.claude/skills` e poluiria o projeto; se o `sentry.toml` já declara pastas diferentes, a flag é recusada com a instrução de editar o arquivo, em vez de sobrescrever uma escolha do usuário; pasta absoluta, com `..` ou vazia é recusada antes de gravar qualquer coisa; a skill gravada em qualquer pasta é arquivo gerado pelo Sentry e fica fora do diff, como já ficava em `.claude/skills/`.

## Campos

- **pastas_de_skills**: booleano — se as pastas da skill foram declaradas (no `sentry.toml` ou pela flag) em vez de usar o padrão.

## Caso: sem declaracao a skill vai para a pasta padrao

- **Requisito:** "o padrão continua `.claude/skills`" — quem usa o Claude não vê mudança
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** pastas_de_skills/valido
- **Dado:** um projeto sem `[init]` no `sentry.toml`
- **Quando:** o usuário roda `sentry init`
- **Então:** a skill é gravada em `.claude/skills/sentry-cases/SKILL.md` e em nenhuma outra pasta
- **Entrada:** `pastas_de_skills = falso`

## Caso: pasta declarada no sentry toml recebe a skill e a padrao nao e criada

- **Requisito:** "a pasta é configurável no sentry.toml"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** pastas_de_skills/valido
- **Dado:** um `sentry.toml` com `[init] skills_dirs = [".agentes/skills"]`
- **Quando:** o usuário roda `sentry init`
- **Então:** a skill é gravada em `.agentes/skills/sentry-cases/SKILL.md` e `.claude/skills` não é criada
- **Entrada:** `pastas_de_skills = verdadeiro`

## Caso: lista vazia nao grava skill e mantem o guia universal

- **Requisito:** quem só quer o `AGENT-SENTRY.md` não precisa de uma pasta de skill
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** pastas_de_skills/valido
- **Dado:** `[init] skills_dirs = []`
- **Quando:** o usuário roda `sentry init`
- **Então:** nenhuma skill é gravada e o `AGENT-SENTRY.md` na raiz continua sendo escrito
- **Entrada:** `pastas_de_skills = verdadeiro`

## Caso: varias pastas declaradas recebem a mesma skill

- **Requisito:** "a lista aceita mais de uma pasta" — um projeto com mais de um agente
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** pastas_de_skills/valido
- **Dado:** `skills_dirs = [".claude/skills", ".agentes/skills"]`
- **Quando:** o usuário roda `sentry init` duas vezes
- **Então:** as duas pastas têm o mesmo `SKILL.md`, e a segunda execução não regrava nada
- **Entrada:** `pastas_de_skills = verdadeiro`

## Caso: a flag skills-dir grava a escolha no sentry toml

- **Requisito:** "com a flag --skills-dir" — a escolha tem de sobreviver às próximas execuções do init
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** pastas_de_skills/valido
- **Dado:** um projeto novo e `sentry init --skills-dir .agentes/skills`
- **Quando:** o usuário roda o `init` com a flag e depois sem ela
- **Então:** o `sentry.toml` passa a declarar `[init] skills_dirs`, a skill fica em `.agentes/skills` e a execução sem a flag não cria `.claude/skills`
- **Entrada:** `pastas_de_skills = verdadeiro`

## Caso: a flag e recusada quando o sentry toml ja declara outras pastas

- **Requisito:** o Sentry não sobrescreve uma escolha que o usuário escreveu
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** pastas_de_skills/valido
- **Dado:** um `sentry.toml` que declara `skills_dirs = [".claude/skills"]` e `sentry init --skills-dir .agentes/skills`
- **Quando:** o `init` roda
- **Então:** sai com código de infraestrutura, diz para editar `[init] skills_dirs` no `sentry.toml` e não grava skill nem altera o arquivo
- **Entrada:** `pastas_de_skills = verdadeiro`

## Caso: pasta insegura e recusada antes de gravar qualquer coisa

- **Requisito:** a pasta vira caminho de arquivo; `..` e caminho absoluto gravariam fora do projeto
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** pastas_de_skills/valido
- **Dado:** `skills_dirs` com caminho absoluto, com `..`, com texto vazio ou que não é lista de textos (a lista vazia é válida: é o caso anterior)
- **Quando:** o usuário roda `sentry init`
- **Então:** sai com código de infraestrutura, a mensagem explica o formato esperado e nada é gravado fora do projeto
- **Entrada:** `pastas_de_skills = verdadeiro`

## Caso: skill em pasta declarada fica fora do diff como arquivo gerado

- **Requisito:** a skill é gerada pelo Sentry, em qualquer pasta, e não é mudança do usuário
- **Camada:** integração
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** pastas_de_skills/valido
- **Dado:** a skill `sentry-cases` gravada em `.agentes/skills/sentry-cases/SKILL.md` e outra skill do usuário na mesma pasta
- **Quando:** o diff do projeto é montado
- **Então:** a `sentry-cases` não aparece como alteração e a skill do usuário continua aparecendo
- **Entrada:** `pastas_de_skills = verdadeiro`

## Caso: o checklist do init mostra o caminho da skill sem citar uma marca

- **Requisito:** "pensa que uma skill é universal para agentes"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** pastas_de_skills/valido
- **Dado:** um `init` que grava a skill em duas pastas
- **Quando:** o checklist é impresso
- **Então:** a linha diz "Instalando skill" com os dois caminhos e não menciona Claude; numa reexecução sem nada novo a linha diz só "Skill"
- **Entrada:** `pastas_de_skills = verdadeiro`

## Classes não aplicáveis

- **pastas_de_skills/vazio**: é um booleano; a declaração vazia ou malformada é o caso "pasta insegura e recusada antes de gravar qualquer coisa".
