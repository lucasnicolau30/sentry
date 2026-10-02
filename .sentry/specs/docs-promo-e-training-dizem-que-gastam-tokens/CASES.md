# docs: promo e training dizem que gastam tokens

## Prompt

Os documentos descrevem promo e training mas não dizem que eles gastam tokens (usam o agente), só quando o usuário pede. Alinhar README, guia do agente, AGENT-SENTRY.md e DocsPage com o que as boxes e a cena zero do vídeo já dizem.

Decisões do Lucas: o texto fala em "gastar tokens" com todas as letras, e que isso só acontece quando o
usuário pede. A afirmação de "zero IA" continua valendo só para o veredito.

## Campos

- **documento**: booleano — se o texto de cada documento (`README.md`, `README.pt.md`, `AGENT-SENTRY.md`,
  o guia de `skills.py` e `DocsPage.tsx`) diz que o comando gasta tokens.

## Caso: documentos dizem que o promo gasta tokens so quando o usuario pede

- **Requisito:** "alinhar os documentos: promo e training gastam tokens, só quando o usuário pede" — promo
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** documento/valido
- **Dado:** os documentos que descrevem `sentry promo`
- **Quando:** o texto da descrição do comando é lido
- **Então:** cada documento diz que o comando roda o agente e gasta tokens, só quando o usuário pede
- **Entrada:** `documento = README.md, README.pt.md, AGENT-SENTRY.md, guia do skills.py, DocsPage.tsx`

## Caso: documentos dizem que o training gasta tokens so quando o usuario pede

- **Requisito:** "alinhar os documentos: promo e training gastam tokens, só quando o usuário pede" — training
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** documento/valido
- **Dado:** os documentos que descrevem `sentry training`
- **Quando:** o texto da descrição do comando é lido
- **Então:** cada documento diz que o comando roda o agente e gasta tokens, só quando o usuário pede
- **Entrada:** `documento = README.md, README.pt.md, AGENT-SENTRY.md, guia do skills.py, DocsPage.tsx`

## Classes não aplicáveis

- **documento/vazio**: os documentos já existem e descrevem os comandos; um documento vazio é coberto pelo
  teste de consistência dos comandos.
