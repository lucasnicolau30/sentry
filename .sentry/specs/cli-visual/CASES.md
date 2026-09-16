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
(10) `sentry --version` -- a saida inteira (numeros e pontos, ex.:
`2.0.0`) sai colorida em verde, com cor habilitada. Diferente do item 9
(que colore o nome da flag `--version` dentro do texto de ajuda), este
e' o valor que o proprio `--version` imprime quando chamado sozinho.
(11) Quatro comandos que ainda imprimiam so' texto puro (alem do icone que ja
tinham) ganham a mesma linguagem visual do resto da CLI -- nenhum ganha
masthead/dashboard novo, so' cor e simbolo sobre o que ja existe, igual ao
`sentry check` fez antes. `sentry new`: o caminho do diretorio criado sai em
verde; o bloco de template ganha o mesmo titulo com tracinho que
`COMANDOS`/`EXTRAS` usam (`Template`); as quatro linhas de valores aceitos
(camadas, tipos, prioridades, tipos de campo) saem em azul; o comando
sugerido no final (`sentry check <slug>`) sai destacado em verde.
`sentry history`: cada delta de cobertura/teste sai verde quando o numero
favorece o projeto (cobertura sobe, passed sobe, failed/not_run cai) e
vermelho no sentido contrario -- zero e `indisponivel` ficam sem cor, nem
bons nem ruins; achados novos saem vermelhos (regressao), resolvidos verdes
(melhora), persistentes amarelos (ainda la, sem novidade); a transicao de
veredito usa a cor de cada status (`VERDICT_COLOR`) dos dois lados da seta.
`sentry clear`: "Nada a remover" ganha o simbolo de aprovado
(nada pra fazer e' o caso feliz); a contagem do que seria removido sai em
amarelo (aviso, ainda nao e' destrutivo); apos aplicar, a confirmacao ganha
o simbolo de aprovado em verde; sem `--yes`, o aviso pra repetir com
`--yes` sai em amarelo (e' irreversivel, e o padrao so mostra o escopo).
`sentry watch`: o modo de cada reavaliacao (`instantâneo`/`completo`) sai
colorido -- azul pro instantaneo (barato, e' o que roda a maior parte do
tempo), magenta pro completo (a suite inteira, mais caro); "Parado." ao
sair com Ctrl+C sai em amarelo, no mesmo tom do restante dos avisos de
interrupcao normal (nao e' erro).
(12) Reversao do item (5): a badge alinhada a direita por categoria
(created/written/installed/ready) na linha do checklist do `sentry init` sai
de novo -- "antes nao existia, remova". Cada linha do checklist volta a ser
so' o `✓` verde e o texto (mais o detalhe do item de ambiente, que o item 6
ja cobre e continua valendo); nenhuma badge aparece mais, nem na primeira
execucao nem em reexecucao. `render_checklist_item` perde os parametros
`badge`/`badge_color` -- sem nenhum outro lugar que os use, mante-los seria
parametro morto.
(13) `sentry <comando> -h`/`--help`, o `usage:` de qualquer comando (raiz ou
subcomando) e as mensagens de erro do argparse (argumento obrigatorio
ausente, escolha invalida, nao reconhecido) ficam no mesmo padrao visual e
no mesmo idioma que o resto da CLI -- ate aqui so' a raiz (`sentry -h`)
tinha decoracao; `sentry new -h` ou `sentry new` sem o `name` obrigatorio
apareciam em ingles cru, sem cor nenhuma. Mudanca: (a) `usage:` vira `uso:`
em qualquer usage impresso (help ou erro); (b) todo token de flag (`--algo`
ou `-x`, generico -- nao so' `-h`/`--help`/`--version` como antes, tambem
`--prompt`, `--json`, `--spec`, `--base`, `--install`, `--keep-last`,
`--yes`, `--no-tests`, `--interval`) sai em verde, em qualquer lugar do
usage/ajuda/erro onde aparecer; (c) o cabecalho `positional arguments:` de
um subcomando vira o titulo com tracinho `ARGUMENTOS` (raiz continua sendo
`COMANDOS`, ja' que ali sao subcomandos de verdade, nao argumentos
posicionais genericos) e `options:` continua virando `EXTRAS`, com a mesma
indentacao unificada que a raiz ja tem; (d) as mensagens de erro mais
comuns do argparse ganham traducao: "the following arguments are required:
X" vira "argumento(s) obrigatorio(s) ausente(s): X", "unrecognized
arguments: X" vira "argumento(s) nao reconhecido(s): X", "argument X:
invalid choice: Y (choose from Z)" vira "argumento X: escolha invalida: Y
(opcoes: Z)", "argument X: expected one argument" vira "argumento X:
esperava um valor" -- uma mensagem sem tradutor reconhecida cai no texto
original em ingles, nunca quebra; (e) a palavra `error:`/`erro:` na linha
de erro sai em vermelho, mesma cor que `sentry check` ja usa pra erro
estrutural. Fora de escopo: traduzir o argparse inteiro via gettext/locale
-- e' regex sobre as mensagens que este projeto realmente produz, nao uma
localizacao completa da biblioteca.
(14) Revisao do item (13.a): trocar a palavra `usage:` por `uso:` inline nao
bastou -- "ainda nao esta bom o suficiente ... quero um titulo uso, alem
disso o comando deveria ficar em verde, padronize". O bloco de uso vira um
titulo com tracinho igual aos outros (`USO`, no mesmo padrao visual de
`COMANDOS`/`EXTRAS`/`ARGUMENTOS`), numa linha propria, com o texto do uso
(inclusive o nome do comando, ex.: `new` em `sentry new [-h] ...`) numa
linha abaixo -- nao mais `uso: sentry new ...` tudo numa linha so'. O nome
do comando dentro do uso tambem sai colorido em verde (reaproveitando a
mesma coloracao de `_COMMAND_NAMES` que o resto da ajuda ja usa), nao so' as
flags como a leva anterior fazia. Vale tanto no uso embutido na ajuda
completa (`sentry new -h`) quanto no uso isolado que aparece antes de
qualquer mensagem de erro do argparse.
(15) Dois ajustes finos sobre o item (14), no mesmo pedido: "sentry new:
delete essa parte, sentry new tudo em verde". (a) `sentry` (o nome do
programa) tambem sai verde dentro do bloco `USO` -- ate aqui so' o nome do
subcomando (`new`) colorial, deixando `sentry` sem cor antes dele; agora
`sentry <comando>` sai inteiro verde, as duas palavras. (b) a linha de erro
do argparse perde o prefixo `{prog}: ` (ex.: `sentry new: `) que o argparse
imprime por padrao antes de `erro:` -- informacao repetida, ja' que o bloco
`USO` logo acima ja' mostra `sentry new` em verde; a linha de erro vira so'
`erro: <mensagem>`.
(16) Excecao ao item 9/case "nenhum outro comando repete o wordmark":
`sentry new` tambem ganha o wordmark ANSI Shadow no topo, igual `sentry
init`/`sentry -h` -- e' a terceira porta de entrada de uso frequente (toda
funcionalidade nova passa por `new`), nao so' a primeira execucao (`init`)
ou quem pede ajuda (`-h`). So' no modo interativo -- `sentry new --json`
continua emitindo so' o payload JSON, sem wordmark nenhum antes, porque essa
saida existe pra ser consumida por maquina. Os demais comandos (`check`,
`run`, `review`, `watch`, `status`, `context`, `report`, `history`,
`clear`) continuam sem wordmark.
(17) O item (16) valia so' pro caminho de sucesso do `new` -- "era pro
fracasso tmb". `sentry new` sem o `name` obrigatorio (ou qualquer outro erro
do argparse nesse subcomando especifico) tambem mostra o wordmark, antes do
bloco `USO`/`erro`. Como o wordmark de sucesso e' impresso dentro do handler
do comando em `main()` (depois que o argparse ja aceitou os argumentos), mas
a falha e' rejeitada pelo proprio argparse antes de chegar la, o wordmark do
caminho de falha e' impresso dentro de `error()` -- so' quando o parser tem
a marca `_wordmark_on_error` (setada so' no parser de `new`, nenhum outro
subcomando). Vai pra stderr, nao stdout -- a mesma stream do usage/erro que
o resto de `error()` ja usa, senao o buffer de stdout (que so' esvazia na
saida do processo) fazia o wordmark aparecer DEPOIS do usage/erro em vez de
antes, invertendo a ordem visual.
(18) Achado ao testar o item (17): `sentry new "..." --json name` (um
argumento sobrando depois de `name`) reportava "unrecognized arguments" com
o usage/erro do parser RAIZ -- a listagem gigante `sentry [-h] [--version]
{init,new,check,...} ...` -- em vez do usage do `new`. "falta tratar esse
tmb ... isso aq ta mt feio". Causa: `ArgumentParser.parse_args` da propria
stdlib sempre reporta argumento nao reconhecido pelo parser em que foi
chamado (a raiz, em `main()`), nunca pelo subcomando que efetivamente
rejeitou o argumento -- e' assim que a biblioteca funciona, nao um bug deste
codigo. Corrigido trocando `parser.parse_args(argv)` por
`parser.parse_known_args(argv)` e roteando manualmente qualquer argumento
sobrando pro subparser certo (`args.command`, se algum foi escolhido) antes
de chamar `.error()` nele -- assim o usage/wordmark que aparecem sao os do
subcomando de verdade, nao os da raiz. Sem subcomando escolhido (ex.:
`sentry --bogus`), o erro continua saindo pela raiz mesmo, que e' o
comportamento certo ali.
(19) A linha unica de uso que o argparse monta sozinho
(`sentry new [-h] [--prompt PROMPT] [--json] name`) fica ilegivel assim que
o comando tem mais de duas ou tres flags. O bloco `USO` passa a ter um token
por linha -- o primeiro colado no nome do comando (`sentry new name`), os
demais indentados por baixo, alinhados sob o primeiro token -- em vez da
linha unica. Vale pra todo comando (raiz inclusive: o `{init,new,...} ...`
que antes vinha colado com `[-h] [--version]` numa linha so' tambem ganha
linha propria). Implementado formatando cada argumento (`action`) do
argparse isoladamente com o proprio formatador da biblioteca
(`HelpFormatter._format_actions_usage`), em vez de tentar quebrar a linha
unica já montada por espaço (que quebraria dentro de colchetes como
`[--base REF]`).
(20) Ordem dos tokens: "ta bagunçado ... organize em uma ordem logica" --
não a ordem que o argparse usa sozinho (todo opcional primeiro, incluindo
`-h`, só depois os posicionais), que escondia o argumento obrigatório atrás
de flags menos importantes. Nova ordem, em qualquer comando: posicionais
primeiro (o que a chamada exige de verdade — inclusive o pseudo-posicional
`{init,new,...} ...` da raiz), depois `-h` (convenção: primeiro entre os
opcionais, mas ainda depois do que é obrigatório), depois o resto dos
opcionais na ordem declarada no código.
(21) `sentry new -h` também ganha o wordmark, igual ao `sentry new` de
sucesso e ao `sentry new` sem `name` (itens 16 e 17) -- as três portas de
entrada do `new` (ajuda, sucesso, falha) ficam consistentes. Implementado
generalizando a marca `_wordmark_on_error` (renomeada para `_wordmark`) pra
também controlar `format_help`, não só `error`.
(22) Margem esquerda inconsistente entre seções: "no init e no help tudo
tem um espaço antes e nos outros alguns tem o espaço e outros não" -- a
seção `ARGUMENTOS` de um subcomando comum (ex.: `slug` do `check`, `name`
do `new`) saía colada na coluna 0, sem nenhum recuo, enquanto `EXTRAS`
sempre teve recuo de 2 espaços. Causa: o código tirava 2 espaços de toda
linha da seção de posicionais, regra calibrada só pro caso da raiz (onde
cada subcomando aparece aninhado com recuo de 4, sob a listagem compacta
`{init,new,...}`) -- mas um posicional comum de subcomando já sai do
argparse com recuo de 2 (igual a `EXTRAS`), então tirar mais 2 zerava ele.
Corrigido: só remove os 2 espaços extras de linhas que começam com 4
(exclusivo da raiz); linhas com recuo de 2 ficam como estão. `COMANDOS`
(raiz) e `ARGUMENTOS` (subcomando) agora têm o mesmo recuo de `EXTRAS` em
qualquer comando, não só na raiz.
(23) O item (22) corrigiu `ARGUMENTOS`/`COMANDOS`, mas faltavam mais dois
lugares com a mesma margem de 2 espaços que `EXTRAS` já tinha: o conteúdo
do bloco `USO` (`sentry new name`, `[-h]`, `[--prompt PROMPT]`...) e a
linha `erro: <mensagem>` -- "sentry new vc n deu o espaçamento aqui... nem
aqui: erro". Ambos saíam colados na coluna 0. Agora toda linha de conteúdo
do `USO` (a primeira e as indentadas por baixo) e a linha de erro ganham a
mesma margem de 2 espaços -- padronizado em toda seção de todo comando, não
só nos blocos que já tinham (`COMANDOS`/`ARGUMENTOS`/`EXTRAS`).
(24) `sentry` sem nenhum argumento não imprimia nada e saía com código 0 --
um usuário novo digitando só `sentry` não recebia pista nenhuma do que
fazer a seguir, diferente de ferramentas como `git`/`docker`, que mostram a
ajuda nesse caso. Agora `sentry` sozinho equivale a `sentry -h` (mesma
saída: wordmark, `COMANDOS`, `EXTRAS`), e continua saindo com código 0 --
não é erro, só ausência de intenção declarada, igual ao resto da CLI trata
"nada foi pedido" quando faz sentido tratar assim.
(25) `sentry comando-que-nao-existe` e `sentry --bogus` (erros da raiz, sem
nenhum subcomando escolhido) também ganham o wordmark -- "primeiramente
quero [wordmark]". Até aqui só `sentry -h` e o caminho de `new` (sucesso,
ajuda, falha) mostravam; a raiz tinha o wordmark na ajuda mas não no erro.
`_RootArgumentParser` agora liga `_wordmark = True` na classe inteira, não
só numa instância específica -- todo erro que sai pela raiz mostra o
wordmark, sem precisar marcar caso a caso.
(26) O token `{init,new,check,run,review,watch,status,context,report,
history,clear} ...` do bloco `USO` da raiz -- colchete curly sem espaço
entre os nomes, mais um `...` solto pro resto dos argumentos -- vira
`[init, new, check, run, review, watch, status, context, report, history,
clear]`: colchete reto, espaço depois de cada vírgula, sem o `...` (cada
subcomando escolhido já tem seu próprio bloco `USO` detalhado; o `...` aqui
era redundante). "com espaçamento entre eles e tire os 3 pontinhos do
final".
(27) O `(opções: init, new, check, ...)` no final da mensagem "escolha
inválida" saía repetindo a mesma lista que o item (26) já deixou legível
no bloco `USO` logo acima, na mesma tela -- "remove pq fica redundante". A
mensagem de erro vira só `escolha inválida: 'x'`, sem a lista de opções --
a única ação com `choices` neste projeto é o subparsers da raiz, então essa
redundância acontece sempre, não é um caso específico a preservar.
(28) `sentry init -h`/`--help` também ganha o wordmark, igual `sentry init`
de sucesso já tinha -- "sentry init -h ... falta o [wordmark]". Mesma marca
`_wordmark` do item (16)/(21), agora ligada também no parser de `init`, não
só na raiz e no `new`.
(29) O token `[-h]` no bloco `USO` só mostrava a forma curta da flag de
ajuda -- "falta add o --help, ponha em todos q estiverem assim". O
formatador padrão do argparse usa só a primeira forma declarada de uma
flag com múltiplos nomes (`-h`/`--help`) no usage de uma linha só; aqui,
onde cada flag já tem sua própria linha, as duas formas cabem sem custo de
espaço. Vira `[-h, --help]` -- mesma vírgula-espaço que a seção `EXTRAS` já
usa pra listar `-h, --help` juntos. Vale em qualquer comando (raiz e todo
subcomando), já que `-h`/`--help` é a única flag deste projeto com mais de
uma forma.
(30) Tentativa de generalizar (29)/EXTRAS fundido no USO pra todo comando
foi feita e desfeita no mesmo pedido -- "cara q merda tu fez? volta pra
como estava" -- e depois restrita só a `sentry init`, por pedido explícito:
"eu quero que o sentry init -h e sentry init --help e somente ele fique
assim, SOMENTE". Só `sentry init -h`/`--help` mostra a descrição de cada
flag colada na mesma linha do `USO`, sem a seção `EXTRAS` (removida só
nesse caso). Todo outro comando (`new`, `check`, `run`, `review`, `watch`,
`status`, `context`, `report`, `history`, `clear`, raiz) continua com
`USO` e `EXTRAS` separados, exatamente como antes. `sentry init --bogus`
(erro) também não é afetado -- continua só com o `USO` compacto, sem
descrição -- porque o pedido foi especificamente sobre `-h`/`--help`.
Implementado com dois parâmetros opt-in (`_render_usage_block(...,
with_descriptions=True)`, `_decorate_sections(..., include_options=False)`)
ligados só via `init._merge_options_into_usage = True` em `build_parser`,
não um comportamento novo do padrão.
(31) `sentry new -h`/`--help` ganha exatamente o mesmo tratamento do item
(30) -- "quero o exato mesmo comportamento do sentry init -h e sentry init
--help, mas deixando o ARGUMENTOS pfv". Cada flag opcional (`[-h,
--help]`, `[--prompt PROMPT]`, `[--json]`) mostra a descrição colada na
mesma linha do `USO`, sem a seção `EXTRAS`. Diferente de `init`, `new` tem
um posicional (`name`) -- a seção `ARGUMENTOS` continua existindo normal,
intocada; só `EXTRAS` some. `sentry new` sem `name` (erro) e `sentry new
-h`/`--help` (ajuda) ficam consistentes entre si e com `init`. Implementado
ligando a mesma flag já existente: `new._merge_options_into_usage = True`
-- nenhuma lógica nova, o parâmetro já suportava isso desde (30).
(32) `sentry new` de sucesso (a linha "Spec criada em..." e a lista de
arquivos criados) ganha o mesmo estilo de checklist que `sentry init` já
usa -- "tire essa caneta e ponha o certinho q eh usado no init ... não
quero em verde ... da pra deixar assim como do init". Três mudanças: (a) o
ícone de comando (`✎`, a "caneta") na frente de "Spec criada em..." vira o
símbolo de aprovado verde (`✓`), igual `render_checklist_item` já usa em
cada linha do checklist do `init`; (b) o caminho da spec criada
(`.sentry/specs/<slug>`) para de sair em verde -- só o `✓` no início da
linha é colorido, o texto depois fica plano, igual `init`; (c) a linha
única `Criados: PROMPT.md, CASES.md` (lista compacta separada por vírgula)
vira uma linha `✓` por arquivo, igual ao checklist do `init` (uma linha
`✓ Diretório .sentry/`, uma `✓ Config sentry.toml e .gitignore`, etc.), em
vez de uma lista horizontal. Implementado reaproveitando
`render_checklist_item` (já usado pelo `init`), sem parâmetro novo nenhum.
(33) Ajuste fino do item (32): "✓ nenhum arquivo novo quero que seja ✓
Nenhum arquivo novo" -- a linha que aparece quando `new` não cria nada
novo (reexecução idempotente) começava com minúscula, diferente do resto
do checklist (`Spec criada em...`, `Diretório .sentry/...`), que começa
sempre maiúsculo.
(34) Segundo ajuste do item (32): cada linha do checklist mostrava o
caminho cru do arquivo criado (`.sentry/specs/<slug>/PROMPT.md`), sem
nenhum rótulo -- "não dava pra colocar algo como 'Diretório .sentry/',
'Config sentry.toml e .gitignore'... ou seja algo antes deles?", apontando
o próprio checklist do `init` como referência de rótulo descritivo em vez
de caminho cru. `PROMPT.md` vira "Guardando o pedido — PROMPT.md" e
`CASES.md` vira "Gerando o template de casos — CASES.md" -- mesmo padrão
verbo + travessão + nome de arquivo que `init` já usa ("Instalando skill
Claude — <path>"). Um arquivo criado que não seja `PROMPT.md`/`CASES.md`
(não deveria acontecer hoje, mas por segurança) cai de volta no caminho
cru, sem quebrar.
(35) As quatro linhas de valores aceitos (Camadas/Tipos/Prioridades/Tipos
de campo) e o `sentry check <slug>` sugerido, no final do `sentry new`,
ficam mais divididos e sem cor sem propósito -- "isso aqui pode ganhar uma
divisao nova nao acha? ... essas cores em azul nao estao com o padrao da
paleta ... sentry check cadastro-de-clientes deve ser [] ou algo
padronizado com a aplicacao, ou sem nada". Três mudanças: (a) as quatro
linhas ganham seu próprio título com tracinho, "VOCABULÁRIO", separado do
título `TEMPLATE` acima -- eram duas coisas diferentes (o template em si,
e o vocabulário aceito nele) empilhadas sem nenhuma divisão visual entre
elas; (b) o azul nessas quatro linhas sai -- não tinha nenhum significado
de estado (diferente do azul do detalhe de ambiente no `init`, que
distingue instalado/ausente); agora ficam em texto plano, igual o corpo do
`TEMPLATE`; (c) o `sentry check <slug>` sugerido perde o destaque verde --
"ou sem nada" foi a opção escolhida, então vira texto plano dentro dos
crases que já existiam, sem cor nenhuma.
(36) Dois ajustes finos sobre o item (35), no mesmo pedido: "ta com
espaçamento duplo, despadronizando a aplicação" e "tire a aspas e deixe em
verde". (a) o espaço antes do título `VOCABULÁRIO` tinha duas linhas em
branco, não uma -- `TEMPLATE` (a constante) já termina com sua própria
quebra de linha, e o `print()` extra que eu tinha adicionado somava mais
uma; removido, sobra só a quebra natural do `print(TEMPLATE)`, igual ao
resto da aplicação (sempre uma linha em branco entre blocos, nunca duas).
(b) reversão parcial do item (35.c): o `sentry check <slug>` sugerido volta
a sair em verde, mas sem as crases que o cercavam antes -- "tire a aspas"
(as crases faziam as vezes de aspas aqui) "e deixe em verde" foram os dois
pedidos juntos, não "volta como era antes" (que tinha crases E sem cor
antes do item 35, ou cor E crases antes disso).
(37) "acho que poderia ter um titulo antes disso tmb ne, ta meio largado"
-- a linha final ("Depois rode sentry check ... até fechar limpo.") ficava
solta, sem nenhum título como `TEMPLATE`/`VOCABULÁRIO` acima dela. Ganha o
título "PRÓXIMO PASSO", no mesmo padrão com tracinho, uma linha em branco
antes (nunca duas, aprendido do item 36.a).
(38) `sentry new --json` -- "podemos padronizar com titulos e o sentry
v2.0.0 pra deixar ate mais legivel". Wordmark/título dentro do `--json`
quebraria o parse (`json.loads` numa saída que não é só JSON falha) -- essa
saída continua existindo pra ser consumida por máquina, sem decoração
nenhuma, igual sempre foi. O pedido, esclarecido, era sobre legibilidade
dentro do próprio JSON, sem quebrar o parse: a ordem das chaves muda pra
ler de cima pra baixo de forma mais natural -- primeiro o que é específico
desta chamada (`specDir`, onde a spec foi criada), depois o contexto
(`artifact`, `relOutputPath`), depois o vocabulário de referência
(`template`, `layers`, `test_types`, `priorities`), terminando no maior
bloco (`field_classes`). Conteúdo idêntico, só a ordem.
(39) "sentry check -h e sentry check --help nao estao com o comportamento
do help do init e do new, padronize" -- `check` ganha a fusão USO+EXTRAS
(item 30/31), depois "quer que eu já aplique em TODOS os comandos
restantes... de uma vez?" respondido que sim. `_merge_options_into_usage`
(antes `False` por padrão, ligado manualmente por comando) vira `True` por
padrão na classe base `_ArgumentParserPT` -- todo subcomando herda; a raiz
(`_RootArgumentParser`) também herda o padrão, e seu `format_help` (que
nunca mostrava bloco `USO` nenhum, so' wordmark + `COMANDOS` + `EXTRAS`)
passa a montar um `USO` com `-h`/`--version` descritos ali dentro, antes de
`COMANDOS`, sem `EXTRAS`. Resultado: `EXTRAS` deixa de existir em qualquer
comando da CLI -- toda descrição de flag mora dentro do `USO` de quem a
declara; `ARGUMENTOS`/`COMANDOS` (descrição de posicional) nunca são
afetados, continuam como sempre.
(40) "faltou justamente a logo do sentry... nos --help e -h" -- o wordmark
(ate aqui exclusivo de `init`/`new`/raiz) passa a aparecer em qualquer
`-h`/`--help`, sem exceção. Mesma mecânica do item (39): `_wordmark` (antes
`False` por padrão, ligado por instância em `init`/`new`/raiz) vira `True`
por padrão na classe base -- todo subcomando herda. A marca continua
controlando tanto a ajuda quanto o caminho de erro juntos (não é possível
ligar só um dos dois): `sentry check --bogus` também passa a mostrar o
wordmark antes do `USO`/erro, igual `init`/`new` já faziam.
(41) O erro de `sentry check` sem `--spec`/`slug` quando existe mais de uma
spec ("Erro: múltiplas specs encontradas...") não estava com o padrão
visual do resto da CLI -- "não está como em erro: argumento(s)
obrigatório(s) ausente(s): name -- falta o erro em vermelho, sem letra
maiúscula e a margem". Esse erro vem de `_check()` (aplicação, não
argparse), então nunca passou pelo `error()` traduzido/colorido que os
erros de argumento já têm. Alinhado ao mesmo padrão: `"Erro: "` vira
`paint("erro:", "red")`, com a mesma margem de 2 espaços que `USO`/erro do
argparse já usam. Vale tanto pra "múltiplas specs encontradas" quanto pra
"nenhuma matriz de casos encontrada" (o outro erro de `_check`). Escopo
explícito: só `sentry check` por enquanto -- `_run_and_report` tem uma
mensagem de erro parecida ("Erro de configuração: ...") que não foi tocada
aqui.
(42) O item (41) só cobriu a cor/caixa-baixa/margem da linha `erro:` --
"no sentry check n tem [wordmark]" comparando `sentry check` (múltiplas
specs) com `sentry check --bogus`, que já mostrava wordmark+`USO` por
passar pelo `error()` do argparse. `_check()` é erro de aplicação, nunca
passou por `error()`; agora `_print_app_error()` (novo helper) replica a
mesma sequência -- wordmark (se o comando tiver `_wordmark`) + bloco `USO`
compacto (sem descrição de flag, igual todo erro do argparse já é) + linha
`erro:` -- antes de imprimir a mensagem. Usado nos dois erros de `_check()`
("múltiplas specs encontradas" e "nenhuma matriz de casos encontrada").
`_check()` ganha um parâmetro `parser` (o subcomando que chamou -- `check`
ou `review`) só pra saber qual `USO`/wordmark mostrar; chamado de `review`
usa o parser de `review`, não o de `check`.
(43) "queria ver funcionando tmb, alem disso falta o [wordmark] e um
titulo ne" -- o item (42) só cobriu o caminho de exceção de `_check()`
(specs não encontradas). O caminho comum (spec encontrada, validada com
sucesso ou com achados de validação -- título ausente, seção ausente, caso
não declarado etc.) nunca mostrava wordmark nem título nenhum, só o ícone
`☑` fixo. Ganha wordmark (se `parser._wordmark`) e um título com
tracinho, "CHECK", antes da linha `☑ <spec>: N caso(s), M campo(s)` -- no
sucesso e na reprovação por achados, os dois passam pelo mesmo trecho de
código. Como `review` chama `_check()` internamente antes de `_run_and_
report()`, o wordmark de `review` agora aparece uma vez no topo, antes do
bloco `CHECK` -- efeito colateral esperado, não pedido à parte, mas
consistente com o resto da CLI (uma execução, um wordmark, no topo).
(44) "☑ tire esse check e coloque o check padrao da aplicação" -- o `☑`
de `COMMAND_ICON['check']` era um símbolo fixo só desse comando, fora do
padrão `✓`/`✗` verde/vermelho que o resto da CLI já usa (masthead,
`render_checklist_item`, `render_dependency_row`). A linha-resumo de
`sentry check` (`<símbolo> <spec>: N caso(s), M campo(s)`) passa a usar
`VERDICT_SYMBOL['aprovado']` (`✓`, verde) quando não há erro estrutural e
`VERDICT_SYMBOL['reprovado']` (`✗`, vermelho) quando há -- o mesmo par que
já colore a linha final "Estrutura valida..." logo abaixo. `COMMAND_ICON`
perde a entrada `check`, já sem uso.

## Campos

- **simbolo_do_veredito**: texto — o caractere associado a cada status
  (`✓`/`⚠`/`✗`/`○`), independente de a cor estar habilitada.
- **simbolo_da_severidade**: texto — o caractere associado a cada severidade de
  achado (`✗`/`⚠`/`○`).
- **quadro_da_suite**: texto — o estado do spinner: `com-tty` (anima em stderr)
  ou `sem-tty` (uma linha estática, sem animação).
- **conteudo_do_dashboard**: texto — um dos elementos que `render_dashboard`
  precisa trazer (testes, cobertura, achados por severidade).
- **status_do_git**: texto — o que a linha `git repo` da tabela de
  dependências mostra: `limpo` (árvore sem alterações), `sujo` (árvore com
  alterações) ou ausente (fora de repositório Git).
- **delta_do_historico**: texto — se um delta de `sentry history` favorece o
  projeto (verde), desfavorece (vermelho) ou é neutro (zero/indisponível,
  sem cor).
- **flag_generica**: texto — um token de flag (`-x` ou `--algo`) reconhecido
  no usage/ajuda/erro de qualquer comando, colorido em verde.
- **mensagem_de_erro_traduzida**: texto — a mensagem de erro do argparse, em
  português quando reconhecida por um dos tradutores, ou intocada em inglês
  quando não reconhecida.

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
- **Então:** a linha-resumo (`<símbolo> <spec>: N caso(s), M campo(s)`) traz
  `✗` vermelho na spec com erro e `✓` verde na spec válida, no lugar do
  ícone fixo `☑`
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

## Caso: comandos de rotina nao repetem o wordmark

- **Requisito:** "nenhum outro comando ganha o wordmark, pra nao repetir a
  mesma marca a cada chamada" -- exceto `init`/`-h`/`new`, ver casos
  específicos abaixo
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** o comando `sentry check` num projeto já inicializado
- **Quando:** a saída é impressa
- **Então:** o wordmark não aparece

## Caso: sentry new mostra o wordmark antes do restante da saida

- **Requisito:** "adicione o [wordmark] no sentry new"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new "nome da feature"` num projeto já inicializado
- **Quando:** a saída é impressa
- **Então:** o wordmark aparece antes do ícone/texto "Spec criada em ..."

