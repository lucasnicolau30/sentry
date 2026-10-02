# Sentry promo

## Prompt

Novo comando `sentry promo` que usa a skill brag por baixo dos panos (`claude -p '/brag ...'`)
para gerar o vídeo promocional do projeto em `.sentry/video/`, PT por padrão e `--lang en`
opcional.

Decisões do Lucas: o brag é uma skill do Claude Code (não um binário), então o Sentry a
aciona por subprocess com `claude -p`. Se falta `claude` ou o `ffmpeg`, ou se o `claude -p`
falha, o comando para com erro claro e código de saída diferente de zero, sem
fallback silencioso. Se falta só a skill brag, o Sentry a instala (`claude plugin marketplace add
latent-spaces/brag` e `claude plugin install brag@brag`) e segue; se a instalação falha, para com
erro claro. `--lang en` roda o brag outra vez com o prompt em inglês, em vez de
traduzir legendas. O brag escreve em `brag-output/` (onde já há vídeos versionados); o
Sentry copia o `.mp4` novo para `.sentry/video/`, sem apagar o original.

## Campos

- **idioma**: idioma — o valor de `--lang`; `pt` por padrão, `en` opcional, qualquer outro
  é recusado.
- **claude_no_path**: booleano — se o executável `claude` é encontrado no PATH.
- **brag_instalado**: booleano — se a skill brag está instalada para o Claude Code; se não,
  o Sentry a instala antes de gerar o vídeo.
- **ffmpeg_no_path**: booleano — se o `ffmpeg` é encontrado no PATH.
- **saida_do_claude**: booleano — se o `claude -p` terminou com código zero e deixou um
  `.mp4` em `brag-output/`.

## Caso: promo gera o video em portugues por padrao

- **Requisito:** "gerar o vídeo promocional do projeto em `.sentry/video/`, PT por padrão"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** idioma/pt
- **Dado:** `claude`, brag e `ffmpeg` disponíveis, e um `claude` simulado que deixa um
  `.mp4` em `brag-output/`
- **Quando:** o usuário roda `sentry promo` sem `--lang`
- **Então:** o `claude -p` é chamado com `/brag` e um prompt em português, o `.mp4` é copiado
  para `.sentry/video/` e o comando sai com código zero informando o caminho
- **Entrada:** `idioma = pt`

## Caso: promo com lang en roda o brag de novo em ingles

- **Requisito:** "`--lang en` roda o brag outra vez com o prompt em inglês"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** idioma/en
- **Dado:** o vídeo em português já gerado em `.sentry/video/`
- **Quando:** o usuário roda `sentry promo --lang en`
- **Então:** o `claude -p` é chamado outra vez com prompt em inglês e o vídeo em inglês é
  gravado em arquivo distinto, sem sobrescrever o português
- **Entrada:** `idioma = en`

## Caso: promo recusa idioma desconhecido

- **Requisito:** "PT por padrão e `--lang en` opcional" — só esses dois idiomas existem
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** idioma/desconhecido
- **Dado:** nenhum pré-requisito além do projeto
- **Quando:** o usuário roda `sentry promo --lang fr`
- **Então:** o comando recusa listando `pt` e `en`, sai com código diferente de zero e não
  chama o `claude`
- **Entrada:** `idioma = fr`

## Caso: promo para quando o claude nao esta no PATH

- **Requisito:** "para com erro claro e código de saída diferente de zero, sem fallback
  silencioso"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** claude_no_path/ausente
- **Dado:** um PATH sem o executável `claude`
- **Quando:** o usuário roda `sentry promo`
- **Então:** o comando diz que falta o Claude Code e como instalar, sai com código diferente
  de zero e não cria nada em `.sentry/video/`
- **Entrada:** `claude_no_path = falso`

## Caso: promo instala o brag quando ele esta ausente

- **Requisito:** "Se falta só a skill brag, o Sentry a instala e segue" — quem nunca instalou
  o brag não precisa saber o comando de plugin
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** brag_instalado/ausente
- **Dado:** `claude` e `ffmpeg` no PATH e nenhuma skill brag instalada
- **Quando:** o usuário roda `sentry promo`
- **Então:** o Sentry avisa que vai instalar, roda `claude plugin marketplace add
  latent-spaces/brag` e `claude plugin install brag@brag`, e só então chama o `claude -p` e
  gera o vídeo
- **Entrada:** `brag_instalado = falso`

## Caso: promo para quando a instalacao do brag falha

- **Requisito:** "se a instalação falha, para com erro claro" — gerar sem a skill seria
  inventar um vídeo que o brag não fez
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** brag_instalado/instalacao-falhou
- **Dado:** `claude` e `ffmpeg` no PATH, nenhuma skill brag e um `claude plugin install` que
  sai com código diferente de zero
- **Quando:** o usuário roda `sentry promo`
- **Então:** o comando mostra o erro da instalação e como instalar à mão, sai com código
  diferente de zero e não chama o `claude -p`
- **Entrada:** `brag_instalado = instalacao-falhou`

## Caso: promo para quando o ffmpeg esta ausente

- **Requisito:** "para com erro claro e código de saída diferente de zero" quando falta o
  `ffmpeg`, pré-requisito do brag
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** ffmpeg_no_path/ausente
- **Dado:** `claude` e brag disponíveis e um PATH sem `ffmpeg`
- **Quando:** o usuário roda `sentry promo`
- **Então:** o comando diz que falta o `ffmpeg`, sai com código diferente de zero e não
  chama o `claude -p`
- **Entrada:** `ffmpeg_no_path = falso`

## Caso: promo propaga a falha do claude sem deixar video parcial

- **Requisito:** "se o `claude -p` falha, o comando para com erro claro e código de saída
  diferente de zero"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** saida_do_claude/falhou
- **Dado:** tudo disponível e um `claude` simulado que sai com código diferente de zero
- **Quando:** o usuário roda `sentry promo`
- **Então:** o comando mostra o erro do `claude`, sai com código diferente de zero e não
  deixa `.mp4` em `.sentry/video/`
- **Entrada:** `saida_do_claude = falhou`

## Caso: promo nao afirma sucesso quando o claude nao gerou o video

- **Requisito:** o comando só é bem-sucedido se existe um `.mp4`; sucesso sem arquivo seria
  afirmar o falso
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** saida_do_claude/sem-mp4
- **Dado:** um `claude` simulado que sai com código zero mas não escreve nenhum `.mp4`
- **Quando:** o usuário roda `sentry promo`
- **Então:** o comando informa que o vídeo não foi gerado e sai com código diferente de zero
- **Entrada:** `saida_do_claude = sem-mp4`

## Classes não aplicáveis

- **idioma/vazio**: `--lang` sem valor é recusado pelo argparse antes do Sentry agir; o
  default `pt` cobre a ausência da opção.
