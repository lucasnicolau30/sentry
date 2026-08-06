from pathlib import Path
import subprocess
from sentry.adapters.local_tools import LocalGitAdapter

def git(root: Path, *args: str):
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)

def test_git_adapter_reads_files_status_and_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf8")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ("module.py",)
    assert change.statuses == {"module.py": "M"}
    assert change.changed_lines["module.py"] == (2,)

def test_git_adapter_reports_repo_without_previous_revision(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ()
    assert change.error is None

def test_git_adapter_reports_missing_repository(tmp_path: Path):
    change = LocalGitAdapter(tmp_path).change()
    assert change.error == "diretorio nao e um repositorio Git"

def test_git_adapter_filters_generated_artifacts(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf8")
    (tmp_path / ".coverage").write_text("data", encoding="utf8")
    (tmp_path / "artifact.pyo").write_text("data", encoding="utf8")
    (tmp_path / ".sentry").mkdir()
    (tmp_path / ".sentry" / "report.md").write_text("data", encoding="utf8")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ("module.py",)
    assert ".coverage" not in change.files
    assert "artifact.pyo" not in change.files
    assert ".sentry/report.md" not in change.files

def test_git_adapter_filters_generated_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf8")
    (tmp_path / ".sentry").mkdir()
    (tmp_path / ".sentry" / "report.md").write_text("a\nb\n", encoding="utf8")
    git(tmp_path, "add", "module.py", ".sentry/report.md")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf8")
    (tmp_path / ".sentry" / "report.md").write_text("a\nb\nc\n", encoding="utf8")
    change = LocalGitAdapter(tmp_path).change()
    assert "module.py" in change.files
    assert "module.py" in change.changed_lines
    assert ".sentry/report.md" not in change.files
    assert ".sentry/report.md" not in change.changed_lines

def test_git_adapter_includes_untracked_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "new_mod.py").write_text("a\nb\nc\n", encoding="utf8")
    change = LocalGitAdapter(tmp_path).change()
    assert "new_mod.py" in change.files
    assert change.changed_lines["new_mod.py"] == (1, 2, 3)

def test_git_adapter_ignores_untracked_docs_in_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "notes.md").write_text("doc\n", encoding="utf8")
    change = LocalGitAdapter(tmp_path).change()
    assert "notes.md" in change.files
    assert "notes.md" not in change.changed_lines


