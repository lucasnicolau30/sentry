# Sentry - Test Quality Intelligence

## Contexto

Equipes sem testers dedicados dependem de agentes de IA para criar testes, mas ainda precisam de uma avaliação crítica independente: os testes realmente exercitam o comportamento importante? As mudanças introduziram riscos sem cobertura? A cobertura evoluiu ou apenas aumentou por linhas pouco relevantes? Hoje essas respostas ficam dispersas entre ferramentas de cobertura, revisão manual e histórico de desenvolvimento.

## Objetivo

Criar uma ferramenta orientada a mudanças que avalie a qualidade dos testes associados a uma alteração de código, combine cobertura quantitativa com sinais qualitativos e armazene os resultados para comparação histórica. A ferramenta deve produzir recomendações acionáveis para desenvolvedores e um veredito claro para a revisão da alteração.

## Princípios arquiteturais

O Sentry será uma ferramenta irmã do Draun. Ele consumirá as specs e issues geradas pelo Draun como fonte de contexto para derivar casos de teste e avaliar a implementação. O Sentry não deve alterar os artefatos originais do Draun; deve produzir plano de testes, rastreabilidade e relatórios próprios.

O Sentry deve seguir arquitetura hexagonal (Ports and Adapters). O núcleo de domínio não deve depender de Git, frameworks de testes, formatos de cobertura, bancos de dados ou modelos de IA. Essas integrações devem ser adaptadores substituíveis por meio de portas bem definidas.

O código deve aplicar Clean Code e SOLID, priorizando responsabilidades pequenas, dependências invertidas, interfaces coesas, nomes explícitos e regras testáveis isoladamente. A arquitetura deve permitir executar o mesmo caso de uso pela CLI local ou por uma futura API sem duplicar a lógica de negócio.

As decisões devem ser explicáveis e rastreáveis. IA pode complementar regras determinísticas, mas não deve ocultar evidências, substituir políticas configuradas ou impedir a execução sem serviço externo.

## Decisões tomadas para o primeiro corte

- Linguagem de implementação: Python.
- Distribuição: pacote Python `sentry-test`.
- Instalação oficial: `pip install sentry-test`.
- Comando executável instalado: `sentry`.
- Framework de testes analisado: pytest.
- Primeira integração de cobertura: formatos produzidos pelo ecossistema Python/pytest, priorizando cobertura de código alterado.
- Interface inicial: CLI local durante o ciclo de desenvolvimento.
- O núcleo deve permanecer independente de pytest para permitir futuros adaptadores.
- Testes de comportamento de frontend: Playwright como adaptador inicial.
- Integração frontend/backend: testes de contrato como camada intermediária.
- Formato preferencial dos critérios Draun: `Dado`, `Quando`, `Então` e `E`.
- Adaptadores oficiais do MVP: Draun, Git, pytest, coverage.py, Playwright, SQLite, Markdown e JSON. 

O armazenamento inicial será SQLite local. O acesso deve ocorrer por uma porta de persistência, permitindo migrar futuramente para PostgreSQL sem alterar o núcleo de domínio.

## Escopo

O primeiro modo de uso será local. O desenvolvedor executará o Sentry durante o desenvolvimento para avaliar a mudança, os testes relacionados, a cobertura e o contexto geral do código antes de enviar a alteração para revisão.

O Sentry deve localizar e ler a estrutura de specs do Draun, incluindo `SPEC.md`, arquivos de issues e critérios de aceitação. Requisitos, comportamentos e critérios devem ser convertidos em cenários de teste verificáveis.

## Integração com o ciclo do Draun

O Sentry deve ser ativado pelo agente de IA após a implementação de uma issue ou após a conclusão da spec. O fluxo esperado é:

1. O Draun finaliza ou disponibiliza uma `SPEC.md` válida.
2. O agente implementa o código e os testes da issue.
3. O agente executa `sentry analyze --spec <slug> --run-tests`.
4. O Sentry avalia a implementação, os testes, a cobertura e os comportamentos esperados.
5. O Sentry gera recomendações e salva a análise.
6. O agente corrige as lacunas ou conclui o trabalho com o relatório como evidência.

