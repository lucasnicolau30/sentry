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
from .reporting import load_runs
from .reuse import COMPLETE, INSTANT, cached_execution, cached_run, input_fingerprint, provenance, reused_coverage
from .traceability import DEFAULT_TEST_PATHS, TEST_DEFINITIONS, build_traceability, collect_test_files
from .frontend_evidence import evidence_by_case
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

def _coverage_lines(contextual,changed_lines:dict|None)->dict:
    """As linhas medidas e executadas, so dos arquivos que a mudanca tocou.

    Quem consome isto (`sentry context`) precisa das faixas descobertas para apontar
    onde falta teste, e sem as linhas ele devolveria lista vazia -- um "nada falta"
    falso, que e' pior que nao responder. O recorte pelo diff e' o que torna o dado
    barato: o projeto inteiro seriam centenas de KB gravados a cada execucao, e
    nenhuma linha fora da mudanca participa da decisao."""
    changed=set(changed_lines or {})
    return {'executed_lines':{name:lines for name,lines in (contextual.executed_lines or {}).items() if name in changed},
            'measured_lines':{name:lines for name,lines in (contextual.measured_lines or {}).items() if name in changed}}

def _execution_payload(test)->dict:
    """A contagem publicada no relatorio. Igual para a suite recem-executada e para a
    que voltou do cache: o que muda entre as duas e' a procedencia declarada ao lado,
    nunca o formato -- um relatorio que descrevesse a execucao reusada noutro formato
    convidaria quem le a trata-la como outra coisa."""
    return {'command':test.command,'passed':test.passed,'failed':test.failed,'skipped':test.skipped,'not_run':test.not_run,'duration_seconds':test.duration_seconds,'output':test.output,'infrastructure_error':test.infrastructure_error}

