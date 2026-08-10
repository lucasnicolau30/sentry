from __future__ import annotations
import sqlite3, uuid
from dataclasses import replace
from pathlib import Path
from ..adapters.case_specs import CaseDocument, CaseSpecAdapter, validate_document
from ..domain.models import InfrastructureError, Run, Severity, to_json
from ..domain.rules import EvaluationContext, Thresholds, evaluate
from ..domain.catalog import merge_catalog, missing_classes, unknown_field_types
from ..init_project import initialize_project
from ..adapters.local_tools import LocalGitAdapter, SuiteAdapter, CoverageAdapter
from ..adapters.toml_config import load_config
from ..ports.inputs import GitChange, SpecScenario
from .cases import build_test_cases, summarize
from .traceability import DEFAULT_TEST_PATHS, build_traceability
from .coverage_context import calculate_changed_coverage
from .impact import SOURCE_EXTENSIONS, select_impacted_tests
from .error_paths import select_error_paths
from .dimensions import evaluate_dimensions

CASES_PATH='.sentry/specs'

def _select(root:Path,slug:str|None,specs_path:str,filename:str)->Path|None:
    base=root/specs_path
    if slug:
        # O slug vem da linha de comando e vira caminho: sem resolver e conferir
        # o containment, `../..` sobe para fora de specs_path e um caminho
        # absoluto descarta a base inteira, lendo arquivo arbitrario do disco.
        resolved_base=base.resolve()
        path=(base/slug/filename).resolve()
        if not path.is_relative_to(resolved_base):
            raise ValueError(f"slug inválido: {slug!r} aponta para fora de {specs_path}")
        return path if path.exists() else None
    candidates=[p/filename for p in base.iterdir() if (p/filename).exists()] if base.exists() else []
    if not candidates: return None
    if len(candidates)>1:
        slugs=', '.join(sorted(p.parent.name for p in candidates))
        raise ValueError(f"múltiplas specs encontradas ({slugs}); informe --spec <slug> para escolher qual analisar")
    return candidates[0]

def is_all_spec(slug:str|None)->bool:
    return (slug or "").strip().casefold()=="all"

def spec_documents(root:Path,specs_path:str=CASES_PATH)->list[tuple[str,Path]]:
    """Toda pasta com CASES.md em specs_path, para --spec all."""
    base=root/specs_path
    if not base.exists(): return []
    return sorted((p.name,p/'CASES.md') for p in base.iterdir() if (p/'CASES.md').exists())

def merge_documents(entries:list[tuple[str,CaseDocument]])->CaseDocument:
    """Junta todas as specs num documento so, para --spec all rodar o mesmo pipeline
    de uma spec so. Caso duplicado entre specs diferentes ainda vira erro estrutural
    (validate_document), porque --spec all exige nome de caso unico no conjunto."""
    fields=[]; seen_fields=set(); cases=[]; not_applicable=[]; sections=[]
    for slug,document in entries:
        sections.append(f"### {document.title or slug}\n\n{document.prompt}")
        for spec_field in document.fields:
            key=(spec_field.name,spec_field.type)
            if key not in seen_fields: seen_fields.add(key); fields.append(spec_field)
        cases.extend(document.cases)
        not_applicable.extend(document.not_applicable)
    return CaseDocument(title=f"Todas as specs ({len(entries)})",prompt="\n\n".join(sections),fields=tuple(fields),cases=tuple(cases),not_applicable=tuple(not_applicable))

def select_spec(root:Path,slug:str|None,specs_path:str=CASES_PATH)->Path:
    """Resolve a matriz de casos a analisar."""
    cases=_select(root,slug,specs_path,'CASES.md')
    if cases: return cases
    if slug:
        raise FileNotFoundError(f"spec não encontrada: {slug}; esperado {specs_path}/{slug}/CASES.md")
    raise ValueError(f"nenhuma matriz de casos encontrada em {root/specs_path}; crie uma com `sentry new <nome>` e preencha o CASES.md")

def _severity_policy(config:dict)->dict:
    """Severidades declaradas em [policy.severities] do sentry.toml."""
    declared=(config.get('policy') or {}).get('severities') or {}
    policy={}
    for rule,level in declared.items():
        try: policy[rule]=Severity(str(level))
        except ValueError: continue
    return policy

def _thresholds(config:dict)->Thresholds:
    """Limiares numéricos declarados em [policy.thresholds] do sentry.toml."""
    declared=(config.get('policy') or {}).get('thresholds') or {}
    def number(key):
        value=declared.get(key)
        return float(value) if isinstance(value,(int,float)) else None
    return Thresholds(number('changed_coverage'),number('global_coverage'))

