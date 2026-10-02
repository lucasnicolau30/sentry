# docs: árvore do .sentry com training e media

## Prompt

A árvore de .sentry/ na documentação ainda não tem as pastas dos vídeos. Adicionar training/ (roteiros) e media/ (vídeos gerados por promo e training) e dizer na seção O que fica versionado o que vai para o Git.

Decisões do Lucas: a árvore da documentação (`DocsPage.tsx`) passa a mostrar `training/` com o roteiro
do módulo e `media/` com os vídeos de `promo` e `training`. Os roteiros são versionados (intenção
declarada, como as specs); `.sentry/video/` fica fora do Git por padrão, porque os vídeos podem ser regerados
(é o que o `.gitignore` gerado pelo `init` já faz). Em 2026-10-02 o pool `.sentry/media/` deixou de existir e a
pasta dos vídeos passou a se chamar `.sentry/video/`; o `sentry clear` não a toca. Depois, o Lucas pediu que a árvore mostrasse onde
ficam os `.mp4` e dissesse que eles podem ser versionados se o dev precisar: o brag grava o original em
`brag-output/`, na raiz do projeto, e o Sentry copia para `.sentry/video/`. Depois o Lucas escolheu a opção A: o
`init` passa a ignorar `brag-output/` (spec `init-ignora-a-pasta-de-trabalho-do-brag`), e a pasta oficial dos
vídeos vira só `.sentry/video/`.

## Campos

- **documento**: booleano — se a página de documentação mostra a árvore e a seção de versionamento com as
  pastas dos vídeos, em português e em inglês.

## Caso: a arvore do sentry mostra training e media

- **Requisito:** "adicionar training/ (roteiros) e media/ (vídeos gerados por promo e training)"
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** documento/valido
- **Dado:** a árvore de `.sentry/` da página de documentação
- **Quando:** o texto da árvore é lido
- **Então:** a árvore mostra `training/` com o arquivo `.json` do roteiro, `video/` com `promo-<idioma>.mp4` e `training-<modulo>-<idioma>.mp4` `composition/` e `share-copy.txt` (a saída do brag que o Sentry leva para lá) e, ao lado dos `.mp4`, a nota de que podem ser versionados; ao lado do roteiro de `training/`, a nota de que é o roteiro que gera o treinamento, e ao lado de `composition/`, a nota de que são o roteiro e a composição que geram o promo; e não mostra `brag-output/`, que é a pasta de trabalho do brag e fica ignorada pelo `init`
- **Entrada:** `documento = DocsPage.tsx`

## Caso: a secao o que fica versionado diz o que vai para o git

- **Requisito:** "dizer na seção O que fica versionado o que vai para o Git"
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** documento/valido
- **Dado:** a seção "O que fica versionado" da página de documentação
- **Quando:** o texto da seção é lido, em português e em inglês
- **Então:** a seção diz que os roteiros em `.sentry/training/` são versionados, que os vídeos de `promo` e `training` ficam em `.sentry/video/`, fora do Git, que `brag-output/` também fica fora do Git (o `init` o ignora), que quem precisar versionar um vídeo força a cópia de `.sentry/video/` com `git add -f` e que o `sentry clear` não toca nessa pasta
- **Entrada:** `documento = DocsPage.tsx`

## Classes não aplicáveis

- **documento/vazio**: o documento já existe e descreve a árvore; um documento vazio é coberto pelo teste de
  consistência dos comandos.
