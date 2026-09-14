"""`sentry status`: o mapa da aplicação inteira, não só do diff.

O truque é reaproveitar `analyze()` inteiro com um `GitChange` sintético que
trata todo arquivo de código-fonte como alterado — o mesmo mecanismo que já
existia para um `.py` novo sem hunk reconhecível (`LocalGitAdapter.change()`).
Nada de pipeline novo: cobertura, traceability, achados e veredito saem do
mesmo lugar, só que sobre o projeto inteiro em vez do diff.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sentrytest.adapters.local_tools import LocalGitAdapter, SuiteAdapter
from sentrytest.application.analyze import analyze
from sentrytest.application.reporting import markdown_report
from sentrytest.domain import models
from sentrytest.ports import inputs

CASES = """# Demo

## Prompt

Somar dois numeros.

## Caso: soma retorna o total

- **Requisito:** somar dois numeros
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** dois inteiros validos
- **Quando:** somar e chamado
- **Então:** retorna a soma
"""

APP = "def somar(a, b):\n    return a + b\n"
TESTE = ("from app import somar\n\n\n"
         "# cenario: soma retorna o total\n"
         "def test_soma_retorna_o_total():\n    assert somar(1, 2) == 3\n")


def _git(root: Path, *args: str):
    return subprocess.run(['git', *args], cwd=root, capture_output=True)


def _commit(root: Path, message: str) -> None:
    for args in (('add', '-A',), ('commit', '-qm', message)):
        _git(root, *args)


def _projeto(root: Path) -> None:
    spec = root / '.sentry' / 'specs' / 'demo'
    spec.mkdir(parents=True)
    (spec / 'CASES.md').write_text(CASES, encoding='utf-8')
    (root / 'tests').mkdir()
    (root / 'app.py').write_text(APP, encoding='utf-8')
    (root / 'tests' / 'test_app.py').write_text(TESTE, encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        _git(root, *args)
    _commit(root, 'base')


def _cobertura(files: dict[str, float]) -> str:
    """JSON de coverage.py: um arquivo por entrada, com a linha 1 executada ou não
    conforme o percentual pedido -- so' 0.0 e 100.0 sao usados nos testes aqui."""
    return json.dumps({
        "totals": {"percent_covered": sum(files.values()) / len(files) if files else 0.0},
        "files": {name: {"summary": {"percent_covered": pct},
                         "executed_lines": [1] if pct else [],
                         "missing_lines": [] if pct else [1]}
                  for name, pct in files.items()},
    })


def _suite_instrumentada(monkeypatch, coverage_json: str) -> list[Path]:
    """Substitui a execução real por uma que grava a cobertura pedida e conta
    quantas vezes rodou -- a prova direta de que `status` nunca volta do cache."""
    chamadas: list[Path] = []

    def executar(self, coverage_file: Path, timeout_seconds: int = 300):
        chamadas.append(coverage_file)
        coverage_file.parent.mkdir(parents=True, exist_ok=True)
        coverage_file.write_text(coverage_json, encoding='utf-8')
        return inputs.TestExecution('pytest', passed=1, output='1 passed',
                                    status=models.TestStatus.COVERED, duration_seconds=0.1), None

    monkeypatch.setattr(SuiteAdapter, 'run', executar)
    return chamadas


# cenario: status reporta cobertura alterada igual a cobertura global
def test_status_reporta_cobertura_alterada_igual_a_cobertura_global(tmp_path: Path, monkeypatch):
    _projeto(tmp_path)
    _suite_instrumentada(monkeypatch, _cobertura({'app.py': 100.0}))

    run = analyze(tmp_path, whole_project=True)

    coverage = run.configuration['coverage']
    assert coverage['changed_percent'] == coverage['global_percent']
    assert run.configuration['whole_project'] is True


# cenario: sentry run comum nao trata a cobertura alterada como a global
def test_sentry_run_comum_nao_trata_a_cobertura_alterada_como_a_global(tmp_path: Path, monkeypatch):
    """Contraste: fora do modo `status`, um arquivo fora do diff com cobertura
    diferente ainda derruba a global sem mexer na alterada."""
    _projeto(tmp_path)
    (tmp_path / 'extra.py').write_text("def nunca_chamado():\n    return None\n", encoding='utf-8')
    _commit(tmp_path, 'extra sem cobertura')
    _suite_instrumentada(monkeypatch, _cobertura({'app.py': 100.0, 'extra.py': 0.0}))
    (tmp_path / 'app.py').write_text(APP + "\n\ndef dobrar(a):\n    return a * 2\n", encoding='utf-8')

    run = analyze(tmp_path, run_tests=True)

    coverage = run.configuration['coverage']
    assert coverage['global_percent'] == 50.0
    assert coverage['changed_percent'] != coverage['global_percent']
    assert run.configuration['whole_project'] is False


def _payload_com_cobertura(files: dict[str, float]) -> dict:
    return {'data': {
        'id': 'r1', 'project': 'demo', 'commit': 'abcdef0', 'timestamp': '2026-09-11T12:00:00+00:00',
        'verdict': {'status': 'aprovado'}, 'findings': [], 'infrastructure_errors': [], 'test_cases': [],
        'configuration': {
            'whole_project': True, 'from_cache': False, 'run_tests': True,
            'test_execution': {'command': 'pytest', 'passed': 1, 'failed': 0, 'skipped': 0, 'not_run': 0},
            'coverage': {'global_percent': 50.0, 'changed_percent': 50.0, 'files': files, 'error': None,
                        'diff_bytes': 0, 'diff_chars': 0},
            'git_change': {'files': list(files), 'reference': None, 'diff_bytes': 0, 'diff_chars': 0},
            'traceability': {}, 'impact': {}, 'error_paths': {}, 'cases': {},
        }}}


