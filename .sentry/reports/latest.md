# Sentry Report

- Run: daac6ebe-6fdb-4c1c-8415-a5e7d31d83d5
- Projeto: sentry
- Veredito: **aprovado** — nenhum achado relevante — pode seguir.

## Achados

- Nenhum achado registrado.

## Contexto

- Arquivos alterados: 68
- Testes impactados: 19
- Testes não relacionados: 0
- Cenários sem teste: 0
- Cobertura global (todo o projeto): 97,95%
- Cobertura alterada (só o código desta mudança): 94,06%
- Testes: 194 passados, 0 falhos, 0 ignorados, 0 nao executados
- Duracao: 13.94 s

## Dimensões de cobertura

| Dimensão | Status | Evidência | Justificativa |
| --- | --- | --- | --- |
| requisitos e regras de negócio | coberta | 62/62 cenários da spec com teste associado | todos os itens têm evidência de cobertura |
| APIs, persistência, transações e integrações | coberta | 8/8 casos de contrato ou integração cobertos | todos os itens têm evidência de cobertura |
| exceções, resiliência e recuperação | coberta | 20/20 caminhos de erro alterados executados por algum teste | todos os itens têm evidência de cobertura |
| segurança e autorização | não aplicável | nenhum campo do tipo `rota` declarado | nada desta dimensão foi declarado ou alterado nesta análise |

## Matriz de casos

- Total: 62
- Por status: coberto=62

### Backend

