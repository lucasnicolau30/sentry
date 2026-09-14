# Fase 1 — parar de aprovar sem medir

## Prompt

Fase 1: parar de aprovar sem medir. (a) O init do Sentry escreve .sentry/specs/ no
.gitignore de todo projeto, tornando spec — intencao declarada — invisivel para o CI e
para o resto do time; specs precisam passar a ser versionadas, e projetos existentes devem
ter essa linha removida na proxima inicializacao, sem apagar as outras entradas. (b) O
workflow de auto-analise trata o codigo de saida 3 (inconclusivo/infraestrutura) como
sucesso, entao um checkout sem spec fica verde sem medir nada; qualquer codigo de saida
acima de ressalva precisa derrubar o build. (c) O relatorio nao registra qual commit foi
analisado, entao latest.md envelhece sem avisar: o relatorio passa a gravar o commit e o
instante da analise, e o comando report acusa quando o commit gravado nao e o HEAD atual,
em vez de exibir como veredito corrente.

## Campos

- **entrada_gitignore**: texto — uma linha do `.gitignore` que o `sentry init` gerencia.
  A questão é qual conjunto de linhas o init escreve e qual ele passa a remover.
- **codigo_de_saida**: inteiro — o código que o `sentry run` devolve ao job de
  auto-análise: 0 aprovado, 1 ressalva, 2 reprovado, 3 inconclusivo/infraestrutura.
  O que se cobra aqui é a tradução desse código em build verde ou vermelho.
- **commit_analisado**: texto — o SHA do commit sobre o qual a análise foi feita, gravado
  no relatório. É ele que permite saber se `latest.md` ainda descreve o HEAD.
- **linha_alterada**: texto — uma linha do diff, candidata a entrar no cálculo da
  cobertura do código alterado. O que se cobra é quais linhas o denominador aceita.

## Caso: specs saem do gitignore na proxima inicializacao

- **Requisito:** "specs precisam passar a ser versionadas... projetos existentes devem ter
  essa linha removida na proxima inicializacao"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** entrada_gitignore/valido
- **Dado:** um projeto cujo `.gitignore` já contém `.sentry/specs/`, escrito por uma
  versão anterior do `init`
- **Quando:** o `sentry init` roda de novo
- **Então:** a linha `.sentry/specs/` não está mais no arquivo
- **Entrada:** `entrada_gitignore = ".sentry/specs/"`

## Caso: gitignore novo nasce sem a linha de specs

- **Requisito:** "specs precisam passar a ser versionadas" — vale para projeto novo, não
  só para migração
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** entrada_gitignore/vazio
- **Dado:** um projeto sem `.gitignore` nenhum
- **Quando:** o `sentry init` cria o arquivo
- **Então:** o arquivo criado não contém `.sentry/specs/`
- **Entrada:** `entrada_gitignore = ""`

## Caso: as outras entradas do init sobrevivem a remocao

- **Requisito:** "sem apagar as outras entradas"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** entrada_gitignore/valido
- **Dado:** um `.gitignore` com todas as entradas que o `init` escreve, inclusive
  `.sentry/specs/`
- **Quando:** o `sentry init` roda de novo
- **Então:** `.sentry/sentry.db`, `.sentry/runs/`, `.sentry/test-plans/`,
  `.sentry/reports/*` e `!.sentry/reports/latest.md` continuam no arquivo
- **Entrada:** `entrada_gitignore = ".sentry/runs/"`

## Caso: linha parecida escrita pelo usuario nao e removida

- **Requisito:** a remoção é da entrada que o `init` escreveu, não de qualquer linha que a
  contenha; apagar linha do usuário seria mudar a configuração dele sem pedir
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** entrada_gitignore/caracteres-especiais
- **Dado:** um `.gitignore` com a linha `.sentry/specs/rascunhos/`, escrita pelo usuário
- **Quando:** o `sentry init` roda
- **Então:** essa linha permanece intacta no arquivo
- **Entrada:** `entrada_gitignore = ".sentry/specs/rascunhos/"`