## Caso: sentry new --json nao mostra o wordmark

- **Requisito:** "so' no modo interativo ... --json continua emitindo so' o
  payload"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new "nome da feature" --json`
- **Quando:** a saída é impressa
- **Então:** o wordmark não aparece, só o JSON

## Caso: sentry new sem o name obrigatorio tambem mostra o wordmark

- **Requisito:** "era pro fracasso tmb"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new` sem o argumento `name`
- **Quando:** o argparse rejeita a chamada
- **Então:** o wordmark aparece antes do bloco `USO`/`erro`, na mesma
  stream (stderr)

## Caso: erro de qualquer subcomando tambem ganha o wordmark

- **Requisito:** "faltou justamente a logo do sentry... nos --help e -h"
  (item 40) -- a marca `_wordmark`, ligada por padrão, controla ajuda e
  erro juntos
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry check --bogus` (flag desconhecida)
- **Quando:** o argparse rejeita a chamada
- **Então:** o wordmark aparece antes do bloco `USO`/erro

## Caso: argumento sobrando num subcomando usa o usage do proprio subcomando

- **Requisito:** "falta tratar esse tmb ... isso aq ta mt feio" -- o usage
  gigante da raiz aparecendo no lugar do usage do subcomando
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** `sentry new "nome da feature" --json name` (um argumento
  posicional sobrando depois de `name`)
