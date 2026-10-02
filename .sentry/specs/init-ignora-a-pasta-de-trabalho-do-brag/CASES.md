# init ignora a pasta de trabalho do brag

## Prompt

O sentry init passa a ignorar brag-output/ no .gitignore, e a pasta oficial dos vídeos de promo e training vira só .sentry/media/. O brag-output/ guarda o material de trabalho do brag e aparecia como não rastreado no projeto do dev.

Decisões do Lucas: opção A. `brag-output/` é a pasta de trabalho do brag (composição, planos, legendas e
vídeos soltos) e deixa de aparecer como "não rastreada" no projeto do dev. O `promo` e o `training`
continuam copiando o vídeo final para `.sentry/video/`, que passa a ser a pasta oficial dos vídeos. Quem
precisar versionar um vídeo força a cópia com `git add -f`. O `init` só acrescenta a linha ao `.gitignore`;
não mexe no que o dev já escreveu nem apaga arquivos. Em 2026-10-02 o Lucas decidiu que `brag-output/` é ignorado
nos dois lados (neste repositório também) e que o pool `.sentry/media/` deixa de existir.

## Campos

- **gitignore**: booleano — se o `.gitignore` do projeto tem a linha `brag-output/` depois do `init`.

## Caso: gitignore novo nasce ignorando a pasta de trabalho do brag

- **Requisito:** "o sentry init passa a ignorar brag-output/"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** gitignore/valido
- **Dado:** um projeto sem `.gitignore`
- **Quando:** o usuário roda `sentry init`
- **Então:** o `.gitignore` criado ignora `brag-output/` e `.sentry/video/`, não ignora `.sentry/media/`, e continua sem ignorar `.sentry/specs/` nem o relatório atual
- **Entrada:** `gitignore = sem arquivo`

## Caso: gitignore existente ganha a linha sem duplicar e sem perder as do usuario

- **Requisito:** "o sentry init passa a ignorar brag-output/" num projeto que já tinha `.gitignore`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** gitignore/valido
- **Dado:** um `.gitignore` com linhas do usuário e sem `brag-output/`
- **Quando:** o usuário roda `sentry init` duas vezes
- **Então:** a linha `brag-output/` aparece uma única vez e as linhas do usuário continuam intactas
- **Entrada:** `gitignore = arquivo com linhas do usuário`

## Caso: alteracao so com linhas do init continua sendo do sentry

- **Requisito:** "o init só acrescenta a linha ao .gitignore" — a análise de diff não pode tratar isso como mudança do usuário
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** gitignore/valido
- **Dado:** um projeto recém inicializado, cujo `.gitignore` só tem as linhas do `init`, incluindo `brag-output/`
- **Quando:** a análise decide se o `.gitignore` é um arquivo intocado do `init`
- **Então:** ele é reconhecido como arquivo do `init`, e portanto fora da lista de mudanças a revisar
- **Entrada:** `gitignore = só linhas do init`

## Caso: init remove a linha obsoleta do pool media

- **Requisito:** "o pool `.sentry/media/` deixou de existir" — projetos que já tinham a linha no `.gitignore` não devem carregá-la para sempre
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** gitignore/valido
- **Dado:** um `.gitignore` com linhas do usuário e a linha `.sentry/media/`, escrita por uma versão antiga do `init`
- **Quando:** o usuário roda `sentry init`
- **Então:** a linha `.sentry/media/` some, `.sentry/video/` é acrescentada e as linhas do usuário continuam intactas
- **Entrada:** `gitignore = arquivo com .sentry/media/`

## Caso: init respeita quem versiona a pasta de videos de proposito

- **Requisito:** "pode ser versionado se o dev tiver essa necessidade" — o dev que quer `.sentry/video/` no Git (como este repositório) escreve `!.sentry/video/` e o `init` não o ignora de novo
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** gitignore/valido
- **Dado:** um `.gitignore` com a linha `!.sentry/video/`, escrita pelo dev
- **Quando:** o usuário roda `sentry init` duas vezes
- **Então:** o `init` não acrescenta `.sentry/video/`, mantém `!.sentry/video/` uma única vez e continua acrescentando as outras linhas dele, como `brag-output/`
- **Entrada:** `gitignore = arquivo com !.sentry/video/`

## Classes não aplicáveis

- **gitignore/vazio**: um `.gitignore` vazio é o mesmo caminho de um projeto sem `.gitignore`, que o primeiro caso cobre.
