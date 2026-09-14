# Fase 4: alcançar a aplicação inteira

## Prompt

Fase 4: alcancar a aplicacao inteira. (a) Camada frontend com Playwright: Layer.FRONTEND e TestType.E2E no vocabulario, execucao de segunda suite ([e2e] no sentry.toml) sem que a falha de uma mascare a outra, contagem e evidencia somadas as da suite [test]. (b) Rastreabilidade no frontend: o regex de extracao de teste em JS/TS ja existente cobre .ts/.tsx, o marcador // cenario: e agnostico de linguagem -- so falta frontend/e2e entrar em [tests] paths. (c) Nova dimensao de cobertura, 'interface e fluxo de usuario', alimentada por casos de camada frontend com e2e associado; nao aplicavel quando nenhum caso de frontend foi declarado, na mesma disciplina das outras quatro dimensoes. (d) Novos tipos de campo no catalogo: formulario (vazio, obrigatorio-ausente, invalido, valido, submissao-duplicada), navegacao (rota-existe, rota-inexistente, voltar, deep-link), responsivo (mobile, tablet, desktop), acessibilidade (foco-visivel, navegacao-teclado, rotulo-associado, contraste). (e) Evidencia de execucao anexada por cenario: caminho do trace e do screenshot do Playwright como campo Evidence no caso, nunca cobertura de linha -- o status de um caso de frontend vem de ter rodado e passado, e o relatorio declara essa limitacao na mesma disciplina que separa nao verificada de nao coberta. Aceite: a landing (frontend/) sai do exclude do sentry.toml, ganha spec de frontend cobrindo pelo menos um fluxo real da propria landing/docs, e um caso passa de nao coberto a coberto com trace anexado.

## Caso: camada frontend e aceita no vocabulario da spec

- **Requisito:** Layer.FRONTEND no vocabulário, sem quebrar backend/integração já aceitos
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** um CASES.md com `- **Camada:** frontend` num caso
- **Quando:** o documento é validado
- **Então:** nenhum erro de camada inválida é levantado, e o caso vira `Layer.FRONTEND`

## Caso: tipo e2e e aceito no vocabulario da spec

- **Requisito:** TestType.E2E no vocabulário, sem quebrar os tipos já aceitos
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** um CASES.md com `- **Tipo:** e2e` num caso
- **Quando:** o documento é validado
- **Então:** nenhum erro de tipo inválido é levantado, e o caso vira `TestType.E2E`

## Caso: catalogo cobra as cinco classes do tipo formulario

- **Requisito:** tipo de campo `formulario` cobra vazio, obrigatório-ausente, inválido, válido e submissão-duplicada
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** o catálogo padrão de tipos de campo
- **Quando:** as classes exigidas para `formulario` são consultadas
- **Então:** as cinco classes declaradas no prompt aparecem, nem mais nem menos

## Caso: catalogo cobra as quatro classes do tipo navegacao

- **Requisito:** tipo de campo `navegacao` cobra rota-existe, rota-inexistente, voltar e deep-link
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** o catálogo padrão de tipos de campo
- **Quando:** as classes exigidas para `navegacao` são consultadas
- **Então:** as quatro classes declaradas no prompt aparecem, nem mais nem menos

## Caso: catalogo cobra as tres classes do tipo responsivo

- **Requisito:** tipo de campo `responsivo` cobra mobile, tablet e desktop
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** o catálogo padrão de tipos de campo
- **Quando:** as classes exigidas para `responsivo` são consultadas
- **Então:** as três classes declaradas no prompt aparecem, nem mais nem menos

## Caso: catalogo cobra as quatro classes do tipo acessibilidade

- **Requisito:** tipo de campo `acessibilidade` cobra foco-visível, navegação-teclado, rótulo-associado e contraste
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** o catálogo padrão de tipos de campo
- **Quando:** as classes exigidas para `acessibilidade` são consultadas
- **Então:** as quatro classes declaradas no prompt aparecem, nem mais nem menos

## Caso: sentry check usa o mesmo catalogo mesclado que o sentry run

- **Requisito:** `sentry check` e `sentry run` não podem discordar sobre qual tipo de campo é conhecido
- **Camada:** backend
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** um `sentry.toml` que declara um tipo de campo customizado em `[catalog.fields]`
- **Quando:** `sentry check` valida um CASES.md que usa esse tipo
- **Então:** o tipo não é acusado como limitação fora do catálogo

## Caso: segunda suite e2e roda junto da suite backend sem mascarar a outra

- **Requisito:** `[e2e]` executa como suíte independente da `[test]`, com contagem própria
- **Camada:** backend
- **Tipo:** integração
- **Prioridade:** crítica
- **Dado:** `[e2e]` declarado em sentry.toml e `--run-tests`
- **Quando:** a análise roda
- **Então:** `test_execution` (backend) e `e2e_execution` aparecem os dois na configuração, cada um com sua própria contagem

