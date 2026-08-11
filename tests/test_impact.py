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

# cenario: impacto encontra testes no diretorio declarado
def test_impacto_encontra_testes_no_diretorio_declarado(tmp_path: Path):
    """O sintoma relatado: com o teste ao lado do codigo e `[tests] paths`
    declarado, o impacto varria um `tests/` fixo, nao achava nada e reportava
    zero impactado -- enquanto a matriz, que le a declaracao, associava o teste."""
    (tmp_path / "users").mkdir()
    (tmp_path / "users" / "serializers.py").write_text("def validate_telefone():\n    ...\n", encoding="utf-8")
    (tmp_path / "users" / "test_serializers.py").write_text(
        "from users.serializers import validate_telefone\n", encoding="utf-8")
    assert not (tmp_path / "tests").exists()

    resultado = select_impacted_tests(tmp_path, ("users/serializers.py",), test_paths=("users",))
    assert _paths(resultado["impacted"]) == ["users/test_serializers.py"]
    assert resultado["limitations"] == []

# cenario: impacto e matriz enxergam o mesmo conjunto de arquivos
def test_impacto_e_matriz_partem_do_mesmo_conjunto(tmp_path: Path):
    """A contradicao dentro de um unico relatorio -- "nenhum arquivo de teste
    encontrado" ao lado de um teste associado na matriz -- so some se as duas
    leituras varrerem os mesmos diretorios.

    Os conjuntos nao sao identicos, e nem devem ser: a matriz le todo arquivo do
    diretorio atras do marcador `# cenario:`, enquanto o impacto so considera os
    que tem nome de teste. O que precisa valer e' a inclusao -- nenhum arquivo
    que a matriz possa associar pode ficar invisivel para o impacto."""
    from sentrytest.application.traceability import collect_test_files
    from sentrytest.application.impact import _is_test

    (tmp_path / "users").mkdir()
    (tmp_path / "users" / "serializers.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "users" / "test_serializers.py").write_text(
        "# cenario: rejeita telefone invalido\n"
        "from users.serializers import x\n"
        "def test_rejeita_telefone_invalido():\n    assert True\n",
        encoding="utf-8")

    da_matriz = {str(path.relative_to(tmp_path)) for path in collect_test_files(tmp_path, ("users",)) if _is_test(path)}
    resultado = select_impacted_tests(tmp_path, ("users/serializers.py",), test_paths=("users",))
    do_impacto = {item["path"] for item in resultado["impacted"] + resultado["unrelated"]}
    assert da_matriz and do_impacto == da_matriz

# cenario: padrao cobre os quatro diretorios convencionais
def test_padrao_cobre_os_quatro_diretorios_convencionais(tmp_path: Path):
    """Sem declaracao, o impacto so olhava `tests/`, enquanto a matriz ja olhava
    tambem `test/`, `spec/` e `__tests__/`: um projeto com testes em `spec/`
    ficava com impacto zerado sem nenhuma explicacao."""
    (tmp_path / "spec").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "spec" / "test_app.py").write_text("from src.app import x\n", encoding="utf-8")

    resultado = select_impacted_tests(tmp_path, ("src/app.py",))
    assert _paths(resultado["impacted"]) == ["spec/test_app.py"]
    assert resultado["limitations"] == []

# cenario: diretorio declarado inexistente vira limitacao e nao silencio
def test_diretorio_declarado_inexistente_vira_limitacao_nomeada(tmp_path: Path):
    """Zero impactado por engano de configuracao tem que ser distinguivel de zero
    impactado de verdade -- por isso a limitacao nomeia onde se procurou."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")

    resultado = select_impacted_tests(tmp_path, ("src/app.py",), test_paths=("backend/testes",))
    assert resultado["impacted"] == [] and resultado["unrelated"] == []
    assert len(resultado["limitations"]) == 1
    assert "backend/testes" in resultado["limitations"][0]

# cenario: dependencia de terceiros nao entra como teste do projeto
def test_dependencia_de_terceiros_nao_entra_como_teste(tmp_path: Path):
    """O diretorio declarado pode conter dependencias instaladas; contar o teste
    de um pacote de terceiros como teste do projeto inflaria o impacto."""
    (tmp_path / "frontend" / "node_modules" / "lib").mkdir(parents=True)
    (tmp_path / "frontend" / "app.ts").write_text("export const x = 1\n", encoding="utf-8")
    (tmp_path / "frontend" / "app.test.ts").write_text("import { x } from './app'\n", encoding="utf-8")
    (tmp_path / "frontend" / "node_modules" / "lib" / "index.test.ts").write_text(
        "import { x } from './app'\n", encoding="utf-8")

    resultado = select_impacted_tests(tmp_path, ("frontend/app.ts",), test_paths=("frontend",))
    encontrados = _paths(resultado["impacted"] + resultado["unrelated"])
    assert encontrados == ["frontend/app.test.ts"]
