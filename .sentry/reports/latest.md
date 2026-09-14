# Sentry Report

- Run: eac6c3fa-927b-4fda-863d-ba4511426e8e
- Projeto: sentry
- Commit analisado: a8017525c1e4105d39775bf628292d7d90d7ef24
- Analisado em: 2026-09-14T19:52:57.634585+00:00
- Veredito: **aprovado** — nenhum achado relevante — pode seguir.
- Execução reaproveitada do cache: nada foi executado agora; a evidência é da execução fa721592-d71a-4a82-ad6e-434056053787 de 2026-09-14T19:49:05.990511+00:00.

## Achados

- Nenhum achado registrado.

## Contexto

- Arquivos alterados: 52
- Testes impactados: 31
- Testes não relacionados: 2
- Cenários sem teste: 0
- Cobertura global (todo o projeto): 99,11% — medida na execução anterior (2026-09-14T19:49:05.990511+00:00), não nesta rodada
- Cobertura alterada (só o código desta mudança): 99,50% — medida na execução anterior (2026-09-14T19:49:05.990511+00:00), não nesta rodada
- Testes: 421 passados, 0 falhos, 0 ignorados, 0 nao executados
- Duracao: 135.0 s
- Testes e2e: 2 passados, 0 falhos, 0 ignorados, 0 nao executados
- Duracao e2e: 5.12 s

## Dimensões de cobertura

| Dimensão | Status | Evidência | Justificativa |
| --- | --- | --- | --- |
| requisitos e regras de negócio | coberta | 244/244 cenários da spec com teste associado | todos os itens têm evidência de cobertura |
| APIs, persistência, transações e integrações | coberta | 98/98 casos de contrato ou integração cobertos | todos os itens têm evidência de cobertura |
| exceções, resiliência e recuperação | coberta | 17/17 caminhos de erro alterados executados por algum teste | todos os itens têm evidência de cobertura |
| segurança e autorização | não aplicável | nenhum campo do tipo `rota` declarado | nada desta dimensão foi declarado ou alterado nesta análise |
| interface e fluxo de usuário | coberta | 5/5 casos de interface com evidência de execução e2e | todos os itens têm evidência de cobertura |

## Matriz de casos

- Total: 244
- Por status: coberto=244

### Backend

