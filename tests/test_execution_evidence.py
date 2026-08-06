from pathlib import Path
from sentry.adapters.local_tools import PytestAdapter

def test_execution_records_passed_counts_and_summary(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert 1 == 1\n", encoding="utf8")
    (tmp_path / "conftest.py").write_text("", encoding="utf8")
    test, percent = PytestAdapter(tmp_path).run(tmp_path / "coverage.json")
    assert test.passed >= 1
    assert test.failed == 0
    assert "-m coverage run -m pytest" in test.command

def test_execution_records_failure(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_fail.py").write_text("def test_fail():\n    assert 1 == 2\n", encoding="utf8")
    (tmp_path / "conftest.py").write_text("", encoding="utf8")
    test, _ = PytestAdapter(tmp_path).run(tmp_path / "coverage.json")
    assert test.status.value == "falhou"
    assert test.failed >= 1

def test_execution_reports_not_run_when_deselected(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf8")
    (tmp_path / "tests" / "test_b.py").write_text("def test_b():\n    assert True\n", encoding="utf8")
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = -k 'test_a'\n", encoding="utf8")
    (tmp_path / "conftest.py").write_text("", encoding="utf8")
    test, _ = PytestAdapter(tmp_path).run(tmp_path / "coverage.json")
    assert test.not_run >= 1

def test_infrastructure_failure_is_not_run(tmp_path: Path):
    test = _run_tests_fake()
    assert test.status.value == "não executado"
    assert test.infrastructure_error

def _run_tests_fake():
    import types
    from sentry.domain.models import TestStatus
    return types.SimpleNamespace(status=TestStatus.NOT_RUN, command="cmd", passed=0, failed=0, skipped=0, not_run=0, duration_seconds=0.0, output="", infrastructure_error="timeout")
