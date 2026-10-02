# docs: ressalva de zero IA e training nao certifica

## Prompt

Os documentos e o vídeo dizem "Zero chamada de IA" e que o Sentry nunca chama um modelo, mas `promo` e `training` rodam o agente e gastam tokens. Escrever a ressalva: o veredito não chama IA; os vídeos opcionais usam o agente (não "Claude Code"). E o `training` não certifica nada: só grava, não dá veredito; só o veredito certifica. Vale para README, guia do agente, DocsPage, FeatureGrid e a cena zero do vídeo.

Decisões do Lucas: a ressalva diz "o agente", nunca "Claude Code" (o pré-requisito técnico de
Claude Code nas descrições de `promo` e `training` saiu em 2026-10-02: o agente é configurável, ver `docs-agente-configuravel-do-video`). O
bloco `## Custo` do relatório continua afirmando zero tokens: ele descreve a análise do veredito,
que de fato não chama modelo.

## Campos

- **documento**: booleano — se o texto de cada documento (`README.md`, `README.pt.md`,
  `AGENT-SENTRY.md`, `DocsPage.tsx`, `FeatureGrid.tsx` e o guia de `skills.py`) traz a ressalva.

## Caso: documentos limitam o zero IA ao veredito e dizem que os videos usam o agente

- **Requisito:** "o veredito não chama IA; os vídeos opcionais usam o agente"
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** documento/valido
- **Dado:** os READMEs, a página de documentação e os cards da home
- **Quando:** o texto que afirma que o Sentry não chama modelo é lido
- **Então:** a afirmação vale só para o veredito e o texto diz que os vídeos opcionais usam o
  agente e gastam tokens, sem citar "Claude Code" na ressalva
- **Entrada:** `documento = README.md, README.pt.md, DocsPage.tsx, FeatureGrid.tsx`

## Caso: documentos dizem que o training nao certifica

- **Requisito:** "o training não certifica nada: só grava, não dá veredito; só o veredito certifica"
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** documento/valido
- **Dado:** os documentos que descrevem `sentry training`
- **Quando:** o texto da descrição do comando é lido
- **Então:** cada documento diz que o `training` não certifica nada e que só o veredito certifica
- **Entrada:** `documento = README.md, README.pt.md, AGENT-SENTRY.md, DocsPage.tsx, guia do skills.py`

## Classes não aplicáveis

- **documento/vazio**: os documentos já existem e descrevem os comandos; um documento vazio é
  coberto pelo teste de consistência dos comandos.
