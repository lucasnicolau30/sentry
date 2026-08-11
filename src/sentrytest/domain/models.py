"""Modelos de domínio independentes de integrações externas."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import json

CONTRACT_VERSION = "1.0"

class StrEnum(str, Enum):
    def __str__(self) -> str: return self.value

# v1.0 cobre apenas backend: o produto nao aceita declarar camada que nao sabe
# verificar, para nao produzir caso preso em "nao coberto" para sempre.
class Layer(StrEnum): BACKEND="backend"; INTEGRATION="integração"
class Priority(StrEnum): CRITICAL="crítica"; HIGH="alta"; MEDIUM="média"; LOW="baixa"
class TestType(StrEnum): UNIT="unitário"; INTEGRATION="integração"; CONTRACT="contrato"
class TestStatus(StrEnum): COVERED="coberto"; PARTIAL="parcial"; NOT_COVERED="não coberto"; FAILED="falhou"; NOT_RUN="não executado"
class Severity(StrEnum): CRITICAL="crítica"; HIGH="alta"; MEDIUM="média"; LOW="baixa"
class VerdictStatus(StrEnum): APPROVED="aprovado"; WARNING="aprovado com ressalvas"; REJECTED="reprovado"; INCONCLUSIVE="inconclusivo"
# "nao aplicavel" e distinto de "nao coberta": o primeiro diz que a dimensao nao
# existe neste projeto, o segundo que existe e esta descoberta.
# `não verificada` nao e' um meio-termo entre coberta e nao coberta: e' a recusa a
# afirmar qualquer uma das duas. A dimensao existe nesta mudanca, mas faltou o dado
# que permitiria avalia-la -- dizer "nao aplicavel" ali afirmava que ela nao existia.
class DimensionStatus(StrEnum): COVERED="coberta"; PARTIAL="parcial"; NOT_COVERED="não coberta"; NOT_APPLICABLE="não aplicável"; NOT_MEASURED="não verificada"

@dataclass(frozen=True)
class Evidence:
    source: str
    path: str | None = None
    interval: str | None = None
    summary: str = ""
    confidence: float = 1.0
    def __post_init__(self):
        if not 0 <= self.confidence <= 1: raise ValueError("confidence deve estar entre 0 e 1")

@dataclass(frozen=True)
class TestCase:
    id: str
    requirement: str
    layer: Layer
    preconditions: tuple[str, ...]
    input_data: dict[str, Any]
    action: str
    expected_result: str
    priority: Priority
    test_type: TestType
    status: TestStatus
    related_test: str | None = None
    evidences: tuple[Evidence, ...] = ()
    # Nome legivel do "## Caso:" no CASES.md, preservado com acento. O `id` (TC-XX-slug)
    # normaliza acento para virar caminho de arquivo seguro e nao serve para exibicao.
    name: str = ""

@dataclass(frozen=True)
class Finding:
    rule: str
    severity: Severity
    message: str
    recommendation: str
    evidence: tuple[Evidence, ...] = ()
    location: str | None = None
    impact: str | None = None

@dataclass(frozen=True)
class Verdict:
    status: VerdictStatus
    justification: str
    applied_rules: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class InfrastructureError:
    stage: str
    cause: str
    message: str
    retryable: bool = False

@dataclass(frozen=True)
class Run:
    id: str
    project: str
    commit: str | None
    reference: str | None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    configuration: dict[str, Any] = field(default_factory=dict)
    test_cases: tuple[TestCase, ...] = ()
    findings: tuple[Finding, ...] = ()
    evidences: tuple[Evidence, ...] = ()
    verdict: Verdict | None = None
    infrastructure_errors: tuple[InfrastructureError, ...] = ()

def _plain(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if hasattr(value, '__dataclass_fields__'): return {k: _plain(v) for k,v in asdict(value).items()}
    if isinstance(value, tuple): return [_plain(v) for v in value]
    if isinstance(value, dict): return {k: _plain(v) for k,v in sorted(value.items())}
    return value

def to_dict(value: Any) -> dict[str, Any]: return {"contract_version": CONTRACT_VERSION, "data": _plain(value)}
def to_json(value: Any) -> str: return json.dumps(to_dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))