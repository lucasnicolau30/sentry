# docs: o agente do vídeo é configurável e os textos não citam o Claude Code

## Prompt

Os documentos diziam que o `promo` e o `training` "exigem o Claude Code". Com o agente configurável (spec `video-com-agente-configuravel`), os textos devem dizer que o comando precisa do "agente configurado", ensinar a declarar `[video] agente` no `sentry.toml` e não apresentar nenhuma marca como requisito.

Decisões do Lucas: o Sentry não é uma IA presa a um modelo ou a uma empresa; o brag é uma skill de agente em geral; os textos dizem "o agente"; o padrão aparece como "Claude" (inicial maiúscula, sem destaque) na prosa; o comando real, `claude -p`, fica entre crases onde o texto mostra o que o Sentry executa quando nada é declarado. A skill `sentry-cases` do `init`, que o Sentry grava em `.claude/skills/`, não faz parte desta mudança.

## Campos

- **texto_do_documento**: booleano — se o texto do documento, em cada idioma, traz o conteúdo declarado.

## Caso: os documentos dizem que promo e training precisam do agente configurado

- **Requisito:** "o Sentry não é uma IA que se prende a um modelo ou empresa" — requisito dos comandos
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** texto_do_documento/valido
- **Dado:** a descrição de `sentry promo` e `sentry training` em `README.md`, `README.pt.md`, `AGENT-SENTRY.md`, no guia de `skills.py`, e a aba Vídeos de `DocsPage.tsx`
- **Quando:** o texto é lido
- **Então:** diz que o comando precisa do agente declarado em `[video] agente` (o `claude` por padrão) e do `ffmpeg`, e não afirma que exige o Claude Code
- **Entrada:** `texto_do_documento = README.md, README.pt.md, AGENT-SENTRY.md, guia do skills.py, DocsPage.tsx`

## Caso: a aba de videos ensina a declarar o agente

- **Requisito:** "os documentos passam a dizer o agente configurado"
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** texto_do_documento/valido
- **Dado:** a aba "Vídeos" de `DocsPage.tsx`
- **Quando:** o texto é lido em português e em inglês
- **Então:** há uma seção "Qual agente roda o brag" com o exemplo `[video] agente = [..., "{prompt}"]`, explicando que `{prompt}` marca onde entra o pedido, que o Sentry não procura nem instala o brag para um agente declarado e que um comando sem `{prompt}` é recusado
- **Entrada:** `texto_do_documento = seção do agente, pt e en`

## Caso: o exemplo de sentry toml dos documentos traz a secao video

- **Requisito:** a configuração nova precisa estar na referência do `sentry.toml`
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_do_documento/valido
- **Dado:** o exemplo de `sentry.toml` do `README.md`, do `README.pt.md` e da página Setup de `DocsPage.tsx`
- **Quando:** o texto é lido
- **Então:** cada um traz a seção `[video]` com a chave `agente`, marcada como opcional e com `claude` como padrão
- **Entrada:** `texto_do_documento = README.md, README.pt.md, DocsPage.tsx`

## Classes não aplicáveis

- **texto_do_documento/vazio**: os documentos já existem e descrevem os comandos; um documento vazio é coberto pelos testes de consistência.