O Sentry deve procurar specs em `.draun/specs/<slug>/SPEC.md`. O parâmetro `--spec <slug>` deve permitir selecionar explicitamente uma spec e ser associado ao branch, commit e execução analisados.

Quando houver apenas uma spec aplicável ao projeto ou à mudança atual, o Sentry pode selecioná-la automaticamente. Quando houver mais de uma spec possível, deve exigir `--spec <slug>` e informar os slugs disponíveis, evitando analisar o contexto errado.

A ativação não deve depender de um processo em segundo plano nem alterar os arquivos originais do Draun. Ela ocorre quando o agente executa a CLI como parte natural da implementação.

O escopo comportamental inclui backend e frontend. A análise deve considerar não apenas cobertura de código, mas também contratos, estados visíveis, respostas de erro, validações, acessibilidade, consistência de interação e padrões definidos pelo projeto.

Incluído:

- análise de um diff entre uma referência e uma mudança;
- descoberta e execução, ou ingestão dos resultados, dos testes relacionados à mudança;
- cálculo de cobertura global e cobertura do código alterado;
- identificação de mudanças sem testes relevantes, testes frágeis ou redundantes e cenários importantes ausentes;
- relatório legível para humanos e saída estruturada para automações locais;
- persistência de execuções, métricas, achados e decisões ao longo do tempo;
- comparação entre execuções e detecção de regressões.

Fora do primeiro recorte:

- substituição de frameworks de teste ou de cobertura;
- correção automática do código ou geração automática de testes;
- garantia de que uma suíte prova a ausência de todos os defeitos;
- suporte inicial a todas as linguagens e ferramentas de teste.

## Interface CLI inicial

## Análise de comportamento e padronização

O Sentry deve derivar e avaliar cenários comportamentais para as camadas do sistema.

### Backend

- contratos de entrada e saída de APIs;
- validações de dados e regras de negócio;
- códigos HTTP, mensagens e formato de erros;
- autenticação, autorização e isolamento de dados;
- comportamentos esperados em exceções, timeouts e dependências indisponíveis;
- transações, idempotência e efeitos colaterais;
- logs e tratamento seguro de informações sensíveis.

### Frontend

- estados de carregamento, sucesso, vazio e erro;
- validação e mensagens de formulário;
- tratamento de erros de API e perda de conectividade;
- navegação, permissões e redirecionamentos;
- acessibilidade básica e uso consistente de componentes;
- comportamento responsivo quando especificado;
- estados de interação, como disabled, retry, cancelamento e feedback ao usuário.

### Padronização

O projeto deve poder declarar padrões verificáveis em configuração ou nas specs, como convenções de nomes, formato de erros, componentes obrigatórios, códigos de resposta, mensagens, acessibilidade e regras de tratamento de exceções. O Sentry deve apontar desvios com a regra, evidência, localização e recomendação.

Quando a spec não definir o comportamento de uma exceção ou estado de interface, o Sentry deve registrar uma lacuna de especificação, sem inventar um requisito silenciosamente.

## Dimensões de cobertura do sistema

O Sentry deve organizar a avaliação por dimensões, evitando tratar cobertura de linhas como sinônimo de qualidade completa:

- requisitos e regras de negócio;
- backend, APIs, persistência, transações e integrações;
- frontend, componentes, estados e navegação;
- fluxos ponta a ponta;
- contratos e qualidade dos dados;
- exceções, resiliência e recuperação;
- segurança e autorização;
- performance e volume;
- configuração, observabilidade e operação.

Cada dimensão deve informar `coberta`, `parcial`, `não coberta` ou `não aplicável`, sempre acompanhada da evidência e da justificativa. O projeto deve poder desativar dimensões que não façam parte do seu contexto.

## Rastreabilidade comportamental

O Sentry deve manter uma relação explícita entre requisito da spec, cenário esperado, teste encontrado ou gerado, resultado da execução, evidência de cobertura e achados. Uma lacuna deve indicar em qual etapa a rastreabilidade foi interrompida.

