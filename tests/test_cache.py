"""Cache por hash de conteúdo: não repetir a suíte quando nada mudou.

É a alavanca de tempo que a medição confirmou — ao contrário de filtrar a suíte
por impacto, que cortou 60% dos testes e economizou 0,9 s. O que decide se a
execução completa anterior ainda serve são três entradas: o diff, os arquivos de
teste e as specs. Mudou qualquer uma, aquela execução deixou de descrever esta
situação e a suíte roda de novo.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sentrytest.adapters.local_tools import SuiteAdapter
from sentrytest.application.analyze import analyze
from sentrytest.application.reuse import cached_run, input_fingerprint
from sentrytest.domain import models
from sentrytest.ports import inputs
from sentrytest.ports.inputs import GitChange

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

COBERTURA = json.dumps({
    "totals": {"percent_covered": 87.5},
    "files": {"app.py": {"summary": {"percent_covered": 87.5},
                         "executed_lines": [1, 2, 4], "missing_lines": [5]}},
})


def _git(root: Path, *args: str):
    return subprocess.run(['git', *args], cwd=root, capture_output=True)


def _projeto(root: Path) -> None:
    """Projeto versionado, com spec, teste marcado e uma mudança na árvore."""
    spec = root / '.sentry' / 'specs' / 'demo'
    spec.mkdir(parents=True)
    (spec / 'CASES.md').write_text(CASES, encoding='utf-8')
    (root / 'tests').mkdir()
    (root / 'app.py').write_text(APP, encoding='utf-8')
    (root / 'tests' / 'test_app.py').write_text(TESTE, encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        _git(root, *args)
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'base')
    (root / 'app.py').write_text(APP + "\n\ndef dobrar(a):\n    return a * 2\n", encoding='utf-8')


def _suite_instrumentada(monkeypatch) -> list[Path]:
    """Substitui a execução da suíte por uma que apenas registra que subiu.

    O que se cobra aqui é a decisão de reusar, não o pytest: contar chamadas é a
    prova direta de que a suíte não rodou outra vez, e ainda deixa o teste em
    milissegundos em vez dos 24,6 s que motivaram o cache.
    """
    chamadas: list[Path] = []

    def executar(self, coverage_file: Path, timeout_seconds: int = 300):
        chamadas.append(coverage_file)
        coverage_file.parent.mkdir(parents=True, exist_ok=True)
        coverage_file.write_text(COBERTURA, encoding='utf-8')
        # Importados pelo modulo: `from ... import TestExecution` faria o pytest
        # tentar coletar as classes `Test*` deste arquivo e avisar a cada execucao.
        return inputs.TestExecution('pytest', passed=2, output='2 passed',
                                    status=models.TestStatus.COVERED, duration_seconds=24.6), 87.5

    monkeypatch.setattr(SuiteAdapter, 'run', executar)
    return chamadas


def _mudanca() -> GitChange:
    return GitChange('c0ffee', 'HEAD', ('app.py',), statuses={'app.py': 'M'},
                     changed_lines={'app.py': (1,)})


def _execucao_completa(input_hash: str) -> dict:
    """Uma execução registrada que rodou a suíte de verdade, com o hash gravado."""
    return {'contract_version': '1.0', 'data': {
        'id': 'r1', 'project': 'demo', 'timestamp': '2026-09-01T12:00:00+00:00',
        'configuration': {'run_tests': True, 'from_cache': False, 'input_hash': input_hash,
                          'test_execution': {'command': 'pytest', 'passed': 2,
                                             'infrastructure_error': None}}}}


# cenario: segunda execucao completa sem mudanca volta do cache
def test_segunda_execucao_completa_sem_mudanca_volta_do_cache(tmp_path: Path, monkeypatch):
    """A segunda análise não pode ser uma segunda maneira de avaliar a mesma
    mudança: o veredito e os números têm de ser os mesmos, só sem pagar a suíte."""
    _projeto(tmp_path)
    chamadas = _suite_instrumentada(monkeypatch)

    primeira = analyze(tmp_path, run_tests=True)
    assert len(chamadas) == 1
    assert primeira.configuration['from_cache'] is False
    assert primeira.configuration['cached_from'] is None

    segunda = analyze(tmp_path, run_tests=True)

    assert len(chamadas) == 1  # a suite nao subiu de novo
    assert segunda.configuration['from_cache'] is True
    assert segunda.configuration['cached_from'] == {'run_id': primeira.id, 'timestamp': primeira.timestamp}
    assert segunda.configuration['input_hash'] == primeira.configuration['input_hash']
    assert segunda.verdict.status == primeira.verdict.status
    assert segunda.configuration['test_execution'] == primeira.configuration['test_execution']
    assert segunda.configuration['coverage']['changed_percent'] == primeira.configuration['coverage']['changed_percent']
    # A cobertura tambem nao foi medida agora: veio do artefato da primeira.
    assert segunda.configuration['coverage']['reused_from']['run_id'] == primeira.id


# cenario: mudanca em arquivo de codigo invalida o cache
def test_mudanca_em_arquivo_de_codigo_invalida_o_cache(tmp_path: Path):
    (tmp_path / 'app.py').write_text('x = 1\n', encoding='utf-8')
    antes = input_fingerprint(tmp_path, _mudanca())

    (tmp_path / 'app.py').write_text('x = 2\n', encoding='utf-8')
    depois = input_fingerprint(tmp_path, _mudanca())

    assert antes != depois
    # E o hash diferente e' o que manda a suite rodar: a execucao gravada com o
    # hash antigo descreve outro codigo e nao pode ser reusada.
    assert cached_run([_execucao_completa(antes)], depois, _mudanca()) is None
    assert cached_run([_execucao_completa(antes)], antes, _mudanca()) is not None


# cenario: mudanca em arquivo de teste invalida o cache
def test_mudanca_em_arquivo_de_teste_invalida_o_cache(tmp_path: Path):
    """Sem nenhum arquivo no diff, só a perna dos testes pode diferir — é assim
    que se prova que o conteúdo do teste entra no hash, e não o diff que o
    acompanharia num projeto versionado."""
    sem_diff = GitChange('c0ffee', 'HEAD', ())
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests' / 'test_app.py').write_text(TESTE, encoding='utf-8')
    antes = input_fingerprint(tmp_path, sem_diff, ('tests',))

    (tmp_path / 'tests' / 'test_app.py').write_text(TESTE + "\n\ndef test_novo():\n    assert True\n",
                                                    encoding='utf-8')
    depois = input_fingerprint(tmp_path, sem_diff, ('tests',))

    assert antes != depois
    assert cached_run([_execucao_completa(antes)], depois, _mudanca()) is None


# cenario: mudanca na spec invalida o cache
def test_mudanca_na_spec_invalida_o_cache(tmp_path: Path):
    """Mudou o que se cobra da mudança, mesmo com código e teste intactos: a
    execução anterior respondeu a outra pergunta."""
    sem_diff = GitChange('c0ffee', 'HEAD', ())
    spec = tmp_path / '.sentry' / 'specs' / 'demo' / 'CASES.md'
    spec.parent.mkdir(parents=True)
    spec.write_text(CASES, encoding='utf-8')
    antes = input_fingerprint(tmp_path, sem_diff, spec_paths=(spec,))

    spec.write_text(CASES.replace('- **Prioridade:** alta', '- **Prioridade:** crítica'), encoding='utf-8')
    depois = input_fingerprint(tmp_path, sem_diff, spec_paths=(spec,))

    assert antes != depois
    assert cached_run([_execucao_completa(antes)], depois, _mudanca()) is None


def test_spec_fora_da_raiz_ainda_entra_no_fingerprint(tmp_path: Path):
    """Uma spec compartilhada por caminho absoluto fora do projeto não pode
    quebrar o hash: ela ainda decide se o cache serve, só rotulada pelo caminho
    absoluto em vez do relativo."""
    fora_da_raiz = tmp_path.parent / f"{tmp_path.name}-spec-externa"
    fora_da_raiz.mkdir()
    spec = fora_da_raiz / 'CASES.md'
    spec.write_text(CASES, encoding='utf-8')

    antes = input_fingerprint(tmp_path, _mudanca(), spec_paths=(spec,))
    spec.write_text(CASES.replace('- **Prioridade:** alta', '- **Prioridade:** crítica'), encoding='utf-8')
    depois = input_fingerprint(tmp_path, _mudanca(), spec_paths=(spec,))

    assert antes != depois


# cenario: sem execucao anterior nao ha cache a reusar
def test_sem_execucao_anterior_nao_ha_cache_a_reusar(tmp_path: Path, monkeypatch):
    """Inventar acerto onde não há evidência a reusar seria pior que repetir a
    suíte. Histórico vazio, e histórico só com execuções que não rodaram a suíte,
    dão no mesmo: não há o que reaproveitar."""
    fingerprint = input_fingerprint(tmp_path, _mudanca())
    assert cached_run([], fingerprint, _mudanca()) is None
    instantanea = {'contract_version': '1.0', 'data': {
        'id': 'r0', 'timestamp': '2026-09-01T12:00:00+00:00',
        'configuration': {'run_tests': False, 'input_hash': fingerprint}}}
    assert cached_run([instantanea], fingerprint, _mudanca()) is None

    _projeto(tmp_path)
    chamadas = _suite_instrumentada(monkeypatch)
    run = analyze(tmp_path, run_tests=True)

    assert len(chamadas) == 1  # a suite foi executada
    assert run.configuration['from_cache'] is False
    assert run.configuration['cached_from'] is None