def analyze(root:Path,slug:str|None=None,run_tests:bool|None=None,base:str|None=None,whole_project:bool=False)->Run:
    # Dois modos por desenho, e nao tres: `run_tests` falso *e'* o modo instantaneo.
    # Um parametro novo criaria a combinacao "nao executa a suite e tambem nao
    # reaproveita a ultima medicao", que nao e' modo nenhum -- so uma analise pior que
    # ninguem pediu. Quem chama continua dizendo apenas se quer a suite executada.
    #
    # `whole_project` e' `sentry status`: o mesmo pipeline, mas com um GitChange
    # sintetico que trata todo arquivo de codigo-fonte como alterado, em vez do diff
    # real. Sem cobertura nenhuma nao ha o que reportar sobre o projeto inteiro, entao
    # aqui `run_tests` nao e' escolha de quem chama -- e sempre True.
    if whole_project: slug='all'; run_tests=True
    initialize_project(root)
    config=load_config(root)
    # [test] e' a secao atual; [pytest] continua aceita para nao quebrar
    # sentry.toml ja existentes.
    test_config={**config.get('pytest',{}),**config.get('test',{})}
    test_command=test_config.get('command','pytest')
    junit_xml=test_config.get('junit_xml')
    timeout_seconds=config.get('analysis',{}).get('timeout_seconds',300)
    # [e2e] e' opcional e independente do [test] backend: projeto sem frontend
    # nenhum simplesmente nao declara a secao, e a segunda suite nunca roda.
    e2e_config=config.get('e2e',{})
    e2e_command=e2e_config.get('command')
    e2e_junit=e2e_config.get('junit_xml')
    if run_tests is None: run_tests=config.get('analysis',{}).get('run_tests_by_default',False)
    cases_path=config.get('specs',{}).get('path',CASES_PATH)
    if is_all_spec(slug):
        entries=spec_documents(root,cases_path)
        if not entries: raise ValueError(f"nenhuma matriz de casos encontrada em {root/cases_path}; crie uma com `sentry new <nome>` e preencha o CASES.md")
        document=merge_documents([(name,CaseSpecAdapter(path).document()) for name,path in entries])
        spec_label='all ('+', '.join(name for name,_ in entries)+')'
    else:
        # Sem `--spec` e sem nenhum CASES.md no disco, o Sentry deixa de exigir
        # spec e mede o que nao depende dela: cobertura do alterado, caminhos de
        # erro, testes falhando e testes impactados. A spec e' o teto do produto
        # (requisito rastreado, cenario ligado a teste, classe cobrada), nao o piso
        # -- exigi-la antes de entregar qualquer coisa fazia a analise de uma
        # mudanca nao pre-especificada valer zero.
        #
        # `--spec all` e um slug explicito continuam sendo erro: ali o pedido e'
        # nomeado e a realidade nao corresponde, o que e' diferente de nao haver
        # intencao declarada. E' o que mantem a auto-analise honesta no CI.
        spec=_select(root,slug,cases_path,'CASES.md') if slug is None else select_spec(root,slug,cases_path)
        if spec is None:
            document=CaseDocument(title='',prompt='')
            spec_label=None
        else:
            document=CaseSpecAdapter(spec).document()
            spec_label=spec.parent.name
    # Nenhuma intencao declarada: as regras e dimensoes que dependem de spec precisam
    # saber disso para se calarem com justificativa, em vez de afirmarem cobertura.
    without_spec=spec_label is None
    catalog_limitations=[]; justified_classes=[]
    # Sem spec nao ha documento a validar: validar o documento vazio acusava titulo
    # ausente, prompt ausente e nenhum caso declarado -- tres achados criticos que
    # reprovavam a mudanca por nao existir uma spec que ninguem prometeu escrever.
    case_errors=() if without_spec else tuple(validate_document(document))
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
    # O mesmo `[tests] paths` alimenta a matriz e o impacto: sao duas leituras da
    # mesma mudanca e discordar sobre quais arquivos existem contradizia o relatorio.
    declared_test_paths=tuple(config.get('tests',{}).get('paths') or DEFAULT_TEST_PATHS)
    # Casos declarados no projeto inteiro, para julgar marcador orfao. Analisar uma
    # spec so nao pode acusar de orfao o marcador que pertence a outra: o diretorio de
    # testes e' um so e atende todas elas.
    declared_names=None if without_spec else tuple(
        case.name for _,path in spec_documents(root,cases_path) for case in CaseSpecAdapter(path).document().cases) or None
    declared_base=base or config.get('analysis',{}).get('base')
    raw_change=LocalGitAdapter(root).whole_tree(SOURCE_EXTENSIONS) if whole_project else LocalGitAdapter(root).change(declared_base)
    git_change=_apply_exclusions(raw_change,_exclusions(config))
    # O diff precisa vir antes da rastreabilidade: e' dele que saem as linhas de teste
    # que a mudanca tocou, e so um marcador escrito numa delas e' achado desta analise.
    changed_test_lines={name:lines for name,lines in (git_change.changed_lines or {}).items() if Path(name).suffix.lower() in TEST_DEFINITIONS}
    traceability=build_traceability(scenarios, root, test_paths=declared_test_paths, declared_names=declared_names, changed_test_lines=changed_test_lines); impact=select_impacted_tests(root, git_change.files, run_tests, test_paths=declared_test_paths); run_id=str(uuid.uuid4()); tests=(); test_execution=None; contextual=None
    history=load_runs(root)
    # O hash e' calculado nos dois modos: no completo ele decide se a suite roda, e no
    # instantaneo ele fica gravado dizendo sobre qual entrada esta analise falou -- e' o
    # que a proxima execucao completa compara. Calcula-lo so quando serve para decidir
    # deixaria buracos no historico exatamente onde o loop de digitacao escreve mais.
    fingerprint=input_fingerprint(root,git_change,declared_test_paths,tuple(path for _,path in spec_documents(root,cases_path)))
    # `status` nunca volta do cache: ele existe para ser a medicao autoritativa do
    # projeto inteiro, e um acerto de cache seria uma segunda maneira de responder a
    # mesma pergunta -- exatamente o que a Fase 3 evitou para `run`/`review`.
    cached=cached_run(history,fingerprint,git_change) if run_tests and not whole_project else None
    if cached is not None:
        # Reaproveita a execucao inteira, nao so o veredito: a cobertura vem do mesmo
        # artefato que a execucao original leu, entao caminhos de erro, dimensoes e
        # regras decidem sobre a mesma evidencia. O cache so pode mudar o tempo -- se
        # mudasse o resultado, seria uma segunda maneira de avaliar a mesma mudanca.
        test=cached_execution(cached); tests=(test,); test_execution=_execution_payload(test)
        declared=config.get('coverage',{}).get('path')
        coverage_data=CoverageAdapter().read((root/declared) if declared else root/'.sentry'/'runs'/f"{provenance(cached)['run_id']}-coverage.json",config.get('coverage',{}).get('format'),root); contextual=calculate_changed_coverage(git_change,coverage_data)
    elif run_tests:
        # O SuiteAdapter sempre grava seu proprio relatorio aqui; com
        # [coverage] path declarado, quem gera o que vale e' a suite do projeto
        # (nyc, JaCoCo, coverlet...) e o Sentry so le do caminho declarado.
        generated=root/'.sentry'/'runs'/f'{run_id}-coverage.json'
        declared=config.get('coverage',{}).get('path')
        test,_=SuiteAdapter(root,test_command,junit_xml).run(generated,timeout_seconds=timeout_seconds); tests=(test,); test_execution=_execution_payload(test)
        coverage_data=CoverageAdapter().read((root/declared) if declared else generated,config.get('coverage',{}).get('format'),root); contextual=calculate_changed_coverage(git_change,coverage_data)
    suite_failed=bool(tests and tests[0].failed)
    # Segunda suite, sem cache: cobertura de linha nao existe para ela, entao nao
    # ha o que o hash de conteudo decidiria reaproveitar alem do tempo -- e o
    # tempo nao e' o que o cache do backend existe para economizar aqui.
    e2e_test=None; e2e_evidence={}
    if run_tests and e2e_command:
        e2e_test,_=SuiteAdapter(root,e2e_command,e2e_junit,cwd=e2e_config.get('cwd')).run(
            root/'.sentry'/'runs'/f'{run_id}-e2e-coverage.json',
            timeout_seconds=e2e_config.get('timeout_seconds',timeout_seconds))
        tests=(*tests,e2e_test)
        if e2e_junit:
            e2e_paths=collect_test_files(root,tuple(e2e_config.get('paths') or ()))
            e2e_evidence=evidence_by_case(root/e2e_junit,e2e_paths)
    e2e_failed=bool(e2e_test and e2e_test.failed)
    test_cases=build_test_cases(document,traceability,run_tests,suite_failed,e2e_failed,e2e_evidence) if document else ()
    # Sem --run-tests nao ha cobertura, entao a regra nao pode afirmar ausencia de
    # teste: select_error_paths devolve limitacao em vez de achado.
    error_paths=select_error_paths(root,git_change.changed_lines,contextual.executed_lines if run_tests and contextual else None,contextual.excluded_lines if run_tests and contextual else None)
    # Do diff so o tamanho e' persistido, nunca o texto: o argumento do produto e' que
    # ele resume 62 KB de diff em 4 KB de relatorio, e esse numero tem de sair medido
    # pelo proprio Sentry. Guardar o texto para prova-lo custaria os mesmos 62 KB por
    # execucao no SQLite e em cada JSON gravado, o que contradiz o que se afirma.
    configuration={'spec':spec_label or 'nenhuma spec declarada','without_spec':without_spec,'run_tests':run_tests,'whole_project':whole_project,'git_change':{'revision':git_change.revision,'reference':git_change.reference,'files':git_change.files,'statuses':git_change.statuses or {},'changed_lines':git_change.changed_lines or {},'error':git_change.error,'diff_bytes':len(git_change.diff.encode('utf-8')),'diff_chars':len(git_change.diff)},'traceability':traceability,'impact':impact,'error_paths':error_paths,'cases':summarize(test_cases),'catalog_limitations':catalog_limitations,'justified_classes':justified_classes}
    disabled=tuple(config.get('dimensions',{}).get('disabled') or ())
    configuration['dimensions']=list(evaluate_dimensions(traceability,test_cases,error_paths,document.fields,missing_classes_found,disabled,without_spec))
    # Reusar sem dizer transformaria evidencia velha em afirmacao nova. O relatorio so
    # consegue acusar o que estiver escrito aqui, entao a procedencia sai junto do dado
    # -- e sai tambem quando nao houve reuso, porque chave ausente e' ambigua onde
    # `False`/`None` sao conclusivos.
    configuration['execution_mode']=COMPLETE if run_tests else INSTANT; configuration['input_hash']=fingerprint; configuration['from_cache']=cached is not None; configuration['cached_from']=provenance(cached) if cached is not None else None
    if run_tests:
        # No acerto de cache a cobertura tambem nao foi medida agora: ela saiu do
        # artefato daquela execucao, e `reused_from` e' o que impede o numero de se
        # apresentar como leitura desta rodada.
        configuration['test_execution']=test_execution; configuration['coverage']={'global_percent':contextual.global_percent,'changed_percent':contextual.changed_percent,'files':contextual.files,'error':contextual.error,**_coverage_lines(contextual,git_change.changed_lines),'reused_from':provenance(cached) if cached is not None else None}
        # Chave so' existe quando [e2e] esta declarado: projeto sem frontend nao
        # ganha um `e2e_execution: null` poluindo todo relatorio que nunca vai usar.
        if e2e_test is not None: configuration['e2e_execution']=_execution_payload(e2e_test)
    else:
        # Modo instantaneo: nenhuma contagem desta rodada a publicar -- a ausencia de
        # `test_execution` e' justamente o que diz que nenhum processo subiu -- e a
        # cobertura, quando existe, e' declarada como da execucao anterior. As regras
        # continuam sem receber cobertura: a medida reusada descreve o diff de outra
        # analise, e reprovar ou aprovar por ela seria julgar codigo que ninguem mediu.
        configuration['coverage']=reused_coverage(history)
    severities=_severity_policy(config)
    if severities: configuration['severity_policy']={rule:level.value for rule,level in severities.items()}
    thresholds=_thresholds(config)
    # A SPEC exige registrar a politica efetivamente aplicada, nao so o resultado.
    if thresholds.changed_coverage is not None or thresholds.global_coverage is not None:
        configuration['thresholds']={'changed_coverage':thresholds.changed_coverage,'global_coverage':thresholds.global_coverage}
    infrastructure=_infrastructure_errors(tests[0] if tests else None,contextual if run_tests else None,test_command,config.get('coverage',{}).get('format') or 'coverage.py')
    # A segunda suite tem sua propria infraestrutura (comando, runner) e sua propria
    # falha de ambiente -- misturar as duas num `execution` so perderia qual delas
    # quebrou. Sem cobertura nenhuma aqui: [e2e] nao mede coverage.py/lcov/cobertura.
    if e2e_test is not None: infrastructure=(*infrastructure,*_infrastructure_errors(e2e_test,None,e2e_command))
    # Sem isto, uma base errada em CI produzia diff vazio e aprovacao: nada a
    # medir e' indistinguivel de nada mudou. Nao e' repetivel -- o nome da
    # referencia nao vai passar a existir numa nova tentativa.
    #
    # So quando a base foi declarada: analisar um diretorio que nao e' repositorio
    # Git ja era possivel antes, e transformar isso em inconclusivo seria punir um
    # uso legitimo por causa de um erro de configuracao de outra natureza.
    if declared_base and git_change.error: infrastructure=(InfrastructureError('leitura do diff','git',git_change.error,False),*infrastructure)
    # `status` nao tem "sem git" como uso legitimo como `run` tem: sem repositorio nao
    # ha como enumerar o projeto inteiro, e ficar em silencio diria "0 arquivos" onde
    # a resposta certa e' "nao consegui olhar".
    if whole_project and git_change.error: infrastructure=(InfrastructureError('leitura do projeto','git',git_change.error,False),*infrastructure)
    if infrastructure: configuration['infrastructure_errors']=[{'stage':e.stage,'cause':e.cause,'message':e.message,'retryable':e.retryable} for e in infrastructure]
    # Um diff so de documentacao/configuracao nao tem cobertura a calcular: sem
    # isto, `coverage-missing` acusa falha onde nao havia nada a medir.
    measurable=any(Path(name).suffix.lower() in SOURCE_EXTENSIONS for name in git_change.files)
    # A extensao e' so um palpite, usado quando nao ha cobertura lida. Com ela em
    # maos, quem decide e' a medicao: um diff de arquivo .py composto apenas de
    # comentario tem extensao de fonte e mesmo assim nada a medir -- e `coverage-missing`
    # dizia "nao foi possivel calcular" onde nao havia o que calcular.
    if run_tests and contextual is not None and contextual.error is None:
        measurable=contextual.changed_percent is not None
    findings,verdict=evaluate(EvaluationContext(tests=tests,has_measurable_change=measurable,changed_files=git_change.files if run_tests else (spec_label or 'sem spec',),changed_coverage=contextual.changed_percent if run_tests else None,coverage_available=contextual.error is None if run_tests else False,requirements_without_scenarios=tuple(traceability['requirements_without_scenarios']),scenarios_without_tests=tuple(traceability['scenarios_without_tests']),error_paths_without_tests=error_paths['uncovered'],missing_equivalence_classes=missing_classes_found,case_spec_errors=case_errors,orphan_markers=tuple(traceability['orphan_markers']),infrastructure_errors=tuple(e.message for e in infrastructure),global_coverage=contextual.global_percent if run_tests and contextual else None,thresholds=thresholds),severities)
    # `[project] name` era decorativo: o relatorio sempre usava o nome do
    # diretorio. Uma chave de configuracao que nao faz nada e' pior que chave
    # nenhuma -- agora ela vale, com o diretorio como fallback.
    project_name=config.get('project',{}).get('name') or root.name
    # O commit analisado ficava em branco enquanto o diff ja o conhecia: sem ele,
    # `latest.md` envelhece sem avisar e um relatorio de cinco commits atras e'
    # indistinguivel do veredito atual. E' o selo de frescor que `sentry report` le.
    run=Run(run_id,project_name,git_change.revision,git_change.reference,configuration=configuration,test_cases=test_cases,findings=findings,verdict=verdict,infrastructure_errors=infrastructure)
    with sqlite3.connect(root/'.sentry'/'sentry.db') as conn:
        conn.execute('INSERT INTO runs VALUES (?,?)',(run.id,to_json(run)))
    (root/'.sentry'/'runs'/f'{run.id}.json').write_text(to_json(run),encoding='utf-8'); return run
