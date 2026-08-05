from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .models import Evidence, Finding, Severity, TestStatus, Verdict, VerdictStatus

DEFAULT_SEVERITIES={'test-failing':Severity.CRITICAL,'changed-code-uncovered':Severity.HIGH,'requirement-without-scenario':Severity.HIGH,'scenario-without-test':Severity.HIGH,'coverage-missing':Severity.MEDIUM,'error-path-without-test':Severity.HIGH,'frontend-error-state-missing':Severity.MEDIUM,'contract-inconsistent':Severity.CRITICAL}
@dataclass(frozen=True)
class EvaluationContext:
    tests: tuple[Any,...]=()
    changed_files: tuple[str,...]=()
    changed_coverage: float|None=None
    coverage_available: bool=True
    requirements_without_scenarios: tuple[str,...]=()
    scenarios_without_tests: tuple[str,...]=()
    error_paths_without_tests: tuple[str,...]=()
    frontend_error_states_missing: tuple[str,...]=()
    inconsistent_contracts: tuple[str,...]=()

def evaluate(context:EvaluationContext,severities:dict[str,Severity]|None=None)->tuple[tuple[Finding,...],Verdict]:
    policy={**DEFAULT_SEVERITIES,**(severities or {})}; findings=[]
    def add(rule,message,recommendation,location=None,evidence=None,impact=None):
        findings.append(Finding(rule,policy[rule],message,recommendation,tuple(evidence or ()),location,impact))
    failed=[t for t in context.tests if getattr(t,'status',None)==TestStatus.FAILED]
    if failed: add('test-failing','Há testes falhando na execução.','Corrigir ou atualizar os testes falhos antes de aprovar.',impact='A mudança não possui evidência de comportamento correto.')
    if context.changed_coverage is None and context.changed_files and context.coverage_available: add('coverage-missing','Não foi possível calcular a cobertura do código alterado.','Gerar e fornecer dados do coverage.py.')
    elif context.changed_coverage == 0: add('changed-code-uncovered','Código alterado sem cobertura.','Adicionar teste para o código alterado.')
    for item in context.requirements_without_scenarios: add('requirement-without-scenario',f'Requisito sem cenário: {item}','Descrever um cenário verificável para o requisito.')
    for item in context.scenarios_without_tests: add('scenario-without-test',f'Cenário sem teste associado: {item}','Adicionar ou associar um teste ao cenário.')
    for item in context.error_paths_without_tests: add('error-path-without-test',f'Caminho de erro sem teste: {item}','Adicionar teste para validação, exceção ou autorização.')
    for item in context.frontend_error_states_missing: add('frontend-error-state-missing',f'Estado de erro frontend não definido: {item}','Definir e testar o estado de erro da interface.')
    for item in context.inconsistent_contracts: add('contract-inconsistent',f'Contrato inconsistente: {item}','Alinhar contrato entre frontend e backend.')
    if not findings and (not context.coverage_available or context.changed_coverage is None): status=VerdictStatus.INCONCLUSIVE
    elif any(f.severity==Severity.CRITICAL for f in findings): status=VerdictStatus.REJECTED
    elif any(f.severity==Severity.HIGH for f in findings): status=VerdictStatus.REJECTED
    elif findings: status=VerdictStatus.WARNING
    else: status=VerdictStatus.APPROVED
    return tuple(findings), Verdict(status,'Veredito calculado pelas regras determinísticas aplicadas.',tuple(f.rule for f in findings),{'findings':len(findings)})