No primeiro corte, o núcleo deve priorizar requisitos, backend Python/pytest, APIs, exceções, cobertura do código alterado e estados de frontend descritos nas specs. Análises profundas de navegador, segurança, performance e operação devem ser extensões desacopladas por adaptadores.

## Modelo de caso de teste

O Sentry deve combinar requisitos da spec, regras determinísticas, análise de código, resultados de pytest, cobertura e, quando habilitado, análise Playwright para produzir a melhor matriz de casos possível. Fontes diferentes podem contribuir para o mesmo caso, mas o relatório deve preservar a origem e o nível de confiança de cada evidência.

No MVP, o Playwright será executado quando o projeto possuir configuração e testes de frontend compatíveis. A ausência de Playwright não deve impedir análises exclusivamente de backend; nesse caso, a dimensão de frontend será marcada como `não aplicável` ou `inconclusiva`, conforme a evidência disponível.

Cada caso de teste deve conter:

- identificador único;
- requisito ou critério de aceitação relacionado;
- camada: `backend`, `frontend` ou `integração`;
- pré-condições;
- dados de entrada;
- ação;
- resultado esperado;
- prioridade: `crítica`, `alta`, `média` ou `baixa`;
- tipo: `unitário`, `integração`, `contrato` ou `E2E`;
- teste existente relacionado, quando houver;
- status: `coberto`, `parcial`, `não coberto`, `falhou` ou `não executado`;
- evidências e recomendação.

O Sentry deve separar no relatório os casos de backend, frontend e integração. Um requisito que atravesse camadas deve gerar casos relacionados em cada camada necessária, evitando que um teste de backend seja considerado suficiente para validar um comportamento visual do frontend.

## Stack inicial de testes comportamentais

- Backend: pytest, coverage.py e adaptadores para testes de API.
- Frontend: Playwright para testar fluxos reais no navegador, estados de interface, navegação, erros de API, responsividade e acessibilidade básica.
- Contratos: validação dos contratos entre frontend e backend, preferencialmente a partir de schemas ou especificações OpenAPI quando disponíveis.

O Sentry deve recomendar a menor camada capaz de verificar cada comportamento. Testes unitários devem cobrir regras isoladas; testes de integração devem cobrir componentes e contratos; Playwright deve cobrir jornadas críticas e interações entre frontend e backend. O sistema não deve exigir E2E para todo cenário, pois isso aumentaria tempo e fragilidade sem melhorar proporcionalmente a análise.

O adaptador Playwright deve procurar `playwright.config.*` na raiz do projeto ou no caminho configurado em `sentry.toml`. Quando a configuração existir, o Sentry deve executar `npx playwright test` conforme a configuração do projeto e coletar resultados, falhas e evidências. Quando não existir configuração Playwright, a dimensão frontend deve ser marcada como `não aplicável` apenas se o projeto não declarar frontend; caso contrário, deve ser marcada como `inconclusiva`, com recomendação para configurar os testes.

Como o Playwright depende do ecossistema Node.js, o `sentry init` deve verificar Node.js, npm, `playwright.config.*` e a instalação de `@playwright/test`. Quando o adaptador frontend for solicitado e alguma dependência estiver ausente, o Sentry deve informar os comandos necessários:

```bash
npm install -D @playwright/test
npx playwright install
```

Esses comandos só podem ser executados pelo Sentry após confirmação explícita do usuário.

O resultado da execução do Playwright deve ser classificado assim:

- teste Playwright falhando: `reprovado` e achado de severidade `crítica`;
- Playwright configurado, mas impossível de executar por dependência, ambiente ou timeout: `inconclusivo` e erro de infraestrutura;
- projeto sem frontend declarado e sem configuração Playwright: `não aplicável`;
- frontend declarado sem configuração Playwright: `inconclusivo` e recomendação de configuração.

## Regras determinísticas do MVP

O MVP deve avaliar pelo menos estas regras:

- teste falhando;
- código alterado sem cobertura;
- requisito sem cenário;
- cenário sem teste associado;
- ausência de dados de cobertura;
- exceção ou caminho de erro alterado sem teste;
- comportamento de frontend sem estado de erro definido ou testado;
- contrato frontend/backend inconsistente.

