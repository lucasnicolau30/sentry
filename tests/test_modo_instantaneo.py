"""Modo instantâneo: veredito sem executar teste nenhum.

O modo completo custa 24,6 s neste repositório, e por isso ninguém o roda a cada
salvamento. O instantâneo entrega o que não depende de execução — estrutura,
rastreabilidade, marcador órfão e diff — e reaproveita a cobertura da última
execução completa, sempre declarada como dela e nunca como medida agora.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from sentrytest.application.analyze import analyze

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


def _spec(root: Path) -> None:
    directory = root / '.sentry' / 'specs' / 'demo'
    directory.mkdir(parents=True)
    (directory / 'CASES.md').write_text(CASES, encoding='utf-8')


def _git(root: Path, *args: str):
    return subprocess.run(['git', *args], cwd=root, capture_output=True)


def _projeto_versionado(root: Path) -> None:
    """Projeto com spec, teste marcado e uma mudança na árvore de trabalho."""
    _spec(root)
    (root / 'tests').mkdir()
    (root / 'app.py').write_text(APP, encoding='utf-8')
    (root / 'tests' / 'test_app.py').write_text(TESTE, encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        _git(root, *args)
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'base')
    (root / 'app.py').write_text(APP + "\n\ndef dobrar(a):\n    return a * 2\n", encoding='utf-8')


def _execucao_registrada(root: Path, run_id: str, run_tests: bool, timestamp: str,
                         global_percent: float | None = None, changed_percent: float | None = None) -> None:
    """Grava uma execução no histórico, como `analyze` a gravaria."""
    (root / '.sentry').mkdir(parents=True, exist_ok=True)
    payload = {'contract_version': '1.0', 'data': {
        'id': run_id, 'project': 'demo', 'commit': None, 'timestamp': timestamp,
        'verdict': {'status': 'aprovado'}, 'findings': [],
        'configuration': {
            'run_tests': run_tests, 'from_cache': False, 'input_hash': 'hash-antigo',
            'test_execution': {'command': 'pytest', 'passed': 12, 'failed': 0,
                               'skipped': 0, 'not_run': 0, 'infrastructure_error': None},
            'coverage': {'global_percent': global_percent, 'changed_percent': changed_percent,
                         'files': {'app.py': global_percent}, 'error': None},
        }}}
    with sqlite3.connect(root / '.sentry' / 'sentry.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        conn.execute('INSERT INTO runs VALUES (?,?)', (run_id, json.dumps(payload)))


# cenario: modo instantaneo nao executa a suite
def test_modo_instantaneo_nao_executa_a_suite(tmp_path: Path):
    """Prova por sentinela, não por contagem zero: o comando declarado grava um
    arquivo se algum processo subir. Contagem zerada também é o que aparece
    quando a suíte roda e falha em coletar, então ela não distingue nada."""
    _spec(tmp_path)
    corredor = tmp_path / 'corredor.py'
    corredor.write_text("from pathlib import Path\nPath('executou.txt').write_text('sim', encoding='utf-8')\n",
                        encoding='utf-8')
    (tmp_path / 'sentry.toml').write_text(
        f'[test]\ncommand = "{sys.executable.replace(chr(92), "/")} {corredor.as_posix()}"\n', encoding='utf-8')

    run = analyze(tmp_path)

    assert run.configuration['execution_mode'] == 'instantâneo'
    assert not (tmp_path / 'executou.txt').exists()
    # Sem contagem desta rodada: a ausência da chave é o que diz que nada rodou.
    assert 'test_execution' not in run.configuration
    # Controle: a sentinela detecta mesmo. Sem isto, um comando quebrado faria o
    # teste passar por nunca escrever, e não por ninguém o ter executado.
    analyze(tmp_path, run_tests=True)
    assert (tmp_path / 'executou.txt').exists()


# cenario: modo instantaneo reusa a cobertura da ultima execucao completa
def test_modo_instantaneo_reusa_a_cobertura_da_ultima_execucao_completa(tmp_path: Path):
    _spec(tmp_path)
    _execucao_registrada(tmp_path, 'r1', True, '2026-09-01T12:00:00+00:00',
                         global_percent=87.5, changed_percent=62.5)

    coverage = analyze(tmp_path).configuration['coverage']

    assert coverage['global_percent'] == 87.5
    assert coverage['changed_percent'] == 62.5
    assert coverage['reused_from'] == {'run_id': 'r1', 'timestamp': '2026-09-01T12:00:00+00:00'}


# cenario: sem execucao completa anterior a cobertura sai indisponivel
def test_sem_execucao_completa_anterior_a_cobertura_sai_indisponivel(tmp_path: Path):
    """Uma execução instantânea anterior não serve de fonte: ela também não mediu
    nada. Reaproveitá-la propagaria indefinidamente uma cobertura sem dono."""
    _spec(tmp_path)
    _execucao_registrada(tmp_path, 'r1', False, '2026-09-01T12:00:00+00:00',
                         global_percent=99.0, changed_percent=99.0)

    coverage = analyze(tmp_path).configuration['coverage']

    assert coverage['global_percent'] is None
    assert coverage['changed_percent'] is None
    assert coverage['files'] == {}
    assert coverage['reused_from'] is None
    assert 'sem execução completa anterior' in coverage['error']


# cenario: modo instantaneo entrega estrutura rastreabilidade e diff
def test_modo_instantaneo_entrega_estrutura_rastreabilidade_e_diff(tmp_path: Path):
    """O que não depende de execução continua saindo inteiro — é isto que faz o
    modo valer a pena no loop de digitação, e não só ser mais barato."""
    _projeto_versionado(tmp_path)

    run = analyze(tmp_path)

    assert run.configuration['execution_mode'] == 'instantâneo'
    assert 'app.py' in run.configuration['git_change']['files']
    rastreabilidade = run.configuration['traceability']
    assert [item['name'] for item in rastreabilidade['scenarios']] == ['soma retorna o total']
    assert rastreabilidade['scenarios'][0]['covered']
    assert rastreabilidade['orphan_markers'] == []
    assert run.configuration['dimensions']
    assert run.verdict is not None
