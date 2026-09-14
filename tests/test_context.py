from sentrytest.application.context import build_context

CHAVES = {"summary", "uncovered_lines", "uncovered_error_paths", "failing_tests",
          "scenarios_without_tests", "missing_equivalence_classes", "orphan_markers",
          "limitations"}


def _payload(configuration=None, findings=(), verdict="aprovado"):
    """O mesmo formato que `markdown_report` recebe: `data` com configuration,
    findings, verdict e test_cases. Montado a mao de proposito -- amarrar o teste
    a uma execucao real do `analyze` mediria o pipeline inteiro, e o que se cobra
    aqui e' o recorte."""
    return {"contract_version": "1.0",
            "data": {"id": "run-1", "project": "p", "verdict": {"status": verdict},
                     "configuration": configuration or {}, "findings": list(findings),
                     "test_cases": []}}


def _cobertura(changed, measured, executed, arquivo="src/app.py"):
    return {"run_tests": True,
            "git_change": {"changed_lines": {arquivo: tuple(changed)}},
            "coverage": {"global_percent": 80.0, "changed_percent": 50.0,
                         "measured_lines": {arquivo: tuple(measured)},
                         "executed_lines": {arquivo: tuple(executed)}}}


# cenario: context emite as faixas de linha sem cobertura
def test_context_emite_as_faixas_de_linha_sem_cobertura():
    """Faixa, e nao linha solta: um diff de 40 linhas descobertas viraria 40
    entradas, e o payload existe justamente para ser menor que o codigo."""
    configuracao = _cobertura(changed=(*range(10, 15), 22, 30),
                              measured=(*range(10, 15), 22, 30), executed=(30,))
    resultado = build_context(_payload(configuracao))
    assert resultado["uncovered_lines"] == [{"file": "src/app.py", "ranges": [[10, 14], [22, 22]]}]


# cenario: context emite as faixas de linha sem cobertura
def test_linha_que_a_cobertura_nao_mediu_nao_vira_faixa_nem_emenda_duas():
    """A 12 e' comentario: a cobertura nao a mediu. Conta-la como lacuna repetiria
    o defeito que a cobertura do alterado ja corrigiu, e emendar 10-14 por cima
    dela afirmaria a mesma coisa com outra forma."""
    configuracao = _cobertura(changed=range(10, 15), measured=(10, 11, 13, 14), executed=())
    assert build_context(_payload(configuracao))["uncovered_lines"] == [
        {"file": "src/app.py", "ranges": [[10, 11], [13, 14]]}]


# cenario: context emite as faixas de linha sem cobertura
def test_arquivo_com_tudo_executado_sai_do_payload():
    """Arquivo sem lacuna nao ocupa espaco: quem le so precisa do que falta."""
    configuracao = _cobertura(changed=(10, 11), measured=(10, 11), executed=(10, 11))
    assert build_context(_payload(configuracao))["uncovered_lines"] == []


# cenario: context emite cenarios classes caminhos de erro e marcadores orfaos
def test_context_emite_cenarios_classes_caminhos_de_erro_e_marcadores_orfaos():
    configuracao = {
        "traceability": {"scenarios_without_tests": ["rejeita slug vazio"],
                         "orphan_markers": [{"marker": "rejeita slug antigo",
                                             "tests": ["tests/test_slug.py"]}]},
        "error_paths": {"uncovered": ["src/app.py:42 (raise)"], "limitations": []},
    }
    achado = {"rule": "missing-equivalence-class", "severity": "alta",
              "message": "Classe de equivalência não coberta: slug/vazio (tipo texto).",
              "recommendation": "..."}
    resultado = build_context(_payload(configuracao, findings=[achado]))
    assert resultado["scenarios_without_tests"] == ["rejeita slug vazio"]
    assert resultado["uncovered_error_paths"] == ["src/app.py:42 (raise)"]
    assert resultado["missing_equivalence_classes"] == [
        {"field": "slug", "class": "vazio", "type": "texto"}]
    assert resultado["orphan_markers"] == [{"marker": "rejeita slug antigo",
                                            "tests": ["tests/test_slug.py"]}]


# cenario: context emite cenarios classes caminhos de erro e marcadores orfaos
def test_classe_de_equivalencia_com_mensagem_ilegivel_nao_some():
    """O dict da classe faltante nao sobrevive a serializacao: so a mensagem do
    achado o carrega. Se o texto mudar, descartar a lacuna em silencio seria pior
    que entrega-la sem os campos separados."""
    achado = {"rule": "missing-equivalence-class", "message": "outro texto qualquer"}
    resultado = build_context(_payload({}, findings=[achado]))
    assert resultado["missing_equivalence_classes"] == [
        {"field": None, "class": None, "type": None, "description": "outro texto qualquer"}]


# cenario: context emite cenarios classes caminhos de erro e marcadores orfaos
def test_limitacoes_juntam_impacto_caminhos_de_erro_e_catalogo():
    """As tres origens que o relatorio ja junta. O agente precisa saber o que o
    Sentry nao conseguiu verificar antes de concluir que o resto esta provado."""
    configuracao = {"impact": {"limitations": ["nenhum arquivo de teste encontrado em: tests"]},
                    "error_paths": {"limitations": ["src/a.go: deteccao por padrao sintatico"]},
                    "catalog_limitations": ["tipos de campo fora do catálogo: cor"]}
    assert build_context(_payload(configuracao))["limitations"] == [
        "nenhum arquivo de teste encontrado em: tests",
        "src/a.go: deteccao por padrao sintatico",
        "tipos de campo fora do catálogo: cor"]


