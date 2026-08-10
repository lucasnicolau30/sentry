import json
from pathlib import Path
from sentrytest.adapters.local_tools import CoverageAdapter, detect_coverage_format
from sentrytest.application.coverage_context import calculate_changed_coverage
from sentrytest.ports.inputs import CoverageData, GitChange

LCOV = """TN:
SF:src/app.js
DA:1,1
DA:2,0
DA:3,4
end_of_record
"""

COBERTURA = """<?xml version="1.0" ?>
<coverage line-rate="0.75">
  <packages><package name="app"><classes>
    <class name="App" filename="src/app.java">
      <lines>
        <line number="1" hits="1"/>
        <line number="2" hits="0"/>
      </lines>
    </class>
  </classes></package></packages>
</coverage>
"""

def coverage_file(path: Path, executed=(2,)):
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src/app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": list(executed)}}}), encoding="utf-8")

def test_coverage_adapter_reads_json(tmp_path: Path):
    path = tmp_path / "coverage.json"
    coverage_file(path)
    result = CoverageAdapter().read(path)
    assert result.global_percent == 80.0
    assert result.executed_lines["src/app.py"] == (2,)

def test_changed_coverage_is_calculated(tmp_path: Path):
    path = tmp_path / "coverage.json"
    coverage_file(path, (2,))
    coverage = CoverageAdapter().read(path)
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (1, 2)})
    result = calculate_changed_coverage(change, coverage)
    assert result.changed_percent == 50.0

def test_coverage_adapter_normalizes_windows_separators(tmp_path: Path):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src\\app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": [2]}}}), encoding="utf-8")
    result = CoverageAdapter().read(path)
    assert result.executed_lines["src/app.py"] == (2,)

def test_changed_coverage_matches_windows_coverage_keys(tmp_path: Path):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src\\app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": [2]}}}), encoding="utf-8")
    coverage = CoverageAdapter().read(path)
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (1, 2)})
    result = calculate_changed_coverage(change, coverage)
    assert result.changed_percent == 50.0

def test_missing_coverage_is_explicit(tmp_path: Path):
    result = CoverageAdapter().read(tmp_path / "missing.json")
    assert result.error == "arquivo de cobertura ausente"

def test_invalid_coverage_is_explicit(tmp_path: Path):
    """Formato conhecido porem malformado: o JSON abre com `{` e nao fecha."""
    path = tmp_path / "coverage.json"
    path.write_text('{"totals": ', encoding="utf-8")
    assert CoverageAdapter().read(path).error.startswith("formato de cobertura invalido")

# cenario: formato irreconhecível é distinto de formato malformado
def test_unrecognized_coverage_format_is_explicit(tmp_path: Path):
    """Conteudo que nao e' nenhum dos formatos aceitos: o erro precisa dizer
    quais sao, em vez de alegar que um formato conhecido esta corrompido."""
    path = tmp_path / "coverage.json"
    path.write_text("invalid", encoding="utf-8")
    error = CoverageAdapter().read(path).error
    assert error.startswith("formato de cobertura nao reconhecido")
    assert "lcov" in error and "cobertura" in error

# cenario: detecta os três formatos pelo conteúdo
def test_detecta_os_tres_formatos_pelo_conteudo():
    assert detect_coverage_format('{"totals": {}}') == "coverage.py"
    assert detect_coverage_format(LCOV) == "lcov"
    assert detect_coverage_format(COBERTURA) == "cobertura"
    assert detect_coverage_format("texto solto") is None

# cenario: relatório lcov produz cobertura por linha
def test_coverage_adapter_reads_lcov(tmp_path: Path):
    """LCOV e' o formato de nyc/c8/Jest e simplecov: DA:<linha>,<execucoes>."""
    path = tmp_path / "lcov.info"
    path.write_text(LCOV, encoding="utf-8")
    result = CoverageAdapter().read(path)
    assert result.error is None
    assert result.executed_lines["src/app.js"] == (1, 3)  # linha 2 tem 0 execucoes
    assert result.files["src/app.js"] == 2 / 3 * 100
    assert result.global_percent == 2 / 3 * 100

