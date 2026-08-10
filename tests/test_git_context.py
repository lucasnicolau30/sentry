from pathlib import Path
import subprocess
from sentrytest.adapters.local_tools import LocalGitAdapter

def git(root: Path, *args: str):
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)

def test_git_adapter_reads_files_status_and_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ("module.py",)
    assert change.statuses == {"module.py": "M"}
    assert change.changed_lines["module.py"] == (2,)

def test_git_adapter_reports_repo_without_previous_revision(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ()
    assert change.error is None

# cenario: arquivos gerados pelo proprio Sentry ficam fora do diff
def test_git_adapter_filters_sentry_own_generated_files(tmp_path: Path):
    """Sem isto, a primeira analise de todo projeto novo mede os arquivos que o
    `init` acabou de criar. sentry.toml e .gitignore ficam de fora do filtro de
    proposito: o Sentry os cria, mas quem os edita depois e' o usuario."""
    from sentrytest.adapters.local_tools import is_generated_artifact
    assert is_generated_artifact("AGENT-SENTRY.md")
    assert is_generated_artifact(".claude/skills/sentry-cases/SKILL.md")
    assert is_generated_artifact(".claude\\skills\\sentry-cases\\SKILL.md")
    assert not is_generated_artifact("sentry.toml")
    assert not is_generated_artifact(".gitignore")
    # Skill de outra ferramenta nao pertence ao Sentry e nao pode ser escondida.
    assert not is_generated_artifact(".claude/skills/minha-skill/SKILL.md")

def test_git_adapter_reports_missing_repository(tmp_path: Path):
    change = LocalGitAdapter(tmp_path).change()
    assert change.error == "diretorio nao e um repositorio Git"

# cenario: arquivo novo ilegivel nao derruba a leitura do diff
def test_git_adapter_skips_unreadable_new_file_when_counting_lines(tmp_path: Path):
    """Um .py novo com bytes invalidos de UTF-8 nao pode quebrar o change():
    so esse arquivo fica sem changed_lines, o resto do diff continua."""
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "ok.py").write_text("um = 1\n", encoding="utf-8")
    (tmp_path / "invalido.py").write_bytes(b"\xff\xfe\x00bytes invalidos")
    change = LocalGitAdapter(tmp_path).change()
    assert change.error is None
    assert "ok.py" in change.changed_lines
    assert "invalido.py" not in change.changed_lines

def test_git_adapter_filters_generated_artifacts(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf-8")
    (tmp_path / ".coverage").write_text("data", encoding="utf-8")
    (tmp_path / "artifact.pyo").write_text("data", encoding="utf-8")
    (tmp_path / ".sentry").mkdir()
    (tmp_path / ".sentry" / "report.md").write_text("data", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ("module.py",)
    assert ".coverage" not in change.files
    assert "artifact.pyo" not in change.files
    assert ".sentry/report.md" not in change.files

def test_git_adapter_filters_generated_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    (tmp_path / ".sentry").mkdir()
    (tmp_path / ".sentry" / "report.md").write_text("a\nb\n", encoding="utf-8")
    git(tmp_path, "add", "module.py", ".sentry/report.md")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf-8")
    (tmp_path / ".sentry" / "report.md").write_text("a\nb\nc\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert "module.py" in change.files
    assert "module.py" in change.changed_lines
    assert ".sentry/report.md" not in change.files
    assert ".sentry/report.md" not in change.changed_lines

def test_git_adapter_includes_untracked_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "new_mod.py").write_text("a\nb\nc\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert "new_mod.py" in change.files
    assert change.changed_lines["new_mod.py"] == (1, 2, 3)

def test_git_adapter_ignores_untracked_docs_in_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "notes.md").write_text("doc\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert "notes.md" in change.files
    assert "notes.md" not in change.changed_lines



def test_subdiretorio_reporta_caminhos_relativos_a_ele(tmp_path: Path):
    """Rodar o Sentry num subdiretorio (monorepo) deve produzir caminhos que resolvem."""
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "raiz.py").write_text("x = 1\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "dentro.py").write_text("y = 1\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "raiz.py").write_text("x = 2\n", encoding="utf-8")
    (sub / "dentro.py").write_text("y = 2\n", encoding="utf-8")

    change = LocalGitAdapter(sub).change()
    assert change.files == ("dentro.py",)
    assert all((sub / name).exists() for name in change.files)
