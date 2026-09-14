# Sentry

Português | [English](README.md)

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)
[![PyPI](https://img.shields.io/pypi/v/sentry-test.svg?style=flat&label=PyPI&color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/sentry-test/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

CLI de qualidade de teste orientada a mudança. O `sentry` cria a pasta da spec, valida a matriz de casos em markdown, roda a suíte, lê o diff e a cobertura, e emite um veredito auditável — e deixa o fluxo escrito para o agente de IA que for implementar a mudança.

Markdown é a fonte da intenção: a CLI parseia e valida `CASES.md` e `PROMPT.md` — ela nunca os escreve. O agente de IA faz a redação; o Sentry garante estrutura, rastreabilidade e veredito.

> Não confundir com o [Sentry da getsentry](https://sentry.io) (monitoramento de erros). Este projeto é distribuído como `sentry-test`.

## A divisão de responsabilidade

- **O agente de IA declara intenção** — escreve o `CASES.md`: requisito, camada, tipo, prioridade, entrada, resultado esperado.
- **O Sentry mede a realidade** — decide status, teste associado, evidência e veredito.

O agente nunca escreve status. O Sentry nunca chama um modelo. É isso que torna o veredito auditável e reproduzível.

## Instalação

```bash
pip install sentry-test
```

Requer Python 3.11+. Confira com `sentry --version` (imprime a versão do pacote).

Se faltar `pytest` ou `coverage`, o `init` avisa. Para instalar junto:

```bash
sentry init --install
```

## Setup

```bash
cd seu-projeto
sentry init
```

Cria `.sentry/` (specs, execuções, relatórios e banco), o `sentry.toml`, as entradas do `.gitignore`, e escreve o fluxo em dois lugares:

- **Skill `sentry-cases`** em `.claude/skills/sentry-cases/SKILL.md` — carregada automaticamente pelo Claude Code e por agentes que seguem essa convenção.
- **`AGENT-SENTRY.md`** na raiz do projeto — o mesmo fluxo em markdown puro, sem depender de convenção de nenhuma ferramenta.

Para outros agentes (Cursor, Windsurf, Codex, opencode), aponte-os para o `AGENT-SENTRY.md` no arquivo de regras que cada um já usa — por exemplo, uma linha em `.cursor/rules` ou `AGENTS.md`:

```markdown
Para escrever ou revisar casos de teste, siga AGENT-SENTRY.md.
```

`init` é idempotente: não apaga histórico, não sobrescreve configuração existente, não duplica estruturas.

## O fluxo

1. `sentry new "cadastro de cliente"` — cria `.sentry/specs/cadastro-de-cliente/` com `PROMPT.md` (pedido preservado) e `CASES.md` em branco
2. **`sentry-cases`** — seu agente pergunta o que estiver ambíguo e preenche o `CASES.md` seguindo o template
3. `sentry check cadastro-de-cliente` — estrutura válida? classes de equivalência do catálogo cobertas?
4. seu agente liga cada caso ao teste real com o marcador `# cenario: <nome exato do caso>`
5. `sentry watch` — deixe rodando enquanto escreve: reavalia a cada salvamento sem executar teste, e escala para a execução completa quando o arquivo salvo é um teste
6. `sentry context --json` — quando aparece lacuna, seu agente trabalha sobre ela em vez de reler o código
7. `sentry review` — `check` + `run` + relatório num comando só, como hook de pre-commit local
8. `sentry status` — periodicamente, a aplicação inteira em vez de só o diff: quais arquivos nenhum teste alcança
9. `sentry report` / `sentry history` — releitura e comparação entre execuções

Todo passo também funciona sem agente, pelos comandos abaixo.

## Comandos

Código de saída `0` em sucesso; veja a tabela de códigos adiante.

| Comando                                                   | O que faz                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sentry init [--install]`                                 | Prepara o repositório: `.sentry/`, `sentry.toml`, `.gitignore`, guia de agente e skills. Com `--install`, instala as dependências ausentes.                                                                                                                                                                                                       |
| `sentry new <nome> [--prompt "..."] [--json]`             | Cria a pasta da spec com slug derivado do nome. `--json` emite template, vocabulário aceito e classes cobradas, para o agente consumir.                                                                                                                                                                                                           |
| `sentry check [<slug>\|all]`                              | Valida `CASES.md`: estrutura, vocabulário e cobrança de classes de equivalência. `all` valida todas as specs juntas.                                                                                                                                                                                                                              |
| `sentry run [--spec <slug>\|all] [--run-tests]`           | Executa a análise e persiste. Sem `--run-tests` roda no modo instantâneo: nenhuma suíte é executada e a cobertura é a da última execução completa, carimbada como tal. Com `--run-tests`, uma execução completa cuja entrada não mudou volta do cache. Sem `--spec` e sem nenhum `CASES.md`, mede o que não depende de spec em vez de exigir uma. |
| `sentry review [--spec <slug>] [--base REF] [--no-tests]` | `check` + `run` + relatório num comando só, com testes por padrão. Funciona em repositório sem `.sentry/` e sem `sentry.toml`.                                                                                                                                                                                                                    |
| `sentry watch`                                            | Reavalia ao salvar. Modo instantâneo para o loop de digitação, escalando para a execução completa quando o arquivo salvo é um teste — é aí que a mudança vira evidência. Faz polling de mtime, sem acrescentar dependência de runtime.                                                                                                            |
| `sentry context --json`                                   | Emite as lacunas da última análise em JSON, para o agente de IA: faixas de linha descobertas, caminhos de erro que nenhum teste executou, testes falhando com nome, cenários sem teste, classes de equivalência ausentes, marcadores órfãos e limitações declaradas.                                                                              |
| `sentry status [--json]`                                  | Mede a aplicação inteira, não só o diff: todo arquivo de código-fonte é tratado como alterado, contra todas as specs declaradas (`--spec all`). Sempre roda a suíte completa, nunca volta do cache — é a medição periódica e autoritativa, não o loop rápido. Reporta quais arquivos têm cobertura zero.                                          |
| `sentry report`                                           | Exibe o último relatório (`.sentry/reports/latest.md`), acusando quando ele é de um commit que não é mais o HEAD.                                                                                                                                                                                                                                 |
| `sentry history`                                          | Lista execuções e compara as duas últimas: cobertura, testes, achados novos, resolvidos e persistentes.                                                                                                                                                                                                                                           |
| `sentry clear [--keep-last N] [--yes]`                    | Poda execuções e relatórios antigos. Sem `--yes` apenas mostra o que sairia — apagar histórico é irreversível. Nunca toca em `.sentry/specs/`.                                                                                                                                                                                                    |

## Dois modos, por desenho

O modo é o que decide o que o relatório pode afirmar sobre cobertura.

- **Instantâneo** — nenhum processo de teste é iniciado. Entrega estrutura, rastreabilidade, marcadores órfãos, o diff e a cobertura da última execução completa. A cobertura reaproveitada é sempre carimbada como vinda daquela execução, com o instante dela, nunca como medida agora. Sem nenhuma execução completa anterior, a cobertura sai indisponível e nenhum número é afirmado.
- **Completo** — executa a suíte. É o modo do hook de pre-commit e de tudo que precisa de contagem própria.

O `sentry watch` escolhe entre os dois a cada salvamento: instantâneo para arquivo de código, completo quando o arquivo salvo é um teste.

Uma execução completa reusa a anterior quando nada que importa mudou. A chave do cache é um hash de conteúdo de três entradas, e nada além delas: os arquivos que o diff lista, os arquivos de teste e as specs. Mudou qualquer uma, a suíte roda de novo — ou o código é outro, ou o que se cobra dele é outro. Uma execução que volta do cache diz isso no relatório, com o identificador e o instante da execução de onde a evidência veio: reusar sem dizer transformaria evidência velha em afirmação nova.

## O payload das lacunas

O `sentry context --json` é a outra metade do loop: o agente para de ler o código e passa a ler o que não tem evidência. Chaves: `summary`, `uncovered_lines`, `uncovered_error_paths`, `failing_tests`, `scenarios_without_tests`, `missing_equivalence_classes`, `orphan_markers`, `limitations`.

Toda chave sempre existe, vazia quando não há nada — chave ausente seria ambígua entre "nada a fazer" e "o Sentry não olhou". Nada ali é recalculado: cada lacuna já foi decidida por quem tinha o dado, e o payload só a recorta, então ele nunca pode discordar do relatório.

## Custo

Todo relatório termina com um bloco `## Custo`: os tokens que o Sentry gastou — **zero**, porque nenhum modelo é chamado em ponto nenhum, e é isso que faz o mesmo commit produzir sempre o mesmo veredito — e o tamanho do que ele resumiu, em bytes: o diff que leu e o próprio relatório. A conversão em tokens é declarada como estimativa a 4 caracteres por token, sem tokenizer real; é ordem de grandeza para dimensionar orçamento de contexto, não contagem exata.

## Códigos de saída

Quatro estados distinguíveis, para separar "código mal testado" de "meu ambiente quebrou":

| Código | Significado                            |
| ------ | -------------------------------------- |
| `0`    | aprovado                               |
| `1`    | aprovado com ressalvas                 |
| `2`    | reprovado                              |
| `3`    | inconclusivo ou erro de infraestrutura |

Erro de infraestrutura nunca produz veredito aprovado: uma suíte que não conseguiu rodar é diferente de uma suíte que reprovou.

`sentry check` mantém semântica própria: `0` estrutura válida, `1` erros estruturais, `2` não foi possível resolver a spec.

## Skills

Geradas para cada agente configurado; o `AGENT-SENTRY.md` cobre os demais.

| Workflow       | O que o agente faz                                                                                                                                                                                                                    |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sentry-cases` | Recebe o pedido em texto livre, cria a spec, **pergunta antes de escrever** toda ambiguidade que mude um caso, preenche o `CASES.md`, liga cada caso ao teste com `# cenario:` e roda `check` até fechar limpo. Nunca escreve status. |

## Regras determinísticas

Dez regras, com severidade configurável por projeto.

| Regra                             | Severidade padrão | Dispara quando                                              |
| --------------------------------- | ----------------- | ----------------------------------------------------------- |
| `test-failing`                    | crítica           | a suíte tem teste falhando                                  |
| `case-spec-invalid`               | crítica           | o `CASES.md` tem erro estrutural                            |
| `changed-code-uncovered`          | alta              | cobertura do código alterado é zero                         |
| `scenario-without-test`           | alta              | caso declarado sem teste associado                          |
| `error-path-without-test`         | alta              | `raise`/`throw` em linha alterada que nenhum teste executou |
| `missing-equivalence-class`       | alta              | classe exigida pelo catálogo que nenhum caso cobre          |
| `coverage-below-threshold`        | alta              | cobertura do código alterado abaixo do limiar declarado     |
| `requirement-without-scenario`    | média             | requisito sem cenário correspondente                        |
| `coverage-missing`                | média             | não foi possível calcular a cobertura do código alterado    |
| `global-coverage-below-threshold` | média             | cobertura global abaixo do limiar declarado                 |

Sem limiar declarado, o Sentry não inventa um mínimo. Quem define "quanto basta" é o projeto, e o relatório registra o número aplicado.

## Catálogo de classes de equivalência

Tabela fixa de situações que precisam de teste, **por tipo de campo**. Não gera casos: cobra os que o agente deixou de declarar.

Tipos conhecidos: `cpf`, `cnpj`, `email`, `senha`, `data`, `telefone`, `cep`, `inteiro`, `decimal`, `texto`, `rota`, `formulario`, `navegacao`, `responsivo`, `acessibilidade` — os quatro últimos são para casos de camada `frontend`, verificados por evidência de execução do Playwright, não por cobertura de linha.

Uma classe que não faz sentido para o campo pode ser dispensada **com justificativa**, em vez de virar caso artificial ou cobrança eterna:

```markdown
## Classes não aplicáveis

- **exclude/tamanho-maximo-excedido**: é parâmetro de configuração, não campo de formulário
```

A dispensa remove o achado, mas fica registrada no relatório — nada some em silêncio.

## Dimensões de cobertura

Cada uma reporta `coberta`, `parcial`, `não coberta` ou `não aplicável`, com evidência.

| Dimensão                                     | De onde tira a evidência                                      |
| -------------------------------------------- | ------------------------------------------------------------- |
| requisitos e regras de negócio               | cenários da spec com teste associado                          |
| APIs, persistência, transações e integrações | casos de tipo `contrato`/`integração` e camada `integração`   |
| exceções, resiliência e recuperação          | caminhos de erro alterados executados por algum teste         |
| segurança e autorização                      | campos de tipo `rota` com todas as classes de acesso cobertas |

`não aplicável` é distinto de `não coberta`: um projeto sem rotas não é punido na dimensão de segurança.

## Configuração

`sentry.toml` na raiz, versionável, sem segredos. Tudo é opcional além do que o `init` já escreve.

```toml
[project]
name = "meu-projeto"

[specs]
path = ".sentry/specs"

[test]                    # qualquer executor que exporte JUnit XML
command = "npx jest"
junit_xml = "reports/junit.xml"   # obrigatório fora do pytest: é a única fonte de contagem

[tests]                   # onde procurar testes
paths = ["tests"]         # padrão: tests, test, spec, __tests__

[coverage]                # relatório gerado pela suíte do próprio projeto
path = "coverage/lcov.info"
format = "lcov"           # opcional: detectado pelo conteúdo quando omitido

[analysis]
run_tests_by_default = false
timeout_seconds = 300
exclude = ["frontend/"]   # diretórios fora do escopo da análise

[policy.thresholds]       # sem isto, nenhum mínimo é cobrado
changed_coverage = 85
global_coverage = 90

[policy.severities]       # sobrescreve a severidade de qualquer regra
coverage-missing = "alta"

[catalog.fields]          # tipos de campo do seu domínio
matricula = ["vazio", "formato-invalido", "valida"]

[dimensions]              # eixos que não se aplicam ao projeto
disabled = []
```

`.sentry/` guarda specs, execuções, relatórios e o banco. Fica fora do Git, com uma exceção deliberada: `.sentry/reports/latest.md` é versionado, para o veredito aparecer no diff da PR sem que o revisor precise rodar o Sentry.

O histórico é mantido indefinidamente, e cresce a cada execução. Para podar:

```bash
sentry clear --keep-last 10        # mostra o que sairia
sentry clear --keep-last 10 --yes  # remove
```

As specs nunca são removidas: são intenção declarada, não evidência gerada.

## Stacks suportadas

A **derivação** — do pedido à matriz de casos — é agnóstica de linguagem: o `CASES.md` é markdown e o catálogo raciocina sobre tipo de dado, não sobre código.

A **verificação** depende do formato de intercâmbio que sua suíte exporta, não da ferramenta:

| Capacidade                 | Suporte                                                                                                                                       |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Execução da suíte          | qualquer comando que exporte **JUnit XML** — pytest, Jest, Vitest, `go test` (gotestsum), Surefire, `dotnet test`, RSpec, PHPUnit             |
| Cobertura                  | **lcov** (nyc, c8, Jest, simplecov), **Cobertura XML** (JaCoCo, coverlet), **coverage.py** (JSON) — detectados pelo conteúdo                  |
| Rastreabilidade caso↔teste | `.py`, `.js`/`.jsx`/`.ts`/`.tsx`, `.go`, `.java`/`.kt`, `.cs`, `.rb`, `.php`, `.rs` — e o marcador `cenario:` funciona em qualquer comentário |
| Caminhos de erro           | por AST em Python; por padrão sintático (`throw`, `catch`, `panic`, `rescue`, `panic!`) nas demais                                            |
| Análise de impacto         | 12 extensões de código-fonte                                                                                                                  |

A detecção de caminho de erro fora de Python é menos precisa que AST, e o relatório registra essa diferença como limitação — nunca a esconde.

Em Python, o **pytest** é o único runner instrumentado automaticamente: o Sentry o reconhece em `pytest`, `python -m pytest` e no executável do venv, embrulha em `coverage run` e coleta a contagem sozinho. Em Django, prefira `command = "python -m pytest"` com `pytest-django` a `manage.py test`. Qualquer outro comando — inclusive `python -m unittest` — roda **exatamente como declarado**, sem flag injetada: para medi-lo, declare o `junit_xml` que sua suíte gera, senão o veredito sai `não executado` por ausência de evidência.

Camada `frontend` é recusada de propósito: sem adaptador que a verifique, um caso declarado ficaria preso em `não coberto` para sempre.

## Local-first

Nenhuma telemetria, nenhuma chamada externa, nenhum envio de código ou diff. Todo o histórico permanece na máquina.

## Desenvolvimento

```bash
python -m pip install -e .
python -m pytest
```

O Sentry se analisa: `sentry run --spec all --run-tests` na raiz do repositório
casa os casos declarados em `.sentry/specs/` com as funções de teste reais e
reporta as quatro dimensões.

## Licença

MIT
