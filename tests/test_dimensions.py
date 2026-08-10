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
