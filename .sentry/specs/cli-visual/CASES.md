# CLI visual

## Prompt

Identidade visual propria da CLI, alem da cor ja feita: (1) simbolos junto da cor --
veredito aprovado=check, ressalva=alerta, reprovado=x, inconclusivo=circulo vazio;
achado critico/alta=x, media=alerta, baixa=circulo vazio -- aplicados em
colorize_report, no resumo compacto de _run_and_report e em sentry check (erro/classe
ausente/sucesso). Simbolo e texto, nao codigo ANSI, entao aparece igual com ou sem
suporte a cor e nao quebra redirecionamento. (2) Spinner em stderr (nunca stdout)
enquanto a suite roda dentro de _run_and_report, com frames braille e tempo decorrido
quando stderr e tty, e uma linha estatica sem animar quando nao e tty (CI/pipe) --
nunca escreve nada no arquivo salvo em disco. (3) render_masthead (caixa com
projeto/veredito/commit) e render_dashboard (rodape com testes, cobertura, achados por
severidade) construidos direto do Run/payload, impressos so no terminal ao redor do
corpo colorido do relatorio -- o arquivo .sentry/reports/latest.md continua exatamente
como markdown_report produz hoje, sem caixa nem simbolo. (4) Um icone por comando
(COMMAND_ICON) prefixando a primeira linha impressa de cada branch de main() em
cli.py. Sem dependencia de runtime nova. Sem selecao de idioma -- fora de escopo,
descartado. (5) Iteracao v2 do `sentry init`, seguindo mockup de referencia: cada
linha do checklist ganha uma badge alinhada a direita por categoria
(created/written/installed/ready), so'
quando a categoria e' nova nesta execucao -- numa reexecucao idempotente a linha
continua aparecendo (toda categoria aparece sempre), so' sem badge nenhuma; o
`✓` verde na frente ja basta, sem precisar de um rotulo tipo "presente". Ganha
tambem uma linha nova de status do git (branch e se a arvore esta limpa),
omitida fora de repositorio Git. Fora de escopo, deliberadamente: nenhum numero
ou detalhe fabricado que o produto nao meça de verdade. (6) Nao existe uma
tabela de dependencias separada: o item "Verificando ambiente do projeto" do
proprio checklist concentra tudo numa unica linha de detalhe -- versao do
Python, cada dependencia detectada com sua versao real (via
importlib.metadata, so' quando o modulo ja foi confirmado instalado; ou
`ausente` quando nao esta instalada) e a arquitetura, nessa ordem
(`python 3.12.10 • sentry-test 2.0.0 • pytest 9.1.1 • coverage 7.15.4 •
AMD64`). A linha inteira carrega a cor do status: verde quando toda
dependencia esta presente, vermelho quando alguma esta ausente -- o mesmo par
que ja colore `sentry check`. "Projeto Sentry inicializado." ganha um `✓`
verde na frente, igual as linhas do checklist acima dela, e fecha o bloco
(ultima linha impressa pelo `init`, sem linha em branco antes). (7) Wordmark
grande no topo do
`sentry init`, na fonte
figlet "ANSI Shadow" (texto literal, os mesmos caracteres de desenho de caixa
Unicode que qualquer fonte monoespacada moderna ja' renderiza -- nao e' gerado nem
depende de largura de terminal nem de cor truecolor), 6 linhas de altura, em tres
faixas de verde -- vivo, normal, apagado -- duas linhas cada, de cima pra baixo. Sem
sombra nem gradiente por pixel: a propria fonte, com seus tracos grossos em blocos,
ja' carrega peso visual suficiente. Sem interatividade nenhuma (um menu de setas do
teclado exigiria ler tecla em tempo real, com dependencia nova ou controle de
terminal raw especifico por SO, e o `sentry init` nao tem escolha nenhuma pra
perguntar). E' a unica marca no topo do `init` -- nao ha cabecalho separado nenhum
(nome/badge "ENGINE ACTIVE" e caixa de proximo passo foram removidos). A versao real
do pacote (`__version__`) aparece no pezinho direito da ultima linha do proprio
wordmark, colada depois da ultima letra, sem cabecalho nem caixa propria.
(8) O `sentry init` tem um unico cabecalho de secao (`INICIALIZANDO`) -- ganha
um tracinho (`─`) na frente e o texto em verde vivo (em vez do cinza discreto
anterior), seguido de outro tracinho da mesma cor apagada que preenche o
resto da linha ate a largura de referencia (`_LINE_WIDTH`) ou ate a largura
real do terminal, o que for menor -- pra nao estourar e quebrar linha
(dobrando visualmente o espaco) num terminal mais estreito. Os dois
tracinhos usam a mesma cor e o mesmo espaçamento de um espaço, sem emoji --
emoji de verdade carrega paleta propria e ignora o ANSI, entao nao sai
colorido igual ao resto da linha.
(9) `sentry -h`/`sentry --help` -- a raiz sem comando, a outra porta de
entrada de quem nunca usou a ferramenta -- ganha o mesmo wordmark do
`sentry init` antes do texto de ajuda. So' o parser raiz: `sentry
<comando> -h` (ex.: `sentry init -h`) continua com o `usage:`/`options:`
crus do argparse, sem wordmark nem decoracao nenhuma, igual toda execucao
de comando alem do `init`. Na raiz, o bloco `usage: sentry [-h]
[--version] ...` e o paragrafo de descricao logo abaixo saem do texto --
o wordmark ja identifica o programa, repetir usage/descricao antes do
titulo `COMANDOS` so' empurraria a informacao util pra baixo. Os
cabecalhos em ingles "positional arguments:"/"options:" viram o mesmo
titulo com tracinho na frente e depois que as secoes do `init` usam
("COMANDOS" e "EXTRAS", ver item 8), com a mesma indentacao de 2 espacos
nos dois (o argparse por padrao indenta comandos com 4 e opcoes com 2;
aqui os dois ficam iguais). Cada nome de comando e cada flag (`-h`,
`--help`, `--version`) saem coloridos em verde, em qualquer lugar do
texto onde aparecerem (inclusive dentro da descricao de outro comando,
ex.: "check + run + relatorio" do `review`) -- mas a listagem compacta
`{init,new,check,...}` (que repetiria os mesmos onze nomes que a lista
com descricao ja mostra) nao aparece em lugar nenhum. "-h"/"--help" e
"--version" tambem ganham texto de ajuda em portugues -- o argparse só
tem em ingles por padrao ("show this help message and exit"/"show
program's version number and exit"); a traducao vale pra raiz e pra
todo subcomando, nao so' a raiz (so' o wordmark e a decoracao de
titulo/indentacao/flag sao exclusivos da raiz).

## Campos

- **simbolo_do_veredito**: texto — o caractere associado a cada status
  (`✓`/`⚠`/`✗`/`○`), independente de a cor estar habilitada.
- **simbolo_da_severidade**: texto — o caractere associado a cada severidade de
  achado (`✗`/`⚠`/`○`).
- **quadro_da_suite**: texto — o estado do spinner: `com-tty` (anima em stderr)
  ou `sem-tty` (uma linha estática, sem animação).
- **conteudo_do_dashboard**: texto — um dos elementos que `render_dashboard`
  precisa trazer (testes, cobertura, achados por severidade).
- **badge_do_checklist**: texto — o rótulo alinhado à direita numa linha do
  checklist do `init` (`created`, `written`, `installed`, `ready`).
- **status_do_git**: texto — o que a linha `git repo` da tabela de
  dependências mostra: `limpo` (árvore sem alterações), `sujo` (árvore com
  alterações) ou ausente (fora de repositório Git).

## Caso: veredito aprovado tem o simbolo de check

- **Requisito:** "veredito aprovado=check"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** simbolo_do_veredito/valido
- **Dado:** um veredito `aprovado`
- **Quando:** o relatório é colorido para o terminal
- **Então:** a linha do veredito traz o símbolo `✓`
- **Entrada:** `simbolo_do_veredito = "✓"`

## Caso: veredito reprovado tem o simbolo de x

- **Requisito:** "reprovado=x"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** simbolo_do_veredito/valido
- **Dado:** um veredito `reprovado`
- **Quando:** o relatório é colorido para o terminal
- **Então:** a linha do veredito traz o símbolo `✗`
- **Entrada:** `simbolo_do_veredito = "✗"`

## Caso: veredito inconclusivo tem o simbolo de circulo vazio

- **Requisito:** "inconclusivo=circulo vazio"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** simbolo_do_veredito/valido
- **Dado:** um veredito `inconclusivo`
- **Quando:** o relatório é colorido para o terminal
- **Então:** a linha do veredito traz o símbolo `○`
- **Entrada:** `simbolo_do_veredito = "○"`

## Caso: achado critico ou alto tem o simbolo de x

- **Requisito:** "achado critico/alta=x"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** simbolo_da_severidade/valido
- **Dado:** um achado de severidade `crítica` e outro `alta`
- **Quando:** o relatório é colorido para o terminal
- **Então:** o rótulo de cada um traz o símbolo `✗`
- **Entrada:** `simbolo_da_severidade = "✗"`

## Caso: resumo compacto do veredito tambem traz o simbolo

- **Requisito:** "aplicados em ... no resumo compacto de _run_and_report"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** simbolo_do_veredito/valido
- **Dado:** uma análise com `print_report=False`
- **Quando:** o resumo compacto é impresso
- **Então:** a linha traz o símbolo do veredito junto do status
- **Entrada:** `simbolo_do_veredito = "✓"`

## Caso: sentry check troca o prefixo por simbolo em erro e sucesso

- **Requisito:** "aplicados em ... sentry check (erro/classe ausente/sucesso)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** simbolo_da_severidade/valido
- **Dado:** uma spec com erro estrutural e, noutra rodada, uma spec válida
- **Quando:** `sentry check` roda em cada uma
- **Então:** a linha de erro traz `✗` e a linha de sucesso traz `✓`, no lugar de
  `[erro]`
- **Entrada:** `simbolo_da_severidade = "✗"`

## Caso: spinner anima em stderr quando e tty

- **Requisito:** "Spinner em stderr (nunca stdout) ... com frames braille e
  tempo decorrido quando stderr e tty"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** quadro_da_suite/valido
- **Dado:** um stream de stderr que responde `isatty()` verdadeiro
- **Quando:** o próximo frame do spinner é escrito
- **Então:** o caractere vem do conjunto de frames braille, não de stdout
- **Entrada:** `quadro_da_suite = "com-tty"`

## Caso: spinner nao anima fora de terminal interativo

- **Requisito:** "uma linha estatica sem animar quando nao e tty (CI/pipe)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** quadro_da_suite/vazio
- **Dado:** um stream de stderr que responde `isatty()` falso
- **Quando:** o spinner inicia
- **Então:** uma única linha estática é escrita, sem nenhum frame de animação
  depois
- **Entrada:** `quadro_da_suite = "sem-tty"`

## Caso: masthead e dashboard nunca aparecem no relatorio salvo em disco

- **Requisito:** "impressos so no terminal ... o arquivo .sentry/reports/latest.md
  continua exatamente como markdown_report produz hoje, sem caixa nem simbolo"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** conteudo_do_dashboard/valido
- **Dado:** uma análise concluída, impressa no terminal com masthead e
  dashboard
- **Quando:** o relatório é gravado em `.sentry/reports/latest.md`
- **Então:** o conteúdo do arquivo não contém nenhuma borda de caixa nem os
  símbolos do dashboard
- **Entrada:** `conteudo_do_dashboard = "testes"`

## Caso: dashboard traz testes cobertura e achados por severidade

- **Requisito:** "render_dashboard (rodape com testes, cobertura, achados por
  severidade)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** conteudo_do_dashboard/valido
- **Dado:** um `Run` com testes executados, cobertura medida e achados de mais
  de uma severidade
- **Quando:** `render_dashboard` monta o rodapé
- **Então:** o texto traz a contagem de testes, a cobertura global e a
  contagem de achados por severidade
- **Entrada:** `conteudo_do_dashboard = "cobertura"`

## Caso: icone do comando prefixa a primeira linha impressa

- **Requisito:** "Um icone por comando (COMMAND_ICON) prefixando a primeira
  linha impressa de cada branch de main()"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** o comando `sentry init` num projeto novo
- **Quando:** a primeira linha é impressa
- **Então:** ela começa com o ícone declarado para `init`

## Caso: sentry init nao termina com nenhuma caixa de proximo passo

- **Requisito:** "a caixa de próximo passo recomendado foi removida -- init
  termina no bloco de dependências, sem sugerir comando nenhum depois"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init` num projeto novo