## Caso: codigo de aprovado mantem o build verde

- **Requisito:** "qualquer codigo de saida acima de ressalva precisa derrubar o build" —
  logo, aprovado não derruba
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** codigo_de_saida/zero
- **Dado:** o job de auto-análise recebendo o código de saída do `sentry run`
- **Quando:** o código é 0 (aprovado)
- **Então:** o passo termina com sucesso e o build fica verde
- **Entrada:** `codigo_de_saida = 0`

## Caso: codigo de ressalva mantem o build verde

- **Requisito:** "acima de ressalva" — ressalva é o limite, e ainda passa
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** codigo_de_saida/valido
- **Dado:** o job de auto-análise recebendo o código de saída do `sentry run`
- **Quando:** o código é 1 (aprovado com ressalvas)
- **Então:** o passo termina com sucesso e o build fica verde
- **Entrada:** `codigo_de_saida = 1`

## Caso: codigo de reprovado derruba o build

- **Requisito:** "qualquer codigo de saida acima de ressalva precisa derrubar o build"
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** codigo_de_saida/valido
- **Dado:** o job de auto-análise recebendo o código de saída do `sentry run`
- **Quando:** o código é 2 (reprovado)
- **Então:** o passo termina com falha e o build fica vermelho
- **Entrada:** `codigo_de_saida = 2`

## Caso: codigo de inconclusivo derruba o build

- **Requisito:** "O workflow de auto-analise trata o codigo de saida 3
  (inconclusivo/infraestrutura) como sucesso, entao um checkout sem spec fica verde sem
  medir nada"
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** crítica
- **Classe:** codigo_de_saida/valido
- **Dado:** o job de auto-análise recebendo o código de saída do `sentry run`
- **Quando:** o código é 3 (inconclusivo/infraestrutura), como acontece num checkout sem
  nenhuma spec
- **Então:** o passo termina com falha e o build fica vermelho
- **Entrada:** `codigo_de_saida = 3`

## Caso: relatorio grava o commit analisado e o instante

- **Requisito:** "o relatorio passa a gravar o commit e o instante da analise"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** commit_analisado/valido
- **Dado:** uma análise feita num repositório Git com HEAD conhecido
- **Quando:** o relatório em Markdown é gerado
- **Então:** o cabeçalho mostra o SHA analisado e o instante da análise
- **Entrada:** `commit_analisado = "a94b1fb"`

## Caso: report acusa relatorio de commit diferente do HEAD

- **Requisito:** "o comando report acusa quando o commit gravado nao e o HEAD atual, em
  vez de exibir como veredito corrente"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** commit_analisado/valido
- **Dado:** um relatório gravado sobre um commit e um HEAD que avançou desde então
- **Quando:** o usuário roda `sentry report`
- **Então:** a saída acusa que o relatório é de outro commit, dizendo qual, antes do
  conteúdo do relatório
- **Entrada:** `commit_analisado = "a94b1fb"`

## Caso: sem repositorio Git o relatorio nao inventa commit

- **Requisito:** o selo de frescor é evidência; sem commit a gravar, o relatório declara a
  ausência em vez de acusar desatualização que não pode comprovar
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** commit_analisado/vazio
- **Dado:** uma análise num diretório que não é repositório Git
- **Quando:** o relatório é gerado e depois exibido por `sentry report`
- **Então:** o cabeçalho registra o commit como indisponível e nenhuma acusação de
  desatualização é emitida
- **Entrada:** `commit_analisado = ""`

## Caso: statement executado conta como coberto

- **Requisito:** a cobertura do alterado precisa continuar medindo o que sempre mediu;
  corrigir o denominador não pode mudar o numerador
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** linha_alterada/valido
- **Dado:** uma linha alterada que a ferramenta de cobertura mediu e registrou como
  executada
- **Quando:** a cobertura do código alterado é calculada
- **Então:** a linha entra no denominador e também no numerador
- **Entrada:** `linha_alterada = "return total"`