# cenario: arquivo com 0% de cobertura entra na secao de arquivos sem teste alcancando
def test_arquivo_com_zero_por_cento_entra_na_secao(tmp_path: Path):
    relatorio = markdown_report(_payload_com_cobertura({'sem_teste.py': 0.0, 'com_teste.py': 100.0}))

    secao = relatorio.split('## Arquivos sem nenhum teste alcançando')[1].split('##')[0]
    assert 'sem_teste.py' in secao


# cenario: arquivo com cobertura maior que zero nao entra na secao
def test_arquivo_com_cobertura_nao_entra_na_secao(tmp_path: Path):
    relatorio = markdown_report(_payload_com_cobertura({'sem_teste.py': 0.0, 'com_teste.py': 100.0}))

    secao = relatorio.split('## Arquivos sem nenhum teste alcançando')[1].split('##')[0]
    assert 'com_teste.py' not in secao


# cenario: marcador orfao em arquivo nao tocado aparece no status
def test_marcador_orfao_em_arquivo_nao_tocado_aparece_no_status(tmp_path: Path, monkeypatch):
    _projeto(tmp_path)
    orfao = tmp_path / 'tests' / 'test_orfao.py'
    orfao.write_text("# cenario: caso que nunca existiu\ndef test_algo():\n    assert True\n", encoding='utf-8')
    _commit(tmp_path, 'marcador orfao ja existente')
    _suite_instrumentada(monkeypatch, _cobertura({'app.py': 100.0}))

    run = analyze(tmp_path, whole_project=True)

    assert any(item['marker'] == 'caso que nunca existiu'
              for item in run.configuration['traceability']['orphan_markers'])


# cenario: mesmo marcador orfao nao aparece num sentry run comum
def test_mesmo_marcador_orfao_nao_aparece_num_run_comum(tmp_path: Path, monkeypatch):
    _projeto(tmp_path)
    orfao = tmp_path / 'tests' / 'test_orfao.py'
    orfao.write_text("# cenario: caso que nunca existiu\ndef test_algo():\n    assert True\n", encoding='utf-8')
    _commit(tmp_path, 'marcador orfao ja existente')
    _suite_instrumentada(monkeypatch, _cobertura({'app.py': 100.0}))
    (tmp_path / 'app.py').write_text(APP + "\n\ndef dobrar(a):\n    return a * 2\n", encoding='utf-8')

    run = analyze(tmp_path, run_tests=True)

    assert run.configuration['traceability']['orphan_markers'] == []


# cenario: status nunca reaproveita execucao do cache
def test_status_nunca_reaproveita_execucao_do_cache(tmp_path: Path, monkeypatch):
    _projeto(tmp_path)
    chamadas = _suite_instrumentada(monkeypatch, _cobertura({'app.py': 100.0}))

    primeira = analyze(tmp_path, whole_project=True)
    segunda = analyze(tmp_path, whole_project=True)

    assert len(chamadas) == 2  # a suite rodou nas duas vezes
    assert primeira.configuration['from_cache'] is False
    assert segunda.configuration['from_cache'] is False


# cenario: fora de repositorio git status sai como erro de infraestrutura
def test_fora_de_repositorio_git_status_sai_como_erro_de_infraestrutura(tmp_path: Path, monkeypatch):
    spec = tmp_path / '.sentry' / 'specs' / 'demo'
    spec.mkdir(parents=True)
    (spec / 'CASES.md').write_text(CASES, encoding='utf-8')
    (tmp_path / 'app.py').write_text(APP, encoding='utf-8')
    _suite_instrumentada(monkeypatch, _cobertura({'app.py': 100.0}))

    run = analyze(tmp_path, whole_project=True)

    assert run.verdict.status == models.VerdictStatus.INCONCLUSIVE
    assert any(error.stage == 'leitura do projeto' for error in run.infrastructure_errors)


# cenario: status --json inclui o payload gravado pelo relatorio
def test_status_json_inclui_o_payload_gravado(tmp_path: Path, monkeypatch):
    _projeto(tmp_path)
    _suite_instrumentada(monkeypatch, _cobertura({'app.py': 100.0}))

    run = analyze(tmp_path, whole_project=True)

    gravado = json.loads((tmp_path / '.sentry' / 'runs' / f'{run.id}.json').read_text(encoding='utf-8'))
    assert gravado['data']['id'] == run.id
    assert gravado['data']['configuration']['whole_project'] is True


def test_whole_tree_ignora_arquivo_rastreado_que_sumiu_do_disco(tmp_path: Path):
    """Caminho defensivo, sem cenário declarado: um arquivo que o Git ainda lista
    (rastreado no índice) mas que sumiu da árvore de trabalho não pode derrubar
    `sentry status` inteiro -- ele só não entra em `changed_lines`."""
    (tmp_path / 'sumido.py').write_text('x = 1\n', encoding='utf-8')
    (tmp_path / 'presente.py').write_text('y = 2\n', encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        _git(tmp_path, *args)
    _commit(tmp_path, 'base')
    (tmp_path / 'sumido.py').unlink()

    change = LocalGitAdapter(tmp_path).whole_tree(frozenset({'.py'}))

    assert change.error is None
    assert 'sumido.py' not in change.changed_lines
    assert 'presente.py' in change.changed_lines
