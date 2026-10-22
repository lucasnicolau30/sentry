# Sentry manual

## Prompt

Comando `sentry manual [<modulo>] [--lang pt|en]`: mantém o manual do usuário do projeto, um PDF só
(`.sentry/manual/manual-<idioma>.pdf`) com uma seção por módulo, só texto (fpdf2), sem vídeo, sem imagem de
tela e sem agente.

Decisões do Lucas: o manual é a mesma pegada do vídeo de treinamento, sem o vídeo: os passos vêm do mesmo
roteiro (`.sentry/training/<modulo>.json`). O PDF tem um cabeçalho padrão, no molde, com a logo e o nome da
aplicação, e as cores são as do app descrito (não as do Sentry): o Sentry lê da própria página de `base`, no
Playwright, o nome (`application-name`, `og:site_name` ou `<title>`), a cor (`theme-color` ou o fundo do
primeiro botão colorido) e a logo (o ícone da página, só PNG ou JPEG). O app de `base` precisa estar no ar.
O PDF abre com um título grande, "MANUAL USUARIO" (escrito como "MANUAL DO USUÁRIO"), numa faixa na cor do app;
os passos são cartões com o selo redondo numerado dentro; toda página tem
rodapé com a página à esquerda e o nome do app à direita.

Em 2026-10-21 o Lucas tirou a seção "Antes de começar": "não gosto desse negócio". Em 2026-10-22 pediu o
manual como documento vivo, "em que o dev vá atualizando a partir dos módulos que eu crio", no estilo do
manual "Integra" que mostrou (seções, introdução, avisos coloridos, cartões lado a lado, nomes de botões em
negrito) e "parecido com o training e isso do markdown": cada módulo é uma seção em Markdown
(`.sentry/manual/secoes/<modulo>.md`), os passos são sincronizados do roteiro a cada `sentry manual <modulo>`
e o resto é escrito à mão ou pelo agente e nunca é tocado. O Sentry não aciona agente.

## Campos

- **modulo**: nome — o módulo a criar ou atualizar no manual; localiza `.sentry/training/<modulo>.json`. Opcional:
  sem ele, atualiza os passos de todas as seções.
- **roteiro**: arquivo — o mesmo JSON do `training`, com `base`, `titulo` e `passos`; é de onde vêm os passos.
- **secao**: arquivo — `.sentry/manual/secoes/<modulo>.md`, fora do Git por padrão (o `init` o ignora): bloco do topo (`modulo`, `ordem`), `# título`
  e blocos (parágrafo, `##`, aviso, `:::cartoes`, `:::passos`).
- **markdown**: formato — só o que `manual_md.py` entende; o resto vira parágrafo; erro sai com `arquivo:linha`.
- **idioma**: idioma — o valor de `--lang`; `pt` por padrão, `en` opcional; só traduz os textos fixos do
  manual, não o que está nas seções.
- **app_na_base**: booleano — se a URL `base` do primeiro módulo responde; é sempre exigido, porque a
  identidade do app é lida dela.
- **identidade**: leitura — nome, cor e logo do app, lidos da página de `base`: nome de
  `application-name`, `og:site_name` ou `<title>`; cor de `theme-color` ou do fundo do primeiro
  botão colorido; logo do ícone da página (PNG ou JPEG).
- **logo**: arquivo — o ícone da página de `base`; só PNG ou JPEG entram no PDF, qualquer outra
  coisa (ou falha ao baixar) deixa o cabeçalho só com o nome.
- **cabecalho**: leitura — o molde repetido no topo de toda página: logo, nome do app, "Seção N" à direita
  dentro de uma seção e um filete na cor do app.
- **capa**: leitura — a primeira página: faixa `MANUAL DO USUÁRIO` (EN: `USER MANUAL`) com o nome do app, a data
  de geração e, com duas seções ou mais, o sumário.
- **rodape**: leitura — o molde repetido no pé de toda página (na capa, "Manual vigente · versão X" à direita): o app em negrito e "Manual do usuário" à esquerda, `Página N de TOTAL` no meio e, da segunda página em diante, "Voltar ao sumário" (ou "Voltar ao início", sem sumário) à direita, como link só do tamanho do texto.
- **passo_so_video**: roteiro — um passo com `"manual": false` no roteiro: o `training` o grava, o manual o pula
  (preparo que se repete em todo módulo, como entrar no sistema).