- **Quando:** a saída é impressa
- **Então:** não aparece nenhuma caixa nem menção a `sentry new` depois do
  bloco de dependências

## Caso: sentry init mostra o wordmark antes do texto de conclusao

- **Requisito:** "o wordmark grande é a única marca no topo do `init`, antes
  de 'Projeto Sentry inicializado.' -- sem cabeçalho separado nenhum"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** o comando `sentry init` num projeto novo
- **Quando:** a saída é impressa
- **Então:** o wordmark aparece antes da linha "Projeto Sentry inicializado."

## Caso: sentry init mostra o checklist dos passos com check verde

- **Requisito:** inspirado em captura de tela de referência (mockup): cada passo
  do `init` aparece como uma linha própria com `✓`, agrupado por o que
  representa — `.sentry/` (reports/runs/test-plans/specs/sentry.db),
  `sentry.toml`/`.gitignore`, skill do Claude, `AGENT-SENTRY.md` — em vez de uma
  única linha "Criados: a, b, c" difícil de escanear
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init` num projeto novo, sem nada ainda criado
- **Quando:** a saída é impressa
- **Então:** cada item criado aparece numa linha própria, prefixada por `✓`,
  agrupado por categoria
- **Entrada:** `simbolo_do_veredito = "✓"`

## Caso: init tem um unico cabecalho verde com tracinho

- **Requisito:** "remova [o emoji] e coloque um tracinho", "o campo
  dependências não deve mais existir" -- um único cabeçalho
  `INICIALIZANDO`, com tracinho na frente, texto verde vivo e outro
  tracinho da mesma cor preenchendo o resto da linha; sem cabeçalho
  separado de dependências
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry init` num projeto novo
- **Quando:** a saída é impressa
- **Então:** `INICIALIZANDO` aparece uma única vez, com um tracinho na
  frente, o texto em verde e outro tracinho depois; nenhum texto
  `DEPENDÊNCIAS` aparece em lugar nenhum

