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

# `missing_lines` nao e' detalhe do fixture: e' o que declara quais linhas sao
# statement. Sem ela, a linha 1 nao e' "descoberta", e sim inexistente para a
# cobertura -- e o calculo, corretamente, a ignora.
def coverage_file(path: Path, executed=(2,), missing=(1,)):
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src/app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": list(executed), "missing_lines": list(missing)}}}), encoding="utf-8")

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
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src\\app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": [2], "missing_lines": [1]}}}), encoding="utf-8")
    result = CoverageAdapter().read(path)
    assert result.executed_lines["src/app.py"] == (2,)

def test_changed_coverage_matches_windows_coverage_keys(tmp_path: Path):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps({"totals": {"percent_covered": 80.0}, "files": {"src\\app.py": {"summary": {"percent_covered": 80.0}, "executed_lines": [2], "missing_lines": [1]}}}), encoding="utf-8")
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

def _cobertura(executadas=(), faltantes=(), arquivo="src/app.py"):
    return CoverageData(80.0, {arquivo: 80.0},
                        executed_lines={arquivo: tuple(executadas)},
                        measured_lines={arquivo: tuple(sorted({*executadas, *faltantes}))})

# cenario: statement executado conta como coberto
def test_statement_executado_entra_no_denominador_e_no_numerador():
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (10,)})
    assert calculate_changed_coverage(change, _cobertura(executadas=(10,))).changed_percent == 100.0

# cenario: statement nao executado continua descoberto
def test_statement_nao_executado_derruba_o_percentual():
    """A correcao tira comentario do denominador; tirar tambem o statement sem teste
    esconderia justamente o que esta medida existe para acusar."""
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (10, 11)})
    resultado = calculate_changed_coverage(change, _cobertura(executadas=(10,), faltantes=(11,)))
    assert resultado.changed_percent == 50.0

# cenario: linha em branco fica fora do calculo
def test_linha_em_branco_nao_entra_no_denominador():
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (10, 11)})
    # A 11 e' linha em branco: a cobertura nao a mediu, entao ela nao aparece nem
    # como executada nem como faltante.
    assert calculate_changed_coverage(change, _cobertura(executadas=(10,))).changed_percent == 100.0

# cenario: linha de comentario fica fora do calculo
def test_linha_de_comentario_nao_derruba_a_cobertura_do_alterado():
    """Neste codigo o comentario registra o porque de cada decisao. Conta-lo como
    descoberto fazia escrever a explicacao derrubar a nota da propria mudanca."""
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": tuple(range(10, 25))})
    resultado = calculate_changed_coverage(change, _cobertura(executadas=(10, 24)))
    assert resultado.changed_percent == 100.0

# cenario: linha de arquivo que a cobertura nao mede fica fora do calculo
def test_arquivo_sem_cobertura_medida_nao_entra_no_denominador():
    """Um workflow YAML alterado nao tem cobertura a medir; no denominador, ele
    reprovava a mudanca por existir."""
    change = GitChange("head", "base", ("src/app.py", ".github/workflows/ci.yml"),
                       changed_lines={"src/app.py": (10,), ".github/workflows/ci.yml": (1, 2, 3)})
    assert calculate_changed_coverage(change, _cobertura(executadas=(10,))).changed_percent == 100.0

def test_mudanca_sem_linha_mensuravel_nao_produz_percentual():
    change = GitChange("head", "base", ("README.md",), changed_lines={"README.md": (1, 2)})
    assert calculate_changed_coverage(change, _cobertura(executadas=(10,))).changed_percent is None

def test_erro_de_cobertura_passa_adiante_sem_calcular_percentual():
    """Sem dados de linha nao ha o que calcular, e o erro precisa chegar ao
    relatorio como limitacao. O branch existia sem teste e passou a carregar
    tambem `measured_lines`: sem cobri-lo, a perda do campo passaria em silencio."""
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (10,)})
    vazia = CoverageData(None, {}, error="arquivo de cobertura ausente")
    resultado = calculate_changed_coverage(change, vazia)
    assert resultado.changed_percent is None
    assert resultado.error == "arquivo de cobertura ausente"
    assert resultado.measured_lines == {}

def test_sem_linhas_executadas_declara_dados_ausentes():
    change = GitChange("head", "base", ("src/app.py",), changed_lines={"src/app.py": (10,)})
    resultado = calculate_changed_coverage(change, CoverageData(80.0, {"src/app.py": 80.0}))
    assert resultado.error == "dados de linhas ausentes"
    assert resultado.changed_percent is None
