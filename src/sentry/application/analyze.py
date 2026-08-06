from __future__ import annotations
import sqlite3, uuid
from pathlib import Path
from ..adapters.markdown_specs import MarkdownSpecAdapter
from ..domain.models import Run, to_json
from ..domain.rules import EvaluationContext, evaluate
from ..init_project import initialize_project
from ..adapters.local_tools import LocalGitAdapter, PytestAdapter, CoverageAdapter
from ..adapters.toml_config import load_config
from .traceability import build_traceability
from .coverage_context import calculate_changed_coverage
from .impact import select_impacted_tests

def select_spec(root:Path,slug:str|None,specs_path:str='.draun/specs')->Path:
    base=root/specs_path
    if slug:
        path=base/slug/'SPEC.md'
        if not path.exists(): raise FileNotFoundError(f"SPEC não encontrada: {slug}")
        return path
    candidates=[p/'SPEC.md' for p in base.iterdir() if (p/'SPEC.md').exists()] if base.exists() else []
    if not candidates:
        raise ValueError(f"nenhuma spec do Draun encontrada em {base}; informe --spec <slug> após criar {specs_path}/<slug>/SPEC.md")
    if len(candidates)>1:
        slugs=', '.join(sorted(p.parent.name for p in candidates))
        raise ValueError(f"múltiplas specs encontradas ({slugs}); informe --spec <slug> para escolher qual analisar")
    return candidates[0]

def analyze(root:Path,slug:str|None=None,run_tests:bool|None=None)->Run:
    initialize_project(root)
    config=load_config(root)
    specs_path=config.get('draun',{}).get('specs_path','.draun/specs')
    pytest_command=config.get('pytest',{}).get('command','pytest')
    timeout_seconds=config.get('analysis',{}).get('timeout_seconds',300)
    if run_tests is None: run_tests=config.get('analysis',{}).get('run_tests_by_default',False)
    spec=select_spec(root,slug,specs_path); adapter=MarkdownSpecAdapter(spec); scenarios=adapter.scenarios(); behaviors=adapter.behaviors(); traceability=build_traceability(scenarios, root, behaviors); git_change=LocalGitAdapter(root).change(); impact=select_impacted_tests(root, git_change.files, run_tests); run_id=str(uuid.uuid4()); tests=(); test_execution=None; contextual=None
    if run_tests:
        coverage_file=root/'.sentry'/'runs'/f'{run_id}-coverage.json'
        test,_=PytestAdapter(root,pytest_command).run(coverage_file,timeout_seconds=timeout_seconds); tests=(test,); test_execution={'command':test.command,'passed':test.passed,'failed':test.failed,'skipped':test.skipped,'not_run':test.not_run,'duration_seconds':test.duration_seconds,'output':test.output,'infrastructure_error':test.infrastructure_error}; coverage_data=CoverageAdapter().read(coverage_file); contextual=calculate_changed_coverage(git_change,coverage_data)
    configuration={'spec':spec.parent.name,'run_tests':run_tests,'git_change':{'revision':git_change.revision,'reference':git_change.reference,'files':git_change.files,'statuses':git_change.statuses or {},'changed_lines':git_change.changed_lines or {},'error':git_change.error},'traceability':traceability,'impact':impact}
    if run_tests:
        configuration['test_execution']=test_execution; configuration['coverage']={'global_percent':contextual.global_percent,'changed_percent':contextual.changed_percent,'files':contextual.files,'error':contextual.error}
    findings,verdict=evaluate(EvaluationContext(tests=tests,changed_files=git_change.files if run_tests else (str(spec),),changed_coverage=contextual.changed_percent if run_tests else None,coverage_available=contextual.error is None if run_tests else False,requirements_without_scenarios=tuple(traceability['requirements_without_scenarios']),scenarios_without_tests=tuple(traceability['scenarios_without_tests'])))
    run=Run(run_id,root.name,None,None,configuration=configuration,findings=findings,verdict=verdict)
    with sqlite3.connect(root/'.sentry'/'sentry.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)'); conn.execute('INSERT INTO runs VALUES (?,?)',(run.id,to_json(run)))
    (root/'.sentry'/'runs'/f'{run.id}.json').write_text(to_json(run),encoding='utf8'); return run
