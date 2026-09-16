import json
import sqlite3
import subprocess
from pathlib import Path
from sentrytest.cli import main
from sentrytest.adapters.terminal import VERDICT_COLOR, VERDICT_SYMBOL, paint

def _insert_run(root: Path, run_id: str, run_tests: bool, passed: int, global_percent: float, verdict: str, coverage_error=None, commit=None, findings=()):
    sentry_dir = root / ".sentry"
    sentry_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract_version": "1.0",
        "data": {
            "id": run_id,
            "project": "demo",
            "commit": commit,
            "timestamp": "2026-08-06T00:00:00+00:00",
            "verdict": {"status": verdict},
            "findings": [{"rule": rule} for rule in findings],
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
    assert "Veredito: ⚠ Aprovado com ressalvas -> ✓ Aprovado" in out

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

def _git(root: Path, *args: str):
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)

def _repositorio(root: Path) -> str:
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "module.py").write_text("um\n", encoding="utf-8")
    _git(root, "add", "module.py")
    _git(root, "commit", "-m", "inicial")
    return _git(root, "rev-parse", "HEAD").stdout.strip()

# cenario: report acusa relatorio de commit diferente do HEAD
def test_report_acusa_relatorio_de_commit_anterior_ao_head(tmp_path: Path, monkeypatch, capsys):
    """A acusacao vem antes do relatorio: quem le a primeira linha precisa saber que
    o que vem abaixo nao descreve o codigo atual. Era isto que faltava quando o CI
    publicava um latest.md de cinco commits atras como se fosse o veredito."""
    monkeypatch.chdir(tmp_path)
    analisado = _repositorio(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado", commit=analisado)
    (tmp_path / "module.py").write_text("um\ndois\n", encoding="utf-8")
    _git(tmp_path, "commit", "-am", "avanca o HEAD")
    atual = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    assert main(["report"]) == 0
    saida = capsys.readouterr().out
    assert "Relatório desatualizado" in saida
    assert analisado[:12] in saida and atual[:12] in saida
    assert saida.index("Relatório desatualizado") < saida.index("# Sentry Report")

def test_report_nao_acusa_quando_o_relatorio_e_do_head_atual(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    atual = _repositorio(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado", commit=atual)
    assert main(["report"]) == 0
    assert "desatualizado" not in capsys.readouterr().out

# cenario: sem repositorio Git o relatorio nao inventa commit
def test_report_fora_de_repositorio_git_nao_acusa_desatualizacao(tmp_path: Path, monkeypatch, capsys):
    """Sem HEAD com que comparar, nao ha desatualizacao a comprovar. A ausencia do
    commit fica declarada no cabecalho, que e' limitacao, nao acusacao."""
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado")
    assert main(["report"]) == 0
    saida = capsys.readouterr().out
    assert "desatualizado" not in saida
    assert "Commit analisado: indisponível" in saida

# cenario: history colore delta de cobertura e de testes pelo sentido
def test_history_colore_delta_de_cobertura_e_de_testes_pelo_sentido(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado")
    _insert_run(tmp_path, "r2", True, passed=12, global_percent=85.0, verdict="aprovado")
    assert main(["history"]) == 0
    saida = capsys.readouterr().out
    assert f"Cobertura global: {paint('+5.0', 'green', enabled=True)}" in saida
    assert f"passed {paint('+2', 'green', enabled=True)}" in saida
    assert "failed 0" in saida  # delta zero nao muda, nao ganha cor

# cenario: history nao colore delta zero ou indisponivel
def test_history_nao_colore_delta_zero_ou_indisponivel(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado")
    _insert_run(tmp_path, "r2", True, passed=10, global_percent=80.0, verdict="aprovado")
    assert main(["history"]) == 0
    saida = capsys.readouterr().out
    assert "Cobertura global: 0" in saida
    assert "\x1b[" not in saida.split("Cobertura global:")[1].split("\n")[0]

# cenario: history colore achados novos resolvidos e persistentes
def test_history_colore_achados_novos_resolvidos_e_persistentes(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado", findings=("regra-a", "regra-b"))
    _insert_run(tmp_path, "r2", True, passed=10, global_percent=80.0, verdict="aprovado", findings=("regra-b", "regra-c"))
    assert main(["history"]) == 0
    saida = capsys.readouterr().out
    assert f"Achados novos: {paint('regra-c', 'red', enabled=True)}" in saida
    assert f"Achados resolvidos: {paint('regra-a', 'green', enabled=True)}" in saida
    assert f"Achados persistentes: {paint('regra-b', 'yellow', enabled=True)}" in saida

# cenario: history colore a transicao de veredito pelos dois status
def test_history_colore_a_transicao_de_veredito_pelos_dois_status(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=10, global_percent=80.0, verdict="aprovado com ressalvas")
    _insert_run(tmp_path, "r2", True, passed=12, global_percent=85.0, verdict="aprovado")
    assert main(["history"]) == 0
    saida = capsys.readouterr().out
    de = paint("⚠", VERDICT_COLOR["aprovado com ressalvas"], enabled=True)
    para = paint("✓", VERDICT_COLOR["aprovado"], enabled=True)
    assert f"Veredito: {de} Aprovado com ressalvas -> {para} Aprovado" in saida

# cenario: clear sem nada a remover ganha o simbolo de aprovado
def test_clear_sem_nada_a_remover_ganha_o_simbolo_de_aprovado(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["clear"]) == 0
    saida = capsys.readouterr().out
    assert f"{VERDICT_SYMBOL['aprovado']} Nada a remover." in saida

# cenario: clear avisa a contagem em amarelo antes de confirmar
def test_clear_avisa_a_contagem_em_amarelo_antes_de_confirmar(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=1, global_percent=80.0, verdict="aprovado")
    _run_files(tmp_path, "r1")
    assert main(["clear"]) == 0
    saida = capsys.readouterr().out
    assert paint("✂", "yellow", enabled=True) + " Execuções a remover: 1" in saida

# cenario: clear aplicado confirma em verde com simbolo de aprovado
def test_clear_aplicado_confirma_em_verde_com_simbolo_de_aprovado(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    _insert_run(tmp_path, "r1", True, passed=1, global_percent=80.0, verdict="aprovado")
    _run_files(tmp_path, "r1")
    assert main(["clear", "--yes"]) == 0
    saida = capsys.readouterr().out
    assert f"{paint(VERDICT_SYMBOL['aprovado'], 'green', enabled=True)} Removidos" in saida