## Caso: falha da suite e2e nao rebaixa caso de backend para parcial

- **Requisito:** a suíte e2e falhando não pode contaminar o status de um caso de backend que passou
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Dado:** um caso de camada backend associado a um teste que passou, e `e2e_failed=True`
- **Quando:** os casos de teste são construídos
- **Então:** o caso de backend continua `coberto`, não `parcial`

## Caso: falha da suite backend nao rebaixa caso de frontend para parcial

- **Requisito:** a suíte backend falhando não pode contaminar o status de um caso de frontend que passou
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Dado:** um caso de camada frontend associado a um teste que passou, e `suite_failed=True` (backend)
- **Quando:** os casos de teste são construídos
- **Então:** o caso de frontend continua `coberto`, não `parcial`

## Caso: SuiteAdapter roda comando declarado num subdiretorio via cwd

- **Requisito:** `[e2e]` roda num subprojeto (`frontend/`) com seu próprio `node_modules`/config
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** `SuiteAdapter(root, comando, cwd="algum-subdir")`
- **Quando:** o comando é executado
- **Então:** o processo sobe com o diretório de trabalho igual a `root/algum-subdir`, não `root`

## Caso: nome puro de executavel e resolvido pelo PATH mesmo sendo shim do Windows

- **Requisito:** um comando declarado por nome puro (`npx`, sem caminho) precisa ser encontrado mesmo quando é um shim `.cmd`/`.bat`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** um executável presente no PATH só como shim (sem extensão declarada no comando)
- **Quando:** o comando da suíte é resolvido
- **Então:** o caminho completo do shim é usado, em vez de falhar com "arquivo não encontrado"

## Caso: dimensao de interface fica coberta quando todos os casos frontend passam

- **Requisito:** "interface e fluxo de usuário" reflete a execução e2e, não cobertura de linha
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** todos os casos de camada frontend com status `coberto`
- **Quando:** as dimensões são avaliadas
- **Então:** a dimensão de interface sai `coberta`

## Caso: dimensao de interface fica nao aplicavel sem nenhum caso frontend declarado

- **Requisito:** "não aplicável" é distinto de "não coberta" também para a dimensão de interface
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** nenhum caso de camada frontend na matriz
- **Quando:** as dimensões são avaliadas
- **Então:** a dimensão de interface sai `não aplicável`, nunca `não coberta`

## Caso: marcador cenario em arquivo ts vincula caso ao teste playwright

- **Requisito:** o marcador `// cenario:` já agnóstico de linguagem associa caso a teste em `.ts`
- **Camada:** backend
- **Tipo:** integração
- **Prioridade:** crítica
- **Dado:** `frontend/e2e` declarado em `[tests] paths` e um arquivo `.spec.ts` com `// cenario: <nome>`
- **Quando:** a rastreabilidade é construída
- **Então:** o caso aparece associado ao arquivo `.ts`, como qualquer caso de backend seria a um `.py`

## Caso: evidencia de trace e screenshot e anexada ao caso quando o teste passou

- **Requisito:** o caminho do trace/screenshot do Playwright vira `Evidence` no caso, não um percentual de cobertura
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Dado:** um relatório JUnit do Playwright com anexos, e o marcador ligando caso a título do teste
- **Quando:** a evidência é cruzada
- **Então:** o caminho do trace e do screenshot aparece na evidência do caso

## Caso: sem relatorio junit a evidencia sai vazia sem inventar caminho

- **Requisito:** ausência de relatório (suíte não rodou, ou JUnit ilegível) não pode virar evidência inventada
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** um caminho de relatório JUnit inexistente, ou um XML corrompido
- **Quando:** a evidência é cruzada
- **Então:** o resultado é um dicionário vazio, nunca uma exceção nem um caminho falso

## Caso: sem e2e configurado no sentry toml a segunda suite nao roda

- **Requisito:** projeto sem `[e2e]` continua exatamente como antes da Fase 4
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Dado:** um `sentry.toml` sem seção `[e2e]`
- **Quando:** a análise roda com `--run-tests`
- **Então:** nenhum processo de e2e sobe, e `e2e_execution` não aparece na configuração

## Caso: landing mostra o titulo e os cards de feature

- **Requisito:** a landing renderiza o título e os quatro cards de feature
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Dado:** a landing carregada em `/`
- **Quando:** a página termina de renderizar
- **Então:** o título e os quatro cards de feature estão visíveis

## Caso: menu mobile abre e fecha ao clicar no hamburguer

- **Requisito:** em viewport mobile, o menu abre e fecha ao clicar no botão hambúrguer
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Dado:** viewport de 390px de largura, landing carregada em `/`
- **Quando:** o botão "Abrir menu" é clicado duas vezes
- **Então:** o link "Docs" do menu vai de oculto para visível e volta a oculto
