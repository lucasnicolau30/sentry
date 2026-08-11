# Sentry Report

- Run: 20f8467b-6fa3-48e5-b0e3-9337d5213866
- Projeto: sentry
- Veredito: **aprovado** — nenhum achado relevante — pode seguir.

## Achados

- Nenhum achado registrado.

## Contexto

- Arquivos alterados: 15
- Testes impactados: 18
- Testes não relacionados: 1
- Cenários sem teste: 0
- Cobertura global (todo o projeto): 98,24%
- Cobertura alterada (só o código desta mudança): 74,03%
- Testes: 229 passados, 0 falhos, 0 ignorados, 0 nao executados
- Duracao: 23.18 s

## Dimensões de cobertura

| Dimensão | Status | Evidência | Justificativa |
| --- | --- | --- | --- |
| requisitos e regras de negócio | coberta | 43/43 cenários da spec com teste associado | todos os itens têm evidência de cobertura |
| APIs, persistência, transações e integrações | coberta | 22/22 casos de contrato ou integração cobertos | todos os itens têm evidência de cobertura |
| exceções, resiliência e recuperação | coberta | 2/2 caminhos de erro alterados executados por algum teste | todos os itens têm evidência de cobertura |
| segurança e autorização | não aplicável | nenhum campo do tipo `rota` declarado | nada desta dimensão foi declarado ou alterado nesta análise |

## Matriz de casos

- Total: 43
- Por status: coberto=43

### Backend

