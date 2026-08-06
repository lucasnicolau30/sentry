from pathlib import Path
from sentry.application.analyze import analyze

def test_analyze_persists_run(tmp_path:Path):
    spec=tmp_path/'.draun'/'specs'/'demo'; spec.mkdir(parents=True); (spec/'SPEC.md').write_text('# Demo\n',encoding='utf8')
    run=analyze(tmp_path)
    assert run.verdict.status.value=='inconclusivo'
    assert (tmp_path/'.sentry'/'runs'/f'{run.id}.json').exists()

def test_analyze_requires_existing_explicit_spec(tmp_path:Path):
    try: analyze(tmp_path,'missing')
    except FileNotFoundError as error: assert 'não encontrada' in str(error)
    else: raise AssertionError('deveria falhar')

def test_analyze_runs_tests_once(tmp_path:Path):
    spec=tmp_path/'.draun'/'specs'/'demo'; spec.mkdir(parents=True); (spec/'SPEC.md').write_text('# Demo\n',encoding='utf8')
    (tmp_path/'tests').mkdir(); (tmp_path/'tests'/'test_ok.py').write_text('def test_ok():\n    assert 1 == 1\n',encoding='utf8'); (tmp_path/'conftest.py').write_text('',encoding='utf8')
    run=analyze(tmp_path,run_tests=True)
    runs_dir=tmp_path/'.sentry'/'runs'
    assert not (runs_dir/'pending-coverage.json').exists()
    assert (runs_dir/f'{run.id}-coverage.json').exists()
    assert run.configuration['test_execution']['passed']>=1