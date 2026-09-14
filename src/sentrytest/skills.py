"""Skills instaladas pelo `sentry init` para agentes que leem .claude/skills.

O Sentry nunca chama um modelo: a skill instrui o agente a preencher o artefato
e devolve o controle para a CLI, que valida de forma determinística.
"""
from __future__ import annotations

from pathlib import Path

SENTRY_CASES = """---
name: sentry-cases
description: Deriva a matriz de casos de teste de um pedido em texto livre e grava em .sentry/specs/<slug>/CASES.md. Use quando o usuário pedir para criar, revisar ou completar casos de teste e coberturas de uma funcionalidade.
---

# sentry-cases

Transforma um pedido em texto livre numa matriz de casos de teste que o Sentry
consegue validar, rastrear e cobrar.

## Fluxo

1. Rode `sentry new "<nome da funcionalidade>" --prompt "<pedido do usuário>" --json`.
   Isso cria `.sentry/specs/<slug>/PROMPT.md` (pedido preservado) e um `CASES.md` em
   branco, e devolve num só passo:
   - `template`: o esqueleto do `CASES.md` a preencher;
   - `layers`, `test_types`, `priorities`: os únicos valores aceitos;
   - `field_classes`: as classes de equivalência que o Sentry vai **cobrar** por tipo de campo;
   - `specDir`: onde o arquivo foi criado.

2. **Pergunte antes de escrever.** Resolva com o usuário toda ambiguidade que mude
   um caso: qual campo é obrigatório, o que acontece no erro, quem tem permissão,
   qual o comportamento esperado no limite. Não invente requisito — se algo ficar
   indefinido, registre em `## Campos` como regra declarada e diga ao usuário.

3. Preencha o `CASES.md` seguindo o template:
   - `## Campos` declara cada campo e seu **tipo**. Use os tipos de `field_classes`
     sempre que couber (`texto`, `inteiro`, `data`, `email`, `rota`...), porque é o
     tipo que faz o Sentry cobrar as classes. Tipo fora do catálogo vira limitação,
     não cobrança.
   - Um `## Caso:` por comportamento verificável, com nome curto e único.
   - `- **Classe:** <campo>/<classe>` conecta o caso à classe de equivalência que ele
     cobre. É por aqui que o Sentry sabe o que ainda falta.
   - Cubra **todas** as classes que `field_classes` lista para cada tipo declarado.

4. Rode `sentry check <slug>`. Corrija cada `[erro]` e cada `[classe ausente]`
   até a saída fechar limpa.

5. **Ligue cada caso ao teste que o exercita.** Escreva, na linha acima da função
   de teste, um comentário `# cenario: <nome exato do caso>`:

   ```python
   # cenario: rejeita slug que escapa da pasta de specs
   def test_select_spec_rejects_slug_escaping_specs_dir(tmp_path):
       ...
   ```

   Sem isso o Sentry tenta adivinhar pela semelhança entre o nome do caso e o
   nome da função — o que falha quando o caso está em português e o teste em
   inglês, e o caso sai como `não coberto` embora o teste exista. O marcador é o
   vínculo declarado; a semelhança de nome é só o palpite de reserva.

6. Só então rode `sentry run --spec <slug> --run-tests`.

## Limites

Você declara **intenção**: requisito, camada, tipo, prioridade, entrada, resultado
esperado. Quem decide **status**, teste associado e evidência é o Sentry, medindo o
código e a execução real. Nunca escreva status no `CASES.md` e nunca afirme que um
caso está coberto — isso é conclusão do Sentry, não sua.

Não edite nada dentro de `.sentry/reports/` ou `.sentry/runs/`: são evidências de
auditoria.
"""

SKILLS = {"sentry-cases": SENTRY_CASES}

