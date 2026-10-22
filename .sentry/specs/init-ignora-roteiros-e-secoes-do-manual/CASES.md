# init ignora roteiros e seções do manual

## Prompt

o sentry init passa a gravar no .gitignore do usuario os roteiros do training e as secoes do manual, e todas as entradas vao agrupadas, cada grupo com o seu comentario

Decisões do Lucas: os roteiros do `training` (`.sentry/training/`) e as seções do manual escritas à mão
(`.sentry/manual/secoes/`) não precisam ir ao Git; isso vale também para os projetos que usam o Sentry, então o
`init` grava as duas linhas no `.gitignore` do usuário. O `.gitignore` sai separado em blocos, cada um com o seu
comentário e uma linha em branco entre eles, no mesmo padrão do `.gitignore` deste repositório. Quem quiser
versionar escreve `!.sentry/training/` ou `!.sentry/manual/secoes/`, e o `init` respeita, como já faz com os vídeos.

## Campos

- **gitignore**: booleano — o conteúdo do `.gitignore` do projeto depois do `init`: as entradas do Sentry, agrupadas em blocos com comentário.

## Caso: gitignore novo nasce em blocos comentados e ignora roteiros e secoes do manual

- **Requisito:** "o init grava no .gitignore do usuário os roteiros do training e as seções do manual, cada grupo com o seu comentário"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** gitignore/valido
- **Dado:** um projeto sem `.gitignore`
- **Quando:** o usuário roda `sentry init` duas vezes
- **Então:** o `.gitignore` criado traz `.sentry/training/` e `.sentry/manual/secoes/` sob um comentário próprio, os três blocos (estado local, vídeos, roteiros e seções) separados por uma linha em branco, cada um com o seu comentário acima das entradas; a segunda execução não muda nada
- **Entrada:** `gitignore = sem arquivo`

## Caso: gitignore existente ganha os blocos que faltam sem repetir comentario nem perder as linhas do usuario

- **Requisito:** o `init` só acrescenta ao `.gitignore`; não mexe no que o dev já escreveu
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** gitignore/valido
- **Dado:** um `.gitignore` com linhas do usuário e só parte de um bloco do Sentry (por exemplo, `brag-output/` sem o comentário nem `.sentry/video/`)
- **Quando:** o usuário roda `sentry init` duas vezes
- **Então:** as linhas do usuário continuam intactas, cada entrada do Sentry aparece uma única vez, os blocos que faltavam chegam com o comentário e o bloco que já estava parcialmente ali só recebe a entrada que faltava, sem comentário repetido
- **Entrada:** `gitignore = arquivo com linhas do usuário e parte de um bloco`

## Caso: init respeita quem versiona roteiros e secoes do manual

- **Requisito:** "quem quiser versionar escreve `!.sentry/training/` ou `!.sentry/manual/secoes/`" e o `init` não ignora de novo
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** gitignore/valido
- **Dado:** um `.gitignore` com as linhas `!.sentry/training/` e `!.sentry/manual/secoes/`, escritas pelo dev
- **Quando:** o usuário roda `sentry init` duas vezes
- **Então:** o `init` não acrescenta `.sentry/training/` nem `.sentry/manual/secoes/`, nem o comentário desse bloco, mantém as duas negações uma única vez e continua acrescentando as outras entradas dele
- **Entrada:** `gitignore = arquivo com as duas negações`

## Caso: alteracao so com linhas e comentarios do init continua sendo do sentry

- **Requisito:** a análise de diff não pode tratar como mudança do usuário o `.gitignore` que só tem o que o `init` escreveu, agora com os comentários
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** gitignore/valido
- **Dado:** um projeto recém inicializado, cujo `.gitignore` só tem as entradas e os comentários do `init`
- **Quando:** a análise decide se o `.gitignore` é um arquivo intocado do `init`
- **Então:** ele é reconhecido como arquivo do `init`, fora da lista de mudanças a revisar; com uma linha a mais, do usuário, deixa de ser
- **Entrada:** `gitignore = entradas e comentários do init`

## Classes não aplicáveis

- **gitignore/vazio**: um `.gitignore` vazio é o mesmo caminho de um projeto sem `.gitignore`, que o primeiro caso cobre.
