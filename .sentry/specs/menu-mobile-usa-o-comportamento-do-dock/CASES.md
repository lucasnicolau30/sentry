# Menu mobile usa o comportamento do dock

## Prompt

na responsividade ao abrir o sanduiche os botoes ainda estao com o comportamento antigo (pilula com brilho glow-btn) e nao o novo do dock do desktop: textos/icones soltos, divisorias, sublinhado no hover e shake no clique

## Campos

- **menu-mobile**: responsivo — abre pelo hambúrguer em viewport mobile

## Caso: menu mobile mostra os itens do dock sem pílula

- **Requisito:** ao abrir o sanduíche, PT, GitHub, PyPI e Docs aparecem soltos, como no dock do desktop, sem fundo/borda de botão com brilho
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** menu-mobile/mobile
- **Dado:** viewport de 390px de largura, landing carregada em `/`
- **Quando:** o botão "Abrir menu" é clicado
- **Então:** os itens "Toggle language", "GitHub", "PyPI" e "Docs" do menu ficam visíveis, sem a classe `glow-btn`, e com divisórias entre eles

## Caso: menu mobile troca o idioma pelo item do dock

- **Requisito:** o item de idioma do menu mobile mantém a função de alternar PT/EN
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** menu-mobile/mobile
- **Dado:** viewport de 390px de largura, menu aberto, idioma em PT
- **Quando:** o item "Toggle language" é clicado
- **Então:** o texto do item passa de "PT" para "EN"

## Classes não aplicáveis

- **menu-mobile/tablet**: o menu hambúrguer só existe abaixo do breakpoint `sm`; acima dele vale o dock do desktop
- **menu-mobile/desktop**: o dock do desktop já está coberto e não muda neste pedido