## Caso: tracinho do cabecalho de secao respeita a largura do terminal

- **Requisito:** um terminal estreito não pode fazer o tracinho quebrar
  linha, o que dobraria visualmente o espaço antes do bloco seguinte
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Dado:** um terminal de 40 colunas
- **Quando:** `render_section` é chamado
- **Então:** a linha inteira (símbolo, texto e tracinho) não passa de 40
  colunas de largura

## Caso: nenhum outro comando repete o wordmark

- **Requisito:** "nenhum outro comando ganha o wordmark, pra nao repetir a
  mesma marca a cada chamada"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** o comando `sentry check` num projeto já inicializado
- **Quando:** a saída é impressa
- **Então:** o wordmark não aparece

## Caso: versao aparece no pezinho direito do wordmark e em chip nas dependencias

- **Requisito:** "o cabeçalho separado (nome + versão + badge 'ENGINE
  ACTIVE') foi removido -- a versão real do pacote (`__version__`) aparece
  no pezinho direito do próprio wordmark, colada na última linha, e também
  como chip junto das dependências"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init` com `__version__` valendo `2.0.0`
- **Quando:** a saída é impressa
- **Então:** `v2.0.0` aparece na última linha do wordmark e o chip
  `sentry-test 2.0.0` aparece no detalhe do item "Verificando ambiente do
  projeto"; nenhuma badge `ENGINE ACTIVE` aparece em lugar nenhum