Cada regra deve possuir identificador estável, severidade configurável, condição verificável, evidência esperada e recomendação. O resultado deve ser reproduzível para a mesma entrada e configuração.

Severidades padrão do MVP:

- teste falhando: `crítica`;
- código alterado sem cobertura: `alta`;
- requisito sem cenário: `alta`;
- cenário sem teste associado: `alta`;
- ausência de dados de cobertura: `média`;
- exceção ou caminho de erro alterado sem teste: `alta`;
- estado de erro de frontend ausente: `média`;
- contrato frontend/backend inconsistente: `crítica`.

O projeto poderá ajustar severidades por configuração, mas o relatório deve registrar a política efetivamente aplicada.

## Critérios de aceitação estruturados

Para gerar cenários com segurança, a spec Draun deve preferencialmente declarar critérios de aceitação em uma estrutura reconhecível, mesmo que mantenha uma explicação em texto livre para humanos. Texto livre pode conter contexto importante, mas não informa de maneira confiável quais são a condição inicial, a ação e o resultado esperado.

O Sentry deve reconhecer, quando disponíveis, os campos:

- `Dado`: pré-condição ou contexto;
- `Quando`: ação ou evento;
- `Então`: resultado esperado;
- `E`: condição adicional ou resultado complementar;
- camada: `backend`, `frontend` ou `integração`;
- tipo de teste e prioridade.

Para specs novas, `Dado`, `Quando` e `Então` são obrigatórios; `E` é opcional e representa uma condição ou resultado adicional. Specs legadas em texto livre continuam aceitas, mas os cenários derivados devem ser marcados com confiança reduzida e recomendação de revisão. O Sentry não deve tratar uma interpretação de texto livre como requisito confirmado sem evidência estruturada.

Exemplo:

```markdown
### Cenário: usuário sem permissão não acessa o recurso

- Dado: usuário autenticado sem a permissão `admin`
- Quando: solicita `GET /admin/reports`
- Então: a API responde `403`
- E: o frontend exibe uma mensagem de acesso negado
- Camada: backend e frontend
- Tipo: contrato e E2E
- Prioridade: alta
```

Quando os critérios estiverem apenas em texto livre, o Sentry pode sugerir cenários, mas deve marcá-los como derivados com menor confiança e solicitar revisão. Ele não deve tratar uma interpretação incerta como requisito confirmado.

O comando `sentry init` deve preparar um projeto para uso do Sentry, verificando a presença de Python, pytest, coverage.py e da estrutura de specs do Draun, criando a configuração inicial e o armazenamento SQLite quando necessário.

## Instalação e inicialização

O pacote deve suportar Python 3.10 ou superior e funcionar em Windows, macOS e Linux. Deve ser instalável com `pip` dentro ou fora de ambientes virtuais. O pacote e o contrato JSON devem seguir versionamento semântico, com migrações compatíveis quando possível.

O nome `sentry-cli` não deve ser usado: ele já identifica no PyPI o CLI oficial da Sentry, mantido pela getsentry. O pacote deste projeto será `sentry-test`, sujeito à confirmação final no momento da publicação. O comando instalado pode continuar sendo `sentry`.

O usuário deve instalar o Sentry com:

```bash
pip install sentry-test
```

Após a instalação, deve conseguir inicializar um projeto com:

```bash
sentry init
```

O comando deve validar dependências, informar o que está ausente e criar apenas os arquivos e diretórios necessários para a configuração local do Sentry.

O `sentry init` deve ser idempotente: executá-lo novamente não pode apagar histórico, sobrescrever configuração existente sem confirmação ou duplicar estruturas. Deve localizar a raiz do projeto a partir do diretório atual e permitir uma opção explícita para informar outro caminho.

O arquivo `sentry.toml`, na raiz do projeto, deve conter apenas configurações versionáveis, como localização das specs Draun, comandos de teste, dimensões habilitadas, políticas e formato de relatório. Segredos não devem ser armazenados nele.

O conteúdo mínimo deve ser:

```toml
[project]
name = "meu-projeto"

[draun]
specs_path = ".draun/specs"

[pytest]
command = "pytest"

[analysis]
run_tests_by_default = false
timeout_seconds = 300
```