- **Quando:** o argparse rejeita a chamada
- **Então:** o `USO` mostrado é o de `new` (`sentry new [-h] ...`), não a
  listagem completa de subcomandos da raiz; o wordmark também aparece,
  porque o erro foi roteado pro parser de `new`

## Caso: argumento sobrando sem subcomando escolhido usa o usage da raiz

- **Requisito:** "sem subcomando escolhido, o erro continua saindo pela
  raiz mesmo" (comportamento correto, não regressão)
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry --bogus` (nenhum subcomando escolhido)
- **Quando:** o argparse rejeita a chamada
- **Então:** o `USO` mostrado é o da raiz (com a listagem de subcomandos)

## Caso: bloco USO mostra um token por linha em vez de tudo numa linha so

- **Requisito:** "isso aq ta mt bangunçado n?" -- `sentry new [-h] [--prompt
  PROMPT] [--json] name` tudo numa linha
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new -h`
- **Quando:** o bloco `USO` é impresso
- **Então:** cada token (`name`, `[-h]`, `[--prompt PROMPT]`, `[--json]`)
  aparece na sua própria linha, a partir da segunda indentada sob o
  primeiro token

## Caso: posicional vem primeiro no USO, depois -h, depois o resto

- **Requisito:** "organize em uma ordem logica ... obrigatório primeiro:
  name, -h, --prompt, --json"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new -h`