# A skill acima só é lida pelo Claude Code (.claude/skills/). Este guia fica na
# raiz do projeto para qualquer agente de IA que consiga rodar comandos de
# shell — sem depender do formato de skill de uma ferramenta específica.
AGENT_GUIDE = """# Sentry — guia para agentes de IA

O Sentry mede se a implementação corresponde à intenção declarada. Ele não gera
código nem testes: quem declara intenção e quem escreve código e testes é você
(o agente) ou o usuário; o Sentry só mede.

Funciona com qualquer agente de IA que consiga rodar comandos de shell — não é
específico do Claude Code.

## Divisão de responsabilidade

- Você declara intenção: escreve o `CASES.md`.
- O Sentry mede a realidade: decide status, teste associado, evidência e veredito.

Nunca escreva `status` ou `coberto` no `CASES.md` — isso é conclusão do Sentry,
não sua.

## Fluxo

1. `sentry new "<nome>" --prompt "<pedido>" --json`
   Cria `.sentry/specs/<slug>/{PROMPT.md,CASES.md}` e devolve, no mesmo comando:
   - `template`: o esqueleto do `CASES.md` a preencher;
   - `layers`, `test_types`, `priorities`: os únicos valores aceitos;
   - `field_classes`: as classes de equivalência cobradas por tipo de campo;
   - `specDir`: onde o arquivo foi criado.

2. **Pergunte antes de escrever.** Resolva com quem pediu a funcionalidade toda
   ambiguidade que mude um caso. Não invente requisito.

3. Preencha o `CASES.md`: um `## Caso:` por comportamento verificável, com
   `Requisito`, `Camada`, `Tipo`, `Prioridade`, `Dado`, `Quando`, `Então`.
   `- **Classe:** <campo>/<classe>` liga o caso a uma classe de equivalência do
   catálogo — é por aqui que o Sentry sabe o que ainda falta declarar.

4. Rode `sentry check <slug>`. Corrija cada `[erro]` e `[classe ausente]` até a
   saída fechar limpa.

5. **Ligue cada caso ao teste real.** Escreva, na linha acima da função de
   teste, um comentário `# cenario: <nome exato do caso>`:

   ```python
   # cenario: rejeita slug que escapa da pasta de specs
   def test_select_spec_rejects_slug_escaping_specs_dir(tmp_path):
       ...
   ```

   O marcador funciona em qualquer linguagem, com qualquer comentário
   (`// cenario:`, `-- cenario:`), e tolera diferença de acento. Sem ele o
   vínculo cai no palpite de reserva por semelhança de nome, que falha quando o
   caso está em português e o teste em inglês.

   A extração de nomes de teste reconhece `.py`, `.js`/`.ts`, `.go`, `.java`,
   `.kt`, `.cs`, `.rb`, `.php` e `.rs`, em `tests/`, `test/`, `spec/` e
   `__tests__/`. Teste ao lado do código exige declarar `[tests] paths`.

6. Rode `sentry review --spec <slug>` — ele encadeia `check`, `run` com testes e o
   relatório, num comando só. Os passos separados (`sentry check <slug>` →
   `sentry run --spec <slug> --run-tests`) continuam valendo quando você quiser
   parar entre eles. Para analisar todas as specs de uma vez, use `--spec all`.

   Sem spec nenhuma, `sentry review` ainda mede o que não depende dela: cobertura
   do alterado, caminhos de erro descobertos, testes falhando e testes impactados.
   As dimensões que dependem de intenção declarada saem `não aplicável` dizendo
   isso — nunca `coberta`. A spec é o teto do produto, não o piso.

7. Leia `.sentry/reports/latest.md`: os achados vêm primeiro, ordenados por
   severidade; evidência bruta (arquivos alterados, saída do pytest) vem depois.

## O loop

O fluxo acima acontece uma vez por funcionalidade. O que se repete dezenas de
vezes por tarefa é este loop, e ele é desenhado para que o passo mais frequente
seja o mais barato:

- **Ao pegar a tarefa** — `sentry new "<nome>" --prompt "<pedido>" --json` e você
  preenche o `CASES.md`. É o passo que custa token, e ele acontece uma vez.
- **Ao salvar** — deixe `sentry watch` rodando e não rode mais nada. Ele reavalia
  sozinho no modo instantâneo: nenhuma suíte executada, nenhum token gasto.
- **Ao salvar um teste** — o próprio watch escala para o modo completo, porque é
  executando que a mudança no teste vira evidência. Se o diff, os arquivos de
  teste e as specs não mudaram desde a última execução completa, a resposta volta
  do cache — e o relatório diz que voltou, e de quando é a evidência.
- **Quando houver lacuna** — rode `sentry context --json` e trabalhe **só sobre o
  que ele devolver**. Reler o código inteiro para descobrir o que falta é gastar
  contexto com o que o Sentry já mediu.
- **Antes de commitar** — `sentry review`: o veredito completo antes de o commit
  existir. É um hook local de desenvolvimento, não um portão remoto.
- **Periodicamente** — `sentry status`: a aplicação inteira, não só o diff. Todo
  arquivo de código é tratado como alterado, sempre com a suíte completa e nunca
  com o cache — é a medição autoritativa, não o loop rápido. Aponta arquivos com
  zero cobertura e marcadores órfãos em qualquer lugar do projeto, mesmo fora do
  que esta tarefa tocou.

Duas regras amarram o loop:

1. **O passo mais frequente é o mais barato.** Se avaliar ao salvar custasse a
   suíte inteira, ninguém deixaria o watch ligado — e a avaliação voltaria a ser
   cerimônia em vez de hábito.
2. **O LLM só é chamado onde a máquina não conclui.** O Sentry tria de forma
   determinística por zero token; você entra onde ele aponta lacuna, não onde ele
   já tem evidência.

### O que `sentry context --json` devolve

Um payload denso, e só do que não tem evidência:

- `summary`: veredito, número de achados e `tests_executed`;
- `uncovered_lines`: por arquivo, as faixas de linha alteradas que nenhum teste
  executou;
- `uncovered_error_paths`: `raise`/`throw` em linha alterada que nenhum teste
  executou;
- `failing_tests`: os nomes dos testes falhos, como a suíte os nomeou;
- `scenarios_without_tests`: casos declarados sem teste associado;
- `missing_equivalence_classes`: as classes que o catálogo cobra e nenhum caso
  cobre;
- `orphan_markers`: marcador `cenario:` que não corresponde a caso nenhum;
- `limitations`: o que o Sentry não pôde medir, dito em voz alta.

Toda chave sempre existe, vazia quando não há nada: chave ausente seria ambígua
entre "nada a fazer" e "o Sentry não olhou". Por isso `summary.tests_executed`
falso com `uncovered_lines` vazio significa que ninguém mediu — não que nada
ficou descoberto.

## Fora de Python

Um projeto de outra stack declara sua suíte e seu relatório de cobertura; o
Sentry executa e lê, sem depender de pytest:

```toml
[test]
command = "npx jest"
junit_xml = "reports/junit.xml"

[coverage]
path = "coverage/lcov.info"

[tests]
paths = ["src"]          # só se os testes não ficam em tests/
```

Cobertura aceita `lcov`, `cobertura` XML e o JSON do coverage.py, detectados
pelo conteúdo. Caminhos de erro são detectados por AST em Python e por padrão
sintático nas demais stacks — a diferença aparece como limitação no relatório.

## Python: prefira pytest à suíte do unittest

O Sentry embrulha o comando em `coverage run` e coleta a contagem via
`--junitxml` **quando reconhece o pytest** — nas três grafias equivalentes:
`pytest`, `python -m pytest` e o executável do venv (`.venv/bin/pytest`).

Qualquer outro comando é executado exatamente como declarado, sem instrumentação
e sem flag injetada. Isso inclui `python -m unittest`: ele roda, mas o Sentry não
tem de onde tirar contagem nem cobertura, e o veredito sai `não executado` —
ausência de evidência, não reprovação. Para medir uma suíte `unittest`, declare o
relatório que ela gera:

```toml
[test]
command = "python -m unittest discover"
junit_xml = "reports/junit.xml"   # gerado por unittest-xml-reporting, p.ex.
```

Em Django, rode a suíte por pytest em vez de `manage.py test` — é o que dá
cobertura medida sem configuração extra:

```toml
[test]
command = "python -m pytest"   # com pytest-django instalado
```

Com `DJANGO_SETTINGS_MODULE` no `pytest.ini`/`pyproject.toml`, ou inline
(`python -m pytest --ds=myproject.settings`). O `manage.py test` cai no caminho
genérico: roda, mas não mede.

## Outros comandos

- `sentry init [--install]` — prepara o projeto (uma vez só; `sentry new` já
  chama isso implicitamente). Idempotente.
- `sentry report` — reexibe o último relatório sem rodar nada de novo.
- `sentry history` — lista execuções e compara as duas últimas: cobertura,
  testes, achados novos, resolvidos e persistentes.
- `sentry clear [--keep-last N] [--yes]` — poda execuções e relatórios antigos.
  Sem `--yes` só mostra o que sairia. Nunca toca em `.sentry/specs/`.

## Limites

- Verifica backend (`Camada: backend | integração`) por cobertura de linha real,
  e frontend (`Camada: frontend`) por evidência de execução do Playwright — trace
  e screenshot por caso, nunca cobertura de linha, porque TypeScript não é medido
  por coverage.py/lcov/Cobertura. Declare `[e2e]` em `sentry.toml` para habilitar
  a segunda suíte.
- Sem `--run-tests` a análise roda no modo instantâneo: nenhuma suíte é
  executada, e a cobertura exibida é a da última execução completa, carimbada
  como vinda dela. Sem nenhuma execução completa anterior, a cobertura sai
  indisponível — e o veredito tende a `inconclusivo`, nunca a `aprovado` por
  ausência de evidência.
- Não edite nada dentro de `.sentry/reports/` ou `.sentry/runs/`: são evidências
  de auditoria.
"""