O `sentry init` deve oferecer instalação assistida das dependências opcionais, sempre pedindo confirmação. Para o backend, pode instalar `pytest` e `coverage`; para o frontend, pode instalar o adaptador Playwright e, quando solicitado, os navegadores necessários. Sem confirmação, deve apenas informar os comandos de instalação.

O diretório `.sentry/` deve conter apenas dados locais: `sentry.db`, relatórios, planos derivados e evidências de execução. Esses dados devem ser ignorados pelo Git por padrão. O `sentry.toml` deve ficar na raiz e ser versionável.

Os planos derivados e evidências devem ser preservados no SQLite e nos arquivos locais para auditoria. O usuário poderá exportá-los para armazenamento de longo prazo, mas o Sentry não deve apagá-los automaticamente.

O banco deve possuir versão de schema e migrações controladas. Uma falha de migração deve interromper a inicialização com uma mensagem acionável, preservando o banco original.

O histórico deve ser mantido indefinidamente por padrão. A limpeza só pode ocorrer por comando explícito, com confirmação e resumo do que será removido. O Sentry deve oferecer exportação antes da limpeza para preservar evidências de auditoria.

O `sentry init` deve criar ou atualizar, somente com confirmação quando já existir, as entradas locais do `.gitignore`:

```gitignore
.sentry/sentry.db
.sentry/reports/
.sentry/runs/
.sentry/test-plans/
```

O arquivo `sentry.toml`, localizado na raiz do projeto, não deve ser ignorado e deve permanecer versionável. Ele contém políticas e caminhos compartilháveis; o `.sentry/` contém histórico, relatórios e evidências específicas de cada máquina.

## Licença e privacidade

O Sentry será distribuído sob a licença MIT, permitindo uso, modificação e distribuição, mantendo os avisos de copyright e licença.

O produto seguirá o princípio local-first:

- nenhuma telemetria será enviada por padrão;
- código-fonte, diffs, specs, resultados e histórico permanecerão locais;
- nenhuma integração com IA ou serviço externo será acionada sem configuração explícita;
- segredos e variáveis sensíveis deverão ser mascarados nos relatórios;
- logs não devem registrar tokens, senhas, chaves ou conteúdo sensível;
- qualquer envio externo futuro deverá ser opt-in, documentado e desativável;
- o usuário poderá remover ou exportar o histórico manualmente.

O comando `sentry analyze` deve iniciar uma análise local. Ele deve ler a spec Draun, identificar o escopo relevante, derivar os casos de teste esperados, localizar ou executar testes pytest, coletar cobertura, aplicar as regras determinísticas e persistir o resultado.

Opções iniciais recomendadas:

- `pip install sentry-test` — instala o Sentry no ambiente Python;
- `sentry init` — inicializa configuração e armazenamento;
- `sentry analyze` — analisa a mudança atual;
- `sentry analyze --spec <slug>` — analisa uma spec Draun específica;
- `sentry report` — exibe o último relatório;
- `sentry history` — lista e compara análises anteriores.

O comando `sentry analyze` não deve executar testes por padrão. Para executar a suíte, o usuário deve confirmar interativamente ou usar explicitamente:

```bash
sentry analyze --run-tests
```

O comando deve aplicar timeout configurável, respeitar o ambiente Python do projeto e classificar falhas de comando, timeout e dependências ausentes como erros de infraestrutura.

O relatório principal deve ser exibido no terminal em formato resumido e salvo em `.sentry/reports/latest.md`. Cada execução também deve possuir um relatório imutável identificado por seu ID, permitindo auditoria e comparação histórica. O mesmo resultado deve poder ser exportado em JSON versionado.

## Fluxo principal

1. O desenvolvedor cria ou atualiza uma spec usando o Draun.
2. O Sentry lê a spec e os critérios de aceitação.
3. O Sentry deriva cenários de teste esperados e cria uma matriz de rastreabilidade.
4. O sistema identifica a mudança atual e os testes pytest relacionados.
5. O sistema executa ou ingere resultados de pytest e coverage.py.
6. As regras determinísticas avaliam cobertura, falhas, lacunas e qualidade dos testes.
7. O Sentry salva a execução no SQLite e apresenta recomendações locais.

