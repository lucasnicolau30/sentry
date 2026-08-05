from sentry.domain.models import Severity, TestStatus as DomainTestStatus
from sentry.domain.rules import EvaluationContext, evaluate

def test_failing_test_is_critical_and_rejected():
    class T: status=DomainTestStatus.FAILED
    findings, verdict=evaluate(EvaluationContext(tests=(T(),)))
    assert findings[0].rule=='test-failing' and findings[0].severity==Severity.CRITICAL
    assert verdict.status.value=='reprovado'

def test_missing_requirement_and_scenario_create_findings():
    findings,_=evaluate(EvaluationContext(requirements_without_scenarios=('R1',),scenarios_without_tests=('C1',)))
    assert {f.rule for f in findings}=={'requirement-without-scenario','scenario-without-test'}

def test_same_input_is_deterministic():
    context=EvaluationContext(changed_files=('a.py',),changed_coverage=0)
    assert evaluate(context)==evaluate(context)