- **Entrada:** `simbolo_do_veredito = "○"`

## Caso: linha do checklist mostra a badge alinhada a direita por categoria

- **Requisito:** "uma badge alinhada a direita por categoria
  (created/written/installed/ready)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** badge_do_checklist/valido
- **Dado:** uma linha de checklist com badge `created`
- **Quando:** a linha é renderizada
- **Então:** o texto `created` aparece alinhado à direita, depois do label
- **Entrada:** `badge_do_checklist = "created"`

## Caso: detalhe do ambiente mostra a versao real de cada dependencia

- **Requisito:** "o detalhe do item de ambiente mostra a versao real de
  pytest/coverage (via importlib.metadata, so' quando o modulo ja foi
  confirmado instalado)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** `sentry init` com pytest e coverage instalados
- **Quando:** a saída é impressa
- **Então:** o detalhe do item "Verificando ambiente do projeto" traz o
  número de versão instalado de cada dependência, não só `presente`

## Caso: dependencia ausente vira vermelho e presente vira verde no detalhe do ambiente

- **Requisito:** "ponha em verde já que são dependências" -- o detalhe do
  item "Verificando ambiente do projeto" (que concentra python, cada
  dependência e a arquitetura) carrega a cor do status: verde quando toda
  dependência está presente, vermelho quando alguma está ausente
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** uma dependência instalada e outra ausente
- **Quando:** a saída de `sentry init` é impressa
- **Então:** a linha do item de ambiente fica vermelha quando alguma
  dependência está ausente, e verde quando todas estão presentes; nenhum
  rótulo `presente` aparece pra dependência instalada