### Desenvolvedor

Quer saber rapidamente se sua mudança está adequadamente testada, quais riscos permanecem e qual teste deve ser adicionado primeiro.

### Revisor técnico

Quer uma evidência independente para revisar mudanças e distinguir cobertura útil de cobertura meramente numérica.

### Responsável técnico

Quer acompanhar tendências de qualidade, regressões recorrentes e áreas do sistema que acumulam risco.

## Comportamentos funcionais

### 1. Avaliar uma mudança

Dado um repositório, uma referência e uma revisão, o sistema deve analisar o diff, identificar arquivos e símbolos alterados e associar testes executados ou encontrados a essa mudança.

O sistema deve separar:

- código alterado coberto e não coberto;
- testes que falharam, foram ignorados, não puderam ser executados ou não foram encontrados;
- achados de alta, média e baixa severidade.

Quando não houver informação suficiente para uma conclusão, o relatório deve declarar a incerteza e a evidência ausente, sem apresentar o resultado como aprovação.

### 2. Avaliar qualidade além da cobertura

O sistema deve gerar achados baseados em evidências disponíveis, incluindo:

- mudança comportamental sem teste correspondente;
- caminho de erro, validação ou autorização alterado sem teste;
- código alterado coberto apenas por teste indireto ou de baixa especificidade;
- teste que não verifica resultado relevante ou possui asserções fracas;
- teste potencialmente flakey, lento, redundante ou dependente de ordem/ambiente;
- cobertura reduzida em relação à referência;
- teste existente que deixou de representar o comportamento alterado.

Cada achado deve conter severidade, explicação, evidência, arquivo/linha quando disponível, impacto provável e recomendação objetiva.

### 3. Produzir um veredito

O relatório deve apresentar um status `aprovado`, `aprovado com ressalvas`, `reprovado` ou `inconclusivo`, configurável por política. O status `inconclusivo` deve ser usado quando faltarem evidências essenciais e nunca deve ser tratado como aprovação.

O veredito deve considerar pelo menos:

- falhas de testes;
- cobertura do código alterado;
- achados críticos;
- mudanças sem testes associados;
- qualidade e confiabilidade dos dados recebidos.

Políticas devem permitir limiares por repositório e, quando aplicável, por diretório ou tipo de mudança. O sistema deve explicar quais regras determinaram o veredito.

### 4. Integrar-se ao fluxo de desenvolvimento

O sistema deve oferecer uma interface de linha de comando adequada para uso local e aceitar configuração versionada no repositório.

Deve produzir:

- resumo textual para terminal;
- relatório Markdown para revisão de código;
- saída JSON versionada para automações;
- código de saída distinto para sucesso, ressalva, reprovação e erro de infraestrutura.

### 5. Persistir e comparar histórico

Cada avaliação deve ser armazenada com identificador da execução, repositório, revisão, referência, timestamp, ferramenta/versão, configuração aplicada, métricas, testes executados e achados.

O sistema deve permitir comparar uma execução com a referência anterior e mostrar:

- variação da cobertura global e alterada;
- novos, resolvidos e persistentes achados;
- evolução do veredito;
- tendência por período, componente e categoria de risco.

Quando os dados forem incomparáveis por mudança de configuração, framework ou base de cobertura, isso deve ser sinalizado.

A referência deve ser escolhida nesta ordem:

- se houver diff Git, usar o commit-base;
- caso contrário, usar a última execução do projeto;
- se não houver histórico, marcar a execução como análise inicial.

### 6. Preservar rastreabilidade

O relatório deve permitir rastrear cada conclusão até sua fonte: diff, resultado de teste, arquivo de cobertura, análise estática ou regra aplicada. Resultados parcialmente analisados devem indicar quais etapas foram concluídas.

## Requisitos não funcionais

