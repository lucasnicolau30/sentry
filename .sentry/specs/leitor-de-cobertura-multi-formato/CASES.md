# Leitor de cobertura multi-formato

## Prompt

`CoverageAdapter` reconhece três formatos de cobertura pelo próprio conteúdo (coverage.py
JSON, lcov, Cobertura XML), sem exigir que o projeto declare qual está usando. Precisa
distinguir "formato não reconhecido" de "formato certo porém malformado" (mensagens de
erro diferentes), rejeitar um relatório do formato certo mas sem nenhum registro real (0%
que na verdade é ausência de evidência), relativizar caminho absoluto do lcov contra a
raiz do projeto (preservando o caminho como veio quando cai fora da raiz, como em
monorepo), e não contar duas vezes a mesma linha quando um relatório lcov mesclado repete
`DA:` pra ela. A cobertura do código alterado (`calculate_changed_coverage`) precisa
funcionar igual a partir de um relatório lcov, não só de coverage.py.

## Campos

- **conteudo_do_relatorio**: texto — o conteúdo bruto do arquivo de
  cobertura, de onde `detect_coverage_format` decide o formato.
- **registro_de_cobertura**: booleano — se o relatório, além de ter o
  formato certo, contém pelo menos um registro real de linha coberta.
- **caminho_no_relatorio**: texto — o caminho de arquivo como o relatório
  de cobertura o grava (absoluto, relativo, dentro ou fora da raiz do
  projeto analisado).
- **linha_repetida**: booleano — se a mesma linha aparece mais de uma vez
  num relatório lcov mesclado.

## Caso: formato irreconhecível é distinto de formato malformado

- **Requisito:** "Conteudo que nao e' nenhum dos formatos aceitos: o erro
  precisa dizer quais sao, em vez de alegar que um formato conhecido esta
  corrompido"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** conteudo_do_relatorio/nao-reconhecido
- **Dado:** um arquivo de cobertura cujo conteúdo não corresponde a
  nenhum dos três formatos suportados
- **Quando:** `CoverageAdapter().read(path)` lê o arquivo
- **Então:** o erro começa com "formato de cobertura nao reconhecido" e
  cita os formatos aceitos (lcov, cobertura)
- **Entrada:** `conteudo_do_relatorio = "invalid"`

## Caso: detecta os três formatos pelo conteúdo

- **Requisito:** reconhecimento automático sem declaração explícita de
  formato
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** conteudo_do_relatorio/valido
- **Dado:** conteúdo de exemplo de coverage.py JSON, lcov, Cobertura XML e
  texto solto
- **Quando:** `detect_coverage_format` analisa cada um
- **Então:** devolve `"coverage.py"`, `"lcov"`, `"cobertura"` e `None`,
  respectivamente

## Caso: relatório lcov produz cobertura por linha

- **Requisito:** "LCOV e' o formato de nyc/c8/Jest e simplecov:
  DA:<linha>,<execucoes>"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** conteudo_do_relatorio/lcov
- **Dado:** um relatório lcov com linhas executadas e não executadas
- **Quando:** `CoverageAdapter().read` lê o arquivo
- **Então:** `executed_lines` traz só as linhas com execução > 0, e o
  percentual do arquivo/global é calculado a partir delas
- **Entrada:** `conteudo_do_relatorio = "SF:src/app.js\\nDA:1,1\\nDA:2,0\\nDA:3,4\\nend_of_record"`

## Caso: relatório cobertura xml produz cobertura por linha

- **Requisito:** "Cobertura XML e' o formato de JaCoCo, coverlet e
  coverage.py xml"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** conteudo_do_relatorio/cobertura-xml
- **Dado:** um relatório Cobertura XML com `line-rate` e linhas com `hits`
- **Quando:** `CoverageAdapter().read` lê o arquivo
- **Então:** `executed_lines` traz as linhas com `hits > 0`, e o
  `global_percent` vem do `line-rate` declarado no próprio relatório

## Caso: lcov com caminho absoluto casa com o caminho relativo do diff

- **Requisito:** "nyc e Jest gravam caminho absoluto; o diff do Git e'
  sempre relativo a raiz. Sem relativizar, nenhum arquivo casaria e a
  cobertura alterada sumiria"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** caminho_no_relatorio/valido