## Caso: conclusao do init ganha um simbolo antes do texto

- **Requisito:** "'Projeto Sentry inicializado.' ganha um símbolo antes,
  igual as linhas do checklist acima dela"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry init` num projeto novo
- **Quando:** a saída é impressa
- **Então:** a linha "Projeto Sentry inicializado." começa com o símbolo de
  veredito aprovado (`✓`)

## Caso: python entra como detalhe do item de ambiente, dentro do checklist

- **Requisito:** "Verificando ambiente do projeto python 3.12.10 •
  sentry-test 2.0.0 • pytest 9.1.1 • coverage 7.15.4 • AMD64" -- python,
  cada dependência e a arquitetura ficam juntos no detalhe de um único
  item do checklist, na ordem: python, dependências (na ordem detectada,
  começando por `sentry-test`), arquitetura
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry init` num projeto novo
- **Quando:** a saída é impressa
- **Então:** a versão do Python aparece no detalhe do item "Verificando
  ambiente do projeto", dentro do bloco `INICIALIZANDO`, antes de
  `sentry-test`

## Caso: conclusao do init nao pula linha antes nem depois do bloco

- **Requisito:** "'Projeto Sentry inicializado.' logo abaixo do último item
  do bloco, com o mesmo comportamento, sem pular linha" -- e fecha o `init`:
  é a última linha impressa, não a do meio
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry init` num projeto novo
- **Quando:** a saída é impressa
- **Então:** a linha "Projeto Sentry inicializado." vem imediatamente depois
  da última linha do bloco (sem linha em branco entre as duas) e é a
  última linha impressa pelo comando

## Caso: linha de git aparece com branch e status quando ha repositorio

- **Requisito:** "ganha uma linha nova de status do git (branch e se a
  arvore esta limpa)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** status_do_git/valido
- **Dado:** `sentry init` dentro de um repositório Git com a árvore limpa
- **Quando:** a saída é impressa
- **Então:** a linha `git repo` aparece com o nome do branch e `limpo`
- **Entrada:** `status_do_git = "limpo"`

## Caso: linha de git some fora de repositorio Git

- **Requisito:** "omitida fora de repositorio Git"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** status_do_git/vazio
- **Dado:** `sentry init` fora de um repositório Git
- **Quando:** a saída é impressa
- **Então:** nenhuma linha `git repo` aparece
- **Entrada:** `status_do_git = ""`

## Caso: checklist do init mostra todas as categorias mesmo em reexecucao

- **Requisito:** "toda categoria aparece sempre, mesmo em uma re-execução
  onde nada foi criado -- a badge só aparece quando a categoria é nova
  nesta execução"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init` rodado uma segunda vez no mesmo projeto, já
  inicializado
