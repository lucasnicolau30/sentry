from sentrytest.domain.models import Severity, TestStatus as DomainTestStatus
from sentrytest.domain.rules import EvaluationContext, evaluate

def test_failing_test_is_critical_and_rejected():
    class T: status=DomainTestStatus.FAILED
    findings, verdict=evaluate(EvaluationContext(tests=(T(),)))
    assert findings[0].rule=='test-failing' and findings[0].severity==Severity.CRITICAL
    assert verdict.status.value=='reprovado'

def test_missing_requirement_and_scenario_create_findings():
    findings,_=evaluate(EvaluationContext(requirements_without_scenarios=('R1',),scenarios_without_tests=('C1',)))
    assert {f.rule for f in findings}=={'requirement-without-scenario','scenario-without-test'}

def test_same_input_is_deterministic():
    context=EvaluationContext(changed_files=('a.py',),changed_coverage=0)
    assert evaluate(context)==evaluate(context)

def test_medium_severity_finding_alone_does_not_block_approval():
    findings,verdict=evaluate(EvaluationContext(requirements_without_scenarios=('R1',),changed_coverage=100.0))
    assert findings[0].severity==Severity.MEDIUM
    assert verdict.status.value=='aprovado'

def test_high_severity_finding_still_warns():
    findings,verdict=evaluate(EvaluationContext(scenarios_without_tests=('C1',),changed_coverage=100.0))
    assert findings[0].severity==Severity.HIGH
    assert verdict.status.value=='aprovado com ressalvas'

def test_erro_de_infraestrutura_nunca_aprova():
    """Sem evidencia confiavel o veredito e inconclusivo, nao aprovado."""
    context=EvaluationContext(changed_coverage=100.0,infrastructure_errors=('nenhum teste coletado',))
    findings,verdict=evaluate(context)
    assert findings==()
    assert verdict.status.value=='inconclusivo'
    assert 'nenhum teste coletado' in verdict.justification

def test_achado_critico_prevalece_sobre_erro_de_infraestrutura():
    """Teste falhando e conclusivo por si, mesmo com ambiente degradado."""
    class T: status=DomainTestStatus.FAILED
    _,verdict=evaluate(EvaluationContext(tests=(T(),),changed_coverage=100.0,infrastructure_errors=('coverage ausente',)))
    assert verdict.status.value=='reprovado'

def test_sem_erro_de_infraestrutura_aprova_normalmente():
    _,verdict=evaluate(EvaluationContext(changed_coverage=100.0))
    assert verdict.status.value=='aprovado'

def test_limiar_de_cobertura_alterada_gera_achado():
    from sentrytest.domain.rules import Thresholds
    findings,verdict=evaluate(EvaluationContext(changed_coverage=62.5,thresholds=Thresholds(changed_coverage=80.0)))
    assert findings[0].rule=='coverage-below-threshold'
    assert '62,50' in findings[0].message.replace('.',',')
    assert verdict.status.value=='aprovado com ressalvas'

def test_limiar_atingido_nao_gera_achado():
    from sentrytest.domain.rules import Thresholds
    findings,verdict=evaluate(EvaluationContext(changed_coverage=85.0,thresholds=Thresholds(changed_coverage=80.0)))
    assert findings==()
    assert verdict.status.value=='aprovado'

def test_sem_limiar_declarado_nao_cobra_nada():
    """Sem politica declarada o Sentry nao inventa um numero minimo."""
    findings,_=evaluate(EvaluationContext(changed_coverage=12.0))
    assert findings==()

def test_limiar_global_e_independente_do_alterado():
    from sentrytest.domain.rules import Thresholds
    findings,_=evaluate(EvaluationContext(changed_coverage=100.0,global_coverage=40.0,thresholds=Thresholds(global_coverage=90.0)))
    assert [f.rule for f in findings]==['global-coverage-below-threshold']

def test_cobertura_zero_continua_sendo_ausencia_e_nao_limiar():
    """Zero e ausencia de teste; abaixo do limiar e politica. Nao devem duplicar."""
    from sentrytest.domain.rules import Thresholds
    findings,_=evaluate(EvaluationContext(changed_files=('a.py',),changed_coverage=0,thresholds=Thresholds(changed_coverage=80.0)))
    assert [f.rule for f in findings]==['changed-code-uncovered']

# cenario: diff sem arquivo mensuravel nao acusa cobertura ausente
def test_diff_sem_arquivo_mensuravel_nao_acusa_cobertura_ausente():
    """Um diff so de .md/.toml nao tem cobertura a calcular: isso e' `nao
    aplicavel`, nao `falhou ao calcular`. Antes, um projeto recem-inicializado
    recebia esse achado por causa dos arquivos do proprio Sentry."""
    findings,_=evaluate(EvaluationContext(changed_files=('README.md','sentry.toml'),has_measurable_change=False))
    assert 'coverage-missing' not in {f.rule for f in findings}

# cenario: diff com codigo continua acusando cobertura ausente
def test_diff_com_codigo_continua_acusando_cobertura_ausente():
    """A precisao nao pode virar silencio: havendo codigo alterado sem cobertura
    calculada, o achado continua sendo legitimo."""
    findings,_=evaluate(EvaluationContext(changed_files=('src/app.py',),has_measurable_change=True))
    assert 'coverage-missing' in {f.rule for f in findings}
