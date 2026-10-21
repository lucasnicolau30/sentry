# Sentry manual

## Prompt

Comando `sentry manual <modulo> [--lang pt|en]`: lê o roteiro `.sentry/training/<modulo>.json` e gera
um manual em PDF só de texto (fpdf2), sem vídeo, sem imagem de tela e sem agente. Saída em
`.sentry/manual/<modulo>-<idioma>.pdf`.

Decisões do Lucas: o manual é a mesma pegada do vídeo de treinamento, sem o vídeo: o fluxo vem do
mesmo roteiro. O PDF tem um cabeçalho padrão, no molde, com a logo e o nome da aplicação, e as cores
são as do app descrito (não as do Sentry): o Sentry lê da própria página de `base`, no Playwright, o
nome (`application-name`, `og:site_name` ou `<title>`), a cor (`theme-color` ou o fundo do primeiro
botão colorido) e a logo (o ícone da página, só PNG ou JPEG). O app de `base` precisa estar no ar. O
PDF abre com um título grande, "MANUAL USUARIO" (escrito como "MANUAL DO USUÁRIO"), numa faixa na cor do
app; os passos são cartões numa linha do tempo (selo redondo numerado, ligado ao seguinte por uma
linha); toda página tem rodapé com a página à esquerda e o nome do app à direita.

Em 2026-10-21 o Lucas tirou a seção "Antes de começar" (a lista dos campos a preencher): "não gosto
desse negócio". Sem ela, o Sentry deixou de reproduzir o fluxo no Playwright e de ler rótulos de campo;
da página de `base` sai só a identidade. O `training` e o roteiro não mudam.

## Campos

- **modulo**: nome — o nome do módulo; localiza `.sentry/training/<modulo>.json`.
- **roteiro**: arquivo — o mesmo JSON do `training`, com `base`, `titulo` e `passos`.
- **passo**: roteiro — um item de `passos` com `titulo`, `fala` e `acao`; vira um cartão do manual.
- **fala**: roteiro — o texto de instrução de um passo; vai para o PDF como está.
- **idioma**: idioma — o valor de `--lang`; `pt` por padrão, `en` opcional; só traduz os textos fixos do
  manual, não as falas.
- **app_na_base**: booleano — se a URL `base` do roteiro responde; é sempre exigido, porque a
  identidade do app é lida dela.
- **identidade**: leitura — nome, cor e logo do app, lidos da página de `base`: nome de
  `application-name`, `og:site_name` ou `<title>`; cor de `theme-color` ou do fundo do primeiro
  botão colorido; logo do ícone da página (PNG ou JPEG).
- **logo**: arquivo — o ícone da página de `base`; só PNG ou JPEG entram no PDF, qualquer outra
  coisa (ou falha ao baixar) deixa o cabeçalho só com o nome.
- **cabecalho**: leitura — o molde repetido no topo de toda página do PDF: logo, nome do app e um
  filete na cor do app.
- **capa**: leitura — a faixa de título da primeira página: `MANUAL DO USUÁRIO` (EN: `USER MANUAL`) e,
  embaixo, o título do roteiro, na cor do app.
- **rodape**: leitura — o molde repetido no pé de toda página: `Página N de TOTAL` à esquerda e o nome
  do app à direita.
- **dependencias**: ambiente — `claude` e `ffmpeg` não são usados; o `fpdf2` vem com o pacote.
- **pdf**: arquivo — `.sentry/manual/<modulo>-<idioma>.pdf`.

## Caso: so a pagina de base e lida e o fluxo nao e reproduzido

- **Requisito:** do app o Sentry lê só a identidade; o fluxo do roteiro vira texto, não é executado
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** app_na_base/so-a-base
- **Dado:** um roteiro com um passo `clicar` num elemento que não existe na página, e o app no ar
- **Quando:** a identidade do app é lida
- **Então:** a leitura não falha (o clique não foi executado) e devolve a identidade do app
- **Entrada:** `acoes = clicar #nao-existe`

## Caso: manual de roteiro valido e gravado em pdf

- **Requisito:** "gera um manual em PDF" em `.sentry/manual/<modulo>-<idioma>.pdf`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** roteiro/valido
- **Dado:** `.sentry/training/cadastro.json` com `base`, `titulo` e passos completos
- **Quando:** o usuário roda `sentry manual cadastro`
- **Então:** `.sentry/manual/cadastro-pt.pdf` existe, começa com `%PDF`, e o comando sai com 0
- **Entrada:** `modulo = cadastro`

## Caso: manual traz titulo e os passos na ordem do roteiro

- **Requisito:** "o passo a passo com título e fala"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** passo/valido
- **Dado:** um roteiro com três passos, cada um com `titulo` e `fala`
- **Quando:** o conteúdo do manual é montado
- **Então:** o título do roteiro abre o manual, e cada passo aparece numerado, na ordem declarada,
  com o seu título e a sua fala; o manual não tem a seção "Antes de começar" nem o valor de exemplo
  dos passos `digitar`
