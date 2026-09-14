"""Dimensões de cobertura: o mapa de risco por eixo, não por linha.

Cobertura de linha responde "o código rodou". Estas dimensões respondem "que
tipo de risco está descoberto". Nenhuma coleta nova acontece aqui: cada
dimensão agrega evidência que outras etapas já produziram.

`não aplicável` é distinto de `não coberta`. A primeira diz que a dimensão não
existe neste projeto — sem rota declarada não há o que cobrar em segurança. A
segunda diz que existe e ninguém cobriu. Tratar as duas como iguais faria o
relatório punir projetos por não terem um eixo, ou esconder eixos vazios.
"""
from __future__ import annotations

from ..domain.models import DimensionStatus, Layer, TestStatus, TestType

REQUIREMENTS = "requisitos e regras de negócio"
APIS = "APIs, persistência, transações e integrações"
EXCEPTIONS = "exceções, resiliência e recuperação"
SECURITY = "segurança e autorização"
INTERFACE = "interface e fluxo de usuário"

ALL_DIMENSIONS = (REQUIREMENTS, APIS, EXCEPTIONS, SECURITY, INTERFACE)

_ROUTE_TYPE = "rota"
_INTEGRATION_TYPES = {"contrato", "integração"}


# No modo sem spec a dimensão continua saindo `não aplicável` — nunca `coberta` —, mas a
# justificativa muda: "nada foi declarado ou alterado" sugere que se olhou a mudança e não
# se achou nada, quando o que houve foi não haver matriz com que comparar. Dizer em voz
# alta o que não pôde ser julgado é o que separa esta ferramenta de um palpite.
NO_INTENT = "nenhuma intenção declarada nesta análise"


def _from_counts(covered: int, total: int, evidence: str, absent: str, no_intent: bool = False) -> dict:
    if total == 0:
        return {"status": DimensionStatus.NOT_APPLICABLE.value, "evidence": absent,
                "justification": NO_INTENT if no_intent
                else "nada desta dimensão foi declarado ou alterado nesta análise"}
    if covered == total:
        status, why = DimensionStatus.COVERED, "todos os itens têm evidência de cobertura"
    elif covered == 0:
        status, why = DimensionStatus.NOT_COVERED, "nenhum item tem evidência de cobertura"
    else:
        status, why = DimensionStatus.PARTIAL, f"{total - covered} de {total} sem evidência de cobertura"
    return {"status": status.value, "evidence": evidence, "justification": why}


def _requirements(traceability: dict, no_intent: bool = False) -> dict:
    scenarios = traceability.get("scenarios") or []
    covered = sum(1 for item in scenarios if item.get("covered"))
    return _from_counts(covered, len(scenarios),
                        f"{covered}/{len(scenarios)} cenários da spec com teste associado",
                        "nenhum CASES.md nesta análise" if no_intent else "nenhum cenário declarado no CASES.md",
                        no_intent)


def _apis(test_cases, no_intent: bool = False) -> dict:
    relevant = [case for case in test_cases
                if str(case.test_type) in _INTEGRATION_TYPES or str(case.layer) == "integração"]
    covered = sum(1 for case in relevant if case.status == TestStatus.COVERED)
    return _from_counts(covered, len(relevant),
                        f"{covered}/{len(relevant)} casos de contrato ou integração cobertos",
                        "nenhum CASES.md nesta análise" if no_intent else "nenhum caso de contrato ou integração declarado",
                        no_intent)


def _exceptions(error_paths: dict) -> dict:
    covered = len(error_paths.get("covered") or ())
    total = covered + len(error_paths.get("uncovered") or ())
    unmeasured = len(error_paths.get("unmeasured") or ())
    # Sem nenhum caminho medido, mas com caminhos existentes, "nao aplicavel" seria
    # falso -- foi o defeito relatado: a tabela dizia "nenhum caminho de erro nas
    # linhas alteradas" enquanto as Limitacoes contavam um. A dimensao existe; o
    # que faltou foi o dado para avalia-la, e e' isso que o relatorio deve dizer.
    if total == 0 and unmeasured:
        return {"status": DimensionStatus.NOT_MEASURED.value,
                "evidence": f"{unmeasured} caminho(s) de erro alterado(s) sem medicao de execucao",
                "justification": "ver Limitações: sem dados de cobertura ou excluídos da medição pelo projeto"}
    result = _from_counts(covered, total,
                          f"{covered}/{total} caminhos de erro alterados executados por algum teste",
                          "nenhum caminho de erro nas linhas alteradas")
    if unmeasured:
        # Medicao parcial: parte foi avaliada e parte nao. O status segue vindo do
        # que se pode afirmar, mas a evidencia nao pode omitir o resto.
        result["evidence"] += f"; {unmeasured} sem medicao de execucao (ver Limitações)"
    return result


def _security(fields, missing_classes, no_intent: bool = False) -> dict:
    routes = [field for field in fields if str(field.type).casefold() == _ROUTE_TYPE]
    if not routes:
        return _from_counts(0, 0, "",
                            "nenhum CASES.md nesta análise" if no_intent
                            else f"nenhum campo do tipo `{_ROUTE_TYPE}` declarado",
                            no_intent)
    names = {field.name for field in routes}
    uncovered = {item["field"] for item in missing_classes if item["field"] in names}
    covered = len(names) - len(uncovered)
    return _from_counts(covered, len(names),
                        f"{covered}/{len(names)} rotas com todas as classes de acesso cobertas",
                        "")


def _interface(test_cases, no_intent: bool = False) -> dict:
    # Sem cobertura de linha no frontend: o caso so' conta como coberto por ter
    # rodado e passado no Playwright -- a mesma disciplina que separa "nao
    # aplicavel" de "nao coberta" nas outras dimensoes, aqui sem numero de
    # cobertura nenhum para nao fingir uma medida que o produto nao faz.
    relevant = [case for case in test_cases
                if case.layer == Layer.FRONTEND or case.test_type == TestType.E2E]
    covered = sum(1 for case in relevant if case.status == TestStatus.COVERED)
    return _from_counts(covered, len(relevant),
                        f"{covered}/{len(relevant)} casos de interface com evidência de execução e2e",
                        "nenhum CASES.md nesta análise" if no_intent else "nenhum caso de camada frontend declarado",
                        no_intent)


def evaluate_dimensions(traceability: dict, test_cases, error_paths: dict, fields,
                        missing_classes, disabled: tuple[str, ...] = (),
                        without_spec: bool = False) -> tuple[dict, ...]:
    """Uma entrada por dimensão habilitada, com status, evidência e justificativa.

    `without_spec` nao silencia dimensao nenhuma: ele so troca a justificativa das que
    dependem de intencao declarada. Excecoes continua sendo medida, porque sai do AST e
    da execucao -- e' justamente o que o modo sem spec ainda tem a dizer.
    """
    produced = {
        REQUIREMENTS: lambda: _requirements(traceability, without_spec),
        APIS: lambda: _apis(test_cases, without_spec),
        EXCEPTIONS: lambda: _exceptions(error_paths),
        SECURITY: lambda: _security(fields, missing_classes, without_spec),
        INTERFACE: lambda: _interface(test_cases, without_spec),
    }
    ignored = {name.casefold() for name in disabled}
    return tuple(
        {"dimension": name, **produced[name]()}
        for name in ALL_DIMENSIONS
        if name.casefold() not in ignored
    )