- **Dado:** um lcov com `SF:` apontando pro caminho absoluto de um arquivo
  dentro da raiz do projeto
- **Quando:** `CoverageAdapter().read(path, root=...)` lê o arquivo
- **Então:** o caminho relativizado à raiz aparece em `executed_lines`

## Caso: lcov mesclado nao infla a contagem ao repetir a mesma linha

- **Requisito:** "Relatorios mesclados repetem DA para a mesma linha;
  contar em lista faria a cobertura passar de 100%"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** linha_repetida/verdadeiro
- **Dado:** um lcov com duas entradas `DA:` para a linha 1 (uma com
  execução, outra sem)
- **Quando:** `CoverageAdapter().read` lê o arquivo
- **Então:** a linha 1 aparece uma única vez em `executed_lines`, sem
  inflar o percentual calculado

## Caso: relatório do formato certo porém sem nenhum registro é recusado

- **Requisito:** "Um lcov só com cabecalho, ou um XML sem <class
  filename=>, tem o formato certo e nenhum dado: aceitar isso reportaria 0%
  em vez de dizer que nao ha evidencia, e 0% de cobertura vira achado de
  codigo sem teste"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** registro_de_cobertura/ausente
- **Dado:** um lcov só com cabeçalho (`TN:`, sem `SF:`/`DA:`) e um XML
  Cobertura sem nenhum `<class filename=...>`
- **Quando:** `CoverageAdapter().read` lê cada um
- **Então:** o erro nomeia a ausência de registro (`"nenhum registro
  SF:/DA:"` ou `"nenhum <class filename="`), em vez de reportar 0%

## Caso: caminho fora da raiz do projeto e mantido como veio

- **Requisito:** "Monorepo pode reportar arquivo fora da raiz analisada:
  relative_to falha e o caminho original precisa ser preservado, nao virar
  erro"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** caminho_no_relatorio/fora-da-raiz
- **Dado:** um lcov com `SF:` apontando pra um arquivo fora da raiz
  declarada em `root=`
- **Quando:** `CoverageAdapter().read(path, root=...)` lê o arquivo
- **Então:** nenhum erro é levantado, e o caminho original (não
  relativizado) aparece em `executed_lines`

## Caso: cobertura alterada funciona a partir de um relatorio lcov

- **Requisito:** "O ponto do item: um projeto Node passa a ter veredito
  real, nao inconclusivo"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Dado:** um relatório lcov lido pelo `CoverageAdapter`, com um arquivo
  alterado em duas linhas (uma coberta, uma não)
- **Quando:** `calculate_changed_coverage` calcula a partir dele
- **Então:** o percentual do código alterado é calculado corretamente
  (50%), a partir do lcov, sem depender de coverage.py

## Classes não aplicáveis

- **conteudo_do_relatorio/vazio**: um arquivo vazio já é o caminho de
  "formato não reconhecido" (nenhum padrão bate) — mesma classe do caso
  acima, não uma classe à parte.
- **conteudo_do_relatorio/tamanho-maximo-excedido**: o conteúdo é lido
  inteiro do arquivo de cobertura; não há corte próprio do Sentry.
- **conteudo_do_relatorio/caracteres-especiais**: o formato é decidido por
  padrão estrutural (chaves JSON, `SF:`/`DA:`, tag `<coverage>`), não por
  caractere isolado que mude o resultado.
- **registro_de_cobertura/valido**: o caminho feliz, já coberto pelos
  casos de leitura de cada formato acima — não é uma classe de erro à
  parte aqui.
- **caminho_no_relatorio/vazio**: um `SF:`/`filename` vazio não é um
  relatório de formato válido — já cai na classe "sem registro".
- **caminho_no_relatorio/tamanho-maximo-excedido**: caminho de arquivo
  cujo comprimento é limite do sistema operacional, não do Sentry.
- **caminho_no_relatorio/caracteres-especiais**: o caminho é comparado por
  `relative_to`/igualdade de string contra o sistema de arquivos real, sem
  parsing que dependa de caractere específico.
- **linha_repetida/falso**: o caminho comum de uma linha aparecer uma
  única vez, já coberto pelos demais casos de leitura de formato.
