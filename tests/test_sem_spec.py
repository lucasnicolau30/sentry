"""O modo sem spec: medir o que nao depende de intencao declarada.

A spec e' o teto do produto -- requisito rastreado, cenario ligado a teste, classe de
equivalencia cobrada. Exigi-la antes de entregar qualquer coisa fazia a analise de uma
mudanca nao pre-especificada valer zero, enquanto jogar o codigo num agente entrega
alguma coisa sempre. Aqui ela vira upgrade: quem escreve CASES.md ganha rastreabilidade
e catalogo, quem nao escreve ainda ganha a medicao.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sentrytest.application.analyze import analyze
from sentrytest.application.dimensions import NO_INTENT, APIS, REQUIREMENTS, EXCEPTIONS

APP = "def somar(a, b):\n    return a + b\n"
APP_COM_ERRO = (
    "def somar(a, b):\n    return a + b\n\n"
    "def dividir(a, b):\n    if b == 0:\n        raise ValueError('divisao por zero')\n    return a / b\n"
)
TESTE = "from app import somar\n\n\ndef test_somar():\n    assert somar(1, 2) == 3\n"

def _git(root: Path, *args: str):
    return subprocess.run(['git', *args], cwd=root, capture_output=True)

def _projeto(root: Path, com_marcador: str | None = None) -> None:
    """Repositorio Git com uma mudanca real a medir e nenhuma spec."""
    (root / 'tests').mkdir()
    (root / 'app.py').write_text(APP, encoding='utf-8')
    marcador = f"# cenario: {com_marcador}\n" if com_marcador else ""
    (root / 'tests' / 'test_app.py').write_text(marcador + TESTE, encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        _git(root, *args)
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'base')
    (root / 'app.py').write_text(APP_COM_ERRO, encoding='utf-8')

def _dimensao(run, nome):
    return next(item for item in run.configuration['dimensions'] if item['dimension'] == nome)

# cenario: run sem spec produz relatorio em vez de excecao
def test_run_sem_spec_produz_relatorio_em_vez_de_excecao(tmp_path: Path):
    _projeto(tmp_path)
    run = analyze(tmp_path, run_tests=True)
    assert run.verdict is not None
    assert run.configuration['without_spec'] is True
    assert run.configuration['spec'] == 'nenhuma spec declarada'

# cenario: run --spec all sem nenhuma spec continua sendo erro
def test_spec_all_sem_nenhuma_spec_continua_sendo_erro(tmp_path: Path):
    """Preserva a garantia da Fase 1: e' por este caminho que a auto-analise no CI
    descobre que o checkout chegou sem matriz de casos, em vez de aprovar sem medir."""
    _projeto(tmp_path)
    with pytest.raises(ValueError, match='nenhuma matriz de casos'):
        analyze(tmp_path, 'all', run_tests=False)

# cenario: run com slug inexistente continua sendo erro
def test_slug_inexistente_continua_sendo_erro(tmp_path: Path):
    """Pedido explicito que a realidade nao atende e' erro; ausencia de pedido nao e'."""
    _projeto(tmp_path)
    with pytest.raises(FileNotFoundError, match='spec não encontrada'):
        analyze(tmp_path, 'nao-existe', run_tests=False)

# cenario: modo sem spec mede cobertura do alterado e testes impactados
def test_modo_sem_spec_mede_cobertura_e_impacto(tmp_path: Path):
    _projeto(tmp_path)
    run = analyze(tmp_path, run_tests=True)
    assert run.configuration['coverage']['changed_percent'] is not None
    assert run.configuration['test_execution']['passed'] == 1
    assert run.configuration['impact']['impacted']
    # O caminho de erro sai do AST e da execucao, nao da spec: e' o que o modo sem
    # spec ainda tem a dizer sobre a mudanca.
    assert run.configuration['error_paths']['uncovered']

# cenario: regras que dependem de spec nao disparam sem spec
def test_regras_que_dependem_de_spec_nao_disparam(tmp_path: Path):
    """Validar o documento vazio acusava titulo ausente, prompt ausente e nenhum caso
    declarado -- tres achados criticos que reprovavam por nao existir uma spec que
    ninguem prometeu escrever."""
    _projeto(tmp_path)
    run = analyze(tmp_path, run_tests=True)
    regras = {finding.rule for finding in run.findings}
    for dependente_de_spec in ('case-spec-invalid', 'scenario-without-test',
                               'requirement-without-scenario', 'missing-equivalence-class'):
        assert dependente_de_spec not in regras

# cenario: dimensao de requisitos sai nao aplicavel sem intencao declarada
def test_dimensao_de_requisitos_declara_intencao_ausente(tmp_path: Path):
    _projeto(tmp_path)
    dimensao = _dimensao(analyze(tmp_path, run_tests=True), REQUIREMENTS)
    assert dimensao['status'] == 'não aplicável'
    assert dimensao['justification'] == NO_INTENT

# cenario: dimensao de APIs sai nao aplicavel sem intencao declarada
def test_dimensao_de_apis_declara_intencao_ausente_e_nunca_coberta(tmp_path: Path):
    _projeto(tmp_path)
    dimensao = _dimensao(analyze(tmp_path, run_tests=True), APIS)
    assert dimensao['status'] == 'não aplicável'
    assert dimensao['status'] != 'coberta'
    assert dimensao['justification'] == NO_INTENT

# cenario: dimensao de excecoes continua medida sem spec
def test_dimensao_de_excecoes_continua_medida(tmp_path: Path):
    """Excecoes sai do AST e da execucao. Cala-la junto com as outras esconderia
    justamente a evidencia que o modo sem spec produz."""
    _projeto(tmp_path)
    dimensao = _dimensao(analyze(tmp_path, run_tests=True), EXCEPTIONS)
    assert dimensao['status'] == 'não coberta'
    assert dimensao['justification'] != NO_INTENT

# cenario: sem spec declarada nenhum marcador e orfao
def test_sem_spec_nenhum_marcador_e_orfao(tmp_path: Path):
    """Sem matriz com que comparar, todo marcador viraria orfao e o modo sem spec
    nasceria produzindo achado para cada teste marcado do projeto."""
    _projeto(tmp_path, com_marcador='qualquer nome')
    run = analyze(tmp_path, run_tests=True)
    assert run.configuration['traceability']['orphan_markers'] == []
    assert 'orphan-scenario-marker' not in {finding.rule for finding in run.findings}