- `coberto` **sem dados de cobertura a dimensao sai como nao verificada** (TC-01) — o status não é "não aplicável" nem "coberta", e a evidência informa quantos (crítica, unitário) — tests\test_dimensions.py
- `coberto` **ausencia real de caminho de erro continua nao aplicavel** (TC-02) — o status é "não aplicável", com a evidência de que não há caminho de erro (alta, unitário) — tests\test_dimensions.py
- `coberto` **com cobertura o veredito de execucao permanece** (TC-03) — o status é "parcial", e com todos executados é "coberta", com nenhum é "não coberta" (crítica, unitário) — tests\test_dimensions.py
- `coberto` **caminho de erro excluido da medicao nao vira ausencia de caminho** (TC-04) — a evidência declara a exclusão em vez de afirmar que não há caminho de erro (alta, unitário) — tests\test_dimensions.py
- `coberto` **pytest invocado por caminho de executavel e reconhecido** (TC-09) — é reconhecido como pytest e normalizado para `-m pytest` (média, unitário) — tests\test_execution_evidence.py
- `coberto` **padrao cobre os quatro diretorios convencionais** (TC-13) — os testes em `spec/` são encontrados (alta, unitário) — tests\test_impact.py
- `coberto` **diretorio declarado inexistente vira limitacao e nao silencio** (TC-14) — a limitação "nenhum arquivo de teste encontrado" é registrada, nomeando o (alta, unitário) — tests\test_impact.py
- `coberto` **dependencia de terceiros nao entra como teste do projeto** (TC-15) — os arquivos de dependência ficam de fora (média, unitário) — tests\test_impact.py
- `coberto` **executavel pytest sem interpretador irmao roda como declarado** (TC-19) — o comando declarado é executado literalmente, sem troca de interpretador, e (média, unitário) — tests\test_execution_evidence.py
- `coberto` **runner sem caminho continua no interpretador do Sentry** (TC-20) — o interpretador do próprio Sentry é usado, com `coverage run -m pytest` (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **base compara a partir do ponto em que a branch divergiu** (TC-23) — só as alterações da branch aparecem; o commit que entrou em `main` depois da (crítica, unitário) — tests\test_git_context.py
- `coberto` **falha sem contagem no resumo ainda conta como reprovacao** (TC-29) — a execução sai como reprovada, com pelo menos uma reprovação contada (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **processo morto por sinal e inconclusivo** (TC-30) — a execução sai como não executada, com erro de infraestrutura (média, unitário) — tests\test_execution_evidence.py
- `coberto` **saida longa e truncada sem perder o resumo** (TC-31) — a evidência é truncada mas mantém o resumo final, e a contagem vem dele (baixa, unitário) — tests\test_execution_evidence.py
- `coberto` **arquivo de nome parecido nao e excluido** (TC-36) — nenhum deles é excluído do diff (média, unitário) — tests\test_git_context.py
- `coberto` **exclusao nao depende de leitura possivel do arquivo** (TC-37) — o arquivo é tratado como mudança do usuário e permanece no diff, sem exceção (média, unitário) — tests\test_git_context.py
- `coberto` **duas hunks no mesmo arquivo acumulam em vez de sobrescrever** (TC-38) — as linhas das duas hunks aparecem, em ordem crescente e sem repetição (crítica, unitário) — tests\test_git_context.py
- `coberto` **hunk que so remove linhas nao apaga as demais do arquivo** (TC-39) — a remoção não contribui linha alguma e as linhas adicionadas permanecem (alta, unitário) — tests\test_git_context.py
- `coberto` **hunk sem contagem explicita vale uma linha** (TC-40) — exatamente a linha indicada é registrada (média, unitário) — tests\test_git_context.py
- `coberto` **muitas hunks no mesmo arquivo e nenhuma e perdida** (TC-41) — todas as linhas de todos os blocos estão presentes (alta, unitário) — tests\test_git_context.py
- `coberto` **hunk de arquivo removido nao e atribuida ao arquivo anterior** (TC-42) — as hunks do arquivo removido não entram nas linhas do arquivo anterior (alta, unitário) — tests\test_git_context.py

### Integração

- `coberto` **dimensao nao verificada aparece no relatorio como ausencia de evidencia** (TC-05) — a linha da dimensão de exceções e a seção de Limitações concordam: ambas (crítica, integração) — tests\test_error_paths.py
- `coberto` **comando nao-pytest sem junit declarado nao recebe a flag do pytest** (TC-06) — o comando roda exatamente como declarado, sem `--junitxml`, e o erro de (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **suite nao-pytest le o junit declarado sem injetar flag** (TC-07) — a contagem vem do relatório, sem flag injetada e sem cobertura própria (alta, integração) — tests\test_execution_evidence.py
- `coberto` **pytest invocado como modulo e reconhecido** (TC-08) — é reconhecido como pytest, embrulhado em `coverage run` e a cobertura é medida (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **comando vazio vira erro de infraestrutura** (TC-10) — a execução sai como não executada com erro de infraestrutura, sem exceção (alta, integração) — tests\test_execution_evidence.py
- `coberto` **impacto encontra testes no diretorio declarado** (TC-11) — `users/test_serializers.py` entra como teste impactado e nenhuma limitação (crítica, integração) — tests\test_impact.py
- `coberto` **impacto e matriz enxergam o mesmo conjunto de arquivos** (TC-12) — todo arquivo de teste que a matriz pode associar é visível para o impacto, (crítica, contrato) — tests\test_impact.py
- `coberto` **interpretador declarado por caminho e usado no lugar do global** (TC-16) — é o interpretador declarado que roda, ainda embrulhado em `coverage run -m pytest` (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **interpretador declarado inexistente vira erro de infraestrutura** (TC-17) — a execução sai como não executada, com erro de infraestrutura nomeando o (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **executavel pytest do venv roda no python do proprio venv** (TC-18) — o comando é montado com o interpretador irmão do venv, mantendo a cobertura (alta, integração) — tests\test_execution_evidence.py
- `coberto` **base declarada revela o que a branch mudou** (TC-21) — os arquivos e as linhas commitados na branch aparecem como alterados, em vez (crítica, integração) — tests\test_git_context.py
- `coberto` **sem base declarada o comportamento atual permanece** (TC-22) — o diff é o da árvore contra `HEAD`, como antes (crítica, integração) — tests\test_git_context.py
- `coberto` **base inexistente vira erro de infraestrutura** (TC-24) — a execução registra erro de infraestrutura nomeando a referência, e o veredito (crítica, integração) — tests\test_git_context.py
- `coberto` **a base efetivamente usada aparece no relatorio** (TC-25) — a referência declarada aparece na evidência da execução (alta, contrato) — tests\test_git_context.py
- `coberto` **runner ausente sai como inconclusivo e nao como reprovacao** (TC-26) — a execução sai como não executada, com erro de infraestrutura, e nenhuma (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **reprovacao real continua sendo reprovacao** (TC-27) — a execução sai como reprovada, sem erro de infraestrutura, com a contagem do resumo (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **suite aprovada permanece coberta** (TC-28) — a execução sai como coberta, sem erro de infraestrutura e sem reprovação fabricada (alta, integração) — tests\test_execution_evidence.py
- `coberto` **sentry.toml intocado desde o init fica fora do diff** (TC-32) — o arquivo não aparece entre os arquivos alterados (crítica, integração) — tests\test_git_context.py
- `coberto` **sentry.toml editado pelo usuario volta ao diff** (TC-33) — o arquivo aparece entre os arquivos alterados (crítica, integração) — tests\test_git_context.py
- `coberto` **gitignore so com as entradas do Sentry fica fora do diff** (TC-34) — o arquivo não aparece entre os arquivos alterados (alta, integração) — tests\test_git_context.py
- `coberto` **gitignore com linha do usuario na mesma mudanca entra no diff** (TC-35) — o arquivo aparece entre os arquivos alterados (alta, integração) — tests\test_git_context.py
- `coberto` **linhas alteradas alimentam a analise de cobertura de todas as hunks** (TC-43) — os dois pontos aparecem entre as linhas alteradas do arquivo (crítica, integração) — tests\test_git_context.py

## Limitações

> O Sentry não conseguiu verificar isto — não é aprovação nem reprovação, é ausência de evidência.

- Nenhuma limitação registrada.

## Classes não aplicáveis

> Dispensadas de propósito, com justificativa declarada no CASES.md — não é lacuna do Sentry.

- caminhos_de_erro/vazio — a quantidade é o tamanho das listas produzidas por
- caminhos_de_erro/nao-numerico — idem, é um comprimento de lista, nunca texto.
- caminhos_de_erro/negativo — idem, um comprimento de lista nunca é negativo.
- caminhos_de_erro/limite-superior — a dimensão agrega por contagem, sem teto próprio;
- cobertura/tamanho-maximo-excedido — a cobertura chega como mapa de arquivo para
- cobertura/caracteres-especiais — idem, os valores já vêm validados pelo leitor de
- comando/tamanho-maximo-excedido — o comprimento do comando é limite do sistema
- junit_xml/tamanho-maximo-excedido — idem, o caminho é validado pelo sistema de arquivos.
- junit_xml/caracteres-especiais — o caminho é usado como `self.root / junit_xml` sem
- test_paths/tamanho-maximo-excedido — o comprimento do caminho é limite do sistema de
- comando/vazio — já verificada na spec `execucao-fiel-da-suite-declarada`, que trata
- comando/tamanho-maximo-excedido — o comprimento do comando é limite do sistema
- base/tamanho-maximo-excedido — o comprimento de uma referência é limite do Git; uma
- codigo_saida/vazio — o código de saída sempre existe quando o processo termina; a
- codigo_saida/nao-numerico — vem do sistema operacional como inteiro, nunca como texto.
- codigo_saida/limite-superior — qualquer código fora da tabela do pytest já cai na
- resumo_da_suite/caracteres-especiais — a saída é lida com `errors="replace"` e o
- arquivo/tamanho-maximo-excedido — o comprimento do caminho é limite do sistema de
- origem_da_alteracao/vazio — verificada no caso de arquivo ilegível, onde a origem não
- origem_da_alteracao/tamanho-maximo-excedido — a origem não é texto digitado, e sim o
- origem_da_alteracao/caracteres-especiais — idem — a comparação é entre o conteúdo
- hunks/negativo — a quantidade de blocos é a contagem de cabeçalhos `@@` presentes
- hunks/nao-numerico — o cabeçalho é casado por expressão regular numérica, então o
- diff/vazio — diff vazio significa nenhum arquivo alterado, caminho já verificado
- diff/tamanho-maximo-excedido — a saída é lida inteira do `git diff`, sem corte

## Evidência

### Arquivos alterados

- Comparado com: árvore de trabalho contra `HEAD`

- src/sentrytest/adapters/local_tools.py
- src/sentrytest/application/analyze.py
- src/sentrytest/application/dimensions.py
- src/sentrytest/application/error_paths.py
- src/sentrytest/application/impact.py
- src/sentrytest/application/reporting.py
- src/sentrytest/application/traceability.py
- src/sentrytest/cli.py
- src/sentrytest/domain/models.py
- src/sentrytest/init_project.py
- tests/test_dimensions.py
- tests/test_error_paths.py
- tests/test_execution_evidence.py
- tests/test_git_context.py
- tests/test_impact.py

### Execução de testes

- Comando: `C:\Users\lucas.ferreira\AppData\Local\Programs\Python\Python312\python.exe -m coverage run -m pytest`
- Saida resumida:
```
n.py ...........                              [ 20%]
tests\test_changed_coverage.py ...............                           [ 27%]
tests\test_cli.py ...........                                            [ 32%]
tests\test_contextual_reporting.py ........                              [ 35%]
tests\test_dimensions.py ...............                                 [ 42%]
tests\test_domain_models.py ...                                          [ 43%]
tests\test_error_paths.py ............                                   [ 48%]
tests\test_execution_evidence.py .....................                   [ 58%]
tests\test_git_context.py .....................                          [ 67%]
tests\test_history_cli.py ........                                       [ 70%]
tests\test_impact.py ..............                                      [ 76%]
tests\test_init_project.py ......                                        [ 79%]
tests\test_input_adapters.py .                                           [ 79%]
tests\test_reporting.py ...                                              [ 81%]
tests\test_rules.py ...............                                      [ 87%]
tests\test_toml_config.py .....                                          [ 89%]
tests\test_traceability.py .......................                       [100%]

- generated xml file: C:\Users\LUCAS~1.FER\AppData\Local\Temp\tmpnigoocew\junit.xml -
============================ 229 passed in 22.40s =============================

```
