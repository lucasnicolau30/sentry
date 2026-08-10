from pathlib import Path

from sentrytest.application.error_paths import select_error_paths

SOURCE = '''def salvar(valor):
    if valor is None:
        raise ValueError("valor obrigatorio")
    try:
        return int(valor)
    except TypeError:
        raise ValueError("tipo invalido")
'''


def _write(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")


def test_raise_alterado_sem_execucao_vira_achado(tmp_path: Path):
    _write(tmp_path)
    result = select_error_paths(tmp_path, {"app.py": (1, 2, 3)}, executed_lines={"app.py": (1, 2)})
    assert result["uncovered"] == ("app.py:3 (raise)",)
    assert result["covered"] == ()


def test_raise_alterado_e_executado_nao_vira_achado(tmp_path: Path):
    _write(tmp_path)
    result = select_error_paths(tmp_path, {"app.py": (1, 2, 3)}, executed_lines={"app.py": (1, 2, 3)})
    assert result["uncovered"] == ()
    assert result["covered"] == ("app.py:3 (raise)",)


def test_except_tambem_e_caminho_de_erro(tmp_path: Path):
    _write(tmp_path)
    result = select_error_paths(tmp_path, {"app.py": (6, 7)}, executed_lines={"app.py": ()})
    assert result["uncovered"] == ("app.py:6 (except)", "app.py:7 (raise)")


def test_linha_alterada_sem_caminho_de_erro_e_ignorada(tmp_path: Path):
    _write(tmp_path)
    result = select_error_paths(tmp_path, {"app.py": (1, 5)}, executed_lines={"app.py": ()})
    assert result["uncovered"] == ()
    assert result["limitations"] == []


def test_sem_cobertura_registra_limitacao_em_vez_de_achado(tmp_path: Path):
    """Sem evidencia de execucao a regra nao pode afirmar ausencia de teste."""
    _write(tmp_path)
    result = select_error_paths(tmp_path, {"app.py": (3,)}, executed_lines=None)
    assert result["uncovered"] == ()
    assert "sem dados de cobertura" in result["limitations"][0]


# cenario: caminho de erro e detectado fora de Python
def test_caminho_de_erro_e_detectado_fora_de_python(tmp_path: Path):
    """Antes so `.py` era analisado: um `throw` alterado e sem teste passava
    despercebido em qualquer projeto que nao fosse Python."""
    (tmp_path / "app.ts").write_text("throw new Error('x');\n", encoding="utf-8")
    result = select_error_paths(tmp_path, {"app.ts": (1,)}, executed_lines={})
    assert result["uncovered"] == ("app.ts:1 (throw)",)

# cenario: deteccao sem AST e registrada como limitacao
def test_deteccao_sem_ast_e_registrada_como_limitacao(tmp_path: Path):
    """Fora de Python a deteccao e' por padrao sintatico. Equiparar as duas
    evidencias esconderia que uma delas pode passar batido."""
    (tmp_path / "app.go").write_text("panic(\"x\")\n", encoding="utf-8")
    result = select_error_paths(tmp_path, {"app.go": (1,)}, executed_lines={})
    assert result["uncovered"] == ("app.go:1 (panic)",)
    assert any("padrao sintatico" in item and "app.go" in item for item in result["limitations"])

# cenario: palavra de erro em comentario ou string nao vira caminho de erro
def test_palavra_de_erro_em_comentario_nao_vira_caminho(tmp_path: Path):
    """Ancorar no inicio da linha e' o que separa deteccao de busca textual."""
    (tmp_path / "app.ts").write_text(
        "// isto pode throw um erro\n"
        "const msg = 'throw new Error';\n"
        "const ok = 1;\n", encoding="utf-8")
    result = select_error_paths(tmp_path, {"app.ts": (1, 2, 3)}, executed_lines={})
    assert result["uncovered"] == ()

# cenario: linha excluida da medicao nao vira caminho de erro sem teste
def test_linha_excluida_da_medicao_nao_vira_achado(tmp_path: Path):
    """`# pragma: no cover` tira a linha da medicao: ela nao aparece nem em
    executed nem em missing. Sem honrar a exclusao, o Sentry acusaria falta de
    teste onde houve decisao declarada -- e o pragma nunca resolveria nada."""
    _write(tmp_path)
    result = select_error_paths(
        tmp_path, {"app.py": (3,)}, executed_lines={"app.py": ()}, excluded_lines={"app.py": (3,)})
    assert result["uncovered"] == ()
    assert result["covered"] == ()
    assert any("pragma: no cover" in item and "app.py:3" in item for item in result["limitations"])

# cenario: exclusao nao vale para linha que o projeto nao excluiu
def test_exclusao_nao_vaza_para_linha_vizinha(tmp_path: Path):
    """A exclusao e' por linha, nao por arquivo: excluir uma nao pode calar as
    demais, senao um pragma isolado silenciaria o arquivo inteiro."""
    _write(tmp_path)
    result = select_error_paths(
        tmp_path, {"app.py": (3, 7)}, executed_lines={"app.py": ()}, excluded_lines={"app.py": (3,)})
    assert result["uncovered"] == ("app.py:7 (raise)",)

# cenario: extensao sem padrao declarado continua fora da analise
def test_extensao_sem_padrao_declarado_e_ignorada(tmp_path: Path):
    (tmp_path / "config.yaml").write_text("raise: true\n", encoding="utf-8")
    result = select_error_paths(tmp_path, {"config.yaml": (1,)}, executed_lines={})
    assert result["uncovered"] == ()
    assert result["limitations"] == []


def test_arquivo_ilegivel_vira_limitacao(tmp_path: Path):
    (tmp_path / "quebrado.py").write_text("def (:\n", encoding="utf-8")
    result = select_error_paths(tmp_path, {"quebrado.py": (1,)}, executed_lines={})
    assert result["uncovered"] == ()
    assert "nao analisados" in result["limitations"][0]