- `coberto` **nome puro continua resolvido pelo PATH** (TC-04) — o nome segue intocado, para o sistema operacional resolver no PATH (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **caminho declarado inexistente nomeia onde foi procurado** (TC-05) — o erro de infraestrutura mostra o caminho já resolvido contra a raiz, dizendo (média, unitário) — tests\test_execution_evidence.py
- `coberto` **cor desabilitada fora de terminal interativo** (TC-07) — nenhum código ANSI aparece na saída (crítica, unitário) — tests\test_terminal_color.py
- `coberto` **NO_COLOR desabilita mesmo em terminal interativo** (TC-08) — nenhum código ANSI aparece na saída (crítica, unitário) — tests\test_terminal_color.py
- `coberto` **FORCE_COLOR habilita mesmo sem terminal interativo** (TC-09) — o código ANSI aparece na saída (alta, unitário) — tests\test_terminal_color.py
- `coberto` **veredito aprovado sai verde** (TC-10) — o texto do veredito é envolvido pelo código de cor verde (alta, unitário) — tests\test_terminal_color.py
- `coberto` **veredito aprovado com ressalvas sai amarelo** (TC-11) — o texto do veredito é envolvido pelo código de cor amarelo (alta, unitário) — tests\test_terminal_color.py
- `coberto` **veredito reprovado sai vermelho** (TC-12) — o texto do veredito é envolvido pelo código de cor vermelho (alta, unitário) — tests\test_terminal_color.py
- `coberto` **veredito inconclusivo sai cinza** (TC-13) — o texto do veredito é envolvido pelo código de cor cinza (média, unitário) — tests\test_terminal_color.py
- `coberto` **achado critico ou alto sai vermelho** (TC-14) — o rótulo de severidade de cada um é envolvido pelo código de cor (alta, unitário) — tests\test_terminal_color.py
- `coberto` **achado de media severidade sai amarelo** (TC-15) — o rótulo de severidade é envolvido pelo código de cor amarelo (média, unitário) — tests\test_terminal_color.py
- `coberto` **veredito aprovado tem o simbolo de check** (TC-22) — a linha do veredito traz o símbolo `✓` (alta, unitário) — tests\test_terminal_ui.py
- `coberto` **veredito reprovado tem o simbolo de x** (TC-23) — a linha do veredito traz o símbolo `✗` (alta, unitário) — tests\test_terminal_ui.py
- `coberto` **veredito inconclusivo tem o simbolo de circulo vazio** (TC-24) — a linha do veredito traz o símbolo `○` (média, unitário) — tests\test_terminal_ui.py
- `coberto` **achado critico ou alto tem o simbolo de x** (TC-25) — o rótulo de cada um traz o símbolo `✗` (alta, unitário) — tests\test_terminal_ui.py
- `coberto` **spinner anima em stderr quando e tty** (TC-28) — o caractere vem do conjunto de frames braille, não de stdout (alta, unitário) — tests\test_terminal_ui.py
- `coberto` **spinner nao anima fora de terminal interativo** (TC-29) — uma única linha estática é escrita, sem nenhum frame de animação (alta, unitário) — tests\test_terminal_ui.py
- `coberto` **dashboard traz testes cobertura e achados por severidade** (TC-31) — o texto traz a contagem de testes, a cobertura global e a (alta, unitário) — tests\test_terminal_ui.py
- `coberto` **tracinho do cabecalho de secao respeita a largura do terminal** (TC-37) — a linha inteira (símbolo, texto e tracinho) não passa de 40 (média, unitário) — tests\test_terminal_ui.py
- `coberto` **linha do checklist mostra a badge alinhada a direita por categoria** (TC-40) — o texto `created` aparece alinhado à direita, depois do label (média, unitário) — tests\test_terminal_ui.py
- `coberto` **wordmark usa tres faixas de verde** (TC-51) — a primeira, a do meio e a última linha usam três códigos de cor (média, unitário) — tests\test_terminal_ui.py
- `coberto` **wordmark sem cor fica so' com o texto puro** (TC-52) — a saída não tem nenhum código ANSI e ainda é a arte em blocos (média, unitário) — tests\test_terminal_ui.py
- `coberto` **caminho de erro e detectado fora de Python** (TC-53) — a linha aparece em `uncovered` como caminho de erro do tipo (crítica, unitário) — tests\test_error_paths.py
- `coberto` **deteccao sem AST e registrada como limitacao** (TC-54) — a linha aparece em `uncovered`, e uma limitação registra que a (alta, unitário) — tests\test_error_paths.py
- `coberto` **palavra de erro em comentario ou string nao vira caminho de erro** (TC-55) — nenhuma linha entra em `uncovered` (alta, unitário) — tests\test_error_paths.py
- `coberto` **linha excluida da medicao nao vira caminho de erro sem teste** (TC-56) — a linha não entra em `uncovered` nem em `covered`, e uma (alta, unitário) — tests\test_error_paths.py
- `coberto` **exclusao nao vale para linha que o projeto nao excluiu** (TC-57) — só a linha não excluída aparece em `uncovered` (alta, unitário) — tests\test_error_paths.py
- `coberto` **extensao sem padrao declarado continua fora da analise** (TC-58) — a linha não entra em `uncovered`, e nenhuma limitação é (média, unitário) — tests\test_error_paths.py
- `coberto` **sem dados de cobertura a dimensao sai como nao verificada** (TC-59) — o status não é "não aplicável" nem "coberta", e a evidência informa quantos (crítica, unitário) — tests\test_dimensions.py
- `coberto` **ausencia real de caminho de erro continua nao aplicavel** (TC-60) — o status é "não aplicável", com a evidência de que não há caminho de erro (alta, unitário) — tests\test_dimensions.py
- `coberto` **com cobertura o veredito de execucao permanece** (TC-61) — o status é "parcial", e com todos executados é "coberta", com nenhum é "não coberta" (crítica, unitário) — tests\test_dimensions.py
- `coberto` **caminho de erro excluido da medicao nao vira ausencia de caminho** (TC-62) — a evidência declara a exclusão em vez de afirmar que não há caminho de erro (alta, unitário) — tests\test_dimensions.py
- `coberto` **pytest invocado por caminho de executavel e reconhecido** (TC-75) — é reconhecido como pytest e normalizado para `-m pytest` (média, unitário) — tests\test_execution_evidence.py
- `coberto` **fora do pytest, ausencia de teste contabilizado e infraestrutura** (TC-78) — sem contagem, a ausência vira erro de infraestrutura nomeando o código de (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **junit.xml corrompido cai no fallback por regex sem quebrar** (TC-79) — a leitura devolve `None` para os dois, sem levantar exceção (média, unitário) — tests\test_execution_evidence.py
- `coberto` **gitignore novo nasce sem a linha de specs** (TC-81) — o arquivo criado não contém `.sentry/specs/` (crítica, unitário) — tests\test_init_project.py
- `coberto` **as outras entradas do init sobrevivem a remocao** (TC-82) — `.sentry/sentry.db`, `.sentry/runs/`, `.sentry/test-plans/`, (alta, unitário) — tests\test_init_project.py
- `coberto` **linha parecida escrita pelo usuario nao e removida** (TC-83) — essa linha permanece intacta no arquivo (alta, unitário) — tests\test_init_project.py
- `coberto` **gitignore antigo e migrado sem duplicar entradas** (TC-84) — `.sentry/reports/` sai do arquivo, `.sentry/reports/*` e (alta, unitário) — tests\test_init_project.py
- `coberto` **relatorio grava o commit analisado e o instante** (TC-89) — o cabeçalho mostra o SHA analisado e o instante da análise (crítica, unitário) — tests\test_reporting.py
- `coberto` **sem repositorio Git o relatorio nao inventa commit** (TC-91) — o cabeçalho registra o commit como indisponível e nenhuma acusação de (alta, unitário) — tests\test_history_cli.py
- `coberto` **statement executado conta como coberto** (TC-92) — a linha entra no denominador e também no numerador (crítica, unitário) — tests\test_changed_coverage.py
- `coberto` **statement nao executado continua descoberto** (TC-93) — a linha entra no denominador e fica fora do numerador, derrubando o (crítica, unitário) — tests\test_changed_coverage.py
- `coberto` **linha em branco fica fora do calculo** (TC-94) — a linha não entra no denominador (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **linha de comentario fica fora do calculo** (TC-95) — a linha não entra no denominador (crítica, unitário) — tests\test_changed_coverage.py
- `coberto` **linha de arquivo que a cobertura nao mede fica fora do calculo** (TC-96) — nenhuma delas entra no denominador (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **diff sem arquivo mensuravel nao acusa cobertura ausente** (TC-98) — nenhum achado `coverage-missing` é emitido (alta, unitário) — tests\test_rules.py
- `coberto` **diff com codigo continua acusando cobertura ausente** (TC-99) — o achado `coverage-missing` é emitido (alta, unitário) — tests\test_rules.py
- `coberto` **run com slug inexistente continua sendo erro** (TC-102) — levanta erro dizendo qual caminho era esperado (alta, unitário) — tests\test_sem_spec.py
- `coberto` **regras que dependem de spec nao disparam sem spec** (TC-104) — nenhum achado de cenário sem teste, requisito sem cenário, classe de (crítica, unitário) — tests\test_sem_spec.py
- `coberto` **dimensao de requisitos sai nao aplicavel sem intencao declarada** (TC-105) — a dimensão de requisitos sai `não aplicável` e a justificativa diz que (alta, unitário) — tests\test_sem_spec.py
- `coberto` **dimensao de APIs sai nao aplicavel sem intencao declarada** (TC-106) — a dimensão de APIs sai `não aplicável` com a mesma justificativa de intenção (alta, unitário) — tests\test_sem_spec.py
- `coberto` **dimensao de excecoes continua medida sem spec** (TC-107) — a dimensão de exceções reporta o que mediu, sem cair em `não aplicável` por (alta, unitário) — tests\test_sem_spec.py
- `coberto` **marcador que aponta para caso inexistente vira achado** (TC-108) — um achado nomeia o marcador órfão e o arquivo onde ele está (alta, unitário) — tests\test_traceability.py
- `coberto` **marcador orfao em linha nao alterada nao vira achado** (TC-109) — nenhum achado é emitido para ele (alta, unitário) — tests\test_traceability.py
- `coberto` **marcador escrito dentro de literal de string nao vira cenario** (TC-110) — nenhum dos dois vira marcador — o marcador é uma linha de comentário, e só (alta, unitário) — tests\test_traceability.py
- `coberto` **marcador que casa com caso declarado nao vira achado** (TC-111) — nenhum achado de marcador órfão é emitido (alta, unitário) — tests\test_traceability.py
- `coberto` **arquivo de teste sem marcador nao vira achado** (TC-112) — nenhum achado de marcador órfão é emitido (média, unitário) — tests\test_traceability.py
- `coberto` **sem spec declarada nenhum marcador e orfao** (TC-113) — nenhum marcador é reportado como órfão, porque não há matriz com que (crítica, unitário) — tests\test_sem_spec.py
- `coberto` **modo instantaneo reusa a cobertura da ultima execucao completa** (TC-119) — o relatório traz a cobertura global e do alterado vindas daquela execução (crítica, unitário) — tests\test_modo_instantaneo.py
- `coberto` **cobertura reusada e declarada como da execucao anterior** (TC-120) — a cobertura aparece marcada como vinda de execução anterior, com o instante (crítica, unitário) — tests\test_custo.py
- `coberto` **sem execucao completa anterior a cobertura sai indisponivel** (TC-121) — a cobertura sai indisponível e nenhum número é afirmado (alta, unitário) — tests\test_modo_instantaneo.py
- `coberto` **mudanca em arquivo de codigo invalida o cache** (TC-124) — o hash difere do gravado e a suíte é executada de novo (crítica, unitário) — tests\test_cache.py
- `coberto` **mudanca em arquivo de teste invalida o cache** (TC-125) — o hash difere do gravado e a suíte é executada de novo (crítica, unitário) — tests\test_cache.py
- `coberto` **mudanca na spec invalida o cache** (TC-126) — o hash difere do gravado e a análise é refeita (alta, unitário) — tests\test_cache.py
- `coberto` **sem execucao anterior nao ha cache a reusar** (TC-127) — o cache não acerta e a suíte é executada (alta, unitário) — tests\test_cache.py
- `coberto` **execucao vinda do cache e declarada no relatorio** (TC-128) — o relatório diz que a execução veio do cache e de quando ela é (crítica, unitário) — tests\test_custo.py
- `coberto` **watch no arquivo de codigo roda o modo instantaneo** (TC-129) — escolhe o modo instantâneo (alta, unitário) — tests\test_watch.py
- `coberto` **watch no arquivo de teste escala para o modo completo** (TC-130) — escolhe o modo completo, porque só executando é que a mudança no teste vira (alta, unitário) — tests\test_watch.py
- `coberto` **context emite as faixas de linha sem cobertura** (TC-131) — ele traz, por arquivo, as faixas de linha descobertas (crítica, unitário) — tests\test_context.py
- `coberto` **context emite cenarios classes caminhos de erro e marcadores orfaos** (TC-132) — cada uma das quatro espécies aparece na sua própria chave (alta, unitário) — tests\test_context.py
- `coberto` **context emite os testes falhando com nome** (TC-133) — os nomes dos testes falhos aparecem no payload (alta, unitário) — tests\test_context.py
- `coberto` **sem lacuna nenhuma o payload sai vazio e nao omitido** (TC-134) — todas as chaves existem, todas vazias (alta, unitário) — tests\test_context.py
- `coberto` **relatorio traz o bloco de custo com zero token gasto** (TC-135) — existe um bloco de custo declarando zero token gasto pelo Sentry (alta, unitário) — tests\test_custo.py
- `coberto` **bloco de custo mede o tamanho do que o relatorio resumiu** (TC-136) — o bloco de custo traz o tamanho do diff resumido e o do próprio relatório, (média, unitário) — tests\test_custo.py
- `coberto` **camada frontend e aceita no vocabulario da spec** (TC-137) — nenhum erro de camada inválida é levantado, e o caso vira `Layer.FRONTEND` (alta, unitário) — tests\test_case_specs.py
- `coberto` **tipo e2e e aceito no vocabulario da spec** (TC-138) — nenhum erro de tipo inválido é levantado, e o caso vira `TestType.E2E` (alta, unitário) — tests\test_case_specs.py
- `coberto` **catalogo cobra as cinco classes do tipo formulario** (TC-139) — as cinco classes declaradas no prompt aparecem, nem mais nem menos (alta, unitário) — tests\test_case_specs.py
- `coberto` **catalogo cobra as quatro classes do tipo navegacao** (TC-140) — as quatro classes declaradas no prompt aparecem, nem mais nem menos (alta, unitário) — tests\test_case_specs.py
- `coberto` **catalogo cobra as tres classes do tipo responsivo** (TC-141) — as três classes declaradas no prompt aparecem, nem mais nem menos (alta, unitário) — tests\test_case_specs.py
- `coberto` **catalogo cobra as quatro classes do tipo acessibilidade** (TC-142) — as quatro classes declaradas no prompt aparecem, nem mais nem menos (alta, unitário) — tests\test_case_specs.py
- `coberto` **sentry check usa o mesmo catalogo mesclado que o sentry run** (TC-143) — o tipo não é acusado como limitação fora do catálogo (alta, integração) — tests\test_cli.py
- `coberto` **segunda suite e2e roda junto da suite backend sem mascarar a outra** (TC-144) — `test_execution` (backend) e `e2e_execution` aparecem os dois na configuração, cada um com sua própria contagem (crítica, integração) — tests\test_analyze.py
- `coberto` **falha da suite e2e nao rebaixa caso de backend para parcial** (TC-145) — o caso de backend continua `coberto`, não `parcial` (crítica, unitário) — tests\test_cases_application.py
- `coberto` **falha da suite backend nao rebaixa caso de frontend para parcial** (TC-146) — o caso de frontend continua `coberto`, não `parcial` (crítica, unitário) — tests\test_cases_application.py
- `coberto` **SuiteAdapter roda comando declarado num subdiretorio via cwd** (TC-147) — o processo sobe com o diretório de trabalho igual a `root/algum-subdir`, não `root` (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **nome puro de executavel e resolvido pelo PATH mesmo sendo shim do Windows** (TC-148) — o caminho completo do shim é usado, em vez de falhar com "arquivo não encontrado" (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **dimensao de interface fica coberta quando todos os casos frontend passam** (TC-149) — a dimensão de interface sai `coberta` (alta, unitário) — tests\test_dimensions.py
- `coberto` **dimensao de interface fica nao aplicavel sem nenhum caso frontend declarado** (TC-150) — a dimensão de interface sai `não aplicável`, nunca `não coberta` (alta, unitário) — tests\test_dimensions.py
- `coberto` **marcador cenario em arquivo ts vincula caso ao teste playwright** (TC-151) — o caso aparece associado ao arquivo `.ts`, como qualquer caso de backend seria a um `.py` (crítica, integração) — tests\test_frontend_evidence.py
- `coberto` **evidencia de trace e screenshot e anexada ao caso quando o teste passou** (TC-152) — o caminho do trace e do screenshot aparece na evidência do caso (crítica, unitário) — tests\test_cases_application.py
- `coberto` **sem relatorio junit a evidencia sai vazia sem inventar caminho** (TC-153) — o resultado é um dicionário vazio, nunca uma exceção nem um caminho falso (alta, unitário) — tests\test_frontend_evidence.py
- `coberto` **sem e2e configurado no sentry toml a segunda suite nao roda** (TC-154) — nenhum processo de e2e sobe, e `e2e_execution` não aparece na configuração (crítica, unitário) — tests\test_analyze.py
- `coberto` **padrao cobre os quatro diretorios convencionais** (TC-159) — os testes em `spec/` são encontrados (alta, unitário) — tests\test_impact.py
- `coberto` **diretorio declarado inexistente vira limitacao e nao silencio** (TC-160) — a limitação "nenhum arquivo de teste encontrado" é registrada, nomeando o (alta, unitário) — tests\test_impact.py
- `coberto` **dependencia de terceiros nao entra como teste do projeto** (TC-161) — os arquivos de dependência ficam de fora (média, unitário) — tests\test_impact.py
- `coberto` **teste com erro de sintaxe vira limitacao, nao quebra a analise** (TC-162) — a análise não levanta exceção; o arquivo quebrado não entra como impactado, (alta, unitário) — tests\test_impact.py
- `coberto` **banco de versao antiga e migrado sem perder dados existentes** (TC-165) — `schema_version.version` passa a ser `CURRENT_SCHEMA_VERSION`, (crítica, unitário) — tests\test_init_project.py
- `coberto` **executavel pytest sem interpretador irmao roda como declarado** (TC-169) — o comando declarado é executado literalmente, sem troca de interpretador, e (média, unitário) — tests\test_execution_evidence.py
- `coberto` **runner sem caminho continua no interpretador do Sentry** (TC-170) — o interpretador do próprio Sentry é usado, com `coverage run -m pytest` (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **formato irreconhecível é distinto de formato malformado** (TC-171) — o erro começa com "formato de cobertura nao reconhecido" e (média, unitário) — tests\test_changed_coverage.py
- `coberto` **detecta os três formatos pelo conteúdo** (TC-172) — devolve `"coverage.py"`, `"lcov"`, `"cobertura"` e `None`, (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **relatório lcov produz cobertura por linha** (TC-173) — `executed_lines` traz só as linhas com execução > 0, e o (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **relatório cobertura xml produz cobertura por linha** (TC-174) — `executed_lines` traz as linhas com `hits > 0`, e o (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **lcov com caminho absoluto casa com o caminho relativo do diff** (TC-175) — o caminho relativizado à raiz aparece em `executed_lines` (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **lcov mesclado nao infla a contagem ao repetir a mesma linha** (TC-176) — a linha 1 aparece uma única vez em `executed_lines`, sem (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **relatório do formato certo porém sem nenhum registro é recusado** (TC-177) — o erro nomeia a ausência de registro (`"nenhum registro (alta, unitário) — tests\test_changed_coverage.py
- `coberto` **caminho fora da raiz do projeto e mantido como veio** (TC-178) — nenhum erro é levantado, e o caminho original (não (média, unitário) — tests\test_changed_coverage.py
- `coberto` **rejeita slug que escapa da pasta de specs** (TC-180) — levanta `ValueError` mencionando que o caminho aponta para fora (crítica, unitário) — tests\test_analyze.py
- `coberto` **rejeita slug com caminho absoluto** (TC-181) — levanta `ValueError` mencionando que o caminho aponta para fora (crítica, unitário) — tests\test_analyze.py
- `coberto` **aceita slug valido** (TC-182) — devolve o caminho resolvido de `.sentry/specs/demo/CASES.md` (alta, unitário) — tests\test_analyze.py
- `coberto` **sem slug e sem nenhuma spec, recusa com erro claro** (TC-183) — levanta `ValueError` mencionando que nenhuma matriz de casos foi (alta, unitário) — tests\test_analyze.py
- `coberto` **sem slug e com mais de uma spec, pede para escolher com --spec** (TC-184) — levanta `ValueError` mencionando que múltiplas specs foram (alta, unitário) — tests\test_analyze.py
- `coberto` **severidade invalida no sentry.toml e ignorada, nao quebra a leitura** (TC-187) — a entrada inválida some da política (sem sobrescrita), e a (média, unitário) — tests\test_analyze.py
- `coberto` **classe nao aplicavel some dos achados e aparece como limitacao registrada** (TC-192) — as classes justificadas não geram achado `missing-equivalence-class` (média, unitário) — tests\test_analyze.py
- `coberto` **nome do projeto vem do toml, com o diretorio como fallback** (TC-193) — `run.project` é `"cobranca-api"`, não o nome do diretório (média, unitário) — tests\test_analyze.py
- `coberto` **rastreabilidade reconhece teste de qualquer stack** (TC-194) — o cenário correspondente aparece como coberto, vinculado (crítica, unitário) — tests\test_traceability.py
- `coberto` **marcador declarado funciona com comentario de qualquer linguagem** (TC-195) — o cenário com aquele nome aparece como coberto, mesmo o nome (alta, unitário) — tests\test_traceability.py
- `coberto` **diretorio de teste declarado substitui os padroes** (TC-196) — sem a declaração o cenário sai não coberto; com (alta, unitário) — tests\test_traceability.py
- `coberto` **arquivo de teste ilegivel nao derruba a rastreabilidade** (TC-197) — o cenário aparece coberto pelo arquivo válido, sem exceção (alta, unitário) — tests\test_traceability.py
- `coberto` **vendor nao e varrido em busca de teste** (TC-198) — o cenário permanece não coberto — o diretório vendor não entra (alta, unitário) — tests\test_traceability.py
- `coberto` **marcador declarado casa com o caso mesmo sem acento** (TC-199) — o cenário aparece coberto, sem entrar em (crítica, unitário) — tests\test_traceability.py
- `coberto` **palavras genericas nao produzem vinculo por semelhanca** (TC-200) — o cenário permanece não coberto — a semelhança de só palavras (crítica, unitário) — tests\test_traceability.py
- `coberto` **semelhanca real continua vinculando sem marcador** (TC-201) — o cenário aparece coberto, sem `scenarios_without_tests` (alta, unitário) — tests\test_traceability.py
- `coberto` **achados aparecem antes da evidência bruta** (TC-202) — `## Achados` aparece antes de `### Arquivos alterados` e de (média, unitário) — tests\test_contextual_reporting.py
- `coberto` **identificador do caso não repete o nome legível** (TC-203) — o nome legível aparece em destaque (`**rejeita slug vazio**`) e (baixa, unitário) — tests\test_contextual_reporting.py
- `coberto` **veredito vem com explicacao do que significa** (TC-204) — a linha do veredito inclui a explicação prática daquele status (baixa, unitário) — tests\test_contextual_reporting.py
- `coberto` **achado mostra a regra que disparou** (TC-205) — o nome da regra aparece entre crases (`` `test-failing` ``) (média, unitário) — tests\test_contextual_reporting.py
- `coberto` **classe nao aplicavel aparece separada das limitacoes reais** (TC-206) — `## Limitações` aparece antes de `## Classes não aplicáveis`, e (média, unitário) — tests\test_contextual_reporting.py
- `coberto` **base compara a partir do ponto em que a branch divergiu** (TC-209) — só as alterações da branch aparecem; o commit que entrou em `main` depois da (crítica, unitário) — tests\test_git_context.py
- `coberto` **falha sem contagem no resumo ainda conta como reprovacao** (TC-215) — a execução sai como reprovada, com pelo menos uma reprovação contada (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **processo morto por sinal e inconclusivo** (TC-216) — a execução sai como não executada, com erro de infraestrutura (média, unitário) — tests\test_execution_evidence.py
- `coberto` **saida longa e truncada sem perder o resumo** (TC-217) — a evidência é truncada mas mantém o resumo final, e a contagem vem dele (baixa, unitário) — tests\test_execution_evidence.py
- `coberto` **arquivo de nome parecido nao e excluido** (TC-226) — nenhum deles é excluído do diff (média, unitário) — tests\test_git_context.py
- `coberto` **exclusao nao depende de leitura possivel do arquivo** (TC-227) — o arquivo é tratado como mudança do usuário e permanece no diff, sem exceção (média, unitário) — tests\test_git_context.py
- `coberto` **arquivos gerados pelo proprio Sentry ficam fora do diff** (TC-228) — todos são reconhecidos como gerados pelo próprio Sentry; uma skill de outra (alta, unitário) — tests\test_git_context.py
- `coberto` **status reporta cobertura alterada igual a cobertura global** (TC-229) — a cobertura "alterada" reportada é igual à cobertura global, porque todo (crítica, unitário) — tests\test_status.py
- `coberto` **sentry run comum nao trata a cobertura alterada como a global** (TC-230) — a cobertura alterada reportada continua diferente da global (média, unitário) — tests\test_status.py
- `coberto` **arquivo com 0% de cobertura entra na secao de arquivos sem teste alcancando** (TC-231) — o arquivo aparece na seção "arquivos sem nenhum teste alcançando" (crítica, unitário) — tests\test_status.py
- `coberto` **arquivo com cobertura maior que zero nao entra na secao** (TC-232) — o arquivo não aparece na seção "arquivos sem nenhum teste alcançando" (alta, unitário) — tests\test_status.py
- `coberto` **status nunca reaproveita execucao do cache** (TC-235) — a suíte é executada de novo, sem voltar do cache (crítica, unitário) — tests\test_status.py
- `coberto` **duas hunks no mesmo arquivo acumulam em vez de sobrescrever** (TC-238) — as linhas das duas hunks aparecem, em ordem crescente e sem repetição (crítica, unitário) — tests\test_git_context.py
- `coberto` **hunk que so remove linhas nao apaga as demais do arquivo** (TC-239) — a remoção não contribui linha alguma e as linhas adicionadas permanecem (alta, unitário) — tests\test_git_context.py
- `coberto` **hunk sem contagem explicita vale uma linha** (TC-240) — exatamente a linha indicada é registrada (média, unitário) — tests\test_git_context.py
- `coberto` **muitas hunks no mesmo arquivo e nenhuma e perdida** (TC-241) — todas as linhas de todos os blocos estão presentes (alta, unitário) — tests\test_git_context.py
- `coberto` **hunk de arquivo removido nao e atribuida ao arquivo anterior** (TC-242) — as hunks do arquivo removido não entram nas linhas do arquivo anterior (alta, unitário) — tests\test_git_context.py
- `coberto` **arquivo novo ilegivel nao derruba a leitura do diff** (TC-244) — o arquivo ilegível fica sem `changed_lines`, mas o resto do diff (incluindo o (alta, unitário) — tests\test_git_context.py

### Integração

- `coberto` **caminho relativo com barra normal executa** (TC-01) — o processo roda, sem erro de infraestrutura (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **as quatro grafias do mesmo executavel sao equivalentes** (TC-02) — as quatro chegam ao mesmo arquivo e produzem o mesmo resultado (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **caminho relativo e resolvido contra a raiz do projeto** (TC-03) — o interpretador do projeto é encontrado e executado (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **suite nao-pytest com caminho relativo tambem e resolvida** (TC-06) — o processo roda, sem erro de infraestrutura (alta, integração) — tests\test_execution_evidence.py
- `coberto` **relatorio salvo em disco nunca contem codigo ANSI** (TC-16) — o conteúdo do arquivo não contém nenhum código de escape ANSI (crítica, integração) — tests\test_terminal_color.py
- `coberto` **sentry check colore erro de vermelho e sucesso de verde** (TC-17) — a linha `[erro]` sai vermelha na primeira, e a linha de sucesso sai (alta, integração) — tests\test_terminal_color.py
- `coberto` **sentry init colore dependencia ausente de vermelho e presente de verde** (TC-18) — `presente` sai verde e `ausente` sai vermelho (média, integração) — tests\test_terminal_color.py
- `coberto` **check com multiplas specs sem --spec imprime erro e retorna 2** (TC-19) — a saída contém `"Erro:"` e o comando devolve o código 2 (alta, integração) — tests\test_cli.py
- `coberto` **falha ao reconfigurar stdout/stderr nao impede o comando de rodar** (TC-20) — o comando termina normalmente, código de saída 0 (média, integração) — tests\test_cli.py
- `coberto` **rodar como modulo (-m) executa o mesmo CLI** (TC-21) — o código de saída é 0 e a saída é a mesma versão que (média, integração) — tests\test_cli.py
- `coberto` **resumo compacto do veredito tambem traz o simbolo** (TC-26) — a linha traz o símbolo do veredito junto do status (alta, integração) — tests\test_terminal_ui.py
- `coberto` **sentry check troca o prefixo por simbolo em erro e sucesso** (TC-27) — a linha de erro traz `✗` e a linha de sucesso traz `✓`, no lugar de (alta, integração) — tests\test_terminal_ui.py
- `coberto` **masthead e dashboard nunca aparecem no relatorio salvo em disco** (TC-30) — o conteúdo do arquivo não contém nenhuma borda de caixa nem os (crítica, integração) — tests\test_terminal_ui.py
- `coberto` **icone do comando prefixa a primeira linha impressa** (TC-32) — ela começa com o ícone declarado para `init` (média, integração) — tests\test_terminal_ui.py
- `coberto` **sentry init nao termina com nenhuma caixa de proximo passo** (TC-33) — não aparece nenhuma caixa nem menção a `sentry new` depois do (média, integração) — tests\test_terminal_ui.py
- `coberto` **sentry init mostra o wordmark antes do texto de conclusao** (TC-34) — o wordmark aparece antes da linha "Projeto Sentry inicializado." (média, integração) — tests\test_terminal_ui.py
- `coberto` **sentry init mostra o checklist dos passos com check verde** (TC-35) — cada item criado aparece numa linha própria, prefixada por `✓`, (média, integração) — tests\test_terminal_ui.py
- `coberto` **init tem um unico cabecalho verde com tracinho** (TC-36) — `INICIALIZANDO` aparece uma única vez, com um tracinho na (baixa, integração) — tests\test_terminal_ui.py
- `coberto` **nenhum outro comando repete o wordmark** (TC-38) — o wordmark não aparece (baixa, integração) — tests\test_terminal_ui.py
- `coberto` **versao aparece no pezinho direito do wordmark e em chip nas dependencias** (TC-39) — `v2.0.0` aparece na última linha do wordmark e o chip (média, integração) — tests\test_terminal_ui.py
- `coberto` **detalhe do ambiente mostra a versao real de cada dependencia** (TC-41) — o detalhe do item "Verificando ambiente do projeto" traz o (alta, integração) — tests\test_terminal_ui.py
- `coberto` **dependencia ausente vira vermelho e presente vira verde no detalhe do ambiente** (TC-42) — a linha do item de ambiente fica vermelha quando alguma (média, integração) — tests\test_terminal_color.py
- `coberto` **conclusao do init ganha um simbolo antes do texto** (TC-43) — a linha "Projeto Sentry inicializado." começa com o símbolo de (baixa, integração) — tests\test_terminal_ui.py
- `coberto` **python entra como detalhe do item de ambiente, dentro do checklist** (TC-44) — a versão do Python aparece no detalhe do item "Verificando (baixa, integração) — tests\test_terminal_ui.py
- `coberto` **conclusao do init nao pula linha antes nem depois do bloco** (TC-45) — a linha "Projeto Sentry inicializado." vem imediatamente depois (baixa, integração) — tests\test_terminal_ui.py
- `coberto` **linha de git aparece com branch e status quando ha repositorio** (TC-46) — a linha `git repo` aparece com o nome do branch e `limpo` (média, integração) — tests\test_terminal_ui.py
- `coberto` **linha de git some fora de repositorio Git** (TC-47) — nenhuma linha `git repo` aparece (média, integração) — tests\test_terminal_ui.py
- `coberto` **checklist do init mostra todas as categorias mesmo em reexecucao** (TC-48) — as cinco linhas do checklist aparecem de novo, sem nenhuma (média, integração) — tests\test_terminal_color.py
- `coberto` **checklist do init em reexecucao nao mostra nenhuma badge** (TC-49) — a palavra `presente` não aparece em nenhuma linha (baixa, integração) — tests\test_terminal_color.py
- `coberto` **wordmark grande aparece no topo do init** (TC-50) — o wordmark aparece antes do cabeçalho de nome/versão/badge, sem (média, integração) — tests\test_terminal_ui.py
- `coberto` **dimensao nao verificada aparece no relatorio como ausencia de evidencia** (TC-63) — a linha da dimensão de exceções e a seção de Limitações concordam: ambas (crítica, integração) — tests\test_error_paths.py
- `coberto` **todo comando do cli aparece no README.md** (TC-64) — todo comando aparece no texto do arquivo (alta, contrato) — tests\test_docs_consistency.py
- `coberto` **todo comando do cli aparece no README.pt.md** (TC-65) — todo comando aparece no texto do arquivo (alta, contrato) — tests\test_docs_consistency.py
- `coberto` **todo comando do cli aparece no AGENT-SENTRY.md** (TC-66) — todo comando aparece no texto do arquivo (crítica, contrato) — tests\test_docs_consistency.py
- `coberto` **todo tipo de campo do catalogo aparece na tabela do README.md** (TC-68) — toda chave aparece no texto do arquivo (alta, contrato) — tests\test_docs_consistency.py
- `coberto` **todo tipo de campo do catalogo aparece na tabela do README.pt.md** (TC-69) — toda chave aparece no texto do arquivo (alta, contrato) — tests\test_docs_consistency.py
- `coberto` **comando nao-pytest sem junit declarado nao recebe a flag do pytest** (TC-72) — o comando roda exatamente como declarado, sem `--junitxml`, e o erro de (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **suite nao-pytest le o junit declarado sem injetar flag** (TC-73) — a contagem vem do relatório, sem flag injetada e sem cobertura própria (alta, integração) — tests\test_execution_evidence.py
- `coberto` **pytest invocado como modulo e reconhecido** (TC-74) — é reconhecido como pytest, embrulhado em `coverage run` e a cobertura é medida (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **comando vazio vira erro de infraestrutura** (TC-76) — a execução sai como não executada com erro de infraestrutura, sem exceção (alta, integração) — tests\test_execution_evidence.py
- `coberto` **comando de teste ausente vira erro de infraestrutura, nao reprovacao** (TC-77) — a execução sai como não executada, com erro de infraestrutura, sem (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **specs saem do gitignore na proxima inicializacao** (TC-80) — a linha `.sentry/specs/` não está mais no arquivo (crítica, integração) — tests\test_init_project.py
- `coberto` **codigo de aprovado mantem o build verde** (TC-85) — o passo termina com sucesso e o build fica verde (média, contrato) — tests\test_autoanalise_workflow.py
- `coberto` **codigo de ressalva mantem o build verde** (TC-86) — o passo termina com sucesso e o build fica verde (média, contrato) — tests\test_autoanalise_workflow.py
- `coberto` **codigo de reprovado derruba o build** (TC-87) — o passo termina com falha e o build fica vermelho (alta, contrato) — tests\test_autoanalise_workflow.py
- `coberto` **codigo de inconclusivo derruba o build** (TC-88) — o passo termina com falha e o build fica vermelho (crítica, contrato) — tests\test_autoanalise_workflow.py
- `coberto` **report acusa relatorio de commit diferente do HEAD** (TC-90) — a saída acusa que o relatório é de outro commit, dizendo qual, antes do (crítica, integração) — tests\test_history_cli.py
- `coberto` **mudanca sem linha mensuravel nao vira achado de cobertura ausente** (TC-97) — a cobertura do alterado sai indisponível e o achado `coverage-missing` não (alta, integração) — tests\test_analyze.py
- `coberto` **run sem spec produz relatorio em vez de excecao** (TC-100) — devolve uma execução com veredito, sem levantar exceção (crítica, integração) — tests\test_sem_spec.py
- `coberto` **run --spec all sem nenhuma spec continua sendo erro** (TC-101) — levanta erro de configuração, e o comando sai com o código de infraestrutura (crítica, integração) — tests\test_cli.py
- `coberto` **modo sem spec mede cobertura do alterado e testes impactados** (TC-103) — o relatório traz cobertura do alterado, contagem de testes e testes (alta, integração) — tests\test_sem_spec.py
- `coberto` **review encadeia check run e report num comando** (TC-114) — a saída traz a validação da spec e o relatório completo, numa só invocação (crítica, integração) — tests\test_review_cli.py
- `coberto` **review devolve o codigo de saida do veredito** (TC-115) — o código de saída é o mesmo que o `run` devolveria para aquele veredito (alta, integração) — tests\test_review_cli.py
- `coberto` **review roda em repositorio sem sentry e sem toml** (TC-116) — devolve relatório útil e código de saída, sem exigir preparo nenhum (crítica, integração) — tests\test_review_cli.py
- `coberto` **review com CASES.md invalido sai reprovado** (TC-117) — a saída acusa o erro do CASES.md e o código de saída é o de reprovado (alta, integração) — tests\test_review_cli.py
- `coberto` **modo instantaneo nao executa a suite** (TC-118) — nenhum processo de teste é iniciado e a execução termina sem contagem de (crítica, integração) — tests\test_modo_instantaneo.py
- `coberto` **modo instantaneo entrega estrutura rastreabilidade e diff** (TC-122) — o relatório traz os arquivos alterados, os cenários da spec com teste (alta, integração) — tests\test_modo_instantaneo.py
- `coberto` **segunda execucao completa sem mudanca volta do cache** (TC-123) — a suíte não é executada outra vez e o veredito é o mesmo da execução anterior (crítica, integração) — tests\test_cache.py
- `coberto` **impacto encontra testes no diretorio declarado** (TC-157) — `users/test_serializers.py` entra como teste impactado e nenhuma limitação (crítica, integração) — tests\test_impact.py
- `coberto` **impacto e matriz enxergam o mesmo conjunto de arquivos** (TC-158) — todo arquivo de teste que a matriz pode associar é visível para o impacto, (crítica, contrato) — tests\test_impact.py
- `coberto` **init instala o guia de agente na raiz do projeto** (TC-163) — `AGENT-SENTRY.md` é criado na raiz, mencionando `sentry new`, e (alta, integração) — tests\test_init_project.py
- `coberto` **init cria o banco ja na versao atual, com a tabela runs pronta** (TC-164) — o banco criado já registra `CURRENT_SCHEMA_VERSION` em (alta, integração) — tests\test_init_project.py
- `coberto` **interpretador declarado por caminho e usado no lugar do global** (TC-166) — é o interpretador declarado que roda, ainda embrulhado em `coverage run -m pytest` (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **interpretador declarado inexistente vira erro de infraestrutura** (TC-167) — a execução sai como não executada, com erro de infraestrutura nomeando o (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **executavel pytest do venv roda no python do proprio venv** (TC-168) — o comando é montado com o interpretador irmão do venv, mantendo a cobertura (alta, integração) — tests\test_execution_evidence.py
- `coberto` **cobertura alterada funciona a partir de um relatorio lcov** (TC-179) — o percentual do código alterado é calculado corretamente (crítica, integração) — tests\test_changed_coverage.py
- `coberto` **spec all junta casos de todas as pastas** (TC-185) — o `Run` traz os casos das duas pastas somados, e `configuration.spec` (alta, integração) — tests\test_analyze.py
- `coberto` **spec all sem nenhuma pasta ainda recusa com erro claro** (TC-186) — levanta `ValueError` mencionando que nenhuma matriz de casos foi (alta, integração) — tests\test_analyze.py
- `coberto` **arquivo em diretório excluído não entra no diff analisado** (TC-188) — o arquivo excluído não aparece na lista de arquivos alterados do (alta, integração) — tests\test_analyze.py
- `coberto` **sem exclude declarado, nada é filtrado** (TC-189) — todo arquivo alterado aparece no diff, sem nenhum ser removido (alta, integração) — tests\test_analyze.py
- `coberto` **projeto de outra stack mede cobertura pelo relatório que ele mesmo gera** (TC-190) — a cobertura do código alterado é calculada a partir do lcov (alta, integração) — tests\test_analyze.py
- `coberto` **projeto de outra stack roda a propria suite e tem veredito real** (TC-191) — os testes são contados a partir do JUnit gerado pelo comando (crítica, integração) — tests\test_analyze.py
- `coberto` **base declarada revela o que a branch mudou** (TC-207) — os arquivos e as linhas commitados na branch aparecem como alterados, em vez (crítica, integração) — tests\test_git_context.py
- `coberto` **sem base declarada o comportamento atual permanece** (TC-208) — o diff é o da árvore contra `HEAD`, como antes (crítica, integração) — tests\test_git_context.py
- `coberto` **base inexistente vira erro de infraestrutura** (TC-210) — a execução registra erro de infraestrutura nomeando a referência, e o veredito (crítica, integração) — tests\test_git_context.py
- `coberto` **a base efetivamente usada aparece no relatorio** (TC-211) — a referência declarada aparece na evidência da execução (alta, contrato) — tests\test_git_context.py
- `coberto` **runner ausente sai como inconclusivo e nao como reprovacao** (TC-212) — a execução sai como não executada, com erro de infraestrutura, e nenhuma (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **reprovacao real continua sendo reprovacao** (TC-213) — a execução sai como reprovada, sem erro de infraestrutura, com a contagem do resumo (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **suite aprovada permanece coberta** (TC-214) — a execução sai como coberta, sem erro de infraestrutura e sem reprovação fabricada (alta, integração) — tests\test_execution_evidence.py
- `coberto` **clear sem confirmacao apenas mostra o que sairia** (TC-218) — a saída inclui `"Repita com \`--yes\`"`, e nenhum arquivo é (crítica, integração) — tests\test_history_cli.py
- `coberto` **clear com confirmacao remove execucoes e preserva as specs** (TC-219) — os quatro arquivos da execução são removidos, a tabela `runs` (crítica, integração) — tests\test_history_cli.py
- `coberto` **keep-last preserva as execucoes mais recentes** (TC-220) — os arquivos de `r1` são removidos, os de `r2` e `r3` (alta, integração) — tests\test_history_cli.py
- `coberto` **clear sem historico nao inventa trabalho** (TC-221) — o comando termina com sucesso (código 0) e a saída inclui (média, integração) — tests\test_history_cli.py
- `coberto` **sentry.toml intocado desde o init fica fora do diff** (TC-222) — o arquivo não aparece entre os arquivos alterados (crítica, integração) — tests\test_git_context.py
- `coberto` **sentry.toml editado pelo usuario volta ao diff** (TC-223) — o arquivo aparece entre os arquivos alterados (crítica, integração) — tests\test_git_context.py
- `coberto` **gitignore so com as entradas do Sentry fica fora do diff** (TC-224) — o arquivo não aparece entre os arquivos alterados (alta, integração) — tests\test_git_context.py
- `coberto` **gitignore com linha do usuario na mesma mudanca entra no diff** (TC-225) — o arquivo aparece entre os arquivos alterados (alta, integração) — tests\test_git_context.py
- `coberto` **marcador orfao em arquivo nao tocado aparece no status** (TC-233) — o achado de marcador órfão aparece para aquele arquivo (alta, integração) — tests\test_status.py
- `coberto` **mesmo marcador orfao nao aparece num sentry run comum** (TC-234) — nenhum achado de marcador órfão aparece para aquele arquivo (média, integração) — tests\test_status.py
- `coberto` **fora de repositorio git status sai como erro de infraestrutura** (TC-236) — a execução registra erro de infraestrutura, sem inventar cobertura nem (crítica, integração) — tests\test_status.py
- `coberto` **status --json inclui o payload gravado pelo relatorio** (TC-237) — o JSON traz o mesmo `Run` que o relatório em Markdown descreve (média, integração) — tests\test_status.py
- `coberto` **linhas alteradas alimentam a analise de cobertura de todas as hunks** (TC-243) — os dois pontos aparecem entre as linhas alteradas do arquivo (crítica, integração) — tests\test_git_context.py

### Frontend

- `coberto` **todo comando do cli aparece no DocsPage.tsx** (TC-67) — todo comando aparece no texto do arquivo (crítica, contrato) — tests\test_docs_consistency.py
- `coberto` **todo tipo de campo do catalogo aparece na tabela do DocsPage.tsx** (TC-70) — toda chave aparece no texto do arquivo (alta, contrato) — tests\test_docs_consistency.py
- `coberto` **o valor de camada no exemplo do DocsPage.tsx e uma camada valida** (TC-71) — o valor é um dos três valores de `Layer` (`backend`, `integração`, (crítica, contrato) — tests\test_docs_consistency.py
- `coberto` **landing mostra o titulo e os cards de feature** (TC-155) — o título e os quatro cards de feature estão visíveis (alta, e2e) — frontend\e2e\home.spec.ts — evidência: ..\test-results\home-mostra-o-título-e-os-quatro-cards-de-feature\test-finished-1.png, ..\test-results\home-mostra-o-título-e-os-quatro-cards-de-feature\trace.zip
- `coberto` **menu mobile abre e fecha ao clicar no hamburguer** (TC-156) — o link "Docs" do menu vai de oculto para visível e volta a oculto (média, e2e) — frontend\e2e\home.spec.ts — evidência: ..\test-results\home-menu-mobile-abre-e-fecha-ao-clicar-no-hambúrguer\test-finished-1.png, ..\test-results\home-menu-mobile-abre-e-fecha-ao-clicar-no-hambúrguer\trace.zip

## Limitações

> O Sentry não conseguiu verificar isto — não é aprovação nem reprovação, é ausência de evidência.

- tipos de campo fora do catálogo, sem cobrança de classes: booleano

## Classes não aplicáveis

> Dispensadas de propósito, com justificativa declarada no CASES.md — não é lacuna do Sentry.

- caminho_do_executavel/vazio — `[test] command` em branco já é verificado na spec
- caminho_do_executavel/tamanho-maximo-excedido — o comprimento do caminho é limite do
- suporte_a_cor/tamanho-maximo-excedido — o valor vem de um conjunto fechado de
- suporte_a_cor/caracteres-especiais — idem — não é entrada de usuário.
- veredito_colorido/tamanho-maximo-excedido — uma de quatro cores fixas do
- veredito_colorido/caracteres-especiais — idem.
- severidade_colorida/vazio — toda severidade do domínio (`Severity`) mapeia
- severidade_colorida/tamanho-maximo-excedido — uma de três cores fixas, não
- severidade_colorida/caracteres-especiais — idem.
- quantidade_de_specs/vazio — nenhuma spec no projeto já é caminho
- quantidade_de_specs/tamanho-maximo-excedido — contagem de diretórios,
- suporte_a_reconfigure/verdadeiro — o caminho feliz (stream normal, com
- forma_de_invocacao/vazio — o CLI sempre é invocado de alguma forma;
- forma_de_invocacao/tamanho-maximo-excedido — a forma de invocação é
- forma_de_invocacao/caracteres-especiais — idem — não é entrada de
- badge_do_checklist/vazio — nem toda linha do checklist tem badge (numa
- badge_do_checklist/tamanho-maximo-excedido — um de quatro rótulos fixos
- badge_do_checklist/caracteres-especiais — idem — não é entrada de
- status_do_git/tamanho-maximo-excedido — nome de branch vem do Git, cujo
- status_do_git/caracteres-especiais — o nome do branch é exibido como o
- simbolo_do_veredito/tamanho-maximo-excedido — um de quatro caracteres
- simbolo_do_veredito/vazio — todo veredito do domínio (`VerdictStatus`)
- simbolo_do_veredito/caracteres-especiais — idem — não é entrada de
- simbolo_da_severidade/tamanho-maximo-excedido — um de três caracteres
- simbolo_da_severidade/vazio — toda severidade (`Severity`) mapeia para um
- simbolo_da_severidade/caracteres-especiais — idem — não é entrada de
- quadro_da_suite/tamanho-maximo-excedido — um de dois estados fechados
- quadro_da_suite/caracteres-especiais — idem.
- conteudo_do_dashboard/tamanho-maximo-excedido — os elementos do dashboard
- conteudo_do_dashboard/vazio — `render_dashboard` sempre recebe um `Run`
- conteudo_do_dashboard/caracteres-especiais — idem — não é entrada de
- extensao_do_arquivo/vazio — um arquivo sempre tem extensão (ou nenhuma
- extensao_do_arquivo/tamanho-maximo-excedido — extensão é um sufixo
- origem_do_texto/vazio — uma linha vazia não contém palavra de erro
- origem_do_texto/tamanho-maximo-excedido — o casamento é por regex
- extensao_do_arquivo/caracteres-especiais — extensão é comparada por
- origem_do_texto/caracteres-especiais — a origem (código real vs.
- origem_do_texto/valido — o caminho normal (código real, não
- linha_excluida/tamanho-maximo-excedido — a exclusão é um conjunto de
- caminhos_de_erro/vazio — a quantidade é o tamanho das listas produzidas por
- caminhos_de_erro/nao-numerico — idem, é um comprimento de lista, nunca texto.
- caminhos_de_erro/negativo — idem, um comprimento de lista nunca é negativo.
- caminhos_de_erro/limite-superior — a dimensão agrega por contagem, sem teto próprio;
- cobertura/tamanho-maximo-excedido — a cobertura chega como mapa de arquivo para
- cobertura/caracteres-especiais — idem, os valores já vêm validados pelo leitor de
- comando_documentado/vazio — a lista de comandos vem sempre de
- comando_documentado/tamanho-maximo-excedido — nome de subcomando é escolhido
- comando_documentado/caracteres-especiais — idem — nomes de comando são
- tipo_de_campo_documentado/vazio — `FIELD_CLASSES` nunca está vazio — é o
- tipo_de_campo_documentado/tamanho-maximo-excedido — idem
- tipo_de_campo_documentado/caracteres-especiais — idem — chaves são
- valor_de_camada_no_exemplo/vazio — o snippet de exemplo sempre declara um
- valor_de_camada_no_exemplo/tamanho-maximo-excedido — o valor é um de três
- valor_de_camada_no_exemplo/caracteres-especiais — idem — valor fechado do
- comando/tamanho-maximo-excedido — o comprimento do comando é limite do sistema
- junit_xml/tamanho-maximo-excedido — idem, o caminho é validado pelo sistema de arquivos.
- junit_xml/caracteres-especiais — o caminho é usado como `self.root / junit_xml` sem
- entrada_gitignore/tamanho-maximo-excedido — as entradas são um conjunto fechado
- codigo_de_saida/vazio — o `sentry run` sempre devolve um código; ausência de código
- codigo_de_saida/nao-numerico — o valor vem do código de saída de um processo, que o
- codigo_de_saida/negativo — código de saída de processo não é negativo; o domínio é
- codigo_de_saida/limite-superior — o domínio é fechado em 3, e o caso de 3 é
- commit_analisado/caracteres-especiais — o valor é a saída de `git rev-parse HEAD`,
- commit_analisado/tamanho-maximo-excedido — idem, comprimento fixo definido pelo Git.
- linha_alterada/tamanho-maximo-excedido — a decisão é sobre o número da linha estar
- argumento_spec/tamanho-maximo-excedido — o valor é um slug de diretório, limitado
- marcador_cenario/tamanho-maximo-excedido — o marcador é comparado com o nome do caso
- arquivo_do_marcador/vazio — nenhuma linha de teste alterada é o caso de marcador em
- arquivo_do_marcador/tamanho-maximo-excedido — o caminho vem do diff do Git, limitado
- modo_de_execucao/tamanho-maximo-excedido — o modo é um de dois valores fechados
- hash_da_entrada/tamanho-maximo-excedido — o hash tem comprimento fixo por
- lacuna/tamanho-maximo-excedido — a espécie de lacuna vem de um conjunto fechado de
- test_paths/tamanho-maximo-excedido — o comprimento do caminho é limite do sistema de
- presenca_do_guia/vazio — o `init` sempre escreve o arquivo com o
- versao_do_schema/vazio — um banco recém-criado pelo `init` sempre
- versao_do_schema/nao-numerico — a coluna é `INTEGER NOT NULL`; o
- versao_do_schema/negativo — a versão só é incrementada pelo próprio
- versao_do_schema/zero — exercitada pelo `Dado` do caso de migração
- versao_do_schema/limite-superior — `CURRENT_SCHEMA_VERSION` é o próprio
- dado_preexistente/vazio — uma tabela vazia não perde nada na migração
- dado_preexistente/caracteres-especiais — o conteúdo é opaco pro
- dado_preexistente/tamanho-maximo-excedido — o conteúdo da tabela do
- comando/vazio — já verificada na spec `execucao-fiel-da-suite-declarada`, que trata
- comando/tamanho-maximo-excedido — o comprimento do comando é limite do sistema
- conteudo_do_relatorio/vazio — um arquivo vazio já é o caminho de
- conteudo_do_relatorio/tamanho-maximo-excedido — o conteúdo é lido
- conteudo_do_relatorio/caracteres-especiais — o formato é decidido por
- registro_de_cobertura/valido — o caminho feliz, já coberto pelos
- caminho_no_relatorio/vazio — um `SF:`/`filename` vazio não é um
- caminho_no_relatorio/tamanho-maximo-excedido — caminho de arquivo
- caminho_no_relatorio/caracteres-especiais — o caminho é comparado por
- linha_repetida/falso — o caminho comum de uma linha aparecer uma
- argumento_slug/vazio — `None` é o próprio caminho de "nenhum slug
- argumento_slug/tamanho-maximo-excedido — o slug vem de um diretório
- quantidade_de_specs/negativo — contagem de diretórios nunca é negativa.
- quantidade_de_specs/nao-numerico — é sempre `len()` de uma lista.
- quantidade_de_specs/zero — mesma contagem que a classe `vazio` (nenhuma
- quantidade_de_specs/limite-superior — contagem de diretórios não tem
- valor_de_severidade/vazio — uma chave sem valor não é TOML válido — o
- valor_de_severidade/tamanho-maximo-excedido — um de quatro valores
- valor_de_severidade/caracteres-especiais — idem — valor fechado do enum.
- valor_de_severidade/valido — o caminho de uma severidade reconhecida
- exclude_declarado/caracteres-especiais — os prefixos são comparados por
- stack_da_suite/vazio — sem `[test] command` nem `[coverage] path`
- stack_da_suite/tamanho-maximo-excedido — o valor é um comando de shell
- stack_da_suite/caracteres-especiais — idem — o comando é executado
- nome_do_projeto/vazio — testado no caso de fallback (nome do
- nome_do_projeto/tamanho-maximo-excedido — o nome é texto livre do
- nome_do_projeto/caracteres-especiais — idem — passa direto para o
- stack_do_teste/vazio — sem nenhum arquivo de teste, o cenário sai não
- stack_do_teste/tamanho-maximo-excedido — a extensão do arquivo é um
- stack_do_teste/caracteres-especiais — idem — extensão é comparada por
- diretorio_de_teste/vazio — sem `test_paths` declarado, o padrão
- diretorio_de_teste/tamanho-maximo-excedido — caminho de diretório
- diretorio_de_teste/caracteres-especiais — o caminho é comparado
- legibilidade_do_arquivo/vazio — um arquivo vazio é texto válido (string
- acento_do_marcador/vazio — um marcador vazio não casa com cenário
- acento_do_marcador/tamanho-maximo-excedido — o texto do marcador vem
- semelhanca_por_nome/vazio — uma função sem nome não existe em nenhuma
- semelhanca_por_nome/tamanho-maximo-excedido — nome de função/teste
- semelhanca_por_nome/caracteres-especiais — o nome de função segue as
- posicao_da_secao/vazio — uma seção sempre tem título fixo no template
- posicao_da_secao/tamanho-maximo-excedido — os títulos são literais
- posicao_da_secao/caracteres-especiais — idem — não é entrada de
- nome_do_caso/vazio — o nome vem sempre do id do caso, que nunca é
- nome_do_caso/tamanho-maximo-excedido — o nome vem do título do caso na
- nome_do_caso/caracteres-especiais — o nome é texto livre em markdown,
- status_do_veredito/vazio — todo `VerdictStatus` é um dos quatro valores
- status_do_veredito/tamanho-maximo-excedido — um de quatro valores
- status_do_veredito/caracteres-especiais — idem — valor fechado do enum.
- regra_do_achado/vazio — toda regra vem de um `Finding` já construído
- regra_do_achado/tamanho-maximo-excedido — nomes de regra são
- regra_do_achado/caracteres-especiais — idem — identificador fechado do
- base/tamanho-maximo-excedido — o comprimento de uma referência é limite do Git; uma
- codigo_saida/vazio — o código de saída sempre existe quando o processo termina; a
- codigo_saida/nao-numerico — vem do sistema operacional como inteiro, nunca como texto.
- codigo_saida/limite-superior — qualquer código fora da tabela do pytest já cai na
- resumo_da_suite/caracteres-especiais — a saída é lida com `errors="replace"` e o
- flag_yes/vazio — a flag é um booleano do argparse — presente ou
- historico_existente/vazio — mesma classe de "ausente" acima — já
- manter_ultimas/vazio — sem `--keep-last`, o padrão é remover tudo
- manter_ultimas/negativo — `--keep-last` é um contador de execuções a
- manter_ultimas/nao-numerico — o argparse já recusa um valor
- manter_ultimas/zero — `--keep-last 0` tem o mesmo efeito de não manter
- manter_ultimas/limite-superior — contador de execuções sem teto
- arquivo/tamanho-maximo-excedido — o comprimento do caminho é limite do sistema de
- origem_da_alteracao/vazio — verificada no caso de arquivo ilegível, onde a origem não
- origem_da_alteracao/tamanho-maximo-excedido — a origem não é texto digitado, e sim o
- origem_da_alteracao/caracteres-especiais — idem — a comparação é entre o conteúdo
- escopo_da_analise/tamanho-maximo-excedido — o campo é um de dois valores fechados
- cobertura_do_arquivo/nao-numerico — vem sempre do parser de cobertura
- cobertura_do_arquivo/negativo — percentual de cobertura é uma proporção de linhas
- cobertura_do_arquivo/casas-excedentes — não há regra de formatação de entrada aqui;
- fonte_da_medicao/vazio — `sentry status` sempre mede agora; não existe um terceiro
- fonte_da_medicao/tamanho-maximo-excedido — idem `escopo_da_analise` — valor fixo
- fonte_da_medicao/caracteres-especiais — idem — não é entrada de usuário.
- hunks/negativo — a quantidade de blocos é a contagem de cabeçalhos `@@` presentes
- hunks/nao-numerico — o cabeçalho é casado por expressão regular numérica, então o
- diff/vazio — diff vazio significa nenhum arquivo alterado, caminho já verificado
- diff/tamanho-maximo-excedido — a saída é lida inteira do `git diff`, sem corte

## Evidência

### Arquivos alterados

- Comparado com: `312181d`

- .github/workflows/ci.yml
- .gitignore
- README.md
- README.pt-BR.md
- README.pt.md
- pyproject.toml
- sentry.toml
- src/sentrytest/__init__.py
- src/sentrytest/adapters/case_specs.py
- src/sentrytest/adapters/local_tools.py
- src/sentrytest/adapters/terminal.py
- src/sentrytest/application/analyze.py
- src/sentrytest/application/cases.py
- src/sentrytest/application/context.py
- src/sentrytest/application/coverage_context.py
- src/sentrytest/application/dimensions.py
- src/sentrytest/application/frontend_evidence.py
- src/sentrytest/application/reporting.py
- src/sentrytest/application/reuse.py
- src/sentrytest/application/traceability.py
- src/sentrytest/application/watch.py
- src/sentrytest/cli.py
- src/sentrytest/domain/catalog.py
- src/sentrytest/domain/models.py
- src/sentrytest/domain/rules.py
- src/sentrytest/init_project.py
- src/sentrytest/ports/inputs.py
- src/sentrytest/skills.py
- tests/test_analyze.py
- tests/test_autoanalise_workflow.py
- tests/test_cache.py
- tests/test_case_specs.py
- tests/test_cases_application.py
- tests/test_changed_coverage.py
- tests/test_cli.py
- tests/test_context.py
- tests/test_custo.py
- tests/test_dimensions.py
- tests/test_docs_consistency.py
- tests/test_execution_evidence.py
- tests/test_frontend_evidence.py
- tests/test_history_cli.py
- tests/test_init_project.py
- tests/test_modo_instantaneo.py
- tests/test_reporting.py
- tests/test_review_cli.py
- tests/test_sem_spec.py
- tests/test_status.py
- tests/test_terminal_color.py
- tests/test_terminal_ui.py
- tests/test_traceability.py
- tests/test_watch.py

### Execução de testes

- Comando: `C:\Users\lucas.ferreira\AppData\Local\Programs\Python\Python312\python.exe -m coverage run -m pytest`
- Saida resumida:
```
e.py .......                                  [ 52%]
tests\test_git_context.py .....................                          [ 57%]
tests\test_history_cli.py ...........                                    [ 59%]
tests\test_impact.py ..............                                      [ 63%]
tests\test_init_project.py ..........                                    [ 65%]
tests\test_input_adapters.py .                                           [ 65%]
tests\test_modo_instantaneo.py ....                                      [ 66%]
tests\test_reporting.py .......                                          [ 68%]
tests\test_review_cli.py .....                                           [ 69%]
tests\test_rules.py ...............                                      [ 73%]
tests\test_sem_spec.py .........                                         [ 75%]
tests\test_status.py ..........                                          [ 77%]
tests\test_terminal_color.py ...............                             [ 81%]
tests\test_terminal_ui.py ...............................                [ 88%]
tests\test_toml_config.py .....                                          [ 89%]
tests\test_traceability.py ...............................               [ 97%]
tests\test_watch.py ............                                         [100%]

- generated xml file: C:\Users\LUCAS~1.FER\AppData\Local\Temp\tmphkxhymav\junit.xml -
======================= 421 passed in 133.64s (0:02:13) =======================

```

## Custo

- Tokens gastos pelo Sentry: **zero**. Nenhum modelo é chamado em nenhum ponto da análise — é por isso que o mesmo commit sempre produz o mesmo veredito.
- Diff resumido: 657.193 bytes ≈ 161.879 tokens
- Este relatório: 65.911 bytes ≈ 15.836 tokens (medido sem este bloco de custo)
- Razão: o relatório é 10,2× menor que o diff cru.

> Conversão a 4 caracteres por token, sem tokenizer real: é ordem de grandeza para dimensionar o orçamento de contexto, não contagem exata.
