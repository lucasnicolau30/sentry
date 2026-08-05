from __future__ import annotations
import json, sqlite3, subprocess, sys, uuid
from pathlib import Path
from ..adapters.markdown_specs import MarkdownSpecAdapter
from ..domain.models import Run, TestStatus, to_json
from ..domain.rules import EvaluationContext, evaluate
from ..init_project import initialize_project

def select_spec(root:Path,slug:str|None)->Path:
    base=root/'.draun'/'specs'
    if slug:
        path=base/slug/'SPEC.md'
        if not path.exists(): raise FileNotFoundError(f'SPEC não encontrada: {slug}')
        return path
    candidates=[p/'SPEC.md' for p in base.iterdir() if (p/'SPEC.md').exists()] if base.exists() else []
    if len(candidates)!=1: raise ValueError('informe --spec quando houver zero ou várias specs')
    return candidates[0]

def _run_tests(root:Path,run_id:str):
    coverage_file=root/'.sentry'/'runs'/f'{run_id}-coverage.json'
    command=[sys.executable,'-m','coverage','run','-m','pytest']
    try:
        result=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=300)
    except (FileNotFoundError,subprocess.TimeoutExpired) as error:
        return (type('T',(),{'status':TestStatus.NOT_RUN})(),None,str(error))
    subprocess.run([sys.executable,'-m','coverage','json','-o',str(coverage_file)],cwd=root,text=True,capture_output=True)
    percent=None
    if coverage_file.exists():
        data=json.loads(coverage_file.read_text(encoding='utf8')); percent=data.get('totals',{}).get('percent_covered')
    status=TestStatus.COVERED if result.returncode==0 else TestStatus.FAILED
    return (type('T',(),{'status':status})(),percent,None)

def analyze(root:Path,slug:str|None=None,run_tests:bool=False)->Run:
    initialize_project(root); spec=select_spec(root,slug); MarkdownSpecAdapter(spec).scenarios(); tests=(); coverage=None
    if run_tests:
        test,coverage,_=_run_tests(root,'pending'); tests=(test,)
    _,verdict=evaluate(EvaluationContext(tests=tests,changed_files=(str(spec),),changed_coverage=coverage,coverage_available=coverage is not None))
    run=Run(str(uuid.uuid4()),root.name,None,None,configuration={'spec':spec.parent.name,'run_tests':run_tests},verdict=verdict)
    if run_tests:
        test,coverage,_=_run_tests(root,run.id); _,verdict=evaluate(EvaluationContext(tests=(test,),changed_files=(str(spec),),changed_coverage=coverage,coverage_available=coverage is not None)); run=Run(run.id,run.project,run.commit,run.reference,run.timestamp,run.configuration,verdict=verdict)
    with sqlite3.connect(root/'.sentry'/'sentry.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)'); conn.execute('INSERT INTO runs VALUES (?,?)',(run.id,to_json(run)))
    (root/'.sentry'/'runs'/f'{run.id}.json').write_text(to_json(run),encoding='utf8'); return run