- O resultado deve ser determinístico para a mesma entrada, versão e configuração, exceto em análises explicitamente probabilísticas.
- A ferramenta deve funcionar sem depender de um serviço externo para executar uma avaliação local.
- Dados históricos devem ser armazenados de forma segura, com isolamento por projeto e possibilidade de retenção configurável.
- Segredos, conteúdo sensível e código-fonte não devem ser enviados para serviços externos sem configuração explícita.
- Falhas de infraestrutura devem ser diferenciadas de falhas de qualidade do código.
- O formato JSON deve ser versionado para evitar quebra de integrações.
- O sistema deve registrar a versão dos analisadores e das regras usadas em cada avaliação.

## Modelos de dados e contratos

O formato JSON versionado deve definir pelo menos:

- `TestCase`: cenário, requisito, camada, tipo, prioridade, status e evidências;
- `Finding`: regra, severidade, mensagem, localização, evidência e recomendação;
- `Run`: identificador, projeto, commit, referência, configuração, timestamp e resultado;
- `Evidence`: fonte, caminho, intervalo, conteúdo resumido e confiança;
- `Verdict`: status, regras aplicadas, métricas e justificativa;
- `InfrastructureError`: etapa, causa, mensagem acionável e possibilidade de repetição.

Esses contratos devem distinguir claramente falha de qualidade, ausência de evidência e erro de infraestrutura.

## Critérios de aceitação

### Inicialização

1. `sentry init` cria `.sentry/`, `sentry.db`, diretórios de relatórios, planos e execuções, além de `sentry.toml` quando ele não existir.
2. Executar `sentry init` novamente preserva histórico e configuração existente, sem duplicar estruturas.
3. O comando identifica a presença ou ausência do Draun, pytest e coverage.py e informa ações corretivas.
4. Configuração inválida impede a análise com erro claro e localização do problema.
5. Migrações de schema são versionadas e não destroem o banco original em caso de falha.

6. Uma avaliação de uma revisão com teste falhando identifica a falha, exibe a evidência e retorna status reprovado.
7. Uma avaliação distingue cobertura global de cobertura do código alterado.
8. Uma função alterada sem teste relevante gera um achado rastreável com recomendação.
9. Um projeto pode configurar limiares e categorias sem alterar o código da ferramenta.
10. A mesma execução gera terminal, Markdown e JSON semanticamente equivalentes.
11. Uma execução é persistida e pode ser comparada com outra revisão do mesmo projeto.
12. A comparação mostra métricas que aumentaram, diminuíram, permaneceram iguais e ficaram incomparáveis.
13. O relatório explicita incertezas e usa `inconclusivo` quando necessário.
14. Um erro para executar o framework ou ler a cobertura retorna erro de infraestrutura distinto de reprovação por qualidade.
15. Cada achado contém severidade, evidência, localização quando disponível e ação recomendada.

## Questões em aberto

- Qual formato de exportação e retenção de auditoria será necessário além do armazenamento local?
- Quais regras determinísticas entram na primeira versão e quais ficam para fases posteriores?
- Quais padrões de frontend serão configuráveis por projeto?
- Quais tipos de projeto devem ser marcados como `não aplicável` em cada dimensão?

## Decisões tomadas para o primeiro corte

Antes da implementação, o time deve decidir:

- SQLite local atrás de uma porta de persistência;
- CLI local como primeiro produto, sem integração de CI;
- regras determinísticas como motor inicial;
- contratos JSON versionados para casos, achados, execuções, evidências, vereditos e erros;
- planos e evidências preservados para auditoria;
- suporte a Python em ambientes virtuais e sistemas operacionais comuns;
- política de privacidade sem envio externo de código ou diff por padrão.

Podem ficar para depois: dashboard completo, suporte a múltiplas linguagens, geração automática de testes, modelos próprios, plugins para todos os provedores e análise distribuída.

## Não objetivos

O produto não substitui revisão humana, não promete medir qualidade de forma perfeita e não deve incentivar metas cegas de cobertura. Seu papel é tornar as evidências, lacunas e tendências visíveis e acionáveis.

No primeiro corte, “gerar casos de teste” significa gerar cenários, dados de entrada, resultados esperados e critérios de rastreabilidade. A geração automática de código pytest fica fora do escopo inicial.