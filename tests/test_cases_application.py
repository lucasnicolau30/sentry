from sentrytest.adapters.case_specs import parse_cases
from sentrytest.application.cases import build_test_cases, scaffold, slugify, summarize
from sentrytest.domain.models import Layer, Priority, TestStatus as DomainTestStatus, TestType as DomainTestType

DOC = """# Login

## Prompt

A tela de login so aceita CPF.

## Campos

- **cpf**: cpf — obrigatorio

## Caso: login rejeita cpf com letras

- **Requisito:** so aceita CPF
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** cpf/letras
- **Dado:** usuario na tela
- **Quando:** digita letras
- **Então:** exibe erro
- **Entrada:** `cpf = "abc"`

## Caso: login aceita cpf valido

- **Requisito:** so aceita CPF
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** crítica
- **Classe:** cpf/valido-formatado
- **Dado:** usuario cadastrado
- **Quando:** submete cpf valido
- **Então:** responde 200
"""

TRACEABILITY = {
    "scenarios": [
        {"name": "login rejeita cpf com letras", "tests": ["tests/test_login.py"], "covered": True},
        {"name": "login aceita cpf valido", "tests": [], "covered": False},
    ]
}


def test_mapeia_camada_tipo_e_prioridade_para_o_dominio():
    cases = build_test_cases(parse_cases(DOC), TRACEABILITY)
    assert cases[0].layer == Layer.BACKEND
    assert cases[0].test_type == DomainTestType.UNIT
    assert cases[0].priority == Priority.HIGH
    assert cases[1].layer == Layer.INTEGRATION
    assert cases[1].priority == Priority.CRITICAL


def test_caso_sem_teste_associado_fica_nao_coberto():
    cases = build_test_cases(parse_cases(DOC), TRACEABILITY)
    assert cases[1].status == DomainTestStatus.NOT_COVERED
    assert cases[1].related_test is None


def test_caso_com_teste_mas_sem_execucao_fica_nao_executado():
    cases = build_test_cases(parse_cases(DOC), TRACEABILITY, tests_ran=False)
    assert cases[0].status == DomainTestStatus.NOT_RUN
    assert cases[0].related_test == "tests/test_login.py"


def test_caso_com_teste_e_execucao_limpa_fica_coberto():
    cases = build_test_cases(parse_cases(DOC), TRACEABILITY, tests_ran=True, suite_failed=False)
    assert cases[0].status == DomainTestStatus.COVERED


def test_suite_falhando_nao_atribui_falha_ao_caso():
    """Sem granularidade por teste nao da para culpar um caso especifico."""
    cases = build_test_cases(parse_cases(DOC), TRACEABILITY, tests_ran=True, suite_failed=True)
    assert cases[0].status == DomainTestStatus.PARTIAL


def test_entrada_declarada_vira_input_data():
    cases = build_test_cases(parse_cases(DOC), TRACEABILITY)
    assert cases[0].input_data == {"cpf": "abc"}


def test_evidencia_registra_origem_do_caso():
    cases = build_test_cases(parse_cases(DOC), TRACEABILITY)
    sources = {evidence.source for evidence in cases[0].evidences}
    assert {"CASES.md", "catálogo", "teste"} <= sources


def test_resumo_separa_por_camada_e_status():
    resumo = summarize(build_test_cases(parse_cases(DOC), TRACEABILITY))
    assert resumo["total"] == 2
    assert resumo["by_layer"] == {"backend": 1, "integração": 1}
    assert resumo["by_status"]["não coberto"] == 1
    assert len(resumo["uncovered"]) == 1


def test_scaffold_cria_prompt_e_cases(tmp_path):
    directory, created = scaffold(tmp_path, "Tela de Login", "so aceita CPF")
    assert directory == tmp_path / ".sentry" / "specs" / "tela-de-login"
    assert (directory / "PROMPT.md").exists()
    assert (directory / "CASES.md").exists()
    assert "so aceita CPF" in (directory / "PROMPT.md").read_text(encoding="utf-8")
    assert len(created) == 2


def test_scaffold_e_idempotente_e_nao_sobrescreve(tmp_path):
    directory, _ = scaffold(tmp_path, "Tela de Login")
    (directory / "CASES.md").write_text("# ja preenchido\n", encoding="utf-8")
    _, created = scaffold(tmp_path, "Tela de Login")
    assert created == []
    assert (directory / "CASES.md").read_text(encoding="utf-8") == "# ja preenchido\n"


def test_slugify_normaliza_acentos_e_espacos():
    assert slugify("Análise de Operadores") == "analise-de-operadores"
