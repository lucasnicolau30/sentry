"""Leitura e validação da matriz de casos declarada em CASES.md.

O agente de IA escreve o arquivo seguindo TEMPLATE; o Sentry apenas parseia e
valida a estrutura. Nenhuma inferência é feita sobre o conteúdo em texto livre.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

TEMPLATE = """# <Título da funcionalidade>

## Prompt

<o pedido original em texto livre, preservado literalmente>

## Campos

- **<nome do campo>**: <tipo> — <regra declarada>

## Caso: <nome curto e único>

- **Requisito:** <o que do prompt este caso verifica>
- **Camada:** backend | integração
- **Tipo:** unitário | integração | contrato
- **Prioridade:** crítica | alta | média | baixa
- **Classe:** <campo>/<classe de equivalência>
- **Dado:** <pré-condição>
- **Quando:** <ação>
- **Então:** <resultado esperado>
- **Entrada:** `campo = valor`

## Classes não aplicáveis

- **<campo>/<classe>**: <motivo pelo qual esta classe do catálogo não se aplica aqui>
"""

LAYERS = ("backend", "integração")
TEST_TYPES = ("unitário", "integração", "contrato")
PRIORITIES = ("crítica", "alta", "média", "baixa")

_TITLE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_SECTION = re.compile(r"^##\s+(.+?)\s*\n([\s\S]*?)(?=\n##\s|\Z)", re.MULTILINE)
_FIELD = re.compile(r"^-\s+\*\*(.+?)\*\*:\s*(\S+)\s*(?:[—-]\s*(.*))?$", re.MULTILINE)
_NOT_APPLICABLE = re.compile(r"^-\s+\*\*(.+?)/(.+?)\*\*:\s*(.*?)\s*$", re.MULTILINE)
_BULLET = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$", re.MULTILINE)
_INPUT_PAIR = re.compile(r"([A-Za-z_][\w.]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^,]+)")

_REQUIRED_BULLETS = ("requisito", "camada", "tipo", "prioridade", "dado", "quando", "entao")


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str
    rule: str = ""


@dataclass(frozen=True)
class CaseSpec:
    name: str
    requirement: str
    layer: str
    test_type: str
    priority: str
    given: str
    when: str
    then: str
    equivalence_class: str | None = None
    input_data: dict[str, str] = None

    def __post_init__(self):
        if self.input_data is None:
            object.__setattr__(self, "input_data", {})


@dataclass(frozen=True)
class NotApplicableClass:
    field: str
    class_name: str
    reason: str


@dataclass(frozen=True)
class CaseDocument:
    title: str
    prompt: str
    fields: tuple[FieldSpec, ...] = ()
    cases: tuple[CaseSpec, ...] = ()
    not_applicable: tuple[NotApplicableClass, ...] = ()


def _normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in stripped if not unicodedata.combining(char))


def _match_enum(value: str, allowed: tuple[str, ...]) -> str | None:
    normalized = _normalize(value)
    for candidate in allowed:
        if _normalize(candidate) == normalized:
            return candidate
    return None


def _parse_input_data(raw: str) -> dict[str, str]:
    content = raw.strip().strip("`").strip()
    if not content:
        return {}
    result: dict[str, str] = {}
    for name, value in _INPUT_PAIR.findall(content):
        cleaned = value.strip()
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'":
            cleaned = cleaned[1:-1]
        result[name] = cleaned
    return result


def _parse_fields(body: str) -> tuple[FieldSpec, ...]:
    fields = []
    for name, type_name, rule in _FIELD.findall(body):
        name = name.strip()
        if not name or name.startswith("<"):
            continue
        fields.append(FieldSpec(name, type_name.strip(), (rule or "").strip()))
    return tuple(fields)


def _parse_not_applicable(body: str) -> tuple[NotApplicableClass, ...]:
    items = []
    for field_name, class_name, reason in _NOT_APPLICABLE.findall(body):
        field_name, class_name, reason = field_name.strip(), class_name.strip(), reason.strip()
        if not field_name or field_name.startswith("<"):
            continue
        items.append(NotApplicableClass(field_name, class_name, reason))
    return tuple(items)


def _parse_case(name: str, body: str) -> CaseSpec:
    bullets = {_normalize(key): value.strip() for key, value in _BULLET.findall(body)}
    return CaseSpec(
        name=name,
        requirement=bullets.get("requisito", ""),
        layer=bullets.get("camada", ""),
        test_type=bullets.get("tipo", ""),
        priority=bullets.get("prioridade", ""),
        given=bullets.get("dado", ""),
        when=bullets.get("quando", ""),
        then=bullets.get("entao", ""),
        equivalence_class=bullets.get("classe") or None,
        input_data=_parse_input_data(bullets.get("entrada", "")),
    )


def parse_cases(text: str) -> CaseDocument:
    title_match = _TITLE.search(text)
    title = title_match.group(1).strip() if title_match else ""
    prompt = ""
    fields: tuple[FieldSpec, ...] = ()
    not_applicable: tuple[NotApplicableClass, ...] = ()
    cases = []
    for heading, body in _SECTION.findall(text):
        heading = heading.strip()
        normalized = _normalize(heading)
        if normalized == "prompt":
            prompt = body.strip()
        elif normalized == "campos":
            fields = _parse_fields(body)
        elif normalized == "classes nao aplicaveis":
            not_applicable = _parse_not_applicable(body)
        elif normalized.startswith("caso:"):
            name = heading.split(":", 1)[1].strip()
            if name and not name.startswith("<"):
                cases.append(_parse_case(name, body))
    return CaseDocument(title=title, prompt=prompt, fields=fields, cases=tuple(cases), not_applicable=not_applicable)


def validate_document(document: CaseDocument) -> list[str]:
    """Erros estruturais do CASES.md. Lista vazia significa documento válido."""
    errors: list[str] = []
    if not document.title or document.title.startswith("<"):
        errors.append("título ausente: a primeira linha deve ser '# <Título da funcionalidade>'")
    if not document.prompt or document.prompt.startswith("<"):
        errors.append("seção '## Prompt' ausente ou não preenchida")
    if not document.cases:
        errors.append("nenhum caso declarado: use '## Caso: <nome>' para cada caso de teste")

    seen: set[str] = set()
    declared_fields = {field.name for field in document.fields}
    for case in document.cases:
        key = _normalize(case.name)
        if key in seen:
            errors.append(f"caso duplicado: '{case.name}'")
        seen.add(key)

        bullets = {
            "requisito": case.requirement, "camada": case.layer, "tipo": case.test_type,
            "prioridade": case.priority, "dado": case.given, "quando": case.when, "entao": case.then,
        }
        for bullet in _REQUIRED_BULLETS:
            if not bullets[bullet]:
                errors.append(f"caso '{case.name}': campo obrigatório ausente '{bullet}'")

        if case.layer and not _match_enum(case.layer, LAYERS):
            errors.append(f"caso '{case.name}': camada inválida '{case.layer}' (use: {', '.join(LAYERS)})")
        if case.test_type and not _match_enum(case.test_type, TEST_TYPES):
            errors.append(f"caso '{case.name}': tipo inválido '{case.test_type}' (use: {', '.join(TEST_TYPES)})")
        if case.priority and not _match_enum(case.priority, PRIORITIES):
            errors.append(f"caso '{case.name}': prioridade inválida '{case.priority}' (use: {', '.join(PRIORITIES)})")

        if case.equivalence_class and "/" in case.equivalence_class:
            field_name = case.equivalence_class.split("/", 1)[0].strip()
            if declared_fields and field_name not in declared_fields:
                errors.append(
                    f"caso '{case.name}': classe referencia o campo '{field_name}', que não está declarado em '## Campos'"
                )

    for item in document.not_applicable:
        if not item.reason:
            errors.append(f"classe não aplicável '{item.field}/{item.class_name}': falta o motivo")
        if declared_fields and item.field not in declared_fields:
            errors.append(
                f"classe não aplicável referencia o campo '{item.field}', que não está declarado em '## Campos'"
            )
    return errors


class CaseSpecAdapter:
    """Implementa a porta SpecReader lendo a matriz declarada em CASES.md."""

    def __init__(self, path: Path):
        self.path = path

    def document(self) -> CaseDocument:
        return parse_cases(self.path.read_text(encoding="utf-8"))

    def scenarios(self):
        from ..ports.inputs import SpecScenario
        return tuple(
            SpecScenario(case.name, case.given, case.when, case.then)
            for case in self.document().cases
        )
