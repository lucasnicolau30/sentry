import json
import sqlite3
from pathlib import Path
from sentrytest.cli import main

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

def _run_files(root: Path, run_id: str) -> list[Path]:
    """Os quatro arquivos que uma execucao deixa no disco."""
    paths = [root / ".sentry" / "runs" / f"{run_id}.json",
             root / ".sentry" / "runs" / f"{run_id}-coverage.json",
             root / ".sentry" / "reports" / f"{run_id}.md",
             root / ".sentry" / "reports" / f"{run_id}.json"]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
    return paths

# cenario: clear sem confirmacao apenas mostra o que sairia
def test_clear_sem_confirmacao_nao_remove_nada(tmp_path: Path, monkeypatch, capsys):
    """Apagar historico e' irreversivel: o padrao precisa mostrar o escopo
    antes de destruir, senao um comando digitado por engano perde evidencia."""
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=1, global_percent=80.0, verdict="aprovado")
    arquivos = _run_files(tmp_path, "r1")
    assert main(["clear"]) == 0
    saida = capsys.readouterr().out
    assert "Repita com `--yes`" in saida
    assert all(path.exists() for path in arquivos)

# cenario: clear com confirmacao remove execucoes e preserva as specs
def test_clear_com_confirmacao_remove_execucoes_e_preserva_specs(tmp_path: Path, monkeypatch, capsys):
    """Spec e' intencao declarada pelo usuario, nao evidencia gerada: podar
    historico nunca pode apagar o trabalho de quem escreveu os casos."""
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=1, global_percent=80.0, verdict="aprovado")
    arquivos = _run_files(tmp_path, "r1")
    spec = tmp_path / ".sentry" / "specs" / "demo" / "CASES.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# Demo\n", encoding="utf-8")

    assert main(["clear", "--yes"]) == 0
    assert not any(path.exists() for path in arquivos)
    assert spec.exists()
    with sqlite3.connect(tmp_path / ".sentry" / "sentry.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0

# cenario: keep-last preserva as execucoes mais recentes
def test_clear_keep_last_preserva_as_mais_recentes(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for name in ("r1", "r2", "r3"):
        _insert_run(tmp_path, name, True, passed=1, global_percent=80.0, verdict="aprovado")
        _run_files(tmp_path, name)
    latest = tmp_path / ".sentry" / "reports" / "latest.md"
    latest.write_text("relatorio", encoding="utf-8")

    assert main(["clear", "--keep-last", "2", "--yes"]) == 0
    assert not (tmp_path / ".sentry" / "runs" / "r1.json").exists()
    assert (tmp_path / ".sentry" / "runs" / "r2.json").exists()
    assert (tmp_path / ".sentry" / "runs" / "r3.json").exists()
    # latest.md aponta para a execucao mais recente, que foi mantida.
    assert latest.exists()

# cenario: clear sem historico nao inventa trabalho
def test_clear_sem_historico_nao_faz_nada(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["clear", "--yes"]) == 0
    assert "Nada a remover" in capsys.readouterr().out

def test_history_marks_incomparable_runs(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", False, passed=0, global_percent=None, verdict="inconclusivo")
    _insert_run(tmp_path, "r2", True, passed=12, global_percent=85.0, verdict="aprovado")
    assert main(["history"]) == 0
    out = capsys.readouterr().out
    assert "Execuções incomparáveis" in out
    assert "execução de testes" in out
