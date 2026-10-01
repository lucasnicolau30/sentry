# docs: refazer promo e training pedindo ao agente

## Prompt

Avisar nos documentos (README.md, README.pt.md, AGENT-SENTRY.md, DocsPage.tsx e o guia em skills.py) que, para alterar o vídeo do sentry promo ou do sentry training, o usuário não precisa rodar o comando de novo: deve pedir ao agente para mudar o script (o projeto do brag / o roteiro .sentry/training/<modulo>.json) até atingir o resultado desejado.

Decisões do Lucas: o `sentry promo` não ganha argumento de prompt (descartado); o aviso vive só
na documentação. Depois, pediu que o `DocsPage.tsx` também ganhe o aviso: como a página só citava
os nomes dos comandos, `promo` e `training` passam a ter entrada própria na referência de
comandos (PT e EN), com o aviso, e entram na faixa de comandos.

## Campos

- **documento**: booleano — se o texto de cada documento que descreve `promo` e `training`
  (`README.md`, `README.pt.md`, `AGENT-SENTRY.md`, `DocsPage.tsx` e o guia gerado por `skills.py`) traz o aviso.

## Caso: documentos dizem para pedir ao agente em vez de rodar promo de novo

- **Requisito:** "o usuário não precisa rodar o comando de novo: deve pedir ao agente para mudar o script" — promo
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** documento/valido
- **Dado:** os documentos que descrevem `sentry promo`
- **Quando:** o texto da descrição do comando é lido
- **Então:** cada documento diz que, para alterar o vídeo, basta pedir ao agente que mude o
  script, sem rodar `sentry promo` outra vez
- **Entrada:** `documento = README.md, README.pt.md, AGENT-SENTRY.md, DocsPage.tsx, guia do skills.py`

## Caso: documentos dizem para pedir ao agente em vez de rodar training de novo

- **Requisito:** "o mesmo para training" — o roteiro `.sentry/training/<modulo>.json`
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** documento/valido
- **Dado:** os documentos que descrevem `sentry training`
- **Quando:** o texto da descrição do comando é lido
- **Então:** cada documento diz que, para alterar o vídeo, basta pedir ao agente que ajuste o
  roteiro, sem rodar `sentry training` outra vez
- **Entrada:** `documento = README.md, README.pt.md, AGENT-SENTRY.md, DocsPage.tsx, guia do skills.py`

## Classes não aplicáveis

- **documento/vazio**: os documentos já existem e descrevem os dois comandos; um documento
  vazio é coberto pelo teste de consistência dos comandos.