- **Quando:** o bloco `USO` é impresso
- **Então:** a ordem dos tokens é `name`, `[-h]`, `[--prompt PROMPT]`,
  `[--json]` -- posicional primeiro, `-h` em seguida, resto na ordem
  declarada

## Caso: sentry new -h tambem mostra o wordmark

- **Requisito:** "no sentry new -h eu quero isso: [wordmark]"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new -h`
- **Quando:** a ajuda é impressa
- **Então:** o wordmark aparece antes do bloco `USO`

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

## Caso: linha do checklist nao mostra nenhuma badge por categoria

- **Requisito:** "esse creates, written, installed e ready nao deveriam
  existir, antes nao existia, remova"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init` numa primeira execução, criando todas as
  categorias
- **Quando:** o checklist é impresso
- **Então:** nenhuma linha traz `created`, `written`, `installed` ou `ready`
  alinhado à direita — só o `✓` verde e o texto (mais o detalhe do item de
  ambiente, quando houver)

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
  ganha o mesmo wordmark que `sentry init` (histórico: nenhum subcomando
  repetia, até o item 40 estender pra todos)
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry -h` (ou `--help`) na raiz
- **Quando:** a ajuda é impressa
- **Então:** o wordmark aparece antes do título `USO`

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

## Caso: comandos e USO tem a mesma indentacao

- **Requisito:** "os comandos em comando estão mt a direita, coloque como
  estão em extras: mais próximos a esquerda" -- o argparse por padrão
  indenta a lista de comandos com 4 espaços e a de opções com 2 (histórico:
  a comparação original era com `EXTRAS`, aposentada desde que a descrição
  de flag passou a morar dentro do `USO` em todo comando)
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** `sentry -h`
- **Quando:** a ajuda é impressa
- **Então:** as linhas de comando (`COMANDOS`) e o bloco `USO` começam com
  a mesma indentação de 2 espaços

## Caso: argumentos e uso de um subcomando tem a mesma indentacao

- **Requisito:** "no init e no help tudo tem um espaço antes e nos outros
  alguns tem o espaço e outros não ... margem a esquerda"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** `sentry check -h` (posicional comum, não a listagem de
  subcomandos da raiz)
- **Quando:** a ajuda é impressa
- **Então:** a linha de `ARGUMENTOS` (`slug`) começa com a mesma
  indentação de 2 espaços que o bloco `USO`

## Caso: bloco USO e linha de erro tem a mesma margem que as outras secoes

- **Requisito:** "sentry new vc n deu o espaçamento aqui... nem aqui: erro
  ... padronize tudo com essa margem"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new -h` (bloco USO) e `sentry new` sem `name` (linha de
  erro)