- **Quando:** a saída é impressa
- **Então:** as cinco linhas do checklist aparecem de novo, sem nenhuma
  badge nas que não mudaram nesta execução

## Caso: checklist do init em reexecucao nao mostra nenhuma badge

- **Requisito:** "tire os presente" -- a badge `presente` do checklist foi
  removida; numa reexecução idempotente a linha não ganha rótulo nenhum, só
  o `✓` verde de sempre
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry init` rodado uma segunda vez no mesmo projeto, já
  inicializado, com cor habilitada
- **Quando:** a saída é impressa
- **Então:** a palavra `presente` não aparece em nenhuma linha

## Caso: wordmark grande aparece no topo do init

- **Requisito:** "SENTRY na fonte figlet ANSI Shadow, 6 linhas de altura,
  sem nenhuma moldura ao redor"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init` num projeto novo
- **Quando:** a saída é impressa
- **Então:** o wordmark aparece antes do cabeçalho de nome/versão/badge, sem
  nenhuma moldura retangular ao redor

## Caso: wordmark usa tres faixas de verde

- **Requisito:** "três faixas de verde (vivo, normal, apagado), duas linhas
  cada, de cima pra baixo -- sem sombra nem gradiente por pixel, a fonte
  já carrega o peso visual sozinha"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Dado:** o wordmark renderizado com cor habilitada
- **Quando:** `render_wordmark` monta as linhas
- **Então:** a primeira, a do meio e a última linha usam três códigos de cor
  diferentes entre si

## Caso: wordmark sem cor fica so' com o texto puro

- **Requisito:** "sem cor habilitada, é só o texto da fonte figlet, sem
  nenhum código ANSI"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Dado:** cor desabilitada
- **Quando:** `render_wordmark` monta as linhas
- **Então:** a saída não tem nenhum código ANSI e ainda é a arte em blocos
  de desenho de caixa

## Caso: sentry -h mostra o wordmark antes do texto de ajuda

- **Requisito:** "coloque [o wordmark] e siga o padrao do init" -- `sentry -h`
  ganha o mesmo wordmark que `sentry init`, mas nenhum subcomando repete
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry -h` (ou `--help`) na raiz, e `sentry init -h` como
  contraste
- **Quando:** a ajuda é impressa
- **Então:** o wordmark aparece antes do texto de uso gerado pelo argparse
  em `sentry -h`, e não aparece em `sentry init -h`

## Caso: sentry -h tem cabecalhos com tracinho, igual as secoes do init

- **Requisito:** "no init temos um titulo em verde com um tracinho na
  direita e esquerda, coisa que não temos aqui", "options: troca por um
  titulo" -- os cabeçalhos em inglês `positional arguments:`/`options:`
  viram o mesmo estilo de título das seções do `init` (`COMANDOS`/`EXTRAS`)
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry -h`
- **Quando:** a ajuda é impressa
- **Então:** os textos `positional arguments:` e `options:` não aparecem;
  em seus lugares aparecem `COMANDOS` e `EXTRAS`, cada um com um tracinho
  antes e depois, no mesmo estilo do cabeçalho de seção do `init`

## Caso: sentry -h colore o nome de cada comando e cada flag em verde

- **Requisito:** "segundo os comando eu quero que eles fiquem em verde",
  "poe -h, --help e --version em verde"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** `sentry -h` com cor habilitada
- **Quando:** a ajuda é impressa
- **Então:** cada nome de comando (`init`, `new`, `check`, `run`, `review`,
  `watch`, `status`, `context`, `report`, `history`, `clear`) e cada flag
  (`-h`, `--help`, `--version`) aparece colorido em verde onde quer que
  apareça no texto

## Caso: sentry -h nao repete a listagem compacta de comandos

