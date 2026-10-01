# home: seção do vídeo de apresentação

## Prompt

Adicionar na home uma nova área com o vídeo gerado pelo brag (apresentação do Sentry), em PT e EN conforme o idioma da página.

Decisões do Lucas: o layout do player foi refeito (janela com os três pontos, botão grande de assistir sobre o pôster, brilho verde e chips); a área é sobre o vídeo promocional (título "Vídeo promocional", não "em ação") e fica
no fim da home, como a última área. Usa o vídeo do brag (`brag.mp4` em PT,
`brag-en.mp4` em EN). Para a web, o vídeo é servido em versão leve (1280 px, cerca de 2 MB) copiada
para `frontend/public/video/`; os originais continuam em `brag-output/`. O vídeo não toca sozinho: o
usuário aperta o play.

## Campos

- **idioma**: idioma — o idioma da página (`pt` ou `en`), que escolhe o arquivo do vídeo e o texto da área.
- **viewport**: responsivo — a largura da tela em que a home é aberta.

## Caso: home mostra a area do video com titulo e player

- **Requisito:** "Adicionar na home uma nova área com o vídeo gerado pelo brag"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** viewport/desktop
- **Dado:** a home aberta em português, em tela de desktop
- **Quando:** a página carrega
- **Então:** aparece a área "Vídeo promocional" com um player de vídeo que aponta para o vídeo em português
- **Entrada:** `viewport = desktop`, `idioma = pt`

## Caso: o video nao toca sozinho e tem controles

- **Requisito:** "o usuário aperta o play"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop
- **Quando:** a área do vídeo é exibida
- **Então:** o player tem controles, não tem `autoplay` e carrega só os metadados
- **Entrada:** `viewport = desktop`

## Caso: o video e o texto trocam com o idioma da pagina

- **Requisito:** "em PT e EN conforme o idioma da página"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** idioma/en
- **Dado:** a home aberta em português com o vídeo em português
- **Quando:** o usuário troca o idioma para inglês
- **Então:** o título vira "Promo video" e o player passa a apontar para o vídeo em inglês
- **Entrada:** `idioma = en`

## Caso: em celular o player cabe na tela

- **Requisito:** "uma nova área na home" — a home já funciona em mobile
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/mobile
- **Dado:** a home aberta em tela de celular de 375 px
- **Quando:** a área do vídeo é exibida
- **Então:** o player ocupa a largura da área sem criar rolagem horizontal na página
- **Entrada:** `viewport = mobile`

## Caso: a area do video e a ultima da home

- **Requisito:** "ponha como última coisa"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop
- **Quando:** a página carrega
- **Então:** a área do vídeo promocional é a última seção da home, depois de todas as outras
- **Entrada:** `viewport = desktop`

## Caso: o poster tem um botao grande de assistir que some ao dar play

- **Requisito:** "melhorar esse layout do vídeo, tá muito fraco" — o player ganha um botão de assistir em destaque
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop, com o vídeo parado no pôster
- **Quando:** o usuário clica no botão grande de assistir
- **Então:** o vídeo começa a tocar e o botão grande some
- **Entrada:** `viewport = desktop`

## Caso: a area mostra a duracao, os idiomas e o comando que gera o video

- **Requisito:** "melhorar esse layout do vídeo, tá muito fraco" — a área explica de onde vem o vídeo
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** baixa
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop
- **Quando:** a área do vídeo é exibida
- **Então:** aparecem os chips com a duração (1:06 min), os idiomas (PT e EN) e o comando `sentry promo`, e o aviso de que o vídeo se muda pedindo ao agente
- **Entrada:** `viewport = desktop`

## Classes não aplicáveis

- **viewport/tablet**: a área usa uma largura máxima fluida, igual às outras seções da home; entre o
  mobile e o desktop o comportamento é o mesmo, sem ponto de quebra próprio.
