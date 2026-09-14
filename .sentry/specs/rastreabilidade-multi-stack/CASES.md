# Rastreabilidade multi-stack e marcador órfão

## Prompt

Rastreabilidade (`build_traceability`) fora de Python: reconhecer definição de teste em
oito stacks (TS, Go, Java, Kotlin, C#, Ruby, PHP, Rust), aceitar o marcador `// cenario:`
(comentário de qualquer linguagem, não só `#`), permitir declarar `test_paths` quando o
projeto não usa a pasta `tests/` convencional, não deixar um arquivo de teste com bytes
inválidos derrubar a varredura dos demais, e nunca varrer `node_modules`/vendor em busca
de teste. E o casamento de marcador contra caso: sem normalizar acento um marcador correto
ficava preso em "não coberto"; e a associação por semelhança de nome de função tinha um
limiar frouxo demais, produzindo vínculo falso quando palavras genéricas (`sem`, `nada`,
`declarado`) somavam similaridade sem relação real de conteúdo.

## Campos

- **stack_do_teste**: texto — a linguagem/extensão do arquivo de teste
  (`.ts`, `.go`, `.java`, `.kt`, `.cs`, `.rb`, `.php`, `.rs`, entre outras).
- **diretorio_de_teste**: texto — onde `build_traceability` procura
  arquivo de teste: o padrão (`tests/`) ou o declarado via `test_paths`.
- **legibilidade_do_arquivo**: booleano — se o conteúdo do arquivo de teste
  pôde ser lido como texto válido.
- **acento_do_marcador**: booleano — se o marcador `# cenario:` foi escrito
  com ou sem acentuação em relação ao nome do caso na spec.
- **semelhanca_por_nome**: texto — o nome da função de teste, usado pra
  vincular por semelhança quando não há marcador explícito.

## Caso: rastreabilidade reconhece teste de qualquer stack

- **Requisito:** "Sem isto o parser so abria .py: um projeto Node, Go ou
  Java teria todo caso preso em 'nao coberto', mesmo com o teste existindo"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** stack_do_teste/valido
- **Dado:** um arquivo de teste em TS, Go, Java, Kotlin, C#, Ruby, PHP ou
  Rust, cujo nome de função/teste é "rejeita slug que escapa"
- **Quando:** `build_traceability` varre o diretório de testes
- **Então:** o cenário correspondente aparece como coberto, vinculado
  àquele arquivo
- **Entrada:** `stack_do_teste = ".go"`

## Caso: marcador declarado funciona com comentario de qualquer linguagem

- **Requisito:** "O marcador nao ancora no `#`: `// cenario:` vale o mesmo,
  e e' o vinculo confiavel para stacks onde a semelhanca de nome falharia"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** stack_do_teste/valido
- **Dado:** um arquivo `.ts` com `// cenario: <nome sem relação com o teste>`
- **Quando:** `build_traceability` varre o arquivo
- **Então:** o cenário com aquele nome aparece como coberto, mesmo o nome
  da função de teste não tendo nenhuma semelhança

## Caso: diretorio de teste declarado substitui os padroes

- **Requisito:** "Projeto com teste ao lado do codigo (src/foo.test.ts) nao
  tem pasta `tests/`: sem declarar onde procurar, nada seria encontrado"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** diretorio_de_teste/valido
- **Dado:** um teste em `src/feature/slug.test.ts`, fora de `tests/`
- **Quando:** `build_traceability` roda sem `test_paths` e depois com
  `test_paths=("src",)`
- **Então:** sem a declaração o cenário sai não coberto; com
  `test_paths=("src",)` o mesmo cenário aparece coberto

## Caso: arquivo de teste ilegivel nao derruba a rastreabilidade

- **Requisito:** "Varremos muito mais extensoes agora; um arquivo com bytes
  invalidos no meio do diretorio de testes nao pode impedir o vinculo dos
  demais"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** legibilidade_do_arquivo/invalido
- **Dado:** um arquivo de teste com bytes inválidos ao lado de um arquivo
  de teste válido cobrindo o mesmo cenário
- **Quando:** `build_traceability` varre o diretório
- **Então:** o cenário aparece coberto pelo arquivo válido, sem exceção
  levantada pelo arquivo ilegível

## Caso: vendor nao e varrido em busca de teste

- **Requisito:** "node_modules tem milhares de testes de terceiros; varrer
  isso seria lento e produziria vinculo com teste que nao e' do projeto"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** diretorio_de_teste/vendor
- **Dado:** um teste dentro de `tests/node_modules/lib/`, cobrindo o mesmo
  nome de um cenário declarado
- **Quando:** `build_traceability` varre o diretório
- **Então:** o cenário permanece não coberto — o diretório vendor não entra
  na varredura
- **Entrada:** `diretorio_de_teste = "tests/node_modules/lib"`

## Caso: marcador declarado casa com o caso mesmo sem acento

- **Requisito:** "Achado ao vivo: um marcador escrito sem acento
  (`evidencia`) ficava preso em 'nao coberto' contra um caso escrito com
  acento (`evidência`), porque o casamento so fazia casefold, sem
  normalizar acento"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** acento_do_marcador/sem-acento
- **Dado:** um marcador `# cenario: achados antes da evidencia bruta` (sem
  acento) contra um cenário declarado como "achados antes da evidência
  bruta" (com acento)
- **Quando:** `build_traceability` casa marcador com cenário
- **Então:** o cenário aparece coberto, sem entrar em
  `scenarios_without_tests`

## Caso: palavras genericas nao produzem vinculo por semelhanca

- **Requisito:** "Falso positivo achado em uso: o caso 'sem exclude
  declarado, nada e filtrado' saiu `coberto` vinculado a uma função sem
  relação real, porque 'sem', 'nada' e 'declarado' somavam exatamente o
  limiar antigo de similaridade. Verde falso e' pior que lacuna: o
  relatorio afirma cobertura inexistente"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** semelhanca_por_nome/generico
- **Dado:** uma função de teste cujo nome só compartilha palavras genéricas
  com o cenário, sem relação de conteúdo real, e nenhum marcador explícito
- **Quando:** `build_traceability` tenta vincular por semelhança de nome
- **Então:** o cenário permanece não coberto — a semelhança de só palavras
  genéricas não basta pra vínculo

## Caso: semelhanca real continua vinculando sem marcador

- **Requisito:** o ajuste do limiar não pode quebrar o vínculo por
  semelhança de nome quando a semelhança é real (mesmo conteúdo, sem
  marcador)
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** semelhanca_por_nome/valido
- **Dado:** uma função `test_login_com_credenciais_validas`, sem marcador,
  cobrindo o cenário "login com credenciais válidas"
- **Quando:** `build_traceability` tenta vincular por semelhança de nome
- **Então:** o cenário aparece coberto, sem `scenarios_without_tests`

## Classes não aplicáveis

- **stack_do_teste/vazio**: sem nenhum arquivo de teste, o cenário sai não
  coberto — já é o caminho feliz de `scenarios_without_tests`, coberto
  noutra spec.
- **stack_do_teste/tamanho-maximo-excedido**: a extensão do arquivo é um
  sufixo curto de um conjunto fechado de linguagens suportadas.
- **stack_do_teste/caracteres-especiais**: idem — extensão é comparada por
  igualdade contra uma lista fixa.
- **diretorio_de_teste/vazio**: sem `test_paths` declarado, o padrão
  (`tests/`) sempre se aplica — não é uma classe de erro à parte.
- **diretorio_de_teste/tamanho-maximo-excedido**: caminho de diretório
  cujo comprimento é limite do sistema de arquivos, não do Sentry.
- **diretorio_de_teste/caracteres-especiais**: o caminho é comparado
  diretamente contra o sistema de arquivos, sem parsing que dependa de
  caractere específico.
- **legibilidade_do_arquivo/vazio**: um arquivo vazio é texto válido (string
  vazia), não um arquivo ilegível — não é a mesma classe.
- **acento_do_marcador/vazio**: um marcador vazio não casa com cenário
  nenhum — já é o caminho de "sem marcador", coberto noutro caso.
- **acento_do_marcador/tamanho-maximo-excedido**: o texto do marcador vem
  do título do caso na spec, cujo comprimento não é limitado pelo Sentry.
- **semelhanca_por_nome/vazio**: uma função sem nome não existe em nenhuma
  linguagem suportada — não há entrada vazia possível aqui.
- **semelhanca_por_nome/tamanho-maximo-excedido**: nome de função/teste
  cujo comprimento é limite da linguagem, não do Sentry.
- **semelhanca_por_nome/caracteres-especiais**: o nome de função segue as
  regras de identificador da própria linguagem; não há caractere fora
  dessas regras a testar.
