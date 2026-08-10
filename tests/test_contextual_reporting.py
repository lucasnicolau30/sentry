from sentrytest.application.reporting import markdown_report

# cenario: achados aparecem antes da evidência bruta
def test_markdown_report_puts_findings_before_raw_evidence():
    """O achado e' o motivo do veredito: tem que aparecer antes de arquivos
    alterados e saida do pytest, que so sustentam o achado."""
    payload = {"data": {"id": "run-4", "project": "demo", "verdict": {"status": "aprovado com ressalvas"},
        "findings": [{"rule": "scenario-without-test", "severity": "alta", "message": "cenario sem teste", "recommendation": "adicionar teste"}],
        "configuration": {"git_change": {"files": ["src/app.py"]}, "test_execution": {"command": "pytest", "output": "1 passed"}}}}
    report = markdown_report(payload)
    assert report.index("## Achados") < report.index("### Arquivos alterados")
    assert report.index("## Achados") < report.index("### Execução de testes")

# cenario: identificador do caso não repete o nome legível
def test_markdown_report_shows_readable_case_name_separate_from_id():
    """TC-01-nome-do-caso-inteiro-repetido e' dificil de escanear: o nome legivel
    do caso vem em destaque, o id vira so uma marca curta ao lado."""
    payload = {"data": {"id": "run-5", "project": "demo", "verdict": {"status": "aprovado"}, "findings": [],
        "test_cases": [{"id": "TC-01-rejeita-slug-vazio", "layer": "backend", "status": "coberto",
            "expected_result": "levanta erro", "priority": "alta", "test_type": "unitário", "related_test": "tests/test_x.py"}]}}
    report = markdown_report(payload)
    assert "**rejeita slug vazio**" in report
    assert "(TC-01)" in report

def test_markdown_report_shows_context():
    payload = {"data": {"id": "run-1", "project": "demo", "verdict": {"status": "inconclusivo"}, "findings": [], "configuration": {
        "git_change": {"files": ["src/app.py"]},
        "traceability": {"scenarios_without_tests": ["login"]},
        "impact": {"impacted": [{"path": "tests/test_app.py"}], "unrelated": [], "limitations": ["selecao estatica"]},
        "coverage": {"global_percent": 80.0, "changed_percent": 50.0},
    }}}
    report = markdown_report(payload)
    assert "Arquivos alterados: 1" in report
    assert "Testes impactados: 1" in report
    assert "Cen\u00e1rios sem teste: 1" in report
    assert "Cobertura alterada (só o código desta mudança): 50,00%" in report
    assert "selecao estatica" in report

def test_markdown_report_lists_changed_files():
    payload = {"data": {"id": "run-2", "project": "demo", "verdict": {"status": "aprovado"}, "findings": [], "configuration": {
        "git_change": {"files": ["src/app.py"], "changed_lines": {"src/app.py": [2, 3]}},
    }}}
    report = markdown_report(payload)
    assert "- src/app.py" in report

def test_markdown_report_shows_execution_evidence():
    payload = {"data": {"id": "run-3", "project": "demo", "verdict": {"status": "reprovado"}, "findings": [], "configuration": {
        "test_execution": {"command": "python -m pytest", "passed": 10, "failed": 1, "skipped": 2, "not_run": 3, "duration_seconds": 1.5, "output": "1 failed"},
    }}}
    report = markdown_report(payload)
    assert "Comando: `python -m pytest`" in report
    assert "10 passados, 1 falhos, 2 ignorados, 3 nao executados" in report
    assert "1 failed" in report

# cenario: veredito vem com explicacao do que significa
def test_markdown_report_explains_what_the_verdict_means():
    """So mostrar 'aprovado com ressalvas' nao diz o que fazer com isso: precisa
    de uma frase curta dizendo o que aquele status implica na pratica."""
    payload = {"data": {"id": "run-6", "project": "demo", "verdict": {"status": "aprovado com ressalvas"}, "findings": []}}
    report = markdown_report(payload)
    assert "severidade alta" in report

# cenario: achado mostra a regra que disparou
def test_markdown_report_shows_which_rule_triggered_the_finding():
    """Sem o nome da regra, nao ha como cruzar o achado com a tabela de regras
    da SPEC para entender por que ele disparou."""
    payload = {"data": {"id": "run-7", "project": "demo", "verdict": {"status": "reprovado"},
        "findings": [{"rule": "test-failing", "severity": "crítica", "message": "suite com falha", "recommendation": "corrigir"}]}}
    report = markdown_report(payload)
    assert "`test-failing`" in report

# cenario: classe nao aplicavel aparece separada das limitacoes reais
def test_markdown_report_separates_justified_classes_from_real_limitations():
    """Misturar dispensa deliberada com lacuna real do Sentry faz o leitor
    tratar as duas como igualmente preocupantes, quando uma delas nao e'."""
    payload = {"data": {"id": "run-8", "project": "demo", "verdict": {"status": "aprovado"}, "findings": [], "configuration": {
        "catalog_limitations": ["tipos de campo fora do catálogo: matricula"],
        "justified_classes": ["exclude/vazio — é parâmetro de configuração"],
    }}}
    report = markdown_report(payload)
    assert report.index("## Limitações") < report.index("## Classes não aplicáveis")
    assert "matricula" in report.split("## Classes não aplicáveis")[0]
    assert "exclude/vazio" in report.split("## Classes não aplicáveis")[1]