- **Quando:** a saída é impressa
- **Então:** a linha `sentry new name` (USO), as linhas indentadas por
  baixo dela e a linha `erro: ...` começam com a mesma indentação de 2
  espaços que `EXTRAS` já usa

## Caso: sentry sem argumento equivale a sentry -h

- **Requisito:** "sentry sem nenhum argumento não imprimia nada ... quer
  que eu mude pra mostrar a ajuda"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry` sem nenhum argumento
- **Quando:** o comando roda
- **Então:** a saída é igual à de `sentry -h` (wordmark, `COMANDOS`,
  `EXTRAS`) e o código de saída é 0

## Caso: erro da raiz sem subcomando tambem mostra o wordmark

- **Requisito:** "primeiramente quero [wordmark]" (nos erros
  `comando-que-nao-existe`/`--bogus`)
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry comando-que-nao-existe` e `sentry --bogus`
- **Quando:** o argparse rejeita a chamada
- **Então:** o wordmark aparece antes do bloco `USO`/`erro`, nos dois casos

## Caso: lista de subcomandos no USO da raiz usa colchete reto sem os 3 pontos

- **Requisito:** "quero que a {...} ... com [] e que seja: init, new, ...
  com espaçamento entre eles e tire os 3 pontinhos do final"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry --bogus` (usage da raiz aparece)
