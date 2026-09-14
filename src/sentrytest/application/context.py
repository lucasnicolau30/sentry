"""O recorte do que não tem evidência, para o agente trabalhar sobre ele.

Um agente lendo o código é estruturalmente incapaz de saber o que os testes
executaram: quando ele diz "isso parece coberto", é inferência sobre o texto do
teste, não medição. O Sentry mede — e este módulo devolve a medição pelo avesso:
não o que foi verificado, mas o que sobrou sem prova. É isso que faz a iteração
seguinte custar o tamanho da lacuna em vez do tamanho do código.

Três disciplinas mandam no formato.

*Toda chave sempre existe, vazia quando não há nada.* Chave ausente é ambígua
entre "nada a fazer" e "o Sentry não olhou"; lista vazia é conclusiva. É a mesma
distinção que o resto do produto faz entre `não aplicável` e `não coberta`.

*Nada aqui é recalculado.* Cada lacuna já foi decidida por quem tinha o dado —
cobertura, AST, rastreabilidade, catálogo — e o payload só a recorta. Um segundo
cálculo que discordasse do relatório destruiria a reprodutibilidade que é a
única coisa separando este produto de um palpite.

*Denso e pequeno.* Copiar o relatório inteiro devolveria ao agente exatamente o
custo de contexto que este comando existe para cortar. O resumo tem três campos,
o suficiente para ele se situar antes de ler as lacunas.
"""
from __future__ import annotations

import re

# A classe de equivalência faltante nasce como dict em `domain.catalog`, mas o
# payload serializado não a guarda: ela só sobrevive dentro da mensagem do achado
# que `domain.rules` monta. Ler o achado é o único caminho, e é um caminho
# estável — a severidade da regra é configurável, o nome dela não.
_MISSING_CLASS_RULE = "missing-equivalence-class"
_MISSING_CLASS = re.compile(r"^Classe de equivalência não coberta: ([^/]+)/(.+) \(tipo (.+)\)\.$")

# `FAILED <nodeid>` é a linha do "short test summary info", que o pytest imprime
# por padrão. A segunda forma é a do progresso em `-v`, onde o nodeid vem antes
# da palavra; ela exige `::` justamente para que prosa de traceback contendo
# "FAILED" não vire nome de teste inventado.
_FAILED_SUMMARY = re.compile(r"^[ \t]*FAILED[ \t]+(\S+)", re.MULTILINE)
_FAILED_VERBOSE = re.compile(r"^(\S+::\S+)[ \t]+FAILED", re.MULTILINE)


def _ranges(lines) -> list[list[int]]:
    """Linhas consecutivas viram uma faixa; nenhum buraco é atravessado.

    Unir 10-11 com 13-14 numa faixa 10-14 encurtaria o payload ao preço de
    afirmar que a 12 é lacuna quando ela pode ser comentário ou linha em branco —
    o mesmo defeito que a cobertura do alterado já corrigiu ao parar de contar o
    que não é statement. A faixa aqui é o que está descoberto, não a região onde
    olhar; quem lê abre o arquivo e vê o resto de graça.
    """
    ranges: list[list[int]] = []
    for line in sorted(lines):
        if ranges and line == ranges[-1][1] + 1:
            ranges[-1][1] = line
        else:
            ranges.append([line, line])
    return ranges


def _uncovered_lines(configuration: dict) -> list[dict]:
    coverage = configuration.get("coverage") or {}
    executed = coverage.get("executed_lines") or {}
    measured = coverage.get("measured_lines") or {}
    changed = (configuration.get("git_change") or {}).get("changed_lines") or {}
    result = []
    for filename in sorted(changed):
        # "Linha medida" é a definição de `coverage_context`: só conta o que a
        # ferramenta de cobertura instrumentou. Divergir dela aqui faria o payload
        # cobrar teste para linha que o relatório não cobrou — e mandaria o agente
        # gastar a iteração escrevendo teste para um comentário.
        countable = set(changed[filename]) & set(measured.get(filename, ()))
        ranges = _ranges(countable - set(executed.get(filename, ())))
        if ranges:
            result.append({"file": filename, "ranges": ranges})
    return result


def _failing_tests(execution: dict) -> list[str]:
    """Os nomes que a saída da suíte nomeou — nem um a mais.

    Sem nome extraível a lista sai curta ou vazia, e a lacuna vira limitação
    declarada. Completar a contagem com um nome genérico mandaria o agente
    procurar um teste que não existe.
    """
    output = execution.get("output") or ""
    names: list[str] = []
    for pattern in (_FAILED_SUMMARY, _FAILED_VERBOSE):
        for name in pattern.findall(output):
            if name not in names:
                names.append(name)
    return names


def _missing_equivalence_classes(findings) -> list[dict]:
    classes = []
    for finding in findings:
        if finding.get("rule") != _MISSING_CLASS_RULE:
            continue
        match = _MISSING_CLASS.match(finding.get("message") or "")
        # Mensagem que não casa não é motivo para descartar a lacuna: perdê-la em
        # silêncio porque o texto da regra mudou seria pior do que entregá-la sem
        # os campos separados. `description` só aparece nesse caso, e é o sinal de
        # que os três campos vieram vazios por falha de leitura, não por ausência.
        classes.append(
            {"field": match.group(1), "class": match.group(2), "type": match.group(3)} if match
            else {"field": None, "class": None, "type": None, "description": finding.get("message")}
        )
    return classes


def _limitations(configuration: dict, failed: int, failing_tests: list[str]) -> list[str]:
    impact = configuration.get("impact") or {}
    error_paths = configuration.get("error_paths") or {}
    limitations = [*(impact.get("limitations") or ()),
                   *(error_paths.get("limitations") or ()),
                   *(configuration.get("catalog_limitations") or ())]
    # A suíte acusou falha e a saída não nomeou nenhuma: sem esta linha, uma lista
    # vazia de testes falhos afirmaria que nenhum falhou. É a lista vazia
    # conclusiva que o payload inteiro promete, e ela não pode mentir aqui.
    if failed and not failing_tests:
        limitations.append(
            f"{failed} teste(s) falharam e nenhum nome foi extraído da saída da suíte")
    return limitations


def build_context(payload: dict) -> dict:
    """O payload denso das lacunas, a partir do dict serializado de uma execução.

    Função pura sobre o mesmo formato que `reporting.markdown_report` recebe: ela
    não lê disco, não roda teste e não chama modelo. O que não estiver no payload
    não vira lacuna — é por isso que uma execução sem `--run-tests` sai com
    `uncovered_lines` vazio e `tests_executed` falso: os dois juntos dizem
    "ninguém mediu", que é diferente de "nada ficou descoberto".
    """
    data = payload.get("data") or {}
    configuration = data.get("configuration") or {}
    traceability = configuration.get("traceability") or {}
    error_paths = configuration.get("error_paths") or {}
    execution = configuration.get("test_execution") or {}
    findings = data.get("findings") or []
    failing_tests = _failing_tests(execution)
    return {
        "summary": {
            "verdict": (data.get("verdict") or {}).get("status"),
            "findings": len(findings),
            "tests_executed": bool(configuration.get("run_tests")),
        },
        "uncovered_lines": _uncovered_lines(configuration),
        "uncovered_error_paths": list(error_paths.get("uncovered") or ()),
        "failing_tests": failing_tests,
        "scenarios_without_tests": list(traceability.get("scenarios_without_tests") or ()),
        "missing_equivalence_classes": _missing_equivalence_classes(findings),
        "orphan_markers": list(traceability.get("orphan_markers") or ()),
        "limitations": _limitations(configuration, execution.get("failed") or 0, failing_tests),
    }
