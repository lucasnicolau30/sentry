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

6. Rode `sentry check <slug>` → `sentry run --spec <slug> --run-tests`. Para
   analisar todas as specs de uma vez, use `--spec all`.

7. Leia `.sentry/reports/latest.md`: os achados vêm primeiro, ordenados por
   severidade; evidência bruta (arquivos alterados, saída do pytest) vem depois.

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

## Limites

- Só verifica backend (`Camada: backend | integração`); frontend é recusado de
  propósito — sem adaptador que o verifique, um caso ali ficaria eternamente
  `não coberto`.
- Sem `--run-tests` não há cobertura: o veredito tende a `inconclusivo`, nunca
  a `aprovado` por ausência de evidência.
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