- **Quando:** o bloco `USO` é impresso
- **Então:** a lista de subcomandos aparece como
  `[init, new, check, run, review, watch, status, context, report,
  history, clear]` -- colchete reto, espaço depois da vírgula, sem `...`
  no final

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

## Caso: sentry --version colore o numero da versao em verde, pontos inclusos

- **Requisito:** "no version eu quero os numeros 2.0.0 tudo em verde, com
  os pontos em verde tmb"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry --version` com cor habilitada
- **Quando:** a versão é impressa
- **Então:** a saída inteira (números e pontos) sai colorida em verde

## Caso: sentry new usa o checklist com check verde do init, sem caneta nem caminho verde

- **Requisito:** "tire essa caneta e ponha o certinho q eh usado no init ...
  não quero em verde ... da pra deixar assim como do init"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new "nome da feature"` com cor habilitada
- **Quando:** a spec é criada
- **Então:** nenhum ícone de caneta (`✎`) aparece; a linha "Spec criada
  em..." e cada arquivo criado (`PROMPT.md`, `CASES.md`) começam com o
  símbolo de aprovado verde (`✓`), não uma lista horizontal separada por
  vírgula; o caminho da spec não sai colorido de verde

## Caso: sentry new sem arquivo novo mostra a linha maiuscula

- **Requisito:** "✓ nenhum arquivo novo quero que seja ✓ Nenhum arquivo
  novo"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** `sentry new` numa reexecução idempotente, sem nada novo pra
  criar
- **Quando:** o checklist é impresso
- **Então:** a linha diz "Nenhum arquivo novo", com N maiúsculo

## Caso: checklist do new usa rotulo descritivo em vez do caminho cru

- **Requisito:** "não dava pra colocar algo como 'Diretório .sentry/' ...
  ou seja algo antes deles?"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new "nome da feature"` criando `PROMPT.md` e
  `CASES.md`
- **Quando:** o checklist é impresso
- **Então:** as linhas dizem "Guardando o pedido — PROMPT.md" e "Gerando o
  template de casos — CASES.md", não o caminho cru do arquivo

## Caso: sentry new tem um titulo com tracinho antes do template

- **Requisito:** "o bloco de template ganha o mesmo titulo com tracinho"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new "nome da feature"`
- **Quando:** o template é impresso
- **Então:** um título "Template" com tracinho antecede o bloco, no mesmo
  estilo de `COMANDOS`/`EXTRAS`

## Caso: sentry new tem um titulo Vocabulario separado do Template

- **Requisito:** "isso aqui pode ganhar uma divisao nova nao acha?"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new "nome da feature"`
- **Quando:** a saída é impressa
- **Então:** um título "VOCABULÁRIO" com tracinho antecede as quatro
  linhas de valores aceitos, separado do título `TEMPLATE` acima

## Caso: valores aceitos do new saem sem cor, texto plano

- **Requisito:** "essas cores em azul nao estao com o padrao da paleta"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new "nome da feature"` com cor habilitada
- **Quando:** as quatro linhas (Camadas/Tipos/Prioridades/Tipos de campo)
  são impressas
- **Então:** nenhuma sai colorida em azul (nem em nenhuma outra cor)

## Caso: comando check sugerido pelo new sai em verde, sem crases

- **Requisito:** "tire a aspas e deixe em verde"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new "nome da feature"` com cor habilitada
- **Quando:** a sugestão final é impressa
- **Então:** `sentry check <slug>` aparece em verde, sem crases ao redor

## Caso: sem espacamento duplo antes do titulo Vocabulario

- **Requisito:** "ta com espaçamento duplo, despadronizando a aplicação"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** `sentry new "nome da feature"`
- **Quando:** a saída é impressa
- **Então:** existe só uma linha em branco entre o fim do `TEMPLATE` e o
  título `VOCABULÁRIO`, nunca duas