## Caso: statement nao executado continua descoberto

- **Requisito:** a correção não pode esconder ausência real de teste — é o risco de
  tirar linhas do denominador
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** linha_alterada/valido
- **Dado:** uma linha alterada que a ferramenta mediu e registrou como não executada
- **Quando:** a cobertura do código alterado é calculada
- **Então:** a linha entra no denominador e fica fora do numerador, derrubando o
  percentual
- **Entrada:** `linha_alterada = "raise ValueError(...)"`

## Caso: linha em branco fica fora do calculo

- **Requisito:** linha em branco não é código a testar; contá-la como descoberta afirma
  ausência de teste onde não havia nada a executar
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** linha_alterada/vazio
- **Dado:** uma linha em branco no meio do trecho alterado
- **Quando:** a cobertura do código alterado é calculada
- **Então:** a linha não entra no denominador
- **Entrada:** `linha_alterada = ""`

## Caso: linha de comentario fica fora do calculo

- **Requisito:** neste código o comentário registra o porquê de cada decisão; contá-lo
  como descoberto faz escrever a explicação derrubar a nota da própria mudança
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** linha_alterada/caracteres-especiais
- **Dado:** uma linha de comentário no trecho alterado
- **Quando:** a cobertura do código alterado é calculada
- **Então:** a linha não entra no denominador
- **Entrada:** `linha_alterada = "# o porque desta decisao"`

## Caso: linha de arquivo que a cobertura nao mede fica fora do calculo

- **Requisito:** um workflow YAML ou um Markdown alterado não tem cobertura a medir;
  no denominador, eles reprovam a mudança por existirem
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** linha_alterada/valido
- **Dado:** linhas alteradas num arquivo ausente do relatório de cobertura
- **Quando:** a cobertura do código alterado é calculada
- **Então:** nenhuma delas entra no denominador
- **Entrada:** `linha_alterada = "runs-on: ubuntu-latest"`

## Caso: mudanca sem linha mensuravel nao vira achado de cobertura ausente

- **Requisito:** com denominador vazio não há percentual, e `Não foi possível calcular a
  cobertura` afirmaria falha onde não havia o que calcular
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** linha_alterada/valido
- **Dado:** uma mudança cujas linhas alteradas são todas comentário, branco ou arquivo
  não medido, com a cobertura lida sem erro
- **Quando:** as regras avaliam a mudança
- **Então:** a cobertura do alterado sai indisponível e o achado `coverage-missing` não
  é emitido
- **Entrada:** `linha_alterada = "# so comentario nesta mudanca"`

## Classes não aplicáveis

- **entrada_gitignore/tamanho-maximo-excedido**: as entradas são um conjunto fechado
  escrito pelo próprio `init`, com no máximo trinta caracteres; não há comprimento do
  usuário a limitar aqui.
- **codigo_de_saida/vazio**: o `sentry run` sempre devolve um código; ausência de código
  não é estado alcançável na expressão do workflow, que recebe `${codigo:-0}`.
- **codigo_de_saida/nao-numerico**: o valor vem do código de saída de um processo, que o
  sistema operacional garante ser inteiro.
- **codigo_de_saida/negativo**: código de saída de processo não é negativo; o domínio é
  0..3, verificado caso a caso.
- **codigo_de_saida/limite-superior**: o domínio é fechado em 3, e o caso de 3 é
  justamente o que se cobra; qualquer valor acima seria falha do próprio interpretador,
  não do produto.
- **commit_analisado/caracteres-especiais**: o valor é a saída de `git rev-parse HEAD`,
  hexadecimal por construção — o Sentry não o compõe nem o recebe digitado.
- **commit_analisado/tamanho-maximo-excedido**: idem, comprimento fixo definido pelo Git.
- **linha_alterada/tamanho-maximo-excedido**: a decisão é sobre o número da linha estar
  entre as que a ferramenta de cobertura mediu; o conteúdo da linha nunca é lido, então
  não há comprimento a limitar.
