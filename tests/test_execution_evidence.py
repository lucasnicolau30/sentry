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
# cenario: runner sem caminho continua no interpretador do Sentry
def test_pytest_por_caminho_de_executavel_e_reconhecido(tmp_path: Path):
    """`.venv/bin/pytest` e `pytest.exe` sao o mesmo runner escrito com caminho.
    Casar so com o literal fazia o venv perder `coverage run` silenciosamente.
    Sem separador no comando nao ha ambiente declarado, e o interpretador do
    proprio Sentry segue sendo a melhor resposta disponivel."""
    import sys
    from sentrytest.adapters.local_tools import _pytest_invocation

    assert _pytest_invocation([".venv/bin/pytest", "-x"]) == (None, ["-x"])
    assert _pytest_invocation([r"C:\proj\.venv\Scripts\pytest.exe"]) == (None, [])
    assert _pytest_invocation(["pytest", "-x"]) == (sys.executable, ["-x"])
    assert _pytest_invocation(["python3", "-m", "pytest", "-q"]) == (sys.executable, ["-q"])
    # Nao e' pytest: precisa seguir intocado pelo caminho generico.
    assert _pytest_invocation(["npx", "jest"]) is None
    assert _pytest_invocation(["python", "-m", "unittest"]) is None
    assert _pytest_invocation([]) is None

    adapter = SuiteAdapter(tmp_path, "pytest -x")
    assert adapter.is_pytest is True
    assert adapter.command[0] == sys.executable
    assert "-m coverage run -m pytest -x" in " ".join(adapter.command)

# cenario: comando vazio vira erro de infraestrutura
def test_comando_vazio_vira_erro_de_infraestrutura(tmp_path: Path):
    """`[test] command` em branco nao pode chegar ao subprocess: no POSIX estoura
    IndexError ao ler args[0] e no Windows o CreateProcess recusa com OSError --
    excecoes diferentes, nenhuma delas dizendo o que fazer. E' configuracao, logo
    infraestrutura, e nao pode derrubar a analise antes do relatorio."""
    adapter = SuiteAdapter(tmp_path, "")
    test, percent = adapter.run(tmp_path / "cov.json")
    assert test.status.value == "não executado"
    assert "[test] command" in (test.infrastructure_error or "")
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

# cenario: runner ausente sai como inconclusivo e nao como reprovacao
def test_runner_ausente_sai_como_inconclusivo(tmp_path: Path):
    """Sem o pacote do runner instalado, quem responde e' o interpretador:
    `No module named 'pytest'` e codigo de saida 1, sem uma linha de resumo. O
    veredito anterior fabricava failed=1 e virava achado critico de teste
    reprovado -- exatamente a mentira que a tabela de codigos existe para evitar.
    Trocar o modulo pelo inexistente reproduz o ambiente sem runner."""
    import sys
    from sentrytest.domain.models import TestStatus

    adapter = SuiteAdapter(tmp_path)
    assert adapter.is_pytest is True
    adapter.command = [sys.executable, "-m", "coverage", "run", "-m", "pytest_que_nao_existe"]
    execution, percent = adapter.run(tmp_path / "cov.json")

    assert "No module named" in execution.output
    assert execution.status == TestStatus.NOT_RUN
    assert execution.infrastructure_error and "runner" in execution.infrastructure_error
    assert (execution.passed, execution.failed, execution.skipped) == (0, 0, 0)

# cenario: reprovacao real continua sendo reprovacao
# cenario: suite aprovada permanece coberta
def test_veredito_de_qualidade_do_pytest_permanece_intacto(tmp_path: Path):
    """O conserto so pode alcancar a execucao sem prova nenhuma: com testes
    contabilizados, 0 continua coberto e 1 continua reprovado, com a contagem
    vinda do resumo e nao de um numero inventado."""
    from sentrytest.domain.models import TestStatus

    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    aprovada, _ = SuiteAdapter(tmp_path).run(tmp_path / "cov.json")
    assert aprovada.status == TestStatus.COVERED
    assert aprovada.infrastructure_error is None
    assert (aprovada.passed, aprovada.failed) == (1, 0)

    (tmp_path / "tests" / "test_ruim.py").write_text("def test_ruim():\n    assert False\n", encoding="utf-8")
    reprovada, _ = SuiteAdapter(tmp_path).run(tmp_path / "cov.json")
    assert reprovada.status == TestStatus.FAILED
    assert reprovada.infrastructure_error is None
    assert (reprovada.passed, reprovada.failed) == (1, 1)

# cenario: falha sem contagem no resumo ainda conta como reprovacao
# cenario: processo morto por sinal e inconclusivo
def test_classificacao_do_pytest_depende_da_evidencia_de_execucao(tmp_path: Path):
    """`ran` e' a prova de que a suite rodou. Com ela, saida != 0 e' reprovacao
    mesmo que o resumo nao traga `N failed` (erro em teardown, por exemplo). Sem
    ela -- inclusive quando o processo morre por sinal, o que no POSIX chega como
    codigo negativo -- e' ambiente, e nenhum numero e' reportado."""
    adapter = SuiteAdapter(tmp_path)
    assert adapter._classify(1, ran=True) is None
    assert adapter._classify(0, ran=True) is None

    for codigo in (1, -9):
        motivo = adapter._classify(codigo, ran=False)
        assert motivo and str(codigo) in motivo
    # A tabela de codigos do pytest tem precedencia sobre o recado generico.
    assert adapter._classify(5, ran=False) == "nenhum teste coletado"