- **fala**: leitura — o texto de instrução de um passo, vindo do roteiro; vai para o PDF como está, só em latin-1.
- **selo**: leitura — a bolinha numerada dentro do cartão de cada passo (e a do fecho, com o visto).
- **orientacao**: leitura — o que diz ao leitor onde ele está: data de geração, "Seção N" no cabeçalho, marcadores
  do PDF e o fecho "Fim do passo a passo".
- **sumario**: leitura — a lista das seções na capa, com a página e o link de cada uma; só com duas seções ou mais.
- **aviso**: leitura — a caixa `> [!INFO]`, `> [!SUCESSO]` ou `> [!ATENCAO]`, na cor de significado do tipo.
- **cartoes**: leitura — o bloco `:::cartoes`, em duas colunas.
- **acessibilidade**: leitura — título, autor e idioma que o PDF declara para leitores de tela.
- **dependencias**: ambiente — `claude` e `ffmpeg` não são usados; o `fpdf2` vem com o pacote.
- **pdf**: arquivo — `.sentry/manual/manual-<idioma>.pdf`.

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

- **Requisito:** saída em `.sentry/manual/manual-<idioma>.pdf`; `--lang en` opcional
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** idioma/en
- **Dado:** um roteiro válido
- **Quando:** o usuário roda `sentry manual cadastro --lang en`
- **Então:** `.sentry/manual/manual-en.pdf` existe e traz `USER MANUAL`, `SECTION 1` e `Step by step`
  no lugar de `MANUAL DO USUÁRIO`, `SEÇÃO 1` e `Passo a passo`; as falas ficam como no roteiro
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

## Caso: rodape traz pagina e nome do app em toda pagina

- **Requisito:** "um rodape com o nome da aplicacao"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** rodape/todas-as-paginas
- **Dado:** um manual longo, de pelo menos duas páginas, para um app de nome `Loja Verde`
- **Quando:** o PDF é montado
- **Então:** cada página termina com `Página N de TOTAL` (EN: `Page N of TOTAL`) e o nome do app, além do nome no cabeçalho
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
- **Então:** o título `MANUAL DO USUÁRIO` e o nome do app ficam centralizados na faixa; com logo,
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

## Caso: capa traz so a data de geracao sob a faixa

- **Requisito:** Nielsen 1, visibilidade do status: o leitor sabe se o manual é recente; sem contagem de passos, que não ajuda a decidir nada
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** orientacao/data
- **Dado:** um roteiro de 4 passos, em português e em inglês
- **Quando:** o conteúdo do manual é montado numa data conhecida
- **Então:** uma linha centralizada sob a faixa diz só "Gerado em" e a data, no formato do idioma
  (`22/10/2026` em PT, `2026-10-22` em EN); a capa não traz a quantidade de passos
- **Entrada:** `hoje = 2026-10-22`

## Caso: cada passo vira marcador do pdf

- **Requisito:** Nielsen 7: o leitor de PDF navega pelos passos no painel lateral, sem pesar no papel
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** orientacao/passo
- **Dado:** um roteiro de 4 passos
- **Quando:** o manual é montado
- **Então:** o PDF tem um marcador `n. título` por passo, na ordem
- **Entrada:** `passos = 4`

## Caso: linha do tempo fecha com fim do passo a passo junto do ultimo passo

- **Requisito:** Nielsen 3 e 10: o leitor sabe que acabou e tem para onde ir; o fecho nunca fica órfão
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** orientacao/fecho
- **Dado:** roteiros de 1 a 30 passos (as quebras de página caem em lugares diferentes) e um em inglês
- **Quando:** o manual é montado
- **Então:** a última página sempre traz "Fim do passo a passo" junto do último passo, nunca sozinho; em inglês,
  "End of the step by step"
- **Entrada:** `passos = 1..30`

## Caso: numero do passo fica no centro exato do selo

- **Requisito:** o número dentro da bolinha (1, 7, 10, 11) fica no meio dela, na horizontal e na vertical,
  inclusive os de dois dígitos
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** selo/alinhamento
- **Dado:** selos com número de um e de dois dígitos
- **Quando:** o número é desenhado no selo
- **Então:** o meio do texto coincide com o centro do selo na horizontal, e o meio da altura dos algarismos
  com o centro na vertical, com tolerância de 0,3 pt
- **Entrada:** `n = 1, 7, 10, 11`

## Caso: manual de roteiro valido e gravado em pdf

