from sentrytest.application.dimensions import (
    ALL_DIMENSIONS, APIS, EXCEPTIONS, REQUIREMENTS, SECURITY, evaluate_dimensions,
)
from sentrytest.domain.models import (
    Layer, Priority,
    TestCase as DomainTestCase,
    TestStatus as DomainTestStatus,
    TestType as DomainTestType,
)


class Field:
    def __init__(self, name, type_):
        self.name, self.type = name, type_


def _case(status, test_type=DomainTestType.CONTRACT, layer=Layer.BACKEND):
    return DomainTestCase("TC-1", "r", layer, (), {}, "a", "e", Priority.HIGH, test_type, status)


def _run(**kwargs):
    base = {"traceability": {"scenarios": []}, "test_cases": (), "error_paths": {},
            "fields": (), "missing_classes": ()}
    base.update(kwargs)
    return {item["dimension"]: item for item in evaluate_dimensions(**base)}


def test_produz_uma_entrada_por_dimensao():
    assert tuple(_run()) == ALL_DIMENSIONS


def test_dimensao_sem_insumo_e_nao_aplicavel_nao_nao_coberta():
    """Projeto sem rota declarada nao pode ser punido na dimensao de seguranca."""
    assert _run()[SECURITY]["status"] == "não aplicável"


def test_requisitos_parcial_quando_alguns_cenarios_tem_teste():
    traceability = {"scenarios": [{"covered": True}, {"covered": False}, {"covered": True}]}
    resultado = _run(traceability=traceability)[REQUIREMENTS]
    assert resultado["status"] == "parcial"
    assert "2/3" in resultado["evidence"]
    assert "1 de 3" in resultado["justification"]


def test_requisitos_coberta_quando_todos_tem_teste():
    traceability = {"scenarios": [{"covered": True}, {"covered": True}]}
    assert _run(traceability=traceability)[REQUIREMENTS]["status"] == "coberta"


def test_requisitos_nao_coberta_quando_nenhum_tem_teste():
    traceability = {"scenarios": [{"covered": False}]}
    assert _run(traceability=traceability)[REQUIREMENTS]["status"] == "não coberta"


def test_apis_considera_contrato_e_integracao():
    cases = (_case(DomainTestStatus.COVERED), _case(DomainTestStatus.NOT_COVERED, DomainTestType.INTEGRATION))
    assert _run(test_cases=cases)[APIS]["status"] == "parcial"


def test_apis_ignora_caso_unitario_de_backend():
    cases = (_case(DomainTestStatus.NOT_COVERED, DomainTestType.UNIT),)
    assert _run(test_cases=cases)[APIS]["status"] == "não aplicável"


def test_excecoes_usa_os_caminhos_de_erro():
    error_paths = {"covered": ("a.py:1 (raise)",), "uncovered": ("a.py:9 (except)",)}
    resultado = _run(error_paths=error_paths)[EXCEPTIONS]
    assert resultado["status"] == "parcial"
    assert "1/2" in resultado["evidence"]


def test_seguranca_cobra_rota_com_classe_faltando():
    fields = (Field("perfil", "rota"),)
    missing = ({"field": "perfil", "class": "sem-permissao", "type": "rota"},)
    assert _run(fields=fields, missing_classes=missing)[SECURITY]["status"] == "não coberta"


def test_seguranca_coberta_quando_rota_nao_tem_classe_faltando():
    fields = (Field("perfil", "rota"),)
    assert _run(fields=fields)[SECURITY]["status"] == "coberta"


def test_dimensao_desabilitada_nao_aparece():
    resultado = _run(disabled=(SECURITY,))
    assert SECURITY not in resultado
    assert len(resultado) == len(ALL_DIMENSIONS) - 1


# cenario: sem dados de cobertura a dimensao sai como nao verificada
def test_sem_dados_de_cobertura_a_dimensao_sai_como_nao_verificada():
    """O defeito relatado: `covered` e `uncovered` vazios levavam a dimensao a
    concluir ausencia de caminho de erro, enquanto as Limitacoes do mesmo
    relatorio contavam um. A dimensao existe; o que faltou foi o dado."""
    error_paths = {"covered": (), "uncovered": (), "unmeasured": ("users/serializers.py:50 (raise)",)}
    resultado = _run(error_paths=error_paths)[EXCEPTIONS]
    assert resultado["status"] == "não verificada"
    assert resultado["status"] not in ("não aplicável", "coberta")
    assert "1" in resultado["evidence"] and "caminho" in resultado["evidence"]
    assert "nenhum caminho de erro" not in resultado["evidence"]


# cenario: ausencia real de caminho de erro continua nao aplicavel
def test_ausencia_real_de_caminho_de_erro_continua_nao_aplicavel():
    """"Nao aplicavel" precisa seguir significando que a dimensao nao existe nesta
    mudanca -- e' o que impede o relatorio de punir projeto por eixo inexistente."""
    for error_paths in ({}, {"covered": (), "uncovered": (), "unmeasured": ()}):
        resultado = _run(error_paths=error_paths)[EXCEPTIONS]
        assert resultado["status"] == "não aplicável"
        assert "nenhum caminho de erro" in resultado["evidence"]


# cenario: com cobertura o veredito de execucao permanece
def test_com_cobertura_o_veredito_de_execucao_permanece():
    """O conserto so pode alcancar o caso sem medicao: havendo dados, os tres
    vereditos de execucao continuam saindo como antes."""
    def status(covered, uncovered):
        return _run(error_paths={"covered": covered, "uncovered": uncovered})[EXCEPTIONS]

    assert status(("a:1 (raise)", "a:2 (except)"), ())["status"] == "coberta"
    assert status((), ("a:1 (raise)", "a:2 (except)"))["status"] == "não coberta"
    parcial = status(("a:1 (raise)",), ("a:2 (except)",))
    assert parcial["status"] == "parcial"
    assert "1/2" in parcial["evidence"]


# cenario: caminho de erro excluido da medicao nao vira ausencia de caminho
def test_caminho_excluido_da_medicao_nao_vira_ausencia_de_caminho():
    """Exclusao declarada (`# pragma: no cover`) tambem esvaziava as duas listas,
    produzindo a mesma afirmacao falsa por outro caminho. E quando parte foi
    medida e parte nao, o status vem do que se pode afirmar, mas a evidencia nao
    pode omitir o resto."""
    so_excluido = _run(error_paths={"covered": (), "uncovered": (), "unmeasured": ("app.py:9 (raise)",)})[EXCEPTIONS]
    assert so_excluido["status"] == "não verificada"
    assert "nenhum caminho de erro" not in so_excluido["evidence"]

    parcialmente_medido = _run(error_paths={
        "covered": ("app.py:3 (raise)",), "uncovered": (), "unmeasured": ("app.py:9 (raise)",),
    })[EXCEPTIONS]
    assert parcialmente_medido["status"] == "coberta"
    assert "1/1" in parcialmente_medido["evidence"]
    assert "1 sem medicao" in parcialmente_medido["evidence"]