# cenario: relatório cobertura xml produz cobertura por linha
def test_coverage_adapter_reads_cobertura(tmp_path: Path):
    """Cobertura XML e' o formato de JaCoCo, coverlet e coverage.py xml."""
    path = tmp_path / "coverage.xml"
    path.write_text(COBERTURA, encoding="utf-8")
    result = CoverageAdapter().read(path)
    assert result.error is None
    assert result.executed_lines["src/app.java"] == (1,)
    assert result.global_percent == 75.0  # line-rate declarado no proprio relatorio

# cenario: lcov com caminho absoluto casa com o caminho relativo do diff
def test_lcov_absolute_paths_are_made_relative_to_root(tmp_path: Path):
    """nyc e Jest gravam caminho absoluto; o diff do Git e' sempre relativo a
    raiz. Sem relativizar, nenhum arquivo casaria e a cobertura alterada sumiria."""
    source = tmp_path / "src" / "app.js"
    source.parent.mkdir(parents=True)
    source.write_text("//\n", encoding="utf-8")
    path = tmp_path / "lcov.info"
    path.write_text(f"SF:{source}\nDA:1,1\nDA:2,0\nend_of_record\n", encoding="utf-8")
    result = CoverageAdapter().read(path, root=tmp_path)
    assert "src/app.js" in result.executed_lines

# cenario: lcov mesclado nao infla a contagem ao repetir a mesma linha
def test_lcov_merged_report_does_not_double_count(tmp_path: Path):
    """Relatorios mesclados repetem DA para a mesma linha; contar em lista faria
    a cobertura passar de 100%."""
    path = tmp_path / "lcov.info"
    path.write_text("SF:src/app.js\nDA:1,1\nDA:1,2\nDA:2,0\nend_of_record\n", encoding="utf-8")
    result = CoverageAdapter().read(path)
    assert result.executed_lines["src/app.js"] == (1,)
    assert result.files["src/app.js"] == 50.0

# cenario: relatório do formato certo porém sem nenhum registro é recusado
def test_coverage_report_without_any_record_is_rejected(tmp_path: Path):
    """Um lcov só com cabecalho, ou um XML sem <class filename=>, tem o formato
    certo e nenhum dado: aceitar isso reportaria 0% em vez de dizer que nao ha
    evidencia, e 0% de cobertura vira achado de codigo sem teste."""
    lcov = tmp_path / "vazio.info"
    lcov.write_text("TN:\n", encoding="utf-8")
    assert "nenhum registro SF:/DA:" in CoverageAdapter().read(lcov).error

    xml = tmp_path / "vazio.xml"
    xml.write_text('<coverage line-rate="0.0"><packages/></coverage>', encoding="utf-8")
    assert "nenhum <class filename=" in CoverageAdapter().read(xml).error

# cenario: caminho fora da raiz do projeto e mantido como veio
def test_coverage_path_outside_root_is_kept_as_is(tmp_path: Path):
    """Monorepo pode reportar arquivo fora da raiz analisada: relative_to falha
    e o caminho original precisa ser preservado, nao virar erro."""
    fora = tmp_path / "outro-projeto" / "app.js"
    fora.parent.mkdir(parents=True)
    fora.write_text("//\n", encoding="utf-8")
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    path = tmp_path / "lcov.info"
    path.write_text(f"SF:{fora}\nDA:1,1\nend_of_record\n", encoding="utf-8")
    result = CoverageAdapter().read(path, root=raiz)
    assert result.error is None
    assert any("app.js" in name for name in result.executed_lines)

# cenario: cobertura alterada funciona a partir de um relatorio lcov
def test_changed_coverage_from_lcov(tmp_path: Path):
    """O ponto do item: um projeto Node passa a ter veredito real, nao inconclusivo."""
    path = tmp_path / "lcov.info"
    path.write_text(LCOV, encoding="utf-8")
    coverage = CoverageAdapter().read(path)
    change = GitChange("head", "base", ("src/app.js",), changed_lines={"src/app.js": (1, 2)})
    result = calculate_changed_coverage(change, coverage)
    assert result.changed_percent == 50.0  # linha 1 coberta, linha 2 nao