def install_skills(root: Path) -> list[str]:
    """Grava as skills em .claude/skills/<nome>/SKILL.md. Sobrescreve só o que gerou."""
    created = []
    for name, content in SKILLS.items():
        directory = root / ".claude" / "skills" / name
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "SKILL.md"
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            created.append(str(path.relative_to(root)))
    return created


AGENT_GUIDE_FILE = "AGENT-SENTRY.md"
SKILLS_DIR = ".claude/skills"


def generated_artifacts() -> tuple[str, ...]:
    """Caminhos que o proprio Sentry gera e sobrescreve, para saírem do diff.

    Sem isto, a primeira analise de todo projeto novo mede os arquivos que o
    `init` acabou de criar em vez do codigo do usuario. Derivado de SKILLS para
    nao dessincronizar quando uma skill nova for adicionada.

    `sentry.toml` e `.gitignore` ficam de fora desta lista de proposito: o
    Sentry os cria, mas quem os edita depois e' o usuario.
    """
    return (AGENT_GUIDE_FILE, *(f"{SKILLS_DIR}/{name}/" for name in SKILLS))


def install_agent_guide(root: Path) -> list[str]:
    """Grava o guia agnóstico de agente na raiz do projeto. Mesma semântica de
    install_skills: sobrescreve só quando o conteúdo instalado ficou desatualizado."""
    path = root / AGENT_GUIDE_FILE
    if not path.exists() or path.read_text(encoding="utf-8") != AGENT_GUIDE:
        path.write_text(AGENT_GUIDE, encoding="utf-8")
        return [str(path.relative_to(root))]
    return []