def _exclusions(config:dict)->tuple[str,...]:
    """Diretórios/arquivos fora do escopo da análise, declarados em [analysis.exclude]."""
    return tuple(config.get('analysis',{}).get('exclude') or ())

def _is_excluded(path:str,patterns:tuple[str,...])->bool:
    normalized=path.replace('\\','/')
    return any(normalized==p.rstrip('/') or normalized.startswith(p.rstrip('/')+'/') for p in patterns)

def _apply_exclusions(change:GitChange,patterns:tuple[str,...])->GitChange:
    """Remove do diff arquivos fora do escopo (ex.: frontend/ num monorepo) antes de
    impacto e cobertura os tratarem como código-fonte alterado."""
    if not patterns or change.error: return change
    statuses={name:value for name,value in (change.statuses or {}).items() if not _is_excluded(name,patterns)}
    changed_lines={name:lines for name,lines in (change.changed_lines or {}).items() if not _is_excluded(name,patterns)}
    return replace(change,files=tuple(statuses),statuses=statuses,changed_lines=changed_lines)

def _infrastructure_errors(execution,coverage,runner:str='pytest',coverage_format:str='coverage.py')->tuple[InfrastructureError,...]:
    """Falhas de ambiente detectadas pelos adapters, separadas de falha de qualidade.

    A causa carrega a ferramenta realmente usada: dizer 'pytest' num projeto que
    roda jest mandaria o usuario depurar a ferramenta errada."""
    errors=[]
    if execution is not None and execution.infrastructure_error:
        # Timeout e comando ausente sao transitorios; erro de uso ou suite vazia nao.
        retryable='timed out' in execution.infrastructure_error.lower() or 'interrompida' in execution.infrastructure_error
        errors.append(InfrastructureError('execucao de testes',runner,execution.infrastructure_error,retryable))
    if coverage is not None and coverage.error:
        errors.append(InfrastructureError('leitura de cobertura',coverage_format,coverage.error,False))
    return tuple(errors)

