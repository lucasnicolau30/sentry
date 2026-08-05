import json
import pytest
from sentry.domain.models import Evidence, InfrastructureError, Layer, Priority, Run, TestCase as DomainTestCase, TestStatus as DomainTestStatus, TestType as DomainTestType, to_dict, to_json

def test_test_case_serializes_versioned_and_deterministically():
    case=DomainTestCase("TC-1","login",Layer.BACKEND,(),{"user":"ana"},"POST /login","200",Priority.HIGH,DomainTestType.CONTRACT,DomainTestStatus.COVERED)
    first=to_json(case); second=to_json(case)
    assert first == second
    payload=json.loads(first)
    assert payload["contract_version"] == "1.0"
    assert payload["data"]["layer"] == "backend"

def test_evidence_confidence_is_validated():
    with pytest.raises(ValueError): Evidence("coverage", confidence=2)

def test_run_preserves_distinct_infrastructure_errors():
    error=InfrastructureError("pytest", "missing", "pytest não instalado", retryable=True)
    run=Run("run-1","demo",None,None,infrastructure_errors=(error,))
    assert to_dict(run)["data"]["infrastructure_errors"][0]["retryable"] is True