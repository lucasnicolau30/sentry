import json
import sqlite3
from pathlib import Path
from sentry.cli import main

def _insert_run(root: Path, run_id: str, run_tests: bool, passed: int, global_percent: float, verdict: str, coverage_error=None):
    sentry_dir = root / ".sentry"
    sentry_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract_version": "1.0",
        "data": {
            "id": run_id,
            "project": "demo",
            "timestamp": "2026-08-06T00:00:00+00:00",
            "verdict": {"status": verdict},
            "findings": [],
            "configuration": {
                "run_tests": run_tests,
                "coverage": {"global_percent": global_percent, "changed_percent": global_percent, "error": coverage_error},
                "test_execution": {"passed": passed, "failed": 0, "skipped": 0, "not_run": 0},
            },
        },
    }
    with sqlite3.connect(sentry_dir / "sentry.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.execute("INSERT INTO runs VALUES (?,?)", (run_id, json.dumps(payload)))

def test_history_with_no_runs_reports_initial_analysis(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["history"]) == 0
    out = capsys.readouterr().out
    assert "Análise inicial" in out

def test_history_with_one_run_reports_initial_analysis(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado")
    assert main(["history"]) == 0
    out = capsys.readouterr().out
    assert "r1" in out
    assert "Análise inicial" in out

def test_history_compares_two_comparable_runs(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado com ressalvas")
    _insert_run(tmp_path, "r2", True, passed=12, global_percent=85.0, verdict="aprovado")
    assert main(["history"]) == 0
    out = capsys.readouterr().out
    assert "Cobertura global: +5.0" in out
    assert "passed +2" in out
    assert "Veredito: aprovado com ressalvas -> aprovado" in out

def test_history_marks_incomparable_runs(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", False, passed=0, global_percent=None, verdict="inconclusivo")
    _insert_run(tmp_path, "r2", True, passed=12, global_percent=85.0, verdict="aprovado")
    assert main(["history"]) == 0
    out = capsys.readouterr().out
    assert "Execuções incomparáveis" in out
    assert "execução de testes" in out