- `coberto` **spec all junta casos de todas as pastas** (TC-01) — o total de casos da análise é a soma dos casos das duas pastas, e a configuração registra as duas specs pelo nome (alta, unitário) — tests\test_analyze.py
- `coberto` **spec all sem nenhuma pasta ainda recusa com erro claro** (TC-02) — levanta erro pedindo para criar uma spec com `sentry new` (média, unitário) — tests\test_analyze.py
- `coberto` **caminho de erro e detectado fora de Python** (TC-03) — a linha aparece como caminho de erro não coberto (alta, unitário) — tests\test_error_paths.py
- `coberto` **deteccao sem AST e registrada como limitacao** (TC-04) — o caminho é reportado e o relatório registra que a detecção naquele arquivo foi por padrão sintático, sem AST (alta, unitário) — tests\test_error_paths.py
- `coberto` **palavra de erro em comentario ou string nao vira caminho de erro** (TC-05) — nenhum caminho de erro é reportado (crítica, unitário) — tests\test_error_paths.py
- `coberto` **extensao sem padrao declarado continua fora da analise** (TC-06) — nada é reportado e nenhuma limitação é registrada (média, unitário) — tests\test_error_paths.py
- `coberto` **classe nao aplicavel some dos achados e aparece como limitacao registrada** (TC-07) — as classes dispensadas não geram achado, as demais continuam sendo cobradas, e as justificativas ficam registradas na execução (alta, unitário) — tests\test_analyze.py
- `coberto` **relatório lcov produz cobertura por linha** (TC-08) — as linhas executadas são 1 e 3, e a cobertura do arquivo é 2/3 (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **relatório cobertura xml produz cobertura por linha** (TC-09) — a linha executada é a 1 e a cobertura global é o `line-rate` declarado no próprio relatório (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **detecta os três formatos pelo conteúdo** (TC-10) — devolve `coverage.py`, `lcov`, `cobertura` e `None`, nessa ordem (média, unitário) — tests\test_changed_coverage.py
- `coberto` **lcov com caminho absoluto casa com o caminho relativo do diff** (TC-11) — a chave de cobertura é o caminho relativo `src/app.js` (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **lcov mesclado não infla a contagem ao repetir a mesma linha** (TC-12) — a linha 1 é contada uma vez só e a cobertura é 50%, não mais que 100% (média, unitário) — tests\test_changed_coverage.py
- `coberto` **formato irreconhecível é distinto de formato malformado** (TC-13) — o erro diz que o formato não foi reconhecido e lista os aceitos (média, unitário) — tests\test_changed_coverage.py
- `coberto` **projeto de outra stack mede cobertura pelo relatório que ele mesmo gera** (TC-14) — a cobertura do código alterado é 50%, sem erro de leitura (crítica, integração) — tests\test_analyze.py
- `coberto` **relatório do formato certo porém sem nenhum registro é recusado** (TC-15) — ambos devolvem erro dizendo qual registro faltou, em vez de reportar cobertura zero (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **caminho fora da raiz do projeto e mantido como veio** (TC-16) — o caminho é preservado como veio, sem erro de leitura (média, unitário) — tests\test_changed_coverage.py
- `coberto` **cobertura alterada funciona a partir de um relatorio lcov** (TC-17) — o percentual é 50% (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **arquivo novo ilegivel nao derruba a leitura do diff** (TC-18) — o arquivo válido aparece em `changed_lines`, o ilegível é omitido, e a leitura não registra erro (alta, unitário) — tests\test_git_context.py
- `coberto` **comando de teste ausente vira erro de infraestrutura, nao reprovacao** (TC-19) — registra erro de infraestrutura com status `não executado`, sem percentual de cobertura, e nunca status de falha (crítica, unitário) — tests\test_execution_evidence.py
- `coberto` **junit.xml corrompido cai no fallback por regex sem quebrar** (TC-20) — devolve vazio nos dois casos, sinalizando que a contagem deve vir da saída do executor (média, unitário) — tests\test_execution_evidence.py
- `coberto` **teste com erro de sintaxe vira limitacao, nao quebra a analise** (TC-21) — nenhum teste é marcado como impactado e o arquivo problemático é registrado nas limitações (alta, unitário) — tests\test_impact.py
- `coberto` **falha ao reconfigurar stdout/stderr nao impede o comando de rodar** (TC-22) — o comando roda normalmente e retorna código de saída 0 (média, unitário) — tests\test_cli.py
- `coberto` **severidade invalida no sentry.toml e ignorada, nao quebra a leitura** (TC-23) — a regra com valor inválido fica sem sobrescrita e a regra válida é aplicada (média, unitário) — tests\test_analyze.py
- `coberto` **arquivos gerados pelo proprio Sentry ficam fora do diff** (TC-24) — só os dois primeiros são excluídos; os editáveis pelo usuário e a skill de terceiro permanecem no diff (alta, unitário) — tests\test_git_context.py
- `coberto` **diff sem arquivo mensuravel nao acusa cobertura ausente** (TC-25) — `coverage-missing` não é reportado (alta, unitário) — tests\test_rules.py
- `coberto` **diff com codigo continua acusando cobertura ausente** (TC-26) — `coverage-missing` continua sendo reportado (alta, unitário) — tests\test_rules.py
- `coberto` **arquivo em diretório excluído não entra no diff analisado** (TC-27) — `app.py` aparece em `git_change.files`, e nenhum arquivo com prefixo `frontend/` aparece (alta, unitário) — tests\test_analyze.py
- `coberto` **sem exclude declarado, nada é filtrado** (TC-28) — todos os arquivos alterados permanecem em `git_change.files`, sem filtragem (média, unitário) — tests\test_analyze.py
- `coberto` **linha excluida da medicao nao vira caminho de erro sem teste** (TC-29) — ela não aparece como coberta nem como descoberta, e o relatório registra a exclusão (alta, unitário) — tests\test_error_paths.py
- `coberto` **exclusao nao vaza para linha vizinha** (TC-30) — apenas a linha não excluída aparece como caminho de erro sem teste (alta, unitário) — tests\test_error_paths.py
- `coberto` **suite nao-pytest le o junit declarado sem injetar flag** (TC-31) — as contagens vêm do relatório declarado, nenhuma flag é injetada no comando e nenhuma cobertura Python é gerada (crítica, unitário) — tests\test_execution_evidence.py
- `coberto` **fora do pytest, ausencia de teste contabilizado e infraestrutura** (TC-32) — sem nenhum teste contabilizado vira erro de infraestrutura citando o código; com teste contabilizado volta a ser reprovação legítima; e no pytest a tabela de códigos continua valendo (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **projeto de outra stack roda a propria suite e tem veredito real** (TC-33) — os testes são contabilizados, não há erro de infraestrutura, a cobertura do código alterado é 50% e o veredito não é `inconclusivo` (crítica, integração) — tests\test_analyze.py
- `coberto` **specs ficam fora do git e latest.md fica rastreavel** (TC-34) — `.sentry/specs/` é ignorado, `.sentry/reports/*` é ignorado e `!.sentry/reports/latest.md` reinclui só o relatório mais recente (alta, unitário) — tests\test_init_project.py
- `coberto` **gitignore antigo e migrado sem duplicar entradas** (TC-35) — a linha antiga some, o par `reports/*` + negação passa a valer, e uma segunda execução não altera mais nada (alta, unitário) — tests\test_init_project.py
- `coberto` **init instala o guia de agente na raiz do projeto** (TC-36) — `AGENT-SENTRY.md` é criado na raiz do projeto, com o fluxo `sentry new`/`check`/`run` descrito, e execuções seguintes não o recriam sem necessidade (alta, unitário) — tests\test_init_project.py
- `coberto` **marcador declarado casa com o caso mesmo sem acento** (TC-37) — o caso aparece como coberto, vinculado ao teste (alta, unitário) — tests\test_traceability.py
- `coberto` **init cria o banco ja na versao atual, com a tabela runs pronta** (TC-38) — `schema_version` registra a versão atual e a tabela `runs` já existe, antes de qualquer análise (alta, unitário) — tests\test_init_project.py
- `coberto` **banco de versao antiga e migrado sem perder dados existentes** (TC-39) — a versão passa a ser a atual, a tabela `runs` é criada e os dados preexistentes continuam intactos (crítica, unitário) — tests\test_init_project.py
- `coberto` **clear sem confirmacao apenas mostra o que sairia** (TC-40) — a saída lista o que sairia, orienta a repetir com `--yes`, e nenhum arquivo é removido (crítica, integração) — tests\test_history_cli.py
- `coberto` **clear com confirmacao remove execucoes e preserva as specs** (TC-41) — os arquivos da execução e a linha no banco somem, e o `CASES.md` continua intacto (crítica, integração) — tests\test_history_cli.py
- `coberto` **keep-last preserva as execucoes mais recentes** (TC-42) — só a execução mais antiga é removida, e o `latest.md` é preservado porque aponta para uma execução mantida (alta, integração) — tests\test_history_cli.py
- `coberto` **clear sem historico nao faz nada** (TC-43) — informa que não há nada a remover e sai com sucesso (média, integração) — tests\test_history_cli.py
- `coberto` **rastreabilidade reconhece teste de qualquer stack** (TC-44) — cada arquivo é reconhecido e o caso aparece coberto, vinculado a ele (crítica, unitário) — tests\test_traceability.py
- `coberto` **marcador declarado funciona com comentario de qualquer linguagem** (TC-45) — o caso aparece coberto, pelo marcador e não pela semelhança (alta, unitário) — tests\test_traceability.py
- `coberto` **diretorio de teste declarado substitui os padroes** (TC-46) — sem declarar, o caso sai não coberto; declarando `src`, o caso aparece coberto (alta, unitário) — tests\test_traceability.py
- `coberto` **arquivo de teste ilegivel nao derruba a rastreabilidade** (TC-47) — o arquivo ilegível é ignorado e o caso continua vinculado ao teste válido (média, unitário) — tests\test_traceability.py
- `coberto` **vendor nao e varrido em busca de teste** (TC-48) — o caso sai não coberto, porque o diretório de dependência é ignorado (alta, unitário) — tests\test_traceability.py
- `coberto` **achados aparecem antes da evidência bruta** (TC-49) — a seção `## Achados` aparece antes de `### Arquivos alterados` e de `### Execução de testes` (alta, unitário) — tests\test_contextual_reporting.py
- `coberto` **identificador do caso não repete o nome legível** (TC-50) — o nome legível do caso aparece em destaque e o id aparece separado, como marca curta entre parênteses (média, unitário) — tests\test_contextual_reporting.py
- `coberto` **veredito vem com explicacao do que significa** (TC-51) — o veredito vem seguido de uma frase curta explicando que há achado de severidade alta a revisar (média, unitário) — tests\test_contextual_reporting.py
- `coberto` **achado mostra a regra que disparou** (TC-52) — o identificador da regra aparece junto do achado (média, unitário) — tests\test_contextual_reporting.py
- `coberto` **classe nao aplicavel aparece separada das limitacoes reais** (TC-53) — `## Limitações` vem antes de `## Classes não aplicáveis`, e cada item aparece só na sua seção (alta, unitário) — tests\test_contextual_reporting.py
- `coberto` **rejeita slug que escapa da pasta de specs** (TC-54) — levanta ValueError dizendo que o slug aponta para fora (crítica, unitário) — tests\test_analyze.py
- `coberto` **rejeita slug com caminho absoluto** (TC-55) — levanta ValueError dizendo que o slug aponta para fora (crítica, unitário) — tests\test_analyze.py
- `coberto` **aceita slug valido** (TC-56) — retorna o caminho resolvido do CASES.md (alta, unitário) — tests\test_analyze.py
- `coberto` **sem slug e sem nenhuma spec, recusa com erro claro** (TC-57) — levanta erro dizendo que nenhuma matriz foi encontrada e como criar uma (alta, unitário) — tests\test_analyze.py
- `coberto` **sem slug e com mais de uma spec, pede para escolher com --spec** (TC-58) — levanta erro listando as specs encontradas e pedindo `--spec <slug>` (alta, unitário) — tests\test_analyze.py
- `coberto` **check com multiplas specs sem --spec imprime erro e retorna 2** (TC-59) — imprime o erro e retorna código de saída 2 (média, integração) — tests\test_cli.py
- `coberto` **rodar como modulo (-m) executa o mesmo CLI** (TC-60) — sai com código 0 e imprime a mesma versão do pacote (média, integração) — tests\test_cli.py
- `coberto` **palavras genericas nao produzem vinculo por semelhanca** (TC-61) — o caso sai como não coberto e aparece entre os cenários sem teste (crítica, unitário) — tests\test_traceability.py
- `coberto` **semelhanca real continua vinculando sem marcador** (TC-62) — o caso aparece como coberto, vinculado a esse teste (alta, unitário) — tests\test_traceability.py

## Limitações

> O Sentry não conseguiu verificar isto — não é aprovação nem reprovação, é ausência de evidência.

- caminho(s) de erro excluido(s) da medicao pelo projeto (`# pragma: no cover`): src/sentrytest/cli.py:206 (raise)

## Classes não aplicáveis

> Dispensadas de propósito, com justificativa declarada no CASES.md — não é lacuna do Sentry.

- formato/vazio — arquivo vazio já é recusado antes da detecção, pelo caminho de "arquivo de cobertura ausente"/irreconhecível — não existe caminho de código que trate string vazia como formato distinto
- formato/tamanho-maximo-excedido — é um identificador de formato escolhido entre três valores fixos, não texto livre com limite de tamanho
- exclude/tamanho-maximo-excedido — é lista de prefixos de diretório num arquivo de configuração, não campo de formulário com limite de tamanho
- exclude/caracteres-especiais — é caminho de arquivo declarado pelo próprio desenvolvedor no sentry.toml, não entrada de usuário a sanitizar
- keep-last/nao-numerico — o argparse já recusa valor não numérico com `type=int`, antes de qualquer código do Sentry — não existe caminho que trate a string crua
- keep-last/negativo — valor negativo cai no mesmo ramo de zero (nenhuma execução preservada), sem comportamento distinto a verificar
- keep-last/limite-superior — preservar mais execuções do que existem simplesmente não remove nada, comportamento já coberto pelo caso de histórico vazio
- slug/vazio — `--spec ""` é falsy em Python e cai na mesma seleção automática de `--spec` omitido; não existe caminho de código que trate slug vazio como valor distinto
- slug/tamanho-maximo-excedido — é argumento de linha de comando, sem limite de tamanho definido nem sentido de validação de formulário

## Evidência

### Arquivos alterados

- .gitignore
- AGENTS.md
- README.md
- SPEC.md
- pyproject.toml
- sentry.toml
- src/sentry/__init__.py
- src/sentry/adapters/__init__.py
- src/sentry/adapters/local_tools.py
- src/sentry/adapters/markdown_specs.py
- src/sentry/adapters/toml_config.py
- src/sentry/application/__init__.py
- src/sentry/application/analyze.py
- src/sentry/application/coverage_context.py
- src/sentry/application/impact.py
- src/sentry/application/reporting.py
- src/sentry/application/traceability.py
- src/sentry/cli.py
- src/sentry/domain/__init__.py
- src/sentry/domain/models.py
- src/sentry/domain/rules.py
- src/sentry/init_project.py
- src/sentry/interfaces/__init__.py
- src/sentry/ports/__init__.py
- src/sentry/ports/inputs.py
- tests/test_analyze.py
- tests/test_changed_coverage.py
- tests/test_cli.py
- tests/test_contextual_reporting.py
- tests/test_domain_models.py
- tests/test_execution_evidence.py
- tests/test_git_context.py
- tests/test_history_cli.py
- tests/test_impact.py
- tests/test_init_project.py
- tests/test_input_adapters.py
- tests/test_reporting.py
- tests/test_rules.py
- tests/test_toml_config.py
- tests/test_traceability.py
- LICENSE
- src/sentrytest/__init__.py
- src/sentrytest/adapters/__init__.py
- src/sentrytest/adapters/case_specs.py
- src/sentrytest/adapters/local_tools.py
- src/sentrytest/adapters/toml_config.py
- src/sentrytest/application/__init__.py
- src/sentrytest/application/analyze.py
- src/sentrytest/application/cases.py
- src/sentrytest/application/coverage_context.py
- src/sentrytest/application/dimensions.py
- src/sentrytest/application/error_paths.py
- src/sentrytest/application/impact.py
- src/sentrytest/application/reporting.py
- src/sentrytest/application/traceability.py
- src/sentrytest/cli.py
- src/sentrytest/domain/__init__.py
- src/sentrytest/domain/catalog.py
- src/sentrytest/domain/models.py
- src/sentrytest/domain/rules.py
- src/sentrytest/init_project.py
- src/sentrytest/ports/__init__.py
- src/sentrytest/ports/inputs.py
- src/sentrytest/skills.py
- tests/test_case_specs.py
- tests/test_cases_application.py
- tests/test_dimensions.py
- tests/test_error_paths.py

### Execução de testes

- Comando: `C:\Users\lucas.ferreira\AppData\Local\Python\pythoncore-3.14-64\python.exe -m coverage run -m pytest`
- Saida resumida:
```
n.py ...........                              [ 23%]
tests\test_changed_coverage.py ...............                           [ 30%]
tests\test_cli.py ...........                                            [ 36%]
tests\test_contextual_reporting.py ........                              [ 40%]
tests\test_dimensions.py ...........                                     [ 46%]
tests\test_domain_models.py ...                                          [ 47%]
tests\test_error_paths.py ............                                   [ 54%]
tests\test_execution_evidence.py .........                               [ 58%]
tests\test_git_context.py ..........                                     [ 63%]
tests\test_history_cli.py ........                                       [ 68%]
tests\test_impact.py .........                                           [ 72%]
tests\test_init_project.py ......                                        [ 75%]
tests\test_input_adapters.py .                                           [ 76%]
tests\test_reporting.py ...                                              [ 77%]
tests\test_rules.py ...............                                      [ 85%]
tests\test_toml_config.py .....                                          [ 88%]
tests\test_traceability.py .......................                       [100%]

- generated xml file: C:\Users\LUCAS~1.FER\AppData\Local\Temp\tmpmglgr2ad\junit.xml -
============================ 194 passed in 13.32s =============================

```
