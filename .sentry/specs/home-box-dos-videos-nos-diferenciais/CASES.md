# home: box dos vídeos nos diferenciais

## Prompt

Adicionar nas boxes de diferenciais da home uma sexta box sobre os vídeos (sentry training e sentry promo), depois de Zero chamada de IA; no inglês, o vídeo promocional é o em inglês.

Decisões do Lucas: a box entra nas boxes de diferenciais, e não em "Como funciona" (os cinco passos são o
caminho do pedido até o veredito, e os vídeos não fazem parte dele). Fica logo depois de "Zero chamada de
IA no veredito", porque essa box já explica que só os vídeos opcionais gastam tokens. Com seis boxes o
grid fecha em três fileiras de duas colunas, então a box "Zero chamada de IA" deixa de ocupar a linha
inteira. O texto mantém o Sentry como ferramenta de testes: o vídeo mostra, só o veredito certifica. Diz com todas as letras que os vídeos gastam tokens (só quando o usuário pede) e segue o padrão das outras boxes: primeiro o problema, depois o que o Sentry faz.

## Campos

- **idioma**: idioma — o idioma da página (`pt` ou `en`), que escolhe o texto da box e o vídeo promocional.
- **viewport**: responsivo — a largura da tela em que a home é aberta.

## Caso: a box dos videos aparece depois de zero chamada de IA

- **Requisito:** "uma sexta box sobre os vídeos, depois de Zero chamada de IA"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** viewport/desktop
- **Dado:** a home aberta em português, em tela de desktop
- **Quando:** a página carrega
- **Então:** a última box dos diferenciais é "Vídeos prontos pelo próprio Sentry", logo depois de "Zero chamada de IA no veredito", e o texto, no mesmo padrão das outras boxes (o problema e depois o que o Sentry faz), cita `sentry training`, `sentry promo`, que os vídeos gastam tokens só quando o usuário pede, o pedido ao agente para mudar o vídeo e que só o veredito certifica
- **Entrada:** `viewport = desktop`, `idioma = pt`

## Caso: com seis boxes o grid fica em tres fileiras de duas colunas

- **Requisito:** "com 6 boxes, o grid de 2 colunas fecha em 3 fileiras iguais"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** viewport/desktop
- **Dado:** a home aberta em tela de desktop
- **Quando:** as boxes dos diferenciais são exibidas
- **Então:** são seis boxes em três fileiras de duas, todas com a mesma largura, e nenhuma ocupa a linha inteira
- **Entrada:** `viewport = desktop`

## Caso: em celular as boxes ficam em uma coluna

- **Requisito:** "a home já funciona em mobile"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** baixa
- **Classe:** viewport/mobile
- **Dado:** a home aberta em tela de celular de 375 px
- **Quando:** as boxes dos diferenciais são exibidas
- **Então:** as seis boxes ficam empilhadas em uma coluna, sem rolagem horizontal na página
- **Entrada:** `viewport = mobile`

## Caso: no ingles a box e o video promocional ficam em ingles

- **Requisito:** "no inglês, o vídeo promocional é o em inglês"
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** idioma/en
- **Dado:** a home aberta em português
- **Quando:** o usuário troca o idioma para inglês
- **Então:** a box passa a se chamar "Videos made by Sentry itself", com o texto em inglês, e o player da área de vídeo promocional aponta para o vídeo em inglês, com o pôster em inglês
- **Entrada:** `idioma = en`

## Classes não aplicáveis

- **viewport/tablet**: o grid usa duas colunas a partir do breakpoint `sm`, igual ao celular acima dele; entre
  `sm` e o desktop o comportamento é o mesmo do desktop.
