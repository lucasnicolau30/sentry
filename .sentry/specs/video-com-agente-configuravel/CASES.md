# vídeo: o agente que roda o brag é configurável

## Prompt

O `promo` e o `training` só funcionam com o binário `claude`: o Sentry roda `claude -p`, procura o `claude` no PATH e instala o brag pelo plugin dele. O Sentry não é uma IA presa a um modelo ou a uma empresa, e o brag é uma skill de agente em geral, não do Claude Code. Desacoplar: o comando do agente passa a ser configurável no `sentry.toml`, com o `claude` só como padrão.

Decisões do Lucas: a opção B, desacoplar de verdade; o comando do agente é declarado em `[video] agente` no `sentry.toml`; sem declaração o padrão continua sendo o `claude`; os documentos e os erros falam em "o agente"; o brag não é uma skill do Claude Code, só está em `.claude` porque o Lucas usa o Claude.

Decisões de desenho: `agente` é uma lista de argumentos e o texto `{prompt}` marca onde entra o pedido do brag (`agente = ["codex", "exec", "{prompt}"]`). Com agente declarado o Sentry não sabe onde ele guarda skills: não procura nem instala o brag (isso fica com o agente) e pede a skill pelo nome, sem a barra `/brag`, que é do `claude`. Sem declaração, vale o fluxo de antes: procura o brag em `.claude`, instala por `claude plugin` se faltar e libera as ferramentas do `claude -p`.

## Campos

- **agente_declarado**: booleano — se o `sentry.toml` declara `[video] agente`.

## Caso: promo roda o agente declarado no sentry toml

- **Requisito:** "o comando do agente vira configurável no sentry.toml" — promo
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** agente_declarado/valido
- **Dado:** um `sentry.toml` com `[video] agente = ["meu-agente", "--rodar", "{prompt}"]` e o executável no PATH
- **Quando:** o usuário roda `sentry promo`
- **Então:** o comando executado é o declarado, com `{prompt}` trocado pelo pedido, o pedido pede a skill brag pelo nome e não começa com `/brag`, e o vídeo vai para `.sentry/video/promo-pt.mp4`
- **Entrada:** `agente_declarado = verdadeiro`

## Caso: agente declarado dispensa procurar e instalar o brag do claude

- **Requisito:** "o brag é para qualquer agente" — o Sentry não sabe onde o agente declarado guarda skills
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** agente_declarado/valido
- **Dado:** um agente declarado e nenhuma skill brag em `.claude`
- **Quando:** o usuário roda `sentry promo`
- **Então:** o Sentry não instala nada, não roda `claude plugin` e aciona o agente declarado direto
- **Entrada:** `agente_declarado = verdadeiro`

## Caso: promo para quando o agente declarado nao esta no PATH

- **Requisito:** erro claro, sem fallback silencioso para o claude
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** agente_declarado/valido
- **Dado:** um agente declarado cujo executável não está no PATH, com o `claude` instalado
- **Quando:** o usuário roda `sentry promo`
- **Então:** sai com código de infraestrutura, diz que falta o agente e qual executável procurou, e não aciona o `claude` no lugar dele
- **Entrada:** `agente_declarado = verdadeiro`

## Caso: promo recusa agente declarado sem o marcador do pedido

- **Requisito:** um comando sem `{prompt}` rodaria sem receber o pedido do brag
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** agente_declarado/valido
- **Dado:** `[video] agente` que não é uma lista de textos, é uma lista vazia, tem um argumento vazio ou não traz `{prompt}` em nenhum argumento
- **Quando:** o usuário roda `sentry promo`
- **Então:** sai com código de infraestrutura e a mensagem explica o formato esperado, sem acionar agente nenhum
- **Entrada:** `agente_declarado = verdadeiro`

## Caso: training roda o agente declarado no sentry toml

- **Requisito:** o mesmo agente do promo serve ao training
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** agente_declarado/valido
- **Dado:** um agente declarado, um roteiro válido e o app respondendo
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o agente declarado é acionado com o pedido de treinamento, que pede a skill brag pelo nome, e o vídeo vai para `.sentry/video/training-cadastro-pt.mp4`
- **Entrada:** `agente_declarado = verdadeiro`

## Caso: sem agente declarado o padrao continua sendo o claude

- **Requisito:** "com claude como padrão" — nada muda para quem não configura
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** agente_declarado/valido
- **Dado:** um `sentry.toml` sem `[video]`
- **Quando:** o usuário roda `sentry promo`
- **Então:** o Sentry roda `claude -p` com o pedido começando em `/brag`, procura e instala o brag como antes
- **Entrada:** `agente_declarado = falso`

## Caso: as falhas do agente falam em agente e nao em Claude Code

- **Requisito:** "o erro fala em agente"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** agente_declarado/valido
- **Dado:** o agente padrão ausente do PATH, ou um agente que sai com código diferente de zero, não grava `.mp4` ou não executa
- **Quando:** o usuário roda `sentry promo`
- **Então:** a mensagem diz "agente", cita o executável entre crases e não menciona Claude Code
- **Entrada:** `agente_declarado = falso`

## Classes não aplicáveis

- **agente_declarado/vazio**: é um booleano; o valor declarado malformado é o caso "recusa agente declarado sem o marcador do pedido".
