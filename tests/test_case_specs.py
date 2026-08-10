from sentrytest.adapters.case_specs import TEMPLATE, parse_cases, validate_document
from sentrytest.domain.catalog import merge_catalog, missing_classes, required_classes, unknown_field_types

VALID = """# Tela de login

## Prompt

A tela de login so aceita CPF como identificador.

## Campos

- **cpf**: cpf — obrigatorio, unico identificador aceito

## Caso: login rejeita cpf com letras

- **Requisito:** a tela de login so aceita CPF
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** cpf/letras
- **Dado:** usuario na tela de login
- **Quando:** digita letras no campo CPF e submete
- **Então:** o campo exibe erro de formato
- **Entrada:** `cpf = "abcdefghijk"`
"""


def test_parse_extrai_titulo_prompt_campos_e_casos():
    document = parse_cases(VALID)
    assert document.title == "Tela de login"
    assert document.prompt.startswith("A tela de login")
    assert [field.name for field in document.fields] == ["cpf"]
    assert document.fields[0].type == "cpf"
    assert len(document.cases) == 1
    case = document.cases[0]
    assert case.name == "login rejeita cpf com letras"
    assert case.layer == "backend"
    assert case.equivalence_class == "cpf/letras"
    assert case.input_data == {"cpf": "abcdefghijk"}


def test_documento_valido_nao_gera_erro():
    assert validate_document(parse_cases(VALID)) == []


def test_template_em_branco_e_invalido():
    """O esqueleto nao preenchido nao pode passar na validacao."""
    errors = validate_document(parse_cases(TEMPLATE))
    assert errors
    assert any("título" in error for error in errors)


def test_camada_invalida_gera_erro():
    text = VALID.replace("- **Camada:** backend", "- **Camada:** mobile")
    errors = validate_document(parse_cases(text))
    assert any("camada inválida" in error for error in errors)


def test_bullet_obrigatorio_ausente_gera_erro():
    text = VALID.replace("- **Quando:** digita letras no campo CPF e submete\n", "")
    errors = validate_document(parse_cases(text))
    assert any("'quando'" in error for error in errors)


def test_caso_duplicado_gera_erro():
    document = parse_cases(VALID + VALID.split("## Caso:", 1)[1].join(["## Caso:", ""]))
    if len(document.cases) > 1:
        assert any("duplicado" in error for error in validate_document(document))


def test_classe_referencia_campo_nao_declarado():
    text = VALID.replace("- **Classe:** cpf/letras", "- **Classe:** email/vazio")
    errors = validate_document(parse_cases(text))
    assert any("não está declarado" in error for error in errors)


def test_acentos_e_caixa_sao_tolerados_nas_chaves():
    text = VALID.replace("- **Então:**", "- **ENTAO:**")
    assert validate_document(parse_cases(text)) == []


def test_catalogo_cobra_classes_faltantes():
    document = parse_cases(VALID)
    missing = missing_classes(document.fields, document.cases)
    faltando = {item["class"] for item in missing}
    assert "letras" not in faltando
    assert "digito-verificador-invalido" in faltando
    assert len(missing) == len(required_classes("cpf")) - 1


def test_tipo_fora_do_catalogo_vira_limitacao_nao_cobranca():
    text = VALID.replace("- **cpf**: cpf —", "- **cpf**: matricula —")
    document = parse_cases(text)
    assert missing_classes(document.fields, document.cases) == ()
    assert unknown_field_types(document.fields) == ("matricula",)


def test_catalogo_aceita_tipos_declarados_no_projeto():
    catalog = merge_catalog({"matricula": ["vazio", "letras", "valida"]})
    text = VALID.replace("- **cpf**: cpf —", "- **cpf**: matricula —")
    document = parse_cases(text)
    assert unknown_field_types(document.fields, catalog) == ()
    # 'letras' ja e coberta pelo caso existente (Classe: cpf/letras); sobra o resto.
    assert {item["class"] for item in missing_classes(document.fields, document.cases, catalog)} == {"vazio", "valida"}


NOT_APPLICABLE_TEXT = VALID.replace(
    "- **Entrada:** `cpf = \"abcdefghijk\"`\n",
    "- **Entrada:** `cpf = \"abcdefghijk\"`\n\n"
    "## Classes não aplicáveis\n\n"
    "- **cpf/digito-verificador-invalido**: campo de identificação interna, não vem de formulário de usuário\n",
)


def test_classe_nao_aplicavel_e_parseada_com_motivo():
    document = parse_cases(NOT_APPLICABLE_TEXT)
    assert len(document.not_applicable) == 1
    item = document.not_applicable[0]
    assert item.field == "cpf"
    assert item.class_name == "digito-verificador-invalido"
    assert "identificação interna" in item.reason


def test_classe_nao_aplicavel_sem_motivo_gera_erro():
    text = NOT_APPLICABLE_TEXT.replace(
        "- **cpf/digito-verificador-invalido**: campo de identificação interna, não vem de formulário de usuário",
        "- **cpf/digito-verificador-invalido**:",
    )
    errors = validate_document(parse_cases(text))
    assert any("falta o motivo" in error for error in errors)


def test_classe_nao_aplicavel_referencia_campo_nao_declarado_gera_erro():
    text = NOT_APPLICABLE_TEXT.replace("cpf/digito-verificador-invalido", "email/vazio")
    errors = validate_document(parse_cases(text))
    assert any("não está declarado" in error for error in errors)


def test_classe_nao_aplicavel_remove_a_cobranca_do_catalogo():
    document = parse_cases(NOT_APPLICABLE_TEXT)
    missing = missing_classes(document.fields, document.cases, not_applicable=document.not_applicable)
    faltando = {item["class"] for item in missing}
    assert "digito-verificador-invalido" not in faltando
    # letras (coberta por caso) e digito-verificador-invalido (justificada) saem;
    # o resto do catalogo de cpf continua sendo cobrado normalmente.
    assert len(missing) == len(required_classes("cpf")) - 2
