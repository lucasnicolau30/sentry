# docs: sem repetição dos vídeos entre as abas

## Prompt

Com a aba "Vídeos" na documentação, o assunto estava repetido: a seção de versionamento do Setup e as entradas de `promo` e `training` em "Comandos e Habilidades" traziam o mesmo texto longo. Deixar a aba "Vídeos" como fonte única, encurtar os outros lugares remetendo a ela e corrigir a contagem de comandos, que dizia doze quando a CLI tem catorze.

Decisões do Lucas: a aba "Vídeos" é a fonte; os READMEs, o `AGENT-SENTRY.md` e o guia do agente continuam completos, porque são a referência da CLI em texto; a ressalva de que os vídeos gastam tokens, só quando o usuário pede, e de que o training não certifica fica também nas entradas dos comandos.

## Campos

- **texto_da_aba**: booleano — se o texto da aba de `DocsPage.tsx`, em cada idioma, traz o conteúdo declarado.

## Caso: o setup diz em poucas palavras onde ficam os videos e remete a aba de videos

- **Requisito:** "para que nao tenha repeticao e nem ruidos" — versionamento no Setup
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_da_aba/valido
- **Dado:** a seção "O que fica versionado" do Setup
- **Quando:** o texto é lido em português e em inglês
- **Então:** diz que o roteiro do training é versionado e que os vídeos de `.sentry/video/` ficam fora do Git por padrão, remete à aba "Vídeos" e não repete `!.sentry/video/`, `brag-output/` nem o `sentry clear`
- **Entrada:** `texto_da_aba = seção de versionamento do Setup, pt e en`

## Caso: as entradas de promo e training em comandos sao curtas e remetem a aba de videos

- **Requisito:** a aba "Vídeos" é a fonte única do assunto
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_da_aba/valido
- **Dado:** as entradas de `sentry promo` e `sentry training` em "Comandos e Habilidades"
- **Quando:** o texto é lido em português e em inglês
- **Então:** cada entrada diz o que o comando faz e onde grava o vídeo, mantém que gasta tokens, só quando o usuário pede, e (no training) que não certifica, e remete à aba "Vídeos" em vez de repetir requisitos e como alterar o vídeo
- **Entrada:** `texto_da_aba = entradas de promo e training, pt e en`

## Caso: a aba de comandos conta os catorze comandos da cli

- **Requisito:** "esse errinho de 12 para 14" — o texto de abertura dizia doze comandos
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_da_aba/valido
- **Dado:** o texto de abertura da aba "Comandos e Habilidades" e a lista de comandos da página
- **Quando:** o texto é lido em português e em inglês
- **Então:** diz "Catorze comandos" (EN: "Fourteen commands"), o mesmo número de comandos da lista da página e da CLI
- **Entrada:** `texto_da_aba = abertura da aba de comandos, pt e en`

## Caso: o card dos videos em comece aqui remete a aba de videos

- **Requisito:** "para que nao tenha repeticao" — o card resume e aponta para a fonte
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** baixa
- **Classe:** texto_da_aba/valido
- **Dado:** o card "Gere os vídeos" de "O que você pode fazer"
- **Quando:** o texto é lido em português e em inglês
- **Então:** mantém a ressalva de tokens e termina remetendo à aba "Vídeos"
- **Entrada:** `texto_da_aba = card dos vídeos, pt e en`

## Classes não aplicáveis

- **texto_da_aba/vazio**: o texto já existe na página; a ausência de texto é coberta pelos testes de documentação.
