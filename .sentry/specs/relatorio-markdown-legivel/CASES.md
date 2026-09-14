# Relatório markdown legível

## Prompt

Legibilidade do `markdown_report`: achados aparecem antes da evidência bruta (arquivos
alterados, saída de testes), porque o achado é o motivo do veredito e a evidência só o
sustenta; o nome legível de cada caso vem em destaque na matriz, com o id (`TC-01`) como
marca curta ao lado, em vez de repetir o id inteiro como nome; o veredito vem acompanhado
de uma frase curta explicando o que aquele status implica na prática; todo achado mostra
a regra que disparou (crase em volta do nome), pra cruzar com a tabela de regras da spec;
e classe de equivalência não aplicável aparece numa seção própria, separada das limitações
reais, pra não fazer o leitor tratar dispensa deliberada e lacuna real como igualmente
preocupantes.

## Campos

- **posicao_da_secao**: texto — o título de uma seção do relatório
  (`## Achados`, `### Arquivos alterados`, ...), usado pra checar ordem
  relativa entre seções.
- **nome_do_caso**: texto — o nome legível de um caso de teste, que deve
  aparecer em destaque separado do id curto (`TC-01`).
- **status_do_veredito**: texto — um dos quatro valores de `VerdictStatus`,
  cada um com uma frase de explicação fixa associada.
- **regra_do_achado**: texto — o identificador da regra que gerou o achado
  (`scenario-without-test`, `test-failing`, ...), que precisa aparecer entre
  crases no relatório.

## Caso: achados aparecem antes da evidência bruta

- **Requisito:** "O achado e' o motivo do veredito: tem que aparecer antes
  de arquivos alterados e saida do pytest, que so sustentam o achado"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** posicao_da_secao/valido
- **Dado:** um payload com achados, arquivos alterados e execução de testes
- **Quando:** `markdown_report` monta o documento
- **Então:** `## Achados` aparece antes de `### Arquivos alterados` e de
  `### Execução de testes`

## Caso: identificador do caso não repete o nome legível

- **Requisito:** "TC-01-nome-do-caso-inteiro-repetido e' dificil de
  escanear: o nome legivel do caso vem em destaque, o id vira so uma marca
  curta ao lado"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Classe:** nome_do_caso/valido
- **Dado:** um caso com id `TC-01-rejeita-slug-vazio` e nome legível
  "rejeita slug vazio"
- **Quando:** `markdown_report` monta a matriz de casos
- **Então:** o nome legível aparece em destaque (`**rejeita slug vazio**`) e
  o id aparece separado, encurtado (`(TC-01)`)

## Caso: veredito vem com explicacao do que significa

- **Requisito:** "So mostrar 'aprovado com ressalvas' nao diz o que fazer
  com isso: precisa de uma frase curta dizendo o que aquele status implica
  na pratica"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Classe:** status_do_veredito/valido
- **Dado:** um veredito `aprovado com ressalvas`
- **Quando:** `markdown_report` monta o documento
- **Então:** a linha do veredito inclui a explicação prática daquele status
  (menção a severidade alta ainda bloquear)
- **Entrada:** `status_do_veredito = "aprovado com ressalvas"`

## Caso: achado mostra a regra que disparou

- **Requisito:** "Sem o nome da regra, nao ha como cruzar o achado com a
  tabela de regras da SPEC para entender por que ele disparou"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** regra_do_achado/valido
- **Dado:** um achado com `rule = "test-failing"`
- **Quando:** `markdown_report` monta a lista de achados
- **Então:** o nome da regra aparece entre crases (`` `test-failing` ``)
- **Entrada:** `regra_do_achado = "test-failing"`

## Caso: classe nao aplicavel aparece separada das limitacoes reais

- **Requisito:** "Misturar dispensa deliberada com lacuna real do Sentry faz
  o leitor tratar as duas como igualmente preocupantes, quando uma delas
  nao e'"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Dado:** um payload com `catalog_limitations` (lacuna real) e
  `justified_classes` (dispensa deliberada)
- **Quando:** `markdown_report` monta o documento
- **Então:** `## Limitações` aparece antes de `## Classes não aplicáveis`, e
  cada conteúdo aparece só na sua própria seção, nunca misturado

## Classes não aplicáveis

- **posicao_da_secao/vazio**: uma seção sempre tem título fixo no template
  do relatório; não existe seção sem nome a testar.
- **posicao_da_secao/tamanho-maximo-excedido**: os títulos são literais
  fixos do código, não texto digitado com comprimento a limitar.
- **posicao_da_secao/caracteres-especiais**: idem — não é entrada de
  usuário.
- **nome_do_caso/vazio**: o nome vem sempre do id do caso, que nunca é
  vazio — é derivado do título do `## Caso:` na spec.
- **nome_do_caso/tamanho-maximo-excedido**: o nome vem do título do caso na
  spec, cujo comprimento é decisão de quem escreve a spec, não do Sentry.
- **nome_do_caso/caracteres-especiais**: o nome é texto livre em markdown,
  sem parsing que dependa de caractere específico.
- **status_do_veredito/vazio**: todo `VerdictStatus` é um dos quatro valores
  do enum; não existe veredito vazio.
- **status_do_veredito/tamanho-maximo-excedido**: um de quatro valores
  fixos do enum, não texto digitado.
- **status_do_veredito/caracteres-especiais**: idem — valor fechado do enum.
- **regra_do_achado/vazio**: toda regra vem de um `Finding` já construído
  pelo domínio, que sempre declara uma regra; não existe achado sem regra.
- **regra_do_achado/tamanho-maximo-excedido**: nomes de regra são
  identificadores fixos do código (`kebab-case`), não texto digitado.
- **regra_do_achado/caracteres-especiais**: idem — identificador fechado do
  conjunto de regras do domínio.