- **Entrada:** `passos = 3`

## Caso: identidade vem de application-name theme-color e icone

- **Requisito:** "o nome da aplicação" e as cores do app, lidos da página
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** identidade/declarada
- **Dado:** uma página com `application-name` "Loja Verde", `theme-color` `#15803d` e um ícone PNG,
  e um `<title>` diferente do nome
- **Quando:** a identidade do app é lida
- **Então:** o nome é `Loja Verde` (e não o `<title>`), a cor é RGB 21, 128, 61 e o logo é o PNG do ícone
- **Entrada:** `application-name = Loja Verde`

## Caso: cor cai no fundo do primeiro botao colorido

- **Requisito:** as cores do app, mesmo quando a página não declara `theme-color`
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** identidade/sem-theme-color
- **Dado:** uma página sem `theme-color`, com um link de fundo branco e depois um botão de fundo
  `#0a66c2`
- **Quando:** a identidade do app é lida
- **Então:** a cor é RGB 10, 102, 194 (o link branco é ignorado) e o nome vem do `<title>`
- **Entrada:** `botao = #0a66c2`

## Caso: app sem identidade declarada usa titulo e cor padrao

- **Requisito:** o cabeçalho sempre existe, mesmo num app que não declara nada
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** identidade/ausente
- **Dado:** uma página só com `<title>`, sem `theme-color`, sem botão colorido e sem ícone
- **Quando:** a identidade do app é lida
- **Então:** o nome é o `<title>`, a cor é o cinza padrão e não há logo
- **Entrada:** `title = Só o Título`

## Caso: logo que nao e png nem jpeg fica de fora

- **Requisito:** o PDF só embute PNG e JPEG; o logo é enfeite e não derruba o manual
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** logo/formato-invalido
- **Dado:** um ícone que responde HTML, um endereço que não é http(s), um endereço vazio e um endereço
  em que ninguém responde
- **Quando:** o logo é baixado
- **Então:** nenhum deles vira logo (o resultado é vazio, sem exceção); um PNG válido é aceito
- **Entrada:** `logo = javascript:alert(1)`

## Caso: cabecalho com logo e nome do app em toda pagina

- **Requisito:** "um cabeçalho padrão com a logo e o nome da aplicação, no molde do PDF"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** cabecalho/todas-as-paginas
- **Dado:** um manual longo, de pelo menos duas páginas, para um app de nome `Loja Verde`, cor
  `#15803d` e logo PNG
- **Quando:** o PDF é montado
- **Então:** cada página traz o nome `Loja Verde` e a imagem do logo, e o PDF usa a cor do app
- **Entrada:** `paginas = 2`

## Caso: cor clara demais e escurecida para o texto

- **Requisito:** as cores do app no PDF, sem comprometer a leitura sobre o fundo branco
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** cabecalho/cor-clara
- **Dado:** um app de cor `#39ff14` (verde neon)
- **Quando:** o PDF é montado
- **Então:** o filete do cabeçalho mantém a cor do app e os títulos usam uma versão mais escura,
  legível sobre o branco; uma cor escura é usada como está
- **Entrada:** `cor = #39ff14`

## Caso: app fora do ar e recusado

- **Requisito:** a identidade do app é lida da página de `base`; sem app no ar não há de onde ler
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** app_na_base/fora-do-ar
- **Dado:** nada respondendo na URL de `base`
- **Quando:** o usuário roda `sentry manual`
- **Então:** o comando sai com código 3, o erro pede para subir o app, e nenhum PDF é gravado
- **Entrada:** `base = http://127.0.0.1:8100`

## Caso: manual nao aciona agente nem ffmpeg

- **Requisito:** "sem vídeo, sem imagem e sem agente"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** dependencias/sem-agente
- **Dado:** um ambiente sem `claude` nem `ffmpeg` no PATH
- **Quando:** o usuário roda `sentry manual cadastro`
- **Então:** o manual é gerado, nenhum subprocesso é executado e nenhum token é gasto
- **Entrada:** `agente = ausente`

## Caso: manual recusa modulo com separador de caminho

- **Requisito:** o nome do módulo vira nome de arquivo; `../` ou `/` permitiria ler e gravar fora
  das pastas do Sentry
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** modulo/caracteres-especiais
- **Dado:** um arquivo JSON existente fora de `.sentry/training/`
- **Quando:** o usuário roda `sentry manual ../../segredo`
- **Então:** o comando recusa o nome, sai com código diferente de zero e não lê nem grava nada
- **Entrada:** `modulo = ../../segredo`

## Caso: manual recusa modulo sem roteiro

- **Requisito:** "lê o roteiro `.sentry/training/<modulo>.json`"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** modulo/inexistente
- **Dado:** nenhum arquivo `.sentry/training/inexistente.json`
- **Quando:** o usuário roda `sentry manual inexistente`
- **Então:** o comando sai com código 3 e o erro cita `.sentry/training/inexistente.json`
- **Entrada:** `modulo = inexistente`