## Caso: sentry new tem um titulo Proximo passo antes da dica do check

- **Requisito:** "acho que poderia ter um titulo antes disso tmb ne, ta
  meio largado"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new "nome da feature"`
- **Quando:** a saída é impressa
- **Então:** um título "PRÓXIMO PASSO" com tracinho antecede a linha
  "Depois rode sentry check..."

## Caso: sentry new --json continua JSON valido, so a ordem das chaves muda

- **Requisito:** "podemos padronizar com titulos e o sentry v2.0.0 para
  deixar ate mais legivel" -- esclarecido para legibilidade sem quebrar o
  parse
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new "nome da feature" --json`
- **Quando:** a saída é impressa
- **Então:** `json.loads` na saída inteira não lança exceção, e a primeira
  chave do objeto é `specDir`, não `artifact`

## Caso: history colore delta de cobertura e de testes pelo sentido

- **Requisito:** "cada delta de cobertura/teste sai verde quando o numero
  favorece o projeto ... e vermelho no sentido contrario"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** duas execuções comparáveis, uma com cobertura/passed subindo e
  failed caindo, outra com o sentido invertido
- **Quando:** `sentry history` compara as duas
- **Então:** deltas favoráveis saem em verde e desfavoráveis em vermelho
- **Classe:** delta_do_historico/valido

## Caso: history nao colore delta zero ou indisponivel

- **Requisito:** "zero e indisponivel ficam sem cor, nem bons nem ruins"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** um delta de cobertura igual a zero e outro indisponível
- **Quando:** `sentry history` formata a linha
- **Então:** nenhum dos dois recebe cor de bom ou de ruim
- **Classe:** delta_do_historico/zero-ou-indisponivel

## Caso: history colore achados novos resolvidos e persistentes

- **Requisito:** "achados novos saem vermelhos ... resolvidos verdes ...
  persistentes amarelos"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** duas execuções com achados novos, resolvidos e persistentes
- **Quando:** `sentry history` compara as duas
- **Então:** cada lista sai na cor correspondente ao seu sentido

## Caso: history colore a transicao de veredito pelos dois status

- **Requisito:** "a transicao de veredito usa a cor de cada status dos dois
  lados da seta"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** duas execuções com veredito diferente
- **Quando:** `sentry history` imprime a transição
- **Então:** o status de origem e o de destino saem cada um na cor do seu
  próprio veredito

## Caso: clear sem nada a remover ganha o simbolo de aprovado

- **Requisito:** "'Nada a remover' ganha o simbolo de aprovado"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** nenhuma execução no histórico
- **Quando:** `sentry clear` roda
- **Então:** a linha "Nada a remover." traz o símbolo de aprovado

## Caso: clear avisa a contagem em amarelo antes de confirmar

- **Requisito:** "a contagem do que seria removido sai em amarelo"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** execuções no histórico, `sentry clear` sem `--yes`
- **Quando:** o escopo é impresso
- **Então:** a contagem de execuções a remover sai em amarelo

## Caso: clear aplicado confirma em verde com simbolo de aprovado

- **Requisito:** "apos aplicar, a confirmacao ganha o simbolo de aprovado em
  verde"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry clear --yes` com execuções a remover
- **Quando:** a remoção é aplicada
- **Então:** a linha de confirmação traz o símbolo de aprovado em verde

## Caso: watch colore o modo instantaneo de azul e o completo de magenta

- **Requisito:** "o modo de cada reavaliacao sai colorido -- azul pro
  instantaneo ... magenta pro completo"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** um arquivo comum salvo e, noutra rodada, um arquivo de teste
- **Quando:** `sentry watch` reavalia cada um
- **Então:** o modo impresso sai azul para instantâneo e magenta para
  completo

## Caso: watch imprime Parado em amarelo ao sair com Ctrl+C

- **Requisito:** ""Parado." ao sair com Ctrl+C sai em amarelo"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry watch` rodando
- **Quando:** o usuário interrompe com Ctrl+C
- **Então:** a linha "Parado." sai em amarelo, não em vermelho de erro

## Caso: uso de subcomando ganha titulo com tracinho e colore comando e flag

- **Requisito:** "quero um titulo uso, alem disso o comando deveria ficar em
  verde, padronize"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new -h` com cor habilitada
- **Quando:** o uso é impresso
- **Então:** aparece o título `USO` com tracinho (não a palavra `usage:`
  nem `uso:` inline), seguido de `sentry` e `new` coloridos em verde (as
  duas palavras) e de cada flag (`-h`, `--prompt`, `--json`) também em
  verde
- **Classe:** flag_generica/valido

## Caso: erro do argparse nao repete sentry comando antes de erro

- **Requisito:** "sentry new: delete essa parte"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new` sem o argumento `name`
- **Quando:** a mensagem de erro é impressa
- **Então:** a linha de erro começa direto com `erro:`, sem o prefixo
  `sentry new: ` que o argparse usa por padrão

## Caso: subcomando sem name nem valor colorido ainda assim tem flag colorida

- **Requisito:** "colore algumas coisas como nos outros"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry check -h` com cor habilitada (comando sem flags além de
  `-h`)
- **Quando:** o usage é impresso
- **Então:** `-h` aparece colorido em verde; nenhuma outra palavra do texto
  ganha cor de flag
- **Classe:** flag_generica/valido

## Caso: argumento obrigatorio ausente vira mensagem em portugues

- **Requisito:** "'the following arguments are required' ... nao esta
  padronizado: nao ta em portugues"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** `sentry new` sem o argumento posicional `name`
- **Quando:** o argparse rejeita a chamada
- **Então:** a mensagem de erro diz "argumento(s) obrigatório(s)
  ausente(s): name", nunca "the following arguments are required"
- **Classe:** mensagem_de_erro_traduzida/valido

## Caso: escolha invalida de subcomando vira mensagem em portugues

- **Requisito:** "mensagens de erro do argparse ... ficam no mesmo padrao
  visual e no mesmo idioma"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry comando-que-nao-existe`
- **Quando:** o argparse rejeita a chamada
- **Então:** a mensagem de erro diz "escolha inválida", nunca "invalid
  choice"
- **Classe:** mensagem_de_erro_traduzida/valido

## Caso: escolha invalida nao repete a lista de opcoes que o USO ja mostra

- **Requisito:** "(opções: init, new, check, ...) remove pq fica
  redundante"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry comando-que-nao-existe`
- **Quando:** o argparse rejeita a chamada
- **Então:** a mensagem de erro termina em `escolha inválida: 'x'`, sem
  `(opções: ...)` no final

## Caso: sentry init -h tambem mostra o wordmark

- **Requisito:** "sentry init -h ... falta o [wordmark]"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init -h`
- **Quando:** a ajuda é impressa
- **Então:** o wordmark aparece antes do bloco `USO`

## Caso: token de -h no USO mostra as duas formas da flag

- **Requisito:** "sentry init [-h] , falta add o --help, ponha em todos q
  estiverem assim"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init -h`, `sentry new -h` e `sentry --bogus`