# cenario: saida longa e truncada sem perder o resumo
def test_contagem_lida_do_fim_da_saida_truncada():
    """A evidencia guardada e' o fim da saida, onde o resumo do pytest fica; a
    contagem vem desse resumo, nunca do codigo de saida."""
    from sentrytest.adapters.local_tools import _counts_from_regex

    saida = ("linha de ruido\n" * 8000) + "=== 1 failed, 1 passed in 0.10s ==="
    assert _counts_from_regex(saida)[:3] == (1, 1, 0)
    # Sem resumo nenhum, nada e' inventado -- nem com saida vazia.
    assert _counts_from_regex("")[:3] == (0, 0, 0)
    assert _counts_from_regex("No module named 'pytest'")[:3] == (0, 0, 0)

def _venv_falso(raiz: Path, com_interpretador: bool = True) -> Path:
    """Um venv de mentira com o layout real: o console script e, ao lado dele, o
    interpretador. O `pytest` aqui e' so um arquivo -- nada e' executado a partir
    dele; o que se verifica e' qual interpretador o Sentry escolhe."""
    import sys
    diretorio = raiz / ("Scripts" if sys.platform == "win32" else "bin")
    diretorio.mkdir(parents=True)
    sufixo = ".exe" if sys.platform == "win32" else ""
    (diretorio / f"pytest{sufixo}").write_bytes(b"")
    if com_interpretador:
        # Copiar o interpretador real deixaria o teste lento e dependente de
        # permissao; um link para ele basta, e cai para copia quando o SO recusa.
        alvo = diretorio / ("python.exe" if sys.platform == "win32" else "python")
        try:
            alvo.symlink_to(sys.executable)
        except (OSError, NotImplementedError):
            import shutil
            shutil.copy2(sys.executable, alvo)
    return diretorio

# cenario: interpretador declarado por caminho e usado no lugar do global
def test_interpretador_declarado_por_caminho_e_usado(tmp_path: Path):
    """`.venv/bin/python -m pytest` declara em qual ambiente rodar. Normalizar a
    invocacao para `-m pytest` nao pode virar substituir o interpretador: a suite
    ia parar no Python global, com outro conjunto de dependencias instalado."""
    import sys

    diretorio = _venv_falso(tmp_path / "venv")
    interpretador = str(diretorio / ("python.exe" if sys.platform == "win32" else "python"))
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    adapter = SuiteAdapter(tmp_path, f"{interpretador} -m pytest")
    assert adapter.is_pytest is True
    assert adapter.command[0] == interpretador
    assert adapter.command[0] != sys.executable
    assert adapter.command[1:5] == ["-m", "coverage", "run", "-m"]

    execution, percent = adapter.run(tmp_path / "cov.json")
    assert execution.infrastructure_error is None
    assert execution.passed == 1
    assert percent is not None

# cenario: interpretador declarado inexistente vira erro de infraestrutura
def test_interpretador_declarado_inexistente_nao_cai_no_python_global(tmp_path: Path):
    """O sintoma relatado: um venv que nao existe rodava no Python global sem
    aviso, e o relatorio saia como se a suite do usuario tivesse sido executada.
    O certo e' falhar como infraestrutura, nomeando o caminho declarado."""
    import sys
    from sentrytest.domain.models import TestStatus

    ausente = tmp_path / ".venv" / "Scripts" / "python.exe"
    adapter = SuiteAdapter(tmp_path, f"{ausente} -m pytest")
    assert adapter.command[0] == str(ausente)

    execution, percent = adapter.run(tmp_path / "cov.json")
    assert execution.status == TestStatus.NOT_RUN
    assert str(ausente) in (execution.infrastructure_error or "")
    assert execution.passed == execution.failed == 0
    assert percent is None
    assert sys.executable not in execution.command

# cenario: executavel pytest do venv roda no python do proprio venv
def test_executavel_pytest_do_venv_usa_o_interpretador_irmao(tmp_path: Path):
    """O console script nao aceita `-m coverage`; quem roda e' o interpretador ao
    lado dele no venv -- o mesmo que o script usaria. Assim a instrumentacao e a
    escolha de ambiente valem juntas."""
    import sys

    diretorio = _venv_falso(tmp_path / "venv")
    executavel = diretorio / ("pytest.exe" if sys.platform == "win32" else "pytest")
    irmao = str(diretorio / ("python.exe" if sys.platform == "win32" else "python"))

    adapter = SuiteAdapter(tmp_path, f"{executavel} -x")
    assert adapter.is_pytest is True
    assert adapter.measures_coverage is True
    assert adapter.command[0] == irmao
    assert adapter.command[-3:] == ["-m", "pytest", "-x"]

# cenario: executavel pytest sem interpretador irmao roda como declarado
def test_executavel_pytest_sem_irmao_roda_como_declarado(tmp_path: Path):
    """Sem interpretador ao lado nao ha ambiente a deduzir, e chutar o do Sentry
    seria o mesmo defeito. Roda o que foi declarado: sem cobertura, mas ainda
    reconhecido como pytest, entao a tabela de codigos de saida continua valendo."""
    import sys

    diretorio = _venv_falso(tmp_path / "solto", com_interpretador=False)
    executavel = diretorio / ("pytest.exe" if sys.platform == "win32" else "pytest")

    adapter = SuiteAdapter(tmp_path, str(executavel))
    assert adapter.is_pytest is True
    assert adapter.measures_coverage is False
    assert adapter.command == [str(executavel)]
    assert sys.executable not in adapter.command
