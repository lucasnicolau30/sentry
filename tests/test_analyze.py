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