from pathlib import Path
from sentrytest.application.impact import select_impacted_tests

def _paths(items) -> list[str]:
    """Caminhos com separador normalizado: o adapter devolve o separador do SO,
    e fixar `\\` nas assercoes prenderia a suite ao Windows."""
    return [item["path"].replace("\\", "/") for item in items]

def test_selects_test_importing_changed_module(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("from src.app import run\n", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("src/app.py",), executed=True)
    assert _paths(result["impacted"]) == ["tests/test_app.py"]
    assert result["impacted"][0]["executed"] is True

def test_selects_typescript_test_importing_changed_module(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "app.test.ts").write_text("import { run } from '../src/app';\n", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("src/app.ts",), executed=True)
    assert _paths(result["impacted"]) == ["tests/app.test.ts"]

def test_selects_go_test_importing_changed_module(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "app_test.go").write_text("""package app
import "app/service"
""", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("service/app.go",), executed=True)
    assert _paths(result["impacted"]) == ["tests/app_test.go"]

def test_separates_unrelated_tests(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_other.py").write_text("from src.other import run\n", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("src/app.py",))
    assert result["impacted"] == []
    assert _paths(result["unrelated"]) == ["tests/test_other.py"]

def test_records_limitation_without_supported_changes(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    result = select_impacted_tests(tmp_path, ("README.md",))
    assert result["limitations"] == ["arquivos alterados nao possuem extensao suportada"]

def test_does_not_flag_unrelated_module_sharing_package_root(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_billing.py").write_text("from src.billing import charge\n", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("src/app.py",))
    assert result["impacted"] == []
    assert _paths(result["unrelated"]) == ["tests/test_billing.py"]

def test_layout_src_casa_com_import_sem_o_prefixo(tmp_path: Path):
    """`src/pkg/mod.py` e importado como `pkg.mod`: o prefixo src/ nao existe no import."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_rules.py").write_text(
        "from sentry.domain.rules import evaluate\n", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("src/sentry/domain/rules.py",))
    assert [item["path"].replace("\\", "/") for item in result["impacted"]] == ["tests/test_rules.py"]

# cenario: teste com erro de sintaxe vira limitacao, nao quebra a analise
def test_teste_com_erro_de_sintaxe_vira_limitacao(tmp_path: Path):
    """Um arquivo de teste com sintaxe invalida nao pode derrubar a analise dos
    demais: SyntaxError ao parsear os imports precisa virar limitacao registrada."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_quebrado.py").write_text("def test_algo(:\n    pass\n", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("src/app.py",))
    assert result["impacted"] == []
    assert any("test_quebrado.py" in item for item in result["limitations"])

def test_layout_src_nao_cria_falso_positivo(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_outro.py").write_text(
        "from sentrytest.domain.catalog import merge_catalog\n", encoding="utf-8")
    result = select_impacted_tests(tmp_path, ("src/sentry/domain/rules.py",))
    assert result["impacted"] == []
    assert [item["path"].replace("\\", "/") for item in result["unrelated"]] == ["tests/test_outro.py"]
