from sentry.application.reporting import markdown_report

def test_markdown_report_shows_context():
    payload = {"data": {"id": "run-1", "project": "demo", "verdict": {"status": "inconclusivo"}, "findings": [], "configuration": {
        "git_change": {"files": ["src/app.py"]},
        "traceability": {"scenarios_without_tests": ["login"]},
        "impact": {"impacted": [{"path": "tests/test_app.py"}], "unrelated": [], "limitations": ["selecao estatica"]},
        "coverage": {"global_percent": 80.0, "changed_percent": 50.0},
    }}}
    report = markdown_report(payload)
    assert "Arquivos alterados: 1" in report
    assert "Testes impactados: 1" in report
    assert "Cen\u00e1rios sem teste: 1" in report
    assert "Cobertura alterada: 50,00%" in report
    assert "selecao estatica" in report

def test_markdown_report_lists_changed_files():
    payload = {"data": {"id": "run-2", "project": "demo", "verdict": {"status": "aprovado"}, "findings": [], "configuration": {
        "git_change": {"files": ["src/app.py"], "changed_lines": {"src/app.py": [2, 3]}},
    }}}
    report = markdown_report(payload)
    assert "- src/app.py" in report

def test_markdown_report_shows_execution_evidence():
    payload = {"data": {"id": "run-3", "project": "demo", "verdict": {"status": "reprovado"}, "findings": [], "configuration": {
        "test_execution": {"command": "python -m pytest", "passed": 10, "failed": 1, "skipped": 2, "not_run": 3, "duration_seconds": 1.5, "output": "1 failed"},
    }}}
    report = markdown_report(payload)
    assert "Comando: `python -m pytest`" in report
    assert "10 passados, 1 falhos, 2 ignorados, 3 nao executados" in report
    assert "1 failed" in report
