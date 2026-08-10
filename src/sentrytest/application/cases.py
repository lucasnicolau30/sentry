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
) -> tuple[TestCase, ...]:
    associated = {_normalize(item["name"]): item.get("tests", []) for item in traceability.get("scenarios", [])}
    result = []
    for index, case in enumerate(document.cases, start=1):
        related = associated.get(_normalize(case.name), [])
        evidences = [Evidence(source="CASES.md", summary=f"caso declarado: {case.name}")]
        if case.equivalence_class:
            evidences.append(Evidence(source="catálogo", summary=f"classe coberta: {case.equivalence_class}"))
        for path in related:
            evidences.append(Evidence(source="teste", path=path, summary="teste associado por rastreabilidade"))
        result.append(
            TestCase(
                id=f"TC-{index:02d}-{_slug(case.name)}"[:80],
                name=case.name,
                requirement=case.requirement,
                layer=_enum_for(case.layer, LAYERS, Layer, Layer.BACKEND),
                preconditions=(case.given,) if case.given else (),
                input_data=dict(case.input_data or {}),
                action=case.when,
                expected_result=case.then,
                priority=_enum_for(case.priority, PRIORITIES, Priority, Priority.MEDIUM),
                test_type=_enum_for(case.test_type, TEST_TYPES, TestType, TestType.UNIT),
                status=_status(related, tests_ran, suite_failed),
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