- **Requisito:** "{init,new,check,run,review,watch,status,context,report,
  history,clear} deleta" -- a mesma enumeração entre chaves aparece duas
  vezes (uma no `usage:`, outra logo abaixo do título `COMANDOS`) e não
  acrescenta nada que a lista detalhada, com descrição de cada comando,
  já não mostre
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry -h`
- **Quando:** a ajuda é impressa
- **Então:** a linha `{init,new,check,run,review,watch,status,context,
  report,history,clear}` não aparece em lugar nenhum, nem no `usage:` nem
  logo abaixo do título `COMANDOS`

## Caso: sentry -h nao repete usage nem descricao antes do wordmark bastar

- **Requisito:** "delete isso" (o bloco `usage: sentry [-h] [--version]
  ...` seguido do parágrafo "Deriva a matriz de casos de teste...") -- o
  wordmark já identifica o programa
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry -h`
- **Quando:** a ajuda é impressa
- **Então:** nem `usage:` nem o parágrafo de descrição aparecem; o
  wordmark é seguido direto do título `COMANDOS`

## Caso: comandos e extras tem a mesma indentacao

- **Requisito:** "os comandos em comando estão mt a direita, coloque como
  estão em extras: mais próximos a esquerda" -- o argparse por padrão
  indenta a lista de comandos com 4 espaços e a de opções com 2
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** `sentry -h`
- **Quando:** a ajuda é impressa
- **Então:** as linhas de comando (`COMANDOS`) e as linhas de flag
  (`EXTRAS`) começam com a mesma indentação de 2 espaços

## Caso: -h e --version tem texto de ajuda em portugues

- **Requisito:** "show program's version number and exit / show this help
  message and exit português" -- o argparse só tem esses textos em inglês
  por padrão
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry -h` e `sentry init -h`
- **Quando:** a ajuda é impressa
- **Então:** a linha de `-h`/`--help` diz "mostra esta mensagem de ajuda e
  sai" e a linha de `--version` diz "mostra a versão do programa e sai",
  nenhuma delas em inglês, tanto na raiz quanto em qualquer subcomando

## Classes não aplicáveis

- **badge_do_checklist/vazio**: nem toda linha do checklist tem badge (numa
  reexecução idempotente, nenhuma tem) — a ausência já é o caso feliz,
  coberto pelos casos que declaram badge; não é uma classe de erro a testar
  aqui.
- **badge_do_checklist/tamanho-maximo-excedido**: um de quatro rótulos fixos
  do código, não texto digitado.
- **badge_do_checklist/caracteres-especiais**: idem — não é entrada de
  usuário.
- **status_do_git/tamanho-maximo-excedido**: nome de branch vem do Git, cujo
  próprio limite de tamanho já é a garantia; não há validação adicional
  aqui.
- **status_do_git/caracteres-especiais**: o nome do branch é exibido como o
  Git o devolve, sem parsing que quebre por caractere especial.

- **simbolo_do_veredito/tamanho-maximo-excedido**: um de quatro caracteres
  fixos do domínio, não texto digitado com comprimento a limitar.
- **simbolo_do_veredito/vazio**: todo veredito do domínio (`VerdictStatus`)
  mapeia para um símbolo; não existe veredito sem símbolo que chegue aqui.
- **simbolo_do_veredito/caracteres-especiais**: idem — não é entrada de
  usuário.
- **simbolo_da_severidade/tamanho-maximo-excedido**: um de três caracteres
  fixos, mesma razão.
- **simbolo_da_severidade/vazio**: toda severidade (`Severity`) mapeia para um
  símbolo.
- **simbolo_da_severidade/caracteres-especiais**: idem — não é entrada de
  usuário.
- **quadro_da_suite/tamanho-maximo-excedido**: um de dois estados fechados
  decididos por `isatty()`, não texto livre.
- **quadro_da_suite/caracteres-especiais**: idem.
- **conteudo_do_dashboard/tamanho-maximo-excedido**: os elementos do dashboard
  são um conjunto fechado de chaves do `Run`, não texto de comprimento
  variável.
- **conteudo_do_dashboard/vazio**: `render_dashboard` sempre recebe um `Run`
  concluído; não há chamada com payload vazio a testar aqui — o caso "sem
  achados" já é coberto pela contagem zerada, não por ausência de dado.
- **conteudo_do_dashboard/caracteres-especiais**: idem — não é entrada de
  usuário.
