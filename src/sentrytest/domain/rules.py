from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .models import Evidence, Finding, Severity, TestStatus, Verdict, VerdictStatus

DEFAULT_SEVERITIES={'test-failing':Severity.CRITICAL,'changed-code-uncovered':Severity.HIGH,'requirement-without-scenario':Severity.MEDIUM,'scenario-without-test':Severity.HIGH,'coverage-missing':Severity.MEDIUM,'error-path-without-test':Severity.HIGH,'missing-equivalence-class':Severity.HIGH,'case-spec-invalid':Severity.CRITICAL,'coverage-below-threshold':Severity.HIGH,'global-coverage-below-threshold':Severity.MEDIUM}
# Sem limiar declarado o Sentry nao inventa um numero: so cobra zero de cobertura,
# que e ausencia de teste, nao politica. Quem define "quanto basta" e o projeto.
@dataclass(frozen=True)
class Thresholds:
    changed_coverage: float|None=None
    global_coverage: float|None=None
@dataclass(frozen=True)
class EvaluationContext:
    tests: tuple[Any,...]=()
    changed_files: tuple[str,...]=()
    changed_coverage: float|None=None
    coverage_available: bool=True
    requirements_without_scenarios: tuple[str,...]=()
    scenarios_without_tests: tuple[str,...]=()
    error_paths_without_tests: tuple[str,...]=()
    missing_equivalence_classes: tuple[dict,...]=()
    case_spec_errors: tuple[str,...]=()
    infrastructure_errors: tuple[str,...]=()
    global_coverage: float|None=None
    thresholds: Thresholds=Thresholds()
    # Ha entre os arquivos alterados algum cuja cobertura poderia ser medida?
    # Um diff so de .md/.toml nao tem cobertura a calcular -- isso e' "nao
    # aplicavel", nao "falhou ao calcular". Padrao True preserva o comportamento
    # de quem constroi o contexto sem informar.
    has_measurable_change: bool=True

def evaluate(context:EvaluationContext,severities:dict[str,Severity]|None=None)->tuple[tuple[Finding,...],Verdict]:
    policy={**DEFAULT_SEVERITIES,**(severities or {})}; findings=[]
    def add(rule,message,recommendation,location=None,evidence=None,impact=None):
        findings.append(Finding(rule,policy[rule],message,recommendation,tuple(evidence or ()),location,impact))
    failed=[t for t in context.tests if getattr(t,'status',None)==TestStatus.FAILED]
    if failed: add('test-failing','Há testes falhando na execução.','Corrigir ou atualizar os testes falhos antes de aprovar.',impact='A mudança não possui evidência de comportamento correto.')
    if context.changed_coverage is None and context.changed_files and context.coverage_available and context.has_measurable_change: add('coverage-missing','Não foi possível calcular a cobertura do código alterado.','Gerar e fornecer dados do coverage.py.')
    elif context.changed_coverage == 0: add('changed-code-uncovered','Código alterado sem cobertura.','Adicionar teste para o código alterado.')
    limit=context.thresholds.changed_coverage
    if limit is not None and context.changed_coverage is not None and 0 < context.changed_coverage < limit:
        add('coverage-below-threshold',f'Cobertura do código alterado em {context.changed_coverage:.2f}%, abaixo do mínimo de {limit:.2f}%.',f'Cobrir mais do código alterado até atingir {limit:.2f}%.')
    limit=context.thresholds.global_coverage
    if limit is not None and context.global_coverage is not None and context.global_coverage < limit:
        add('global-coverage-below-threshold',f'Cobertura global em {context.global_coverage:.2f}%, abaixo do mínimo de {limit:.2f}%.',f'Elevar a cobertura global até {limit:.2f}%.')
    for item in context.requirements_without_scenarios: add('requirement-without-scenario',f'Requisito sem cenário: {item}',f'Peça ao agente de IA para gerar o cenário "{item}" na spec com a estrutura: "### Cenário: <nome>" seguido de "- Dado: <pré-condição>", "- Quando: <ação>", "- Então: <resultado esperado>" e, se necessário, "- E: <condição ou resultado complementar>".')
    for item in context.scenarios_without_tests: add('scenario-without-test',f'Cenário sem teste associado: {item}','Adicionar ou associar um teste ao cenário.')
    for item in context.error_paths_without_tests: add('error-path-without-test',f'Caminho de erro sem teste: {item}','Adicionar teste para validação, exceção ou autorização.')
    for item in context.missing_equivalence_classes: add('missing-equivalence-class',f'Classe de equivalência não coberta: {item["field"]}/{item["class"]} (tipo {item["type"]}).',f'Declarar em CASES.md um caso com "- **Classe:** {item["field"]}/{item["class"]}" cobrindo essa entrada.')
    for item in context.case_spec_errors: add('case-spec-invalid',f'CASES.md inválido: {item}','Corrigir a estrutura do CASES.md e rodar `sentry check <slug>` novamente.')
    # Achado crítico é conclusivo por si: teste falhando continua reprovando mesmo
    # com o ambiente degradado. Fora isso, sem evidência confiável não se aprova.
    if any(f.severity==Severity.CRITICAL for f in findings): status=VerdictStatus.REJECTED
    elif context.infrastructure_errors: status=VerdictStatus.INCONCLUSIVE
    elif not findings and (not context.coverage_available or context.changed_coverage is None): status=VerdictStatus.INCONCLUSIVE
    elif any(f.severity==Severity.HIGH for f in findings): status=VerdictStatus.WARNING
    else: status=VerdictStatus.APPROVED
    justification='Veredito calculado pelas regras determinísticas aplicadas.'
    if context.infrastructure_errors and status==VerdictStatus.INCONCLUSIVE:
        justification='Evidência incompleta por erro de infraestrutura: '+'; '.join(context.infrastructure_errors)
    return tuple(findings), Verdict(status,justification,tuple(f.rule for f in findings),{'findings':len(findings),'infrastructure_errors':len(context.infrastructure_errors)})