- **Requisito:** "gera um manual em PDF": um PDF só do projeto, `.sentry/manual/manual-<idioma>.pdf`, e a seção do módulo em Markdown
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** roteiro/valido
- **Dado:** `.sentry/training/cadastro.json` com `base`, `titulo` e passos completos e nenhuma seção ainda
- **Quando:** o usuário roda `sentry manual cadastro`
- **Então:** a seção `.sentry/manual/secoes/cadastro.md` é criada, `.sentry/manual/manual-pt.pdf` existe e começa com `%PDF`, o comando diz as duas coisas e sai com 0
- **Entrada:** `modulo = cadastro`

## Caso: manual traz titulo e os passos na ordem do roteiro

- **Requisito:** os passos do roteiro viram o bloco `:::passos` da seção e os cartões do PDF, na ordem do roteiro
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** roteiro/passos
- **Dado:** o roteiro `cadastro` com 4 passos
- **Quando:** a seção é criada e o manual é gerado
- **Então:** a seção começa com o bloco do topo (`modulo`, `ordem: 1`) e o título do roteiro (`# Como criar uma conta`); o bloco `:::passos` tem `n. título` e a fala recuada, na ordem; o PDF mostra os títulos na mesma ordem, sem "Antes de começar" e sem os valores digitados no fluxo
- **Entrada:** `passos = 4`

## Caso: secao nova nasce do roteiro com a ordem seguinte

- **Requisito:** "o dev vai atualizando a partir dos módulos que eu crio": cada módulo novo vira uma seção nova
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** secao/nova
- **Dado:** uma seção `cadastro` já criada (ordem 1) e um segundo roteiro, `entrada`
- **Quando:** o usuário roda `sentry manual entrada`
- **Então:** nasce `secoes/entrada.md` com `ordem: 2`, o título do roteiro e comentários que ensinam a escrever introdução, avisos e cartões; a seção anterior não muda
- **Entrada:** `modulo = entrada`

## Caso: atualizar os passos preserva o que foi escrito a mao

- **Requisito:** o documento é vivo: o roteiro muda, os passos acompanham; a introdução e os avisos do autor ficam
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** secao/atualizacao
- **Dado:** uma seção com introdução em negrito e um aviso escritos à mão, e o roteiro com uma fala trocada e um passo novo
- **Quando:** o usuário roda `sentry manual cadastro` de novo
- **Então:** o que foi escrito à mão fica intacto; o bloco `:::passos` é trocado (fala nova, passo 5 novo, fala velha sumiu) e há um só bloco `:::passos` no arquivo
- **Entrada:** `roteiro.passos[1].fala = nova; passos + 1`

## Caso: manual sem modulo atualiza todas as secoes

- **Requisito:** `sentry manual` sem módulo refaz o manual inteiro a partir dos roteiros
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** secao/todas
- **Dado:** duas seções criadas e o roteiro de uma delas com o título de um passo trocado
- **Quando:** o usuário roda `sentry manual` sem módulo
- **Então:** os passos de todas as seções são atualizados, o comando só diz o PDF (nenhuma seção é criada) e o PDF traz o passo novo
- **Entrada:** `modulo = (nenhum)`

## Caso: passo marcado como so do video fica fora do manual

- **Requisito:** "toda hora fala, loga na aplicação": o preparo que só o vídeo precisa não entra no manual
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** passo_so_video/marcado
- **Dado:** um roteiro com o primeiro passo `"manual": false`; depois um com `"manual": "nao"`; depois um com todos os passos `false`
- **Quando:** o usuário roda `sentry manual cadastro`
- **Então:** o passo marcado não está no bloco `:::passos` nem no PDF e a numeração recomeça em 1; o roteiro continua
  válido para o `training`; `"manual"` que não é booleano é recusado dizendo o passo; com todos os passos
  marcados o manual sai com 3 dizendo que precisa de pelo menos um
- **Entrada:** `manual = false, "nao", todos false`

## Caso: secoes saem na ordem declarada

- **Requisito:** a ordem do manual é a da chave `ordem`: primeiro as que têm, depois as outras pelo nome do módulo
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** secao/ordem
- **Dado:** três seções, uma com `ordem: 9`, uma com `ordem: 2` e uma sem `ordem`
- **Quando:** as seções são listadas e o PDF é gerado
- **Então:** a lista vem `b` (2), `a` (9) e `c` (sem ordem); no PDF os títulos aparecem nessa ordem
- **Entrada:** `ordem = 9, 2, (nenhuma)`