# cenario: context emite os testes falhando com nome
def test_context_emite_os_testes_falhando_com_nome():
    saida = ("=========================== short test summary info ===========================\n"
             "FAILED tests/test_slug.py::test_rejeita_slug_vazio - AssertionError: ...\n"
             "FAILED tests/test_slug.py::test_aceita_slug_valido\n"
             "======================== 2 failed, 231 passed in 24.62s =======================\n")
    configuracao = {"run_tests": True, "test_execution": {"failed": 2, "output": saida}}
    assert build_context(_payload(configuracao, verdict="reprovado"))["failing_tests"] == [
        "tests/test_slug.py::test_rejeita_slug_vazio",
        "tests/test_slug.py::test_aceita_slug_valido"]


# cenario: context emite os testes falhando com nome
def test_saida_verbosa_tambem_nomeia_e_nao_repete_o_mesmo_teste():
    """Com `-v` o nodeid vem antes da palavra FAILED, e o resumo final repete a
    mesma falha: o nome sai uma vez so."""
    saida = ("tests/test_slug.py::test_rejeita_slug_vazio FAILED                       [ 50%]\n"
             "FAILED tests/test_slug.py::test_rejeita_slug_vazio\n")
    configuracao = {"run_tests": True, "test_execution": {"failed": 1, "output": saida}}
    assert build_context(_payload(configuracao))["failing_tests"] == [
        "tests/test_slug.py::test_rejeita_slug_vazio"]


# cenario: context emite os testes falhando com nome
def test_falha_sem_nome_extraivel_vira_limitacao_em_vez_de_nome_inventado():
    """Runner que nao imprime o nodeid deixaria `failing_tests` vazio -- e vazio,
    neste payload, significa "nao ha". A limitacao e' o que impede a lista vazia
    de mentir."""
    configuracao = {"run_tests": True,
                    "test_execution": {"failed": 3, "output": "3 tests failed\n"}}
    resultado = build_context(_payload(configuracao, verdict="reprovado"))
    assert resultado["failing_tests"] == []
    assert resultado["limitations"] == [
        "3 teste(s) falharam e nenhum nome foi extraído da saída da suíte"]


# cenario: sem lacuna nenhuma o payload sai vazio e nao omitido
def test_sem_lacuna_nenhuma_o_payload_sai_vazio_e_nao_omitido():
    """Chave ausente e' ambigua entre "nada a fazer" e "o Sentry nao olhou"; lista
    vazia e' conclusiva. E' a mesma disciplina que separa `nao aplicavel` de
    `nao coberta` no resto do produto."""
    configuracao = _cobertura(changed=(10,), measured=(10,), executed=(10,))
    resultado = build_context(_payload(configuracao))
    assert set(resultado) == CHAVES
    assert all(resultado[chave] == [] for chave in CHAVES - {"summary"})
    assert resultado["summary"] == {"verdict": "aprovado", "findings": 0, "tests_executed": True}


# cenario: sem lacuna nenhuma o payload sai vazio e nao omitido
def test_execucao_sem_testes_declara_que_ninguem_mediu():
    """`uncovered_lines` vazio com `tests_executed` falso diz "ninguem mediu", que
    e' diferente de "nada ficou descoberto" -- e a diferenca decide se o agente
    escreve teste ou segue em frente."""
    configuracao = {"run_tests": False,
                    "git_change": {"changed_lines": {"src/app.py": (10, 11)}},
                    "error_paths": {"uncovered": (), "limitations": [
                        "src/app.py: 1 caminho(s) de erro alterado(s) sem dados de cobertura"]}}
    resultado = build_context(_payload(configuracao, verdict="inconclusivo"))
    assert resultado["summary"]["tests_executed"] is False
    assert resultado["uncovered_lines"] == []
    assert resultado["limitations"] == [
        "src/app.py: 1 caminho(s) de erro alterado(s) sem dados de cobertura"]


# cenario: sem lacuna nenhuma o payload sai vazio e nao omitido
def test_execucao_sem_spec_traz_as_chaves_de_intencao_vazias():
    """No modo sem spec nao ha cenario, classe nem marcador a cobrar. As chaves
    continuam existindo: some-las faria o agente supor que o Sentry as omitiu."""
    configuracao = {"without_spec": True, "run_tests": True, "spec": "nenhuma spec declarada",
                    "traceability": {"scenarios": [], "scenarios_without_tests": [],
                                     "orphan_markers": []}}
    resultado = build_context(_payload(configuracao))
    assert set(resultado) == CHAVES
    assert resultado["scenarios_without_tests"] == []
    assert resultado["missing_equivalence_classes"] == []
    assert resultado["orphan_markers"] == []


# cenario: sem lacuna nenhuma o payload sai vazio e nao omitido
def test_payload_sem_configuracao_nenhuma_ainda_traz_todas_as_chaves():
    """Execucao gravada por uma versao anterior, ou payload truncado: a funcao e'
    pura e nao pode explodir por chave ausente -- o comando dela seria justamente
    o usado para entender o que aconteceu."""
    resultado = build_context({"data": {}})
    assert set(resultado) == CHAVES
    assert resultado["summary"] == {"verdict": None, "findings": 0, "tests_executed": False}