def analyze(root:Path,slug:str|None=None,run_tests:bool|None=None)->Run:
    initialize_project(root)
    config=load_config(root)
    # [test] e' a secao atual; [pytest] continua aceita para nao quebrar
    # sentry.toml ja existentes.
    test_config={**config.get('pytest',{}),**config.get('test',{})}
    test_command=test_config.get('command','pytest')
    junit_xml=test_config.get('junit_xml')
    timeout_seconds=config.get('analysis',{}).get('timeout_seconds',300)
    if run_tests is None: run_tests=config.get('analysis',{}).get('run_tests_by_default',False)
    cases_path=config.get('specs',{}).get('path',CASES_PATH)
    if is_all_spec(slug):
        entries=spec_documents(root,cases_path)
        if not entries: raise ValueError(f"nenhuma matriz de casos encontrada em {root/cases_path}; crie uma com `sentry new <nome>` e preencha o CASES.md")
        document=merge_documents([(name,CaseSpecAdapter(path).document()) for name,path in entries])
        spec_label='all ('+', '.join(name for name,_ in entries)+')'
    else:
        spec=select_spec(root,slug,cases_path)
        document=CaseSpecAdapter(spec).document()
        spec_label=spec.parent.name
    catalog_limitations=[]; justified_classes=[]
    case_errors=tuple(validate_document(document))
    scenarios=tuple(SpecScenario(c.name,c.given,c.when,c.then) for c in document.cases)
    catalog=merge_catalog(config.get('catalog',{}).get('fields'))
    missing_classes_found=missing_classes(document.fields,document.cases,catalog,document.not_applicable)
    unknown=unknown_field_types(document.fields,catalog)
    if unknown: catalog_limitations.append(f"tipos de campo fora do catálogo, sem cobrança de classes: {', '.join(unknown)}")
    # Separado de catalog_limitations: isto e' uma dispensa deliberada e justificada,
    # nao uma lacuna do Sentry -- misturar os dois no relatorio confunde "o Sentry
    # nao sabe verificar" com "o time decidiu, com motivo, que nao se aplica aqui".
    for item in document.not_applicable:
        justified_classes.append(f"{item.field}/{item.class_name} — {item.reason}")
    # O vínculo requisito->caso é declarado no CASES.md, então não há o que inferir
    # por semelhança de nome: build_traceability só precisa casar caso com teste.
    traceability=build_traceability(scenarios, root, test_paths=tuple(config.get('tests',{}).get('paths') or DEFAULT_TEST_PATHS)); git_change=_apply_exclusions(LocalGitAdapter(root).change(),_exclusions(config)); impact=select_impacted_tests(root, git_change.files, run_tests); run_id=str(uuid.uuid4()); tests=(); test_execution=None; contextual=None
    if run_tests:
        # O SuiteAdapter sempre grava seu proprio relatorio aqui; com
        # [coverage] path declarado, quem gera o que vale e' a suite do projeto
        # (nyc, JaCoCo, coverlet...) e o Sentry so le do caminho declarado.
        generated=root/'.sentry'/'runs'/f'{run_id}-coverage.json'
        declared=config.get('coverage',{}).get('path')
        test,_=SuiteAdapter(root,test_command,junit_xml).run(generated,timeout_seconds=timeout_seconds); tests=(test,); test_execution={'command':test.command,'passed':test.passed,'failed':test.failed,'skipped':test.skipped,'not_run':test.not_run,'duration_seconds':test.duration_seconds,'output':test.output,'infrastructure_error':test.infrastructure_error}
        coverage_data=CoverageAdapter().read((root/declared) if declared else generated,config.get('coverage',{}).get('format'),root); contextual=calculate_changed_coverage(git_change,coverage_data)
    suite_failed=bool(tests and tests[0].failed)
    test_cases=build_test_cases(document,traceability,run_tests,suite_failed) if document else ()
    # Sem --run-tests nao ha cobertura, entao a regra nao pode afirmar ausencia de
    # teste: select_error_paths devolve limitacao em vez de achado.
    error_paths=select_error_paths(root,git_change.changed_lines,contextual.executed_lines if run_tests and contextual else None,contextual.excluded_lines if run_tests and contextual else None)
    configuration={'spec':spec_label,'run_tests':run_tests,'git_change':{'revision':git_change.revision,'reference':git_change.reference,'files':git_change.files,'statuses':git_change.statuses or {},'changed_lines':git_change.changed_lines or {},'error':git_change.error},'traceability':traceability,'impact':impact,'error_paths':error_paths,'cases':summarize(test_cases),'catalog_limitations':catalog_limitations,'justified_classes':justified_classes}
    disabled=tuple(config.get('dimensions',{}).get('disabled') or ())
    configuration['dimensions']=list(evaluate_dimensions(traceability,test_cases,error_paths,document.fields,missing_classes_found,disabled))
    if run_tests:
        configuration['test_execution']=test_execution; configuration['coverage']={'global_percent':contextual.global_percent,'changed_percent':contextual.changed_percent,'files':contextual.files,'error':contextual.error}
    severities=_severity_policy(config)
    if severities: configuration['severity_policy']={rule:level.value for rule,level in severities.items()}
    thresholds=_thresholds(config)
    # A SPEC exige registrar a politica efetivamente aplicada, nao so o resultado.
    if thresholds.changed_coverage is not None or thresholds.global_coverage is not None:
        configuration['thresholds']={'changed_coverage':thresholds.changed_coverage,'global_coverage':thresholds.global_coverage}
    infrastructure=_infrastructure_errors(tests[0] if tests else None,contextual if run_tests else None,test_command,config.get('coverage',{}).get('format') or 'coverage.py')
    if infrastructure: configuration['infrastructure_errors']=[{'stage':e.stage,'cause':e.cause,'message':e.message,'retryable':e.retryable} for e in infrastructure]
    # Um diff so de documentacao/configuracao nao tem cobertura a calcular: sem
    # isto, `coverage-missing` acusa falha onde nao havia nada a medir.
    measurable=any(Path(name).suffix.lower() in SOURCE_EXTENSIONS for name in git_change.files)
    findings,verdict=evaluate(EvaluationContext(tests=tests,has_measurable_change=measurable,changed_files=git_change.files if run_tests else (spec_label,),changed_coverage=contextual.changed_percent if run_tests else None,coverage_available=contextual.error is None if run_tests else False,requirements_without_scenarios=tuple(traceability['requirements_without_scenarios']),scenarios_without_tests=tuple(traceability['scenarios_without_tests']),error_paths_without_tests=error_paths['uncovered'],missing_equivalence_classes=missing_classes_found,case_spec_errors=case_errors,infrastructure_errors=tuple(e.message for e in infrastructure),global_coverage=contextual.global_percent if run_tests and contextual else None,thresholds=thresholds),severities)
    # `[project] name` era decorativo: o relatorio sempre usava o nome do
    # diretorio. Uma chave de configuracao que nao faz nada e' pior que chave
    # nenhuma -- agora ela vale, com o diretorio como fallback.
    project_name=config.get('project',{}).get('name') or root.name
    run=Run(run_id,project_name,None,None,configuration=configuration,test_cases=test_cases,findings=findings,verdict=verdict,infrastructure_errors=infrastructure)
    with sqlite3.connect(root/'.sentry'/'sentry.db') as conn:
        conn.execute('INSERT INTO runs VALUES (?,?)',(run.id,to_json(run)))
    (root/'.sentry'/'runs'/f'{run.id}.json').write_text(to_json(run),encoding='utf-8'); return run