## Caso: sumario lista as secoes com a pagina sem pintar link na linha

- **Requisito:** Nielsen 6: com várias seções o leitor acha a que quer pela página; "esse hover amarelo não ta legal": o leitor de PDF pinta a área de todo link ao passar o mouse, então a linha do sumário não é link
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** sumario/secoes
- **Dado:** quatro seções, uma de 12 passos (que ocupa mais de uma página) e uma com título comprido demais para a linha
- **Quando:** o manual é montado
- **Então:** a capa traz "Sumário" com cada seção, o número da página onde ela de fato começa (descoberto numa primeira montagem e impresso numa segunda) e o título comprido cortado com reticências; toda seção começa em página nova; a capa não tem link nenhum e o único link de cada página seguinte é o "Voltar ao sumário" do rodapé, que leva à capa
- **Entrada:** `secoes = 4`

## Caso: rodape traz o app o manual e a volta ao sumario

- **Requisito:** "adicione isso ao rodapé": "App · Manual do usuário" à esquerda e "Voltar ao sumário" à direita, como no manual de referência
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** rodape/volta
- **Dado:** um manual de duas seções, em português e em inglês, e outro de uma seção só com várias páginas
- **Quando:** o manual é montado
- **Então:** todo rodapé traz "Loja · Manual do usuário" (EN: "Loja · User manual"); a capa não traz "Voltar"; da segunda página em
  diante o rodapé traz "Voltar ao sumário" (EN: "Back to contents"), ou "Voltar ao início" quando não há sumário, com um link
  só do tamanho do texto, sem faixa larga
- **Entrada:** `secoes = 2, 1`

## Caso: rodape da capa traz a versao do manual

- **Requisito:** "bota isso no rodapé da página do sumário": "Manual vigente · versão 1.0" no rodapé da capa
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** rodape/versao
- **Dado:** um manual de duas seções, em português e em inglês, sem e com `[manual] versao = "2.3"` no `sentry.toml`
- **Quando:** o manual é montado
- **Então:** o rodapé da capa (a página do sumário) traz "Manual vigente · versão 1.0" à direita (EN: "Current manual · version 1.0"),
  ou a versão declarada no `sentry.toml`; as demais páginas não trazem esse texto
- **Entrada:** `versao = padrão, 2.3`

## Caso: manual com uma secao so nao tem sumario

- **Requisito:** Nielsen 8, minimalista: um manual de uma seção cabe numa olhada
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** sumario/uma-secao
- **Dado:** um manual com uma seção só
- **Quando:** o manual é montado
- **Então:** não há "Sumário" nem link interno, e a seção começa na própria capa
- **Entrada:** `secoes = 1`

## Caso: introducao e negrito aparecem na secao

- **Requisito:** a introdução da seção, o `**negrito**` (nome de botão ou campo) e o subtítulo `##` vão para o PDF
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** secao/texto
- **Dado:** uma seção com parágrafo com `**antes**` em negrito, um subtítulo e os passos
- **Quando:** o manual é montado
- **Então:** o texto aparece sem os asteriscos, o trecho em negrito usa a fonte em negrito e o subtítulo aparece
- **Entrada:** `texto = "... **antes** ..."`

## Caso: aviso tem icone e cor do tipo

- **Requisito:** avisos `> [!INFO]`, `> [!SUCESSO]` e `> [!ATENCAO]`, com a cor de significado do tipo, independente da cor do app
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** aviso/tipos
- **Dado:** um aviso de cada tipo, com título, e um sem título
- **Quando:** o manual é montado
- **Então:** o título aparece em maiúsculas, o texto aparece e a cor do tipo (azul-petróleo, verde, âmbar) é usada, também numa barra fina na borda esquerda da caixa, que acompanha os cantos arredondados; sem título, só o texto
- **Entrada:** `tipo = info, sucesso, atencao`

## Caso: cartoes ficam lado a lado

- **Requisito:** um bloco `:::cartoes` vira cartões em duas colunas
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** cartoes/colunas
- **Dado:** um bloco de três cartões
- **Quando:** o manual é montado
- **Então:** o primeiro e o segundo ficam na mesma altura, o segundo à direita do primeiro; o terceiro vem na fileira de baixo, na coluna da esquerda; cada cartão leva a barra fina na borda esquerda, na cor do app (os passos não)
- **Entrada:** `cartoes = 3`

