from pathlib import Path
from sentry.application.impact import select_impacted_tests

def test_selects_test_importing_changed_module(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("from src.app import run\n", encoding="utf8")
    result = select_impacted_tests(tmp_path, ("src/app.py",), executed=True)
    assert result["impacted"][0]["path"] == "tests\\test_app.py"
    assert result["impacted"][0]["executed"] is True

def test_selects_typescript_test_importing_changed_module(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "app.test.ts").write_text("import { run } from '../src/app';\n", encoding="utf8")
    result = select_impacted_tests(tmp_path, ("src/app.ts",), executed=True)
    assert result["impacted"][0]["path"] == "tests\\app.test.ts"

def test_selects_go_test_importing_changed_module(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "app_test.go").write_text("""package app
import "app/service"
""", encoding="utf8")
    result = select_impacted_tests(tmp_path, ("service/app.go",), executed=True)
    assert result["impacted"][0]["path"] == "tests\\app_test.go"

def test_separates_unrelated_tests(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_other.py").write_text("from src.other import run\n", encoding="utf8")
    result = select_impacted_tests(tmp_path, ("src/app.py",))
    assert result["impacted"] == []
    assert result["unrelated"][0]["path"] == "tests\\test_other.py"

def test_records_limitation_without_supported_changes(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    result = select_impacted_tests(tmp_path, ("README.md",))
    assert result["limitations"] == ["arquivos alterados nao possuem extensao suportada"]
