# home: seção do vídeo de apresentação

## Prompt

Adicionar na home uma nova área com o vídeo gerado pelo brag (apresentação do Sentry), em PT e EN conforme o idioma da página.

Decisões do Lucas: o layout refeito (janela, botão grande de assistir, brilho e chips) foi descartado por ficar demais, e o player voltou ao layout simples; a área é sobre o vídeo promocional (título "Vídeo promocional", não "em ação") e fica
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

- **Requisito:** "o usuário aperta o play"; a barra nativa foi trocada por uma barra própria, com o visual do site
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop
- **Quando:** a área do vídeo é exibida
- **Então:** o vídeo não tem `autoplay`, carrega só os metadados e a barra de controles tem progresso, tempo, volume e tela cheia
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

## Caso: o player sobe ao passar o mouse como os terminais

- **Requisito:** "coloca o hover ao passar o mouse como tem nos terminais" e "tira esse brilho, quero o comportamento do hover dos terminais"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** baixa
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop, com o mouse fora do player
- **Quando:** o mouse passa por cima do player
- **Então:** o player sobe alguns pixels, igual aos terminais da home, sem borda brilhante; ao tirar o mouse, ele volta
- **Entrada:** `viewport = desktop`

## Caso: o play do centro e verde com icone branco e alterna com o pause

- **Requisito:** "um play bonitinho no centro que o usuário apertasse, não aquele na borda esquerda inferior; verde e o svg em branco, o mesmo para o pause", "centraliza o svg" e "o botão não some"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop, com o vídeo parado
- **Quando:** o usuário clica no botão do centro, espera o vídeo tocar sem mexer o mouse, mexe o mouse e clica de novo
- **Então:** o botão é um círculo verde com o ícone branco centralizado; ao clicar o vídeo toca e o botão vira o de pausar, que some sozinho se o mouse fica parado e volta quando o mouse se mexe; o segundo clique pausa e o botão de assistir volta à vista
- **Entrada:** `viewport = desktop`

## Caso: os icones ficam verdes no hover e o volume e uma barra vertical

- **Requisito:** "o hover em verde só nos ícones, mas mantenha as sombras, e ponha a barra de volume vertical"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop, com a barra de controles à vista
- **Quando:** o mouse passa sobre o botão de volume e sobre o de tela cheia
- **Então:** o ícone vira verde e o botão mantém o fundo escuro translúcido; sobre o volume aparece uma barra vertical (mais alta que larga) e silenciar liga e desliga o som
- **Entrada:** `viewport = desktop`

## Classes não aplicáveis

- **viewport/tablet**: a área usa uma largura máxima fluida, igual às outras seções da home; entre o
  mobile e o desktop o comportamento é o mesmo, sem ponto de quebra próprio.