## Caso: markdown invalido e recusado dizendo o arquivo e a linha

- **Requisito:** o que o leitor do Markdown não entende é recusado com `arquivo:linha`, e nada é gerado
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** markdown/invalido
- **Dado:** seções com: sem bloco do topo, sem título, aviso sem tipo, bloco desconhecido, bloco não fechado e `ordem` que não é número
- **Quando:** o usuário roda `sentry manual` sem módulo
- **Então:** o comando sai com 3 e a mensagem traz `secoes/cadastro.md`, a linha e o que esperava
- **Entrada:** `markdown = (6 formas tortas)`

## Caso: manual sem secoes pede a primeira

- **Requisito:** sem nenhuma seção não há o que montar
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** secao/nenhuma
- **Dado:** um projeto sem nenhuma seção
- **Quando:** o usuário roda `sentry manual` sem módulo
- **Então:** sai com 3, a mensagem manda criar a primeira com `sentry manual <modulo>` e nenhum PDF é gravado
- **Entrada:** `secoes = 0`

## Caso: secao com roteiro apagado e recusada

- **Requisito:** uma seção aponta para o roteiro do `training` de onde vêm os passos
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** secao/sem-roteiro
- **Dado:** o manual tem uma só seção e o roteiro dela foi apagado
- **Quando:** o usuário roda `sentry manual` sem módulo
- **Então:** sai com 3 e a mensagem diz que nenhuma seção tem roteiro em `.sentry/training/`, de onde viriam o nome, a cor e a logo do app
- **Entrada:** `roteiro = (apagado)`

## Caso: secao so de texto convive com as secoes de roteiro

- **Requisito:** "adiciona todos os comandos e como eles funcionam": um manual de linha de comando tem seções que só explicam, sem passos de tela
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** secao/so-texto
- **Dado:** o manual tem uma seção com roteiro e outra escrita só em Markdown, sem roteiro, com `sentry init --install` no texto
- **Quando:** o usuário roda `sentry manual` sem módulo e depois `sentry manual <modulo da seção só de texto>`
- **Então:** a seção só de texto não é alterada e entra no PDF, com os dois traços de `--install` visíveis; a identidade do app vem da primeira
  seção que tem roteiro; pedir o módulo sem roteiro continua sendo erro de roteiro não encontrado
- **Entrada:** `roteiro = (ausente)`

## Caso: capa traz MANUAL DO USUARIO e o nome do app

- **Requisito:** "MANUAL USUARIO" como título grande, numa faixa na cor do app, com o nome do app embaixo
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** capa/titulo
- **Dado:** o manual em português e em inglês
- **Quando:** o manual é montado
- **Então:** a capa traz `MANUAL DO USUÁRIO` (EN: `USER MANUAL`, sem o texto em português) e o nome do app embaixo; o texto sobre a faixa é branco em cor escura e escuro em cor clara
- **Entrada:** `idioma = pt, en`

## Caso: cabecalho mostra a secao da pagina

- **Requisito:** Nielsen 1: em qualquer página solta se sabe em que seção se está
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** orientacao/cabecalho
- **Dado:** um manual de duas seções, a primeira com mais de uma página
- **Quando:** o manual é montado
- **Então:** a capa não traz "Seção" no cabeçalho; as páginas da primeira seção trazem "Seção 1" à direita, e a da segunda "Seção 2" (EN: "Section 2")
- **Entrada:** `secoes = 2`

## Caso: pdf declara titulo autor e idioma

- **Requisito:** acessibilidade: o leitor de tela e a aba do leitor de PDF leem o título e o idioma certos
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** acessibilidade/metadados
- **Dado:** um manual em português e outro em inglês
- **Quando:** o manual é montado
- **Então:** o título é `<app> - MANUAL DO USUÁRIO`, o autor é o app, e o idioma é `pt-BR` ou `en`
- **Entrada:** `idioma = pt, en`

## Classes não aplicáveis

- **idioma/vazio**: `--lang` sem valor é recusado pelo argparse antes do Sentry agir; o default
  `pt` cobre a ausência da opção.
- **modulo/vazio**: o módulo é opcional; a ausência é o caso "atualiza todas as seções", coberto acima.
- **modulo/tamanho-maximo-excedido**: a validação do nome do módulo é a mesma do `training`
  (`validar_modulo`), já coberta na spec `sentry-training`.