- **Quando:** o bloco `USO` é impresso
- **Então:** o token da flag de ajuda aparece como `[-h, --help]`, nunca só
  `[-h]`, em qualquer um dos três

## Caso: sentry init -h funde a descricao de cada flag no USO e some com EXTRAS

- **Requisito:** "eu quero que o sentry init -h e sentry init --help e
  somente ele fique assim, SOMENTE"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry init -h` e `sentry init --help`
- **Quando:** a ajuda é impressa
- **Então:** cada flag no `USO` (`[-h, --help]`, `[--install]`) vem seguida
  da própria descrição na mesma linha, e a seção `EXTRAS` não aparece

## Caso: sentry new -h funde a descricao no USO mantendo ARGUMENTOS

- **Requisito:** "quero o exato mesmo comportamento do sentry init -h e
  sentry init --help, mas deixando o ARGUMENTOS pfv"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry new -h` e `sentry new --help`
- **Quando:** a ajuda é impressa
- **Então:** cada flag no `USO` (`[-h, --help]`, `[--prompt PROMPT]`,
  `[--json]`) vem seguida da própria descrição na mesma linha, a seção
  `EXTRAS` não aparece, e a seção `ARGUMENTOS` (com `name`) continua
  existindo normalmente

## Caso: fusao de USO e EXTRAS vale em todo comando, raiz inclusive

- **Requisito:** começou restrito a `init` ("e somente ele fique assim,
  SOMENTE", item 30), depois `new` (item 31), depois `check`
  ("sentry check -h e sentry check --help nao estao com o comportamento do
  help do init e do new, padronize"), até virar "aplica em todos de uma vez"
  (item 39) -- `EXTRAS` sai de todo comando, `check`/`run`/`review`/`watch`/
  `status`/`context`/`report`/`history`/`clear`/raiz inclusive
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry check -h`, `sentry clear -h`, `sentry run -h`,
  `sentry review -h`, `sentry watch -h`, `sentry status -h`,
  `sentry context -h`, `sentry report -h`, `sentry history -h` e
  `sentry -h` (raiz)
- **Quando:** a ajuda de cada um é impressa
- **Então:** todos mostram a descrição de cada flag dentro do `USO`, sem
  seção `EXTRAS` -- nenhuma exceção sobra

## Caso: erro de sentry init e sentry new nao funde USO com EXTRAS

- **Requisito:** "somente ele" -- restrito à ajuda (`-h`/`--help`), não ao
  caminho de erro, em ambos os comandos
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry init --bogus` e `sentry new` sem `name`
- **Quando:** o argparse rejeita cada chamada
- **Então:** o `USO` continua compacto, sem descrição de flag colada, nos
  dois casos

## Caso: mensagem de erro sem tradutor reconhecida cai no texto original

- **Requisito:** "uma mensagem sem tradutor reconhecida cai no texto
  original em ingles, nunca quebra"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Dado:** uma mensagem de erro do argparse sem padrão conhecido pelo
  tradutor
- **Quando:** a tradução é tentada
- **Então:** a mensagem original volta intocada, sem lançar exceção
- **Classe:** mensagem_de_erro_traduzida/nao-reconhecida

## Caso: palavra erro sai em vermelho na linha de erro

- **Requisito:** "a palavra error:/erro: na linha de erro sai em vermelho"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new` sem o argumento `name`, com cor habilitada
- **Quando:** a mensagem de erro é impressa
- **Então:** a palavra "erro:" aparece em vermelho

## Caso: subcomando sem subcomandos proprios usa titulo Argumentos

- **Requisito:** "o cabecalho positional arguments: de um subcomando vira
  o titulo com tracinho ARGUMENTOS (raiz continua sendo COMANDOS)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** baixa
- **Dado:** `sentry new -h` (tem o posicional `name`) e `sentry -h` (raiz)
- **Quando:** a ajuda de cada um é impressa
- **Então:** `sentry new -h` mostra o título `ARGUMENTOS`, `sentry -h`
  continua mostrando `COMANDOS`

## Caso: erro de multiplas specs do check sai vermelho minusculo e com margem

- **Requisito:** "não está como em erro: argumento(s) obrigatório(s)
  ausente(s): name -- falta o erro em vermelho, sem letra maiúscula e a
  margem"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry check` sem `slug`, com mais de uma spec no projeto
- **Quando:** o erro é impresso
- **Então:** a linha começa com margem de 2 espaços e `erro:` (minúsculo)
  em vermelho, nunca `Erro:`

## Caso: erro de multiplas specs do check tambem mostra wordmark e USO

- **Requisito:** "no sentry check n tem [wordmark]" -- comparado com
  `sentry check --bogus`, que já mostrava
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry check` sem `slug`, com mais de uma spec no projeto
- **Quando:** o erro é impresso
- **Então:** o wordmark aparece antes do bloco `USO`, que aparece antes da
  linha `erro:`; o `USO` é compacto (sem descrição de flag), igual todo
  erro do argparse já é

## Caso: check com sucesso ou achados de validacao mostra wordmark e titulo CHECK

- **Requisito:** "queria ver funcionando tmb, alem disso falta o [wordmark]
  e um titulo ne"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Dado:** `sentry check <slug>` com uma spec que existe -- validada com
  sucesso, e noutra rodada com achados (título ausente, seção ausente)
- **Quando:** o resultado é impresso
- **Então:** nos dois casos, o wordmark aparece antes do título "CHECK" com
  tracinho, que aparece antes da linha `☑ <spec>: N caso(s), M campo(s)`

## Classes não aplicáveis

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
- **delta_do_historico/vazio**: o campo é um de três estados fechados
  (favorável/desfavorável/neutro) decidido pelo sinal do número, nunca
  ausente — mesmo "indisponível" já é o próprio caso neutro.
- **delta_do_historico/tamanho-maximo-excedido**: não é texto digitado, é uma
  classificação derivada de um número.
- **delta_do_historico/caracteres-especiais**: idem — não é entrada de
  usuário.
- **flag_generica/vazio**: toda flag vem de um `add_argument` declarado no
  código; não existe usage/ajuda sem nenhuma flag a testar aqui — `sentry
  clear -h` por exemplo já tem `-h` sempre presente.
- **flag_generica/tamanho-maximo-excedido**: nome de flag é um dos poucos
  declarados no código, não texto digitado por quem usa a CLI.
- **flag_generica/caracteres-especiais**: idem — não é entrada de usuário.
- **mensagem_de_erro_traduzida/vazio**: o argparse nunca chama `error()` com
  mensagem vazia; não há esse caso a testar.
- **mensagem_de_erro_traduzida/tamanho-maximo-excedido**: a mensagem vem do
  argparse formatando nomes de argumento e valores já limitados pelo próprio
  código, não texto arbitrário digitado por quem usa a CLI.
- **mensagem_de_erro_traduzida/caracteres-especiais**: idem — o texto de
  origem é sempre um dos padrões fixos do argparse.
