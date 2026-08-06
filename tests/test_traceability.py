from pathlib import Path
from sentry.application.traceability import build_traceability
from sentry.ports.inputs import SpecScenario

def test_traceability_links_scenario_to_test(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_access.py").write_text("# scenario: acesso negado\n", encoding="utf8")
    result = build_traceability((SpecScenario("acesso negado", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["tests"] == ["tests\\test_access.py"]
    assert result["scenarios_without_tests"] == []

def test_traceability_reports_uncovered_scenario(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    result = build_traceability((SpecScenario("pagamento aprovado", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is False
    assert result["scenarios_without_tests"] == ["pagamento aprovado"]

def test_traceability_supports_multiple_tests(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    for name in ("a.py", "b.py"):
        (tmp_path / "tests" / name).write_text("# cenario: login\n", encoding="utf8")
    result = build_traceability((SpecScenario("login", "", "", ""),), tmp_path)
    assert len(result["scenarios"][0]["tests"]) == 2

def test_traceability_distinguishes_missing_requirement_from_missing_test(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_login.py").write_text("# scenario: login\n", encoding="utf8")
    result = build_traceability((SpecScenario("login", "", "", ""),), tmp_path, ("changed-files-context", "login"))
    assert result["scenarios_without_tests"] == []
    assert result["requirements_without_scenarios"] == ["changed-files-context"]

def test_traceability_reports_all_behaviors_without_scenario(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    result = build_traceability((), tmp_path, ("requirement-traceability", "contextual-verdict"))
    assert result["requirements_without_scenarios"] == ["requirement-traceability", "contextual-verdict"]
    assert result["scenarios_without_tests"] == []
