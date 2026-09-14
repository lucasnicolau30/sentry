"""Converte a matriz declarada em CASES.md nos TestCase do domínio.

O agente declara intenção (requisito, camada, tipo, prioridade, entrada); o
Sentry mede a realidade (status, teste associado, evidências). A separação é o
que impede a IA de aprovar o próprio trabalho.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from ..adapters.case_specs import LAYERS, PRIORITIES, TEMPLATE, TEST_TYPES, CaseDocument
from ..domain.models import Evidence, Layer, Priority, TestCase, TestStatus, TestType

_SLUG = re.compile(r"[^a-z0-9]+")


def _normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in stripped if not unicodedata.combining(char))


def _slug(text: str) -> str:
    return _SLUG.sub("-", _normalize(text)).strip("-")


def slugify(name: str) -> str:
    return _slug(name) or "spec"


def scaffold(root: Path, name: str, prompt: str = "", specs_path: str = ".sentry/specs") -> tuple[Path, list[str]]:
    """Cria .sentry/specs/<slug>/ com PROMPT.md e CASES.md. Idempotente: nunca sobrescreve."""
    slug = slugify(name)
    directory = root / specs_path / slug
    directory.mkdir(parents=True, exist_ok=True)
    created = []
    prompt_file = directory / "PROMPT.md"
    if not prompt_file.exists():
        body = prompt.strip() or "<descreva aqui, em texto livre, o que precisa ser testado>"
        prompt_file.write_text(f"# {name}\n\n{body}\n", encoding="utf-8")
        created.append(str(prompt_file.relative_to(root)))
    cases_file = directory / "CASES.md"
    if not cases_file.exists():
        cases_file.write_text(TEMPLATE, encoding="utf-8")
        created.append(str(cases_file.relative_to(root)))
    return directory, created


def _enum_for(value: str, allowed: tuple[str, ...], enum_class, default):
    normalized = _normalize(value)
    for candidate in allowed:
        if _normalize(candidate) == normalized:
            return enum_class(candidate)
    return default


def _status(related: list[str], tests_ran: bool, suite_failed: bool) -> TestStatus:
    if not related:
        return TestStatus.NOT_COVERED
    if not tests_ran:
        return TestStatus.NOT_RUN
    # A granularidade atual de execução é por arquivo, não por teste: com a suíte
    # falhando não é possível atribuir a falha a este caso sem ambiguidade.
    return TestStatus.PARTIAL if suite_failed else TestStatus.COVERED


def build_test_cases(
    document: CaseDocument,
    traceability: dict,
    tests_ran: bool = False,
    suite_failed: bool = False,
    e2e_failed: bool = False,
    e2e_evidence: dict[str, tuple[str, ...]] | None = None,
) -> tuple[TestCase, ...]:
    associated = {_normalize(item["name"]): item.get("tests", []) for item in traceability.get("scenarios", [])}
    e2e_evidence = e2e_evidence or {}
    result = []
    for index, case in enumerate(document.cases, start=1):
        related = associated.get(_normalize(case.name), [])
        layer = _enum_for(case.layer, LAYERS, Layer, Layer.BACKEND)
        test_type = _enum_for(case.test_type, TEST_TYPES, TestType, TestType.UNIT)
        evidences = [Evidence(source="CASES.md", summary=f"caso declarado: {case.name}")]
        if case.equivalence_class:
            evidences.append(Evidence(source="catálogo", summary=f"classe coberta: {case.equivalence_class}"))
        for path in related:
            evidences.append(Evidence(source="teste", path=path, summary="teste associado por rastreabilidade"))
        # Camada frontend nao tem cobertura de linha: a prova e' o trace/screenshot
        # da execucao real, nunca um percentual que o produto nao mede ali.
        for path in e2e_evidence.get(_normalize(case.name), ()):
            evidences.append(Evidence(source="playwright", path=path,
                                      summary="evidência de execução e2e (trace/screenshot), não cobertura de linha"))
        # A execucao e' por suite (backend, e2e), nao por caso: falha na suite e2e
        # nao pode marcar como parcial um caso de backend que passou, e vice-versa.
        suite_failed_for_case = e2e_failed if (layer == Layer.FRONTEND or test_type == TestType.E2E) else suite_failed
        result.append(
            TestCase(
                id=f"TC-{index:02d}-{_slug(case.name)}"[:80],
                name=case.name,
                requirement=case.requirement,
                layer=layer,
                preconditions=(case.given,) if case.given else (),
                input_data=dict(case.input_data or {}),
                action=case.when,
                expected_result=case.then,
                priority=_enum_for(case.priority, PRIORITIES, Priority, Priority.MEDIUM),
                test_type=test_type,
                status=_status(related, tests_ran, suite_failed_for_case),
                related_test=related[0] if related else None,
                evidences=tuple(evidences),
            )
        )
    return tuple(result)


def summarize(test_cases: tuple[TestCase, ...]) -> dict:
    """Contagem por camada e por status, para o relatório."""
    by_layer: dict[str, list[str]] = {}
    by_status: dict[str, int] = {}
    for case in test_cases:
        by_layer.setdefault(case.layer.value, []).append(case.id)
        by_status[case.status.value] = by_status.get(case.status.value, 0) + 1
    return {
        "total": len(test_cases),
        "by_layer": {layer: len(ids) for layer, ids in sorted(by_layer.items())},
        "by_status": dict(sorted(by_status.items())),
        "uncovered": [case.id for case in test_cases if case.status == TestStatus.NOT_COVERED],
    }
