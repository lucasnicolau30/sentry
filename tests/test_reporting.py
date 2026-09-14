import json
from pathlib import Path
from sentrytest.application.reporting import compare, markdown_report, staleness

def payload(run_id, rules):
    return {'data': {'id':run_id,'project':'demo','verdict':{'status':'inconclusivo'},'findings':[{'rule':r,'severity':'alta','message':r,'recommendation':'corrigir'} for r in rules]}}

def test_markdown_and_comparison():
    report=markdown_report(payload('r1',['a']))
    assert '# Sentry Report' in report
    result = compare(payload('r1',['a']),payload('r2',['b']))
    assert result['new']==['b'] and result['resolved']==['a'] and result['persistent']==[]
    assert result['comparable'] is True
    assert result['verdict']=={'from':'inconclusivo','to':'inconclusivo','changed':False}

def run_payload(run_id, run_tests, global_percent=None, changed_percent=None, coverage_error=None, passed=0, failed=0, verdict='inconclusivo'):
    return {'data': {
        'id': run_id, 'project': 'demo', 'verdict': {'status': verdict}, 'findings': [],
        'configuration': {
            'run_tests': run_tests,
            'coverage': {'global_percent': global_percent, 'changed_percent': changed_percent, 'error': coverage_error},
            'test_execution': {'passed': passed, 'failed': failed, 'skipped': 0, 'not_run': 0},
        },
    }}

def test_compare_reports_coverage_and_test_deltas():
    first = run_payload('r1', True, global_percent=80.0, changed_percent=70.0, passed=10, failed=2)
    second = run_payload('r2', True, global_percent=85.0, changed_percent=90.0, passed=12, failed=0, verdict='aprovado')
    result = compare(first, second)
    assert result['comparable'] is True
    assert result['coverage'] == {'global_percent_delta': 5.0, 'changed_percent_delta': 20.0}
    assert result['tests']['passed_delta'] == 2 and result['tests']['failed_delta'] == -2
    assert result['verdict'] == {'from': 'inconclusivo', 'to': 'aprovado', 'changed': True}

def test_compare_marks_incomparable_when_run_tests_differs():
    first = run_payload('r1', False)
    second = run_payload('r2', True, passed=5)
    result = compare(first, second)
    assert result['comparable'] is False
    assert result['coverage'] is None and result['tests'] is None
    assert 'execução de testes' in result['incomparable_reasons'][0]
# cenario: relatorio grava o commit analisado e o instante
def test_cabecalho_registra_commit_analisado_e_instante():
    """Sem o selo, `latest.md` se apresenta como veredito atual mesmo com commits
    de distancia -- e' o unico artefato versionado, e o que mais engana ao envelhecer."""
    data = payload('r1', [])['data']
    data['commit'] = 'a94b1fb0000000000000000000000000000000aa'
    data['timestamp'] = '2026-09-10T12:00:00+00:00'
    report = markdown_report({'data': data})
    assert '- Commit analisado: a94b1fb0000000000000000000000000000000aa' in report
    assert '- Analisado em: 2026-09-10T12:00:00+00:00' in report

# cenario: sem repositorio Git o relatorio nao inventa commit
def test_cabecalho_declara_commit_indisponivel_fora_de_repositorio_git():
    report = markdown_report(payload('r1', []))
    assert 'Commit analisado: indisponível (não é repositório Git)' in report
    assert staleness(payload('r1', []), None) is None

# cenario: report acusa relatorio de commit diferente do HEAD
def test_staleness_acusa_relatorio_de_outro_commit():
    data = payload('r1', [])['data']
    data['commit'] = 'a94b1fb0000000000000000000000000000000aa'
    aviso = staleness({'data': data}, 'deadbeef0000000000000000000000000000beef')
    assert aviso is not None
    assert 'a94b1fb00000' in aviso and 'deadbeef0000' in aviso
    assert 'desatualizado' in aviso

def test_staleness_cala_quando_o_commit_e_o_head_atual():
    data = payload('r1', [])['data']
    data['commit'] = 'a94b1fb0000000000000000000000000000000aa'
    assert staleness({'data': data}, 'a94b1fb0000000000000000000000000000000aa') is None
