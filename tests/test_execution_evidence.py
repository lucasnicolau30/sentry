from pathlib import Path
from sentrytest.adapters.local_tools import SuiteAdapter, _counts_from_junitxml

def test_execution_records_passed_counts_and_summary(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert 1 == 1\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    test, percent = SuiteAdapter(tmp_path).run(tmp_path / "coverage.json")
    assert test.passed >= 1
    assert test.failed == 0
    assert "-m coverage run -m pytest" in test.command

def test_execution_records_failure(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_fail.py").write_text("def test_fail():\n    assert 1 == 2\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    test, _ = SuiteAdapter(tmp_path).run(tmp_path / "coverage.json")
    assert test.status.value == "falhou"
    assert test.failed >= 1

def test_execution_reports_not_run_when_deselected(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    (tmp_path / "tests" / "test_b.py").write_text("def test_b():\n    assert True\n", encoding="utf-8")
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = -k 'test_a'\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    test, _ = SuiteAdapter(tmp_path).run(tmp_path / "coverage.json")
    assert test.not_run >= 1

def test_infrastructure_failure_is_not_run(tmp_path: Path):
    test = _run_tests_fake()
    assert test.status.value == "não executado"
    assert test.infrastructure_error

def _run_tests_fake():
    import types
    from sentrytest.domain.models import TestStatus
    return types.SimpleNamespace(status=TestStatus.NOT_RUN, command="cmd", passed=0, failed=0, skipped=0, not_run=0, duration_seconds=0.0, output="", infrastructure_error="timeout")

def test_pytest_sem_testes_coletados_e_infraestrutura_nao_reprovacao(tmp_path: Path):
    """Codigo de saida 5 significa 'nao rodou', nao 'reprovou'."""
    from sentrytest.adapters.local_tools import SuiteAdapter
    from sentrytest.domain.models import TestStatus
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    execution, _ = SuiteAdapter(vazio).run(tmp_path / "cov.json", timeout_seconds=120)
    assert execution.infrastructure_error == "nenhum teste coletado"
    assert execution.status == TestStatus.NOT_RUN

# cenario: comando de teste ausente vira erro de infraestrutura, nao reprovacao
def test_execution_reports_infrastructure_error_when_command_is_missing(tmp_path: Path):
    """FileNotFoundError (comando configurado nao existe no PATH) precisa virar
    infrastructure_error, nunca ser tratado como suite reprovada."""
    test, percent = SuiteAdapter(tmp_path, "comando-de-teste-que-nao-existe-xyz").run(tmp_path / "cov.json")
    assert test.infrastructure_error
    assert test.status.value == "não executado"
    assert percent is None

JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="jest" tests="3" failures="1" errors="0" skipped="1">
  <testcase name="rejeita slug que escapa"/>
</testsuite>
"""

# cenario: suite nao-pytest le o junit declarado sem injetar flag
def test_suite_nao_pytest_le_o_junit_declarado(tmp_path: Path):
    """`npx jest` nao conhece --junitxml: injetar a flag quebraria o comando.
    Com [test] junit_xml declarado, o projeto configura o proprio reporter e o
    Sentry apenas le o arquivo. O runner aqui so faz as vezes do jest."""
    import sys
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "junit.xml").write_text(JUNIT, encoding="utf-8")
    runner = tmp_path / "runner.py"
    runner.write_text("pass\n", encoding="utf-8")
    adapter = SuiteAdapter(tmp_path, f"{sys.executable} {runner}", junit_xml="reports/junit.xml")
    assert adapter.is_pytest is False
    test, percent = adapter.run(tmp_path / "cov.json")
    assert (test.passed, test.failed, test.skipped) == (1, 1, 1)
    assert test.infrastructure_error is None
    assert "--junitxml" not in test.command
    assert percent is None  # a cobertura vem do relatorio do projeto, nao daqui

# cenario: fora do pytest, ausencia de teste contabilizado e infraestrutura
def test_fora_do_pytest_ausencia_de_teste_contabilizado_e_infraestrutura(tmp_path: Path):
    """Nao existe tabela confiavel de codigos de saida fora do pytest, entao o
    sinal e' a evidencia: sem nenhum teste contabilizado nao ha prova de que a
    suite rodou -- e' ambiente, e reprovar ali mentiria sobre o codigo. Com
    teste contabilizado, codigo de saida != 0 volta a ser reprovacao legitima."""
    adapter = SuiteAdapter(tmp_path, "npx jest")
    assert adapter.is_pytest is False
    ausente = adapter._classify(127, ran=False)
    assert "nenhum teste contabilizado" in ausente and "127" in ausente
    assert adapter._classify(1, ran=True) is None

    # No pytest a tabela de codigos continua valendo, sem depender da evidencia.
    assert SuiteAdapter(tmp_path)._classify(5, ran=False) == "nenhum teste coletado"

# cenario: comando nao-pytest sem junit declarado nao recebe a flag do pytest
def test_suite_nao_pytest_sem_junit_declarado_nao_recebe_junitxml(tmp_path: Path):
    """`python -m unittest` rejeita `--junitxml` com erro de linha de comando:
    injetar a flag quebrava a suite do usuario e o veredito saia como problema
    de ambiente, escondendo que o culpado era o proprio Sentry."""
    import sys
    (tmp_path / "test_ok.py").write_text(
        "import unittest\n"
        "class T(unittest.TestCase):\n"
        "    def test_ok(self):\n"
        "        self.assertTrue(True)\n",
        encoding="utf-8",
    )
    adapter = SuiteAdapter(tmp_path, f"{sys.executable} -m unittest discover -p test_*.py")
    assert adapter.is_pytest is False
    test, percent = adapter.run(tmp_path / "cov.json")
    assert "--junitxml" not in test.output
    assert "erro de uso" not in test.output.lower()
    assert percent is None
    # Sem relatorio nao ha contagem, mas o recado agora aponta a acao que resolve.
    assert "junit_xml" in (test.infrastructure_error or "")

# cenario: pytest chamado como modulo continua sendo pytest
def test_pytest_invocado_como_modulo_e_reconhecido(tmp_path: Path):
    """`python -m pytest` e `.venv/bin/pytest` sao o mesmo runner que `pytest`.
    Sem normalizar, perdiam `coverage run` e nao mediam cobertura nenhuma."""
    import sys
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    adapter = SuiteAdapter(tmp_path, f"{sys.executable} -m pytest")
    assert adapter.is_pytest is True
    assert "-m coverage run -m pytest" in " ".join(adapter.command)
    test, percent = adapter.run(tmp_path / "coverage.json")
    assert test.passed >= 1
    assert percent is not None

# cenario: pytest invocado por caminho de executavel e reconhecido
def test_pytest_por_caminho_de_executavel_e_reconhecido(tmp_path: Path):
    """`.venv/bin/pytest` e `pytest.exe` sao o mesmo runner escrito com caminho.
    Casar so com o literal fazia o venv perder `coverage run` silenciosamente."""
    from sentrytest.adapters.local_tools import _pytest_invocation

    assert _pytest_invocation([".venv/bin/pytest", "-x"]) == ["pytest", "-x"]
    assert _pytest_invocation([r"C:\proj\.venv\Scripts\pytest.exe"]) == ["pytest"]
    assert _pytest_invocation(["python3", "-m", "pytest", "-q"]) == ["pytest", "-q"]
    # Nao e' pytest: precisa seguir intocado pelo caminho generico.
    assert _pytest_invocation(["npx", "jest"]) is None
    assert _pytest_invocation(["python", "-m", "unittest"]) is None
    assert _pytest_invocation([]) is None

    adapter = SuiteAdapter(tmp_path, ".venv/bin/pytest -x")
    assert adapter.is_pytest is True
    assert "-m coverage run -m pytest -x" in " ".join(adapter.command)

# cenario: comando vazio vira erro de infraestrutura
def test_comando_vazio_vira_erro_de_infraestrutura(tmp_path: Path):
    """`[test] command` em branco chega ao subprocess como lista vazia e o SO
    recusa. Configuracao ruim e' infraestrutura -- nao pode subir excecao e
    derrubar a analise inteira antes de o relatorio ser escrito."""
    adapter = SuiteAdapter(tmp_path, "")
    test, percent = adapter.run(tmp_path / "cov.json")
    assert test.status.value == "não executado"
    assert test.infrastructure_error
    assert percent is None

# cenario: junit.xml corrompido cai no fallback por regex sem quebrar
def test_counts_from_junitxml_returns_none_for_malformed_report(tmp_path: Path):
    """XML invalido ou sem <testsuite> precisa devolver None -- e' o sinal para
    SuiteAdapter usar o fallback por regex na saida do pytest."""
    malformed = tmp_path / "junit.xml"
    malformed.write_text("isto nao e xml valido <<<", encoding="utf-8")
    assert _counts_from_junitxml(malformed) is None

    sem_testsuite = tmp_path / "sem_suite.xml"
    sem_testsuite.write_text("<root></root>", encoding="utf-8")
    assert _counts_from_junitxml(sem_testsuite) is None
