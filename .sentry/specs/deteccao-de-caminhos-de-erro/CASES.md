# Detecção de caminhos de erro

## Prompt

Detecção de caminhos de erro (`select_error_paths`) fora de Python: reconhecer `throw`,
`panic`, `raise`/`rescue` e assemelhados por padrão sintático ancorado no início da linha,
já que fora de Python não há parser AST na biblioteca padrão -- e declarar essa diferença
de confiabilidade como limitação, não escondê-la atrás da mesma evidência do AST. Palavra
de erro dentro de comentário ou string não pode virar falso caminho de erro. Uma linha
excluída da medição (`# pragma: no cover`) não pode virar achado de "caminho sem teste" --
mas a exclusão é por linha, não contamina as vizinhas nem o arquivo inteiro. E uma extensão
sem padrão declarado (YAML, texto puro) fica fora da análise, sem falso positivo nem
limitação fabricada.

## Campos

- **extensao_do_arquivo**: texto — a extensão do arquivo alterado
  (`.py`, `.ts`, `.go`, `.yaml`, ...), que decide se e como a detecção de
  caminho de erro se aplica.
- **origem_do_texto**: texto — se a palavra de erro (`throw`, `raise`, ...)
  aparece como código de verdade, início de linha, ou dentro de um
  comentário/string, onde não conta.
- **linha_excluida**: booleano — se a linha foi marcada como excluída da
  medição de cobertura (`# pragma: no cover`) pelo projeto.

## Caso: caminho de erro e detectado fora de Python

- **Requisito:** "Antes so `.py` era analisado: um `throw` alterado e sem
  teste passava despercebido em qualquer projeto que nao fosse Python"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** extensao_do_arquivo/valido
- **Dado:** um arquivo `.ts` com `throw new Error('x');` numa linha alterada
  e sem dado de execução
- **Quando:** `select_error_paths` analisa o arquivo
- **Então:** a linha aparece em `uncovered` como caminho de erro do tipo
  `throw`
- **Entrada:** `extensao_do_arquivo = ".ts"`

## Caso: deteccao sem AST e registrada como limitacao

- **Requisito:** "Fora de Python a deteccao e' por padrao sintatico.
  Equiparar as duas evidencias esconderia que uma delas pode passar batido"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** extensao_do_arquivo/valido
- **Dado:** um arquivo `.go` com `panic("x")` numa linha alterada e sem
  dado de execução
- **Quando:** `select_error_paths` analisa o arquivo
- **Então:** a linha aparece em `uncovered`, e uma limitação registra que a
  detecção naquele arquivo foi por padrão sintático, não AST
- **Entrada:** `extensao_do_arquivo = ".go"`

## Caso: palavra de erro em comentario ou string nao vira caminho de erro

- **Requisito:** "Ancorar no inicio da linha e' o que separa deteccao de
  busca textual"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** origem_do_texto/comentario-ou-string
- **Dado:** um arquivo `.ts` onde a palavra `throw` aparece dentro de um
  comentário e dentro de uma string, nunca no início real de uma linha de
  código
- **Quando:** `select_error_paths` analisa o arquivo
- **Então:** nenhuma linha entra em `uncovered`

## Caso: linha excluida da medicao nao vira caminho de erro sem teste

- **Requisito:** "`# pragma: no cover` tira a linha da medicao: ela nao
  aparece nem em executed nem em missing. Sem honrar a exclusao, o Sentry
  acusaria falta de teste onde houve decisao declarada"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** linha_excluida/verdadeiro
- **Dado:** um `raise` numa linha alterada, sem execução, marcada como
  excluída da medição pelo projeto
- **Quando:** `select_error_paths` analisa o arquivo
- **Então:** a linha não entra em `uncovered` nem em `covered`, e uma
  limitação registra a exclusão por pragma, nomeando a linha

## Caso: exclusao nao vale para linha que o projeto nao excluiu

- **Requisito:** "A exclusao e' por linha, nao por arquivo: excluir uma nao
  pode calar as demais, senao um pragma isolado silenciaria o arquivo
  inteiro"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** linha_excluida/falso
- **Dado:** duas linhas de caminho de erro no mesmo arquivo, sem execução,
  só uma delas excluída da medição
- **Quando:** `select_error_paths` analisa o arquivo
- **Então:** só a linha não excluída aparece em `uncovered`

## Caso: extensao sem padrao declarado continua fora da analise

- **Requisito:** uma extensão sem padrão de detecção declarado (YAML, texto
  puro) não pode gerar falso positivo nem limitação fabricada
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** extensao_do_arquivo/sem-padrao
- **Dado:** um arquivo `.yaml` com a palavra `raise` no conteúdo, numa
  linha alterada
- **Quando:** `select_error_paths` analisa o arquivo
- **Então:** a linha não entra em `uncovered`, e nenhuma limitação é
  registrada pra aquele arquivo
- **Entrada:** `extensao_do_arquivo = ".yaml"`

## Classes não aplicáveis

- **extensao_do_arquivo/vazio**: um arquivo sempre tem extensão (ou nenhuma
  parte reconhecível), caso já coberto pela classe "sem-padrao" acima.
- **extensao_do_arquivo/tamanho-maximo-excedido**: extensão é um sufixo
  curto comparado contra um mapa fechado de padrões; não há comprimento de
  usuário a limitar.
- **origem_do_texto/vazio**: uma linha vazia não contém palavra de erro
  nenhuma — não há o que detectar.
- **origem_do_texto/tamanho-maximo-excedido**: o casamento é por regex
  ancorada no início da linha, sem limite de comprimento imposto pelo
  Sentry.
- **extensao_do_arquivo/caracteres-especiais**: extensão é comparada por
  igualdade contra um mapa fechado (`.py`, `.ts`, `.go`, ...); não é texto
  digitado por usuário.
- **origem_do_texto/caracteres-especiais**: a origem (código real vs.
  comentário/string) é decidida por posição da palavra na linha, não pelo
  conteúdo em si; não há caractere que mude a classificação.
- **origem_do_texto/valido**: o caminho normal (código real, não
  comentário/string) é exercitado implicitamente por todo caso desta spec
  que afirma `uncovered` não-vazio — não é uma classe isolada a testar de
  novo aqui.
- **linha_excluida/tamanho-maximo-excedido**: a exclusão é um conjunto de
  números de linha, não texto com comprimento a limitar.