## Caso: roteiro invalido e recusado dizendo o passo

- **Requisito:** o manual usa o mesmo roteiro e a mesma validação do `training`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** roteiro/invalido
- **Dado:** um roteiro cujo passo 3 não tem `fala`
- **Quando:** o usuário roda `sentry manual semfala`
- **Então:** o comando sai com código 3, o erro diz `passo 3: campo 'fala'` e nenhum PDF é gravado
- **Entrada:** `passo 3 = sem fala`

## Caso: idioma desconhecido e recusado

- **Requisito:** `[--lang pt|en]`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** idioma/desconhecido
- **Dado:** um roteiro válido
- **Quando:** o usuário roda `sentry manual cadastro --lang fr`
- **Então:** o comando sai com código 3, o erro lista `pt, en` e nenhum PDF é gravado
- **Entrada:** `idioma = fr`

## Caso: lang en gera o manual com titulos fixos em ingles

- **Requisito:** saída em `.sentry/manual/<modulo>-<idioma>.pdf`; `--lang en` opcional
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** idioma/en
- **Dado:** um roteiro válido
- **Quando:** o usuário roda `sentry manual cadastro --lang en`
- **Então:** `.sentry/manual/cadastro-en.pdf` existe e traz `USER MANUAL` e `Step by step`
  no lugar de `MANUAL DO USUÁRIO` e `Passo a passo`; as falas ficam como no roteiro
- **Entrada:** `idioma = en`

## Caso: texto fora do latin-1 nao derruba o pdf

- **Requisito:** gerar o PDF com `fpdf2`, cujas fontes embutidas só têm latin-1
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** fala/caracteres-especiais
- **Dado:** uma `fala` com travessão, aspas curvas, reticências e um emoji
- **Quando:** o manual é gerado
- **Então:** o PDF é gravado; travessão, aspas e reticências viram o equivalente simples, e o
  caractere sem equivalente vira `?`, sem exceção
- **Entrada:** `fala = Clique — “Salvar”… 🙂`

## Caso: capa traz MANUAL DO USUARIO e o titulo do roteiro

- **Requisito:** "um titulo maiorzao MANUAL USUARIO"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** capa/titulo
- **Dado:** um roteiro de título "Como criar uma conta"
- **Quando:** o manual é gerado em português e em inglês
- **Então:** a primeira página traz `MANUAL DO USUÁRIO` (EN: `USER MANUAL`) numa faixa na cor do app,
  com o título do roteiro embaixo; o texto da faixa é branco sobre cor escura e escuro sobre cor clara
- **Entrada:** `idioma = pt, en`

## Caso: rodape traz pagina e nome do app em toda pagina

- **Requisito:** "um rodape com o nome da aplicacao a direita"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** rodape/todas-as-paginas
- **Dado:** um manual longo, de pelo menos duas páginas, para um app de nome `Loja Verde`
- **Quando:** o PDF é montado
- **Então:** cada página termina com `Página N de TOTAL` à esquerda (EN: `Page N of TOTAL`) e o nome do app
  à direita, além do nome no cabeçalho
- **Entrada:** `paginas = 2`

## Caso: titulo da capa e centralizado e a logo vira marca d'agua na faixa

- **Requisito:** "centraliza manual do usuario" e "a logo da aplicacao como uma sombra" no canto direito
  da faixa
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** capa/marca-dagua
- **Dado:** um app com logo PNG e outro sem logo
- **Quando:** o manual é montado
- **Então:** o título `MANUAL DO USUÁRIO` e o título do roteiro ficam centralizados na faixa; com logo,
  ela aparece translúcida (opacidade 0,14), enorme e cortada pelas bordas, no canto direito da faixa; sem
  logo, a faixa não tem marca
- **Entrada:** `logo = png`

## Caso: marca d'agua tira o fundo solido do logo

- **Requisito:** "tipo esse escudo do flamengo": a logo enorme, tom sobre tom, sem moldura, cortada pelas
  bordas da faixa
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** capa/fundo-do-logo
- **Dado:** logos PNG de fundo escuro sólido (RGB e RGBA opaco), de fundo claro sólido e transparente;
  e arquivos que não dão para ler (JPEG, 16 bits, paleta com transparência, PNG cortado)
- **Quando:** o manual é montado e o fundo de cada logo é lido
- **Então:** o fundo escuro entra com mesclagem `Screen` e o claro com `Multiply`, de modo que o fundo
  some e só o desenho aparece; o logo transparente entra sem mesclagem; o que não dá para ler entra sem
  mesclagem, sem exceção
- **Entrada:** `logo = png fundo preto`

## Classes não aplicáveis

- **idioma/vazio**: `--lang` sem valor é recusado pelo argparse antes do Sentry agir; o default
  `pt` cobre a ausência da opção.
- **modulo/vazio**: o argumento posicional é obrigatório no argparse.
- **modulo/tamanho-maximo-excedido**: a validação do nome do módulo é a mesma do `training`
  (`validar_modulo`), já coberta na spec `sentry-training`.
