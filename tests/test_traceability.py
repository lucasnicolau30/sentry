from pathlib import Path
import pytest
from sentrytest.application.traceability import build_traceability
from sentrytest.ports.inputs import SpecScenario

# Como cada stack declara o mesmo comportamento: "rejeita slug que escapa".
POR_LINGUAGEM = {
    "app.test.ts": 'it("rejeita slug que escapa", async () => { expect(1).toBe(1); });',
    "app_test.go": 'func TestRejeitaSlugQueEscapa(t *testing.T) {}',
    "AppTest.java": '@Test\n    public void rejeitaSlugQueEscapa() { }',
    "AppTest.kt": '@Test\n    fun `rejeita slug que escapa`() { }',
    "AppTests.cs": '[Fact]\n    public void RejeitaSlugQueEscapa() { }',
    "app_spec.rb": 'it "rejeita slug que escapa" do\nend',
    "AppTest.php": 'public function testRejeitaSlugQueEscapa() { }',
    "app_test.rs": '#[test]\n    fn rejeita_slug_que_escapa() { }',
}

# cenario: rastreabilidade reconhece teste de qualquer stack
@pytest.mark.parametrize("filename", sorted(POR_LINGUAGEM))
def test_traceability_matches_test_definitions_in_every_stack(tmp_path: Path, filename: str):
    """Sem isto o parser so abria .py: um projeto Node, Go ou Java teria todo
    caso preso em `nao coberto`, mesmo com o teste existindo."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / filename).write_text(POR_LINGUAGEM[filename], encoding="utf-8")
    result = build_traceability((SpecScenario("rejeita slug que escapa", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is True, f"{filename} nao casou"
    assert [Path(item).name for item in result["scenarios"][0]["tests"]] == [filename]

# cenario: marcador declarado funciona com comentario de qualquer linguagem
def test_traceability_marker_works_with_non_python_comment(tmp_path: Path):
    """O marcador nao ancora no `#`: `// cenario:` vale o mesmo, e e' o vinculo
    confiavel para stacks onde a semelhanca de nome falharia."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "app.test.ts").write_text(
        '// cenario: comportamento com nome totalmente diferente\n'
        'it("something entirely unrelated in english", () => {});\n', encoding="utf-8")
    result = build_traceability(
        (SpecScenario("comportamento com nome totalmente diferente", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is True

# cenario: diretorio de teste declarado substitui os padroes
def test_traceability_honours_declared_test_paths(tmp_path: Path):
    """Projeto com teste ao lado do codigo (src/foo.test.ts) nao tem pasta
    `tests/`: sem declarar onde procurar, nada seria encontrado."""
    colocado = tmp_path / "src" / "feature"
    colocado.mkdir(parents=True)
    (colocado / "slug.test.ts").write_text('it("rejeita slug que escapa", () => {});', encoding="utf-8")
    cenario = (SpecScenario("rejeita slug que escapa", "", "", ""),)
    assert build_traceability(cenario, tmp_path)["scenarios"][0]["covered"] is False
    assert build_traceability(cenario, tmp_path, test_paths=("src",))["scenarios"][0]["covered"] is True

# cenario: arquivo de teste ilegivel nao derruba a rastreabilidade
def test_traceability_skips_unreadable_test_file(tmp_path: Path):
    """Varremos muito mais extensoes agora; um arquivo com bytes invalidos no
    meio do diretorio de testes nao pode impedir o vinculo dos demais."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "quebrado.ts").write_bytes(b"\xff\xfe\x00 it(")
    (tmp_path / "tests" / "app.test.ts").write_text(
        'it("rejeita slug que escapa", () => {});', encoding="utf-8")
    result = build_traceability((SpecScenario("rejeita slug que escapa", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is True

# cenario: vendor nao e varrido em busca de teste
def test_traceability_skips_vendor_directories(tmp_path: Path):
    """node_modules tem milhares de testes de terceiros; varrer isso seria lento
    e produziria vinculo com teste que nao e' do projeto."""
    vendor = tmp_path / "tests" / "node_modules" / "lib"
    vendor.mkdir(parents=True)
    (vendor / "dep.test.js").write_text('it("rejeita slug que escapa", () => {});', encoding="utf-8")
    result = build_traceability((SpecScenario("rejeita slug que escapa", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is False

def test_traceability_links_scenario_to_test(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_access.py").write_text("# scenario: acesso negado\n", encoding="utf-8")
    result = build_traceability((SpecScenario("acesso negado", "", "", ""),), tmp_path)
    assert [item.replace("\\", "/") for item in result["scenarios"][0]["tests"]] == ["tests/test_access.py"]
    assert result["scenarios_without_tests"] == []

def test_traceability_reports_uncovered_scenario(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    result = build_traceability((SpecScenario("pagamento aprovado", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is False
    assert result["scenarios_without_tests"] == ["pagamento aprovado"]

def test_traceability_supports_multiple_tests(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    for name in ("a.py", "b.py"):
        (tmp_path / "tests" / name).write_text("# cenario: login\n", encoding="utf-8")
    result = build_traceability((SpecScenario("login", "", "", ""),), tmp_path)
    assert len(result["scenarios"][0]["tests"]) == 2

def test_traceability_distinguishes_missing_requirement_from_missing_test(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_login.py").write_text("# scenario: login\n", encoding="utf-8")
    result = build_traceability((SpecScenario("login", "", "", ""),), tmp_path, ("changed-files-context", "login"))
    assert result["scenarios_without_tests"] == []
    assert result["requirements_without_scenarios"] == ["changed-files-context"]

def test_traceability_reports_all_behaviors_without_scenario(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    result = build_traceability((), tmp_path, ("requirement-traceability", "contextual-verdict"))
    assert result["requirements_without_scenarios"] == ["requirement-traceability", "contextual-verdict"]
    assert result["scenarios_without_tests"] == []

# cenario: marcador declarado casa com o caso mesmo sem acento
def test_traceability_marker_matches_scenario_regardless_of_accent(tmp_path: Path):
    """Achado ao vivo: um marcador escrito sem acento (`evidencia`) ficava preso
    em 'nao coberto' contra um caso escrito com acento (`evidência`), porque o
    casamento so fazia casefold, sem normalizar acento."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_report.py").write_text("# cenario: achados antes da evidencia bruta\n", encoding="utf-8")
    result = build_traceability((SpecScenario("achados antes da evidência bruta", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is True
    assert result["scenarios_without_tests"] == []

# cenario: palavras genericas nao produzem vinculo por semelhanca
def test_traceability_does_not_match_on_generic_words_alone(tmp_path: Path):
    """Falso positivo achado em uso: o caso 'sem exclude declarado, nada e
    filtrado' saiu `coberto` vinculado a test_sem_limiar_declarado_nao_cobra_nada,
    porque `sem`, `nada` e `declarado` somavam exatamente o limiar antigo de 0,6.
    Verde falso e' pior que lacuna: o relatorio afirma cobertura inexistente."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_rules.py").write_text(
        "def test_sem_limiar_declarado_nao_cobra_nada():\n    pass\n", encoding="utf-8")
    result = build_traceability((SpecScenario("sem exclude declarado, nada é filtrado", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is False
    assert result["scenarios_without_tests"] == ["sem exclude declarado, nada é filtrado"]

# cenario: semelhanca real continua vinculando sem marcador
def test_traceability_matches_test_function_names_without_marker_comment(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_login.py").write_text("def test_login_com_credenciais_validas():\n    pass\n", encoding="utf-8")
    result = build_traceability((SpecScenario("login com credenciais válidas", "", "", ""),), tmp_path)
    assert result["scenarios"][0]["covered"] is True
    assert result["scenarios_without_tests"] == []

def test_traceability_behavior_matches_via_test_function_name(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_git_context.py").write_text("def test_changed_files_context_lists_modified_paths():\n    pass\n", encoding="utf-8")
    result = build_traceability((), tmp_path, ("changed-files-context",))
    assert result["requirements_without_scenarios"] == []

def test_traceability_slug_match_survives_when_issue_text_is_supplied(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_git_context.py").write_text("def test_changed_files_context_lists_modified_paths():\n    pass\n", encoding="utf-8")
    huge_unrelated_blob = " ".join(f"palavra{i}" for i in range(200))
    result = build_traceability((), tmp_path, ("changed-files-context",), {"changed-files-context": huge_unrelated_blob})
    assert result["requirements_without_scenarios"] == []

def test_traceability_matches_behavior_via_issue_text_when_slug_alone_fails(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_verdict.py").write_text("def test_severidade_critica_gera_reprovado():\n    pass\n", encoding="utf-8")
    result = build_traceability((), tmp_path, ("contextual-verdict",), {"contextual-verdict": "o veredito aplica severidade critica para gerar reprovado"})
    assert result["requirements_without_scenarios"] == []
