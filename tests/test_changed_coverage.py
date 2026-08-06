import json
from pathlib import Path
from sentry.adapters.local_tools import CoverageAdapter
from sentry.application.coverage_context import calculate_changed_coverage
from sentry.ports.inputs import CoverageData, GitChange

def coverage_file(path: Path, executed=(2,)):
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src/app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": list(executed)}}}), encoding="utf8")

def test_coverage_adapter_reads_json(tmp_path: Path):
    path = tmp_path / "coverage.json"
    coverage_file(path)
    result = CoverageAdapter().read(path)
    assert result.global_percent == 80.0
    assert result.executed_lines["src/app.py"] == (2,)

def test_changed_coverage_is_calculated(tmp_path: Path):
    path = tmp_path / "coverage.json"
    coverage_file(path, (2,))
    coverage = CoverageAdapter().read(path)
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (1, 2)})
    result = calculate_changed_coverage(change, coverage)
    assert result.changed_percent == 50.0

def test_coverage_adapter_normalizes_windows_separators(tmp_path: Path):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src\\app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": [2]}}}), encoding="utf8")
    result = CoverageAdapter().read(path)
    assert result.executed_lines["src/app.py"] == (2,)

def test_changed_coverage_matches_windows_coverage_keys(tmp_path: Path):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src\\app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": [2]}}}), encoding="utf8")
    coverage = CoverageAdapter().read(path)
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (1, 2)})
    result = calculate_changed_coverage(change, coverage)
    assert result.changed_percent == 50.0

def test_missing_coverage_is_explicit(tmp_path: Path):
    result = CoverageAdapter().read(tmp_path / "missing.json")
    assert result.error == "arquivo de cobertura ausente"

def test_invalid_coverage_is_explicit(tmp_path: Path):
    path = tmp_path / "coverage.json"
    path.write_text("invalid", encoding="utf8")
    assert CoverageAdapter().read(path).error.startswith("formato de cobertura invalido")
