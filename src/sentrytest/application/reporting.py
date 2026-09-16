from __future__ import annotations
import json
import re
import sqlite3
from pathlib import Path

def load_runs(root: Path):
    db = root / ".sentry" / "sentry.db"
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT payload FROM runs ORDER BY rowid").fetchall()
    return [json.loads(row[0]) for row in rows]

def clear_history(root: Path, keep_last: int = 0, apply: bool = False) -> dict:
    """Poda execuções e relatórios, preservando as `keep_last` mais recentes.

    Nunca toca em `.sentry/specs/`: spec é intenção declarada pelo usuário, não
    evidência gerada. Com `apply=False` apenas relata o escopo — apagar
    histórico é irreversível, então o padrão é mostrar antes de destruir.
    """
    reports, runs_dir = root / ".sentry" / "reports", root / ".sentry" / "runs"
    ordered = [item["data"].get("id") for item in load_runs(root)]
    keep = set(ordered[-keep_last:]) if keep_last > 0 else set()
    removing = [run_id for run_id in ordered if run_id not in keep]

    files = [path for run_id in removing for path in (
        runs_dir / f"{run_id}.json", runs_dir / f"{run_id}-coverage.json",
        reports / f"{run_id}.md", reports / f"{run_id}.json",
    ) if path.exists()]
    # latest.md aponta para a execução mais recente: só sai quando nada é mantido.
    latest = reports / "latest.md"
    if not keep and latest.exists():
        files.append(latest)

    if apply:
        for path in files:
            path.unlink()
        database = root / ".sentry" / "sentry.db"
        if removing and database.exists():
            with sqlite3.connect(database) as conn:
                conn.executemany("DELETE FROM runs WHERE id = ?", [(run_id,) for run_id in removing])
    return {
        "removed_runs": removing,
        "kept_runs": [run_id for run_id in ordered if run_id in keep],
        "files": [str(path.relative_to(root)) for path in files],
        "applied": apply,
    }

_SEVERITY_ORDER = {"crítica": 0, "alta": 1, "média": 2, "baixa": 3}
_CASE_ID = re.compile(r"^(TC-\d+)-")
_VERDICT_MEANING = {
    "aprovado": "nenhum achado relevante — pode seguir.",
    "aprovado com ressalvas": "há achado(s) de severidade alta; revise antes de seguir.",
    "reprovado": "há achado de severidade crítica — não deveria seguir sem corrigir.",
    "inconclusivo": "sem evidência suficiente para decidir; não é reprovação nem aprovação.",
}

# O relatorio nao tem tokenizer e nao deveria ter: importar um so' para imprimir
# um numero trocaria uma estimativa declarada por uma precisao que o argumento nao
# precisa -- e amarraria o Sentry ao tokenizer de um modelo especifico, quando o
# ponto e' justamente nao depender de nenhum. 4 caracteres por token e' a mesma
# regra usada na medicao de AVALIACAO-PRODUTO.md, e vai dita no relatorio.
_CHARS_PER_TOKEN = 4

def _thousands(value: int) -> str:
    """Separador de milhar em pt-BR. Numero de seis digitos sem separador se le
    errado de relance, e o bloco de custo existe justamente para ser lido de relance."""
    return f"{value:,}".replace(",", ".")

def _measure(text: str) -> tuple[int, int]:
    """(bytes UTF-8, tokens aproximados).

    Bytes e caracteres divergem em portugues -- cada acento custa dois bytes e um
    caractere so'. Medir o tamanho em bytes e estimar o token em caracteres mantem
    cada numero fiel ao que ele diz ser; derivar um do outro faria o relatorio
    afirmar uma equivalencia que nao existe.
    """
    return len(text.encode("utf-8")), round(len(text) / _CHARS_PER_TOKEN)

def _summarized_size(git_change: dict) -> tuple[int, int] | None:
    """(bytes, tokens) do diff que o relatorio resumiu, ou None quando nao da' para medir.

    O tamanho vem gravado como dois inteiros, nao como o texto: persistir o diff
    inteiro custaria dezenas de KB por execucao no SQLite e no JSON para produzir
    duas linhas de relatorio -- o bloco de custo nao pode ser, ele mesmo, caro.
    Ainda assim o texto e' aceito quando estiver a mao (payload em memoria, teste),
    porque medir a fonte e' sempre melhor que confiar no numero de terceiros.

    Sem nenhum dos dois nao ha medicao: deduzir bytes da lista de nomes de arquivo
    daria um numero plausivel e falso, justamente no bloco que existe para provar
    que o Sentry mede em vez de estimar.
    """
    diff = git_change.get("diff")
    if isinstance(diff, str) and diff:
        return _measure(diff)
    size, chars = git_change.get("diff_bytes"), git_change.get("diff_chars")
    if isinstance(size, int) and size > 0:
        # `diff_chars` ausente cai para os bytes: em diff predominantemente ASCII os
        # dois coincidem, e a diferenca some no arredondamento de uma estimativa que
        # ja se declara aproximada. O que nao pode e' calar o tamanho por causa disso.
        return size, round((chars if isinstance(chars, int) and chars > 0 else size) / _CHARS_PER_TOKEN)
    return None

def _cost_section(report_so_far: str, git_change: dict) -> list[str]:
    """Bloco `## Custo`: o preco de rodar o Sentry a cada iteracao, em numero.

    Zero token nao e' economia de implementacao, e' a razao de o veredito ser
    reproduzivel: nenhum modelo e' chamado em ponto nenhum da analise, entao o
    mesmo commit produz o mesmo relatorio sempre. O contraponto -- quantos tokens
    o agente gastaria lendo o diff cru -- e' o que transforma isso em argumento.

    O relatorio se mede a si mesmo antes de anexar o bloco, e diz isso. Incluir o
    bloco na propria conta seria impossivel (o numero muda o texto que o produz), e
    calar sobre a exclusao seria a mentira pequena que desmoraliza o resto.
    """
    report_bytes, report_tokens = _measure(report_so_far)
    lines = ["", "## Custo", "",
        "- Tokens gastos pelo Sentry: **zero**. Nenhum modelo é chamado em nenhum ponto "
        "da análise — é por isso que o mesmo commit sempre produz o mesmo veredito.",
    ]
    summarized = _summarized_size(git_change)
    if summarized:
        diff_bytes, diff_tokens = summarized
        lines.append(f"- Diff resumido: {_thousands(diff_bytes)} bytes ≈ {_thousands(diff_tokens)} tokens")
    else:
        lines.append("- Diff resumido: indisponível — o payload não trouxe o tamanho do diff, "
                     "e estimar bytes a partir da lista de arquivos seria inventar a medição.")
    lines.append(f"- Este relatório: {_thousands(report_bytes)} bytes ≈ {_thousands(report_tokens)} tokens "
                 "(medido sem este bloco de custo)")
    if summarized and report_tokens:
        ratio = diff_tokens / report_tokens
        # Mudanca pequena demais para haver o que resumir: o cabecalho fixo do
        # relatorio pesa mais que o diff. Dizer "0,4x menor" ali seria numero certo
        # com leitura errada -- o produto nao ganha nada fingindo ganho onde nao ha.
        lines.append(f"- Razão: o relatório é {f'{ratio:.1f}'.replace('.', ',')}× menor que o diff cru."
                     if ratio >= 1 else
                     "- Razão: o relatório é maior que o diff — a mudança é pequena demais "
                     "para haver o que resumir.")
    lines += ["",
        f"> Conversão a {_CHARS_PER_TOKEN} caracteres por token, sem tokenizer real: é ordem de "
        "grandeza para dimensionar o orçamento de contexto, não contagem exata.",
    ]
    return lines

def _case_display(case: dict) -> tuple[str, str]:
    """(tag curto, nome legível). O `id` normaliza acento para virar slug de
    arquivo; usar `name` (quando presente) evita mostrar um nome sem acento."""
    case_id = case.get("id") or ""
    match = _CASE_ID.match(case_id)
    tag = match.group(1) if match else case_id
    name = case.get("name") or (case_id[match.end():].replace("-", " ") if match else case_id)
    return tag, name

def markdown_report(payload):
    data = payload["data"]
    verdict = data.get("verdict") or {}
    config = data.get("configuration") or {}
    git_change = config.get("git_change") or {}
    traceability = config.get("traceability") or {}
    impact = config.get("impact") or {}
    coverage = config.get("coverage") or {}
    execution = config.get("test_execution") or {}
    findings = data.get("findings", [])
    # `status` trata o projeto inteiro como alterado; vários rotulos pensados para
    # diff (o que "alterado" significa, por que a cobertura alterada repete a
    # global) ficam enganosos sem dizer isso.
    whole_project = bool(config.get("whole_project"))
    def percent(value):
        return f"{value:.2f}%".replace(".", ",") if value is not None else "indisponivel"
    files = git_change.get("files", [])
    status = verdict.get("status", "inconclusivo")
    # Selo de frescor: sem o commit e o instante gravados, um relatorio antigo se
    # apresenta como veredito atual -- e' o que `latest.md` fazia. Aqui e' so o
    # registro; quem confronta com o HEAD e acusa e' `sentry report`.
    lines = [
        "# Sentry Report", "",
        f"- Run: {data.get('id')}",
        f"- Projeto: {data.get('project')}",
        f"- Commit analisado: {data.get('commit') or 'indisponível (não é repositório Git)'}",
        f"- Analisado em: {data.get('timestamp') or 'indisponivel'}",
        f"- Veredito: **{status}** — {_VERDICT_MEANING.get(status, '')}",
    ]
    if whole_project:
        lines.append("- Escopo: **projeto inteiro** — todo arquivo de código-fonte foi tratado "
                     "como alterado; isto não é um diff.")
    # Mesma disciplina do selo de frescor: evidencia reusada tem que se declarar
    # reusada. Um relatorio que volta do cache sem dizer converte a execucao de
    # ontem em afirmacao de hoje -- e o usuario nao tem como perceber a troca.
    cached_from = config.get("cached_from") or {}
    if config.get("from_cache"):
        lines.append(f"- Execução reaproveitada do cache: nada foi executado agora; a evidência é da "
                     f"execução {cached_from.get('run_id') or 'anterior'} de "
                     f"{cached_from.get('timestamp') or 'instante indisponível'}.")
    lines.append("")
    # O achado e' o motivo do veredito: vem logo apos ele, antes de qualquer
    # evidencia bruta (arquivos, saida do pytest) que so sustenta o achado.
    lines += ["## Achados", ""]
    ordered_findings = sorted(findings, key=lambda item: _SEVERITY_ORDER.get(item.get("severity"), 9))
    lines += [f"- [{item.get('severity')}] `{item.get('rule')}` — {item.get('message')} — {item.get('recommendation')}" for item in ordered_findings] or ["- Nenhum achado registrado."]
    # Cobertura reusada continua sendo cobertura medida -- so' que de outra rodada.
    # Sem o carimbo, o numero da execucao completa de ontem se apresenta como
    # medicao de agora, que e' exatamente o que o modo instantaneo nao fez.
    reused = coverage.get("reused_from") or {}
    reuse_note = (f" — medida na execução anterior ({reused.get('timestamp') or 'instante indisponível'}), "
                  "não nesta rodada") if reused else ""
    lines += ["", "## Contexto", "",
        f"- Arquivos alterados: {len(files)}",
        f"- Testes impactados: {len(impact.get('impacted', []))}",
        f"- Testes não relacionados: {len(impact.get('unrelated', []))}",
        f"- Cenários sem teste: {len(traceability.get('scenarios_without_tests', []))}",
        f"- Cobertura global (todo o projeto): {percent(coverage.get('global_percent'))}{reuse_note}",
        f"- Cobertura alterada (só o código desta mudança): {percent(coverage.get('changed_percent'))}{reuse_note}"
        + (" — igual à global, porque todo o projeto foi tratado como alterado" if whole_project else ""),
    ]
    if whole_project:
        files_pct = coverage.get("files") or {}
        zero_coverage = sorted(name for name, pct in files_pct.items() if pct == 0)
        lines += ["", "## Arquivos sem nenhum teste alcançando", "",
            "> 0% de cobertura no projeto inteiro — nenhuma linha destes arquivos foi "
            "executada por nenhum teste. Não é lacuna de spec, é ausência de execução.", ""]
        lines += [f"- {name}" for name in zero_coverage] or ["- Nenhum arquivo com 0% de cobertura."]
    # No modo instantaneo nao ha execucao desta rodada, e `0 passados, 0 falhos` se le
    # como medicao que deu zero -- a mesma confusao entre "nada a medir" e "nada mudou"
    # de que o proprio codigo se defende no diff. A cobertura reusada ja vem carimbada;
    # a contagem de testes precisa do mesmo cuidado.
    if not execution:
        lines += ["- Testes: a suíte não foi executada nesta análise (modo instantâneo)",
                  "- Duracao: não se aplica"]
    else:
        lines += [
            f"- Testes: {execution.get('passed', 0)} passados, {execution.get('failed', 0)} falhos, {execution.get('skipped', 0)} ignorados, {execution.get('not_run', 0)} nao executados",
            f"- Duracao: {execution.get('duration_seconds', 'indisponivel')} s",
        ]
    # So' aparece quando [e2e] esta declarado: a chave e' ausente, nao nula, num
    # projeto sem segunda suite -- mesma disciplina do resto do relatorio.
    e2e_execution = config.get("e2e_execution")
    if e2e_execution:
        lines += [
            f"- Testes e2e: {e2e_execution.get('passed', 0)} passados, {e2e_execution.get('failed', 0)} falhos, "
            f"{e2e_execution.get('skipped', 0)} ignorados, {e2e_execution.get('not_run', 0)} nao executados",
            f"- Duracao e2e: {e2e_execution.get('duration_seconds', 'indisponivel')} s",
        ]
    dimensions = config.get("dimensions") or []
    if dimensions:
        lines += ["", "## Dimensões de cobertura", "",
                  "| Dimensão | Status | Evidência | Justificativa |",
                  "| --- | --- | --- | --- |"]
        lines += [f"| {item.get('dimension')} | {item.get('status')} | {item.get('evidence') or '—'} | {item.get('justification')} |"
                  for item in dimensions]
    test_cases = data.get("test_cases", [])
    if test_cases:
        cases_summary = config.get("cases") or {}
        lines += ["", "## Matriz de casos", "",
            f"- Total: {cases_summary.get('total', len(test_cases))}",
            f"- Por status: {', '.join(f'{k}={v}' for k, v in (cases_summary.get('by_status') or {}).items()) or 'indisponivel'}",
        ]
        for layer in ("backend", "integração", "frontend"):
            in_layer = [case for case in test_cases if case.get("layer") == layer]
            if not in_layer:
                continue
            lines += ["", f"### {layer.capitalize()}", ""]
            for case in in_layer:
                related = case.get("related_test") or "sem teste associado"
                tag, name = _case_display(case)
                # Trace/screenshot do Playwright: a unica evidencia que um caso de
                # frontend tem alem do teste associado, porque nao existe cobertura
                # de linha para citar aqui.
                evidence_paths = [item.get("path") for item in (case.get("evidences") or [])
                                  if item.get("source") == "playwright" and item.get("path")]
                evidence_note = f" — evidência: {', '.join(evidence_paths)}" if evidence_paths else ""
                lines.append(f"- `{case.get('status')}` **{name}** ({tag}) — {case.get('expected_result')} ({case.get('priority')}, {case.get('test_type')}) — {related}{evidence_note}")

    infrastructure = data.get("infrastructure_errors") or []
    if infrastructure:
        lines += ["", "## Erros de infraestrutura", "",
            "> Evidência incompleta: estas falhas são de ambiente, não de qualidade do código.", ""]
        lines += [f"- **{item.get('stage')}** ({item.get('cause')}): {item.get('message')}"
                  + (" — pode ser repetido" if item.get("retryable") else "") for item in infrastructure]
    lines += ["", "## Limitações", "",
        "> O Sentry não conseguiu verificar isto — não é aprovação nem reprovação, é ausência de evidência.", ""]
    error_paths = config.get("error_paths") or {}
    limitations = list(impact.get("limitations", [])) + list(error_paths.get("limitations", [])) + list(config.get("catalog_limitations", []))
    lines += [f"- {item}" for item in limitations] or ["- Nenhuma limitação registrada."]
    justified_classes = config.get("justified_classes") or []
    if justified_classes:
        lines += ["", "## Classes não aplicáveis", "",
            "> Dispensadas de propósito, com justificativa declarada no CASES.md — não é lacuna do Sentry.", ""]
        lines += [f"- {item}" for item in justified_classes]
    # Evidencia bruta por ultimo: sustenta os achados de cima, mas nao e' o que
    # se le primeiro para decidir se o veredito faz sentido.
    lines += ["", "## Evidência", "", "### Arquivos alterados", ""]
    # Contra o que se comparou muda inteiramente o que "alterado" significa. Sem
    # declarar isso, uma analise de branch e uma analise da arvore de trabalho sao
    # indistinguiveis no relatorio -- e nenhuma das duas e' auditavel.
    reference = git_change.get("reference")
    if whole_project:
        lines += ["- Comparado com: nada — projeto inteiro tratado como alterado", ""]
    else:
        lines += [f"- Comparado com: `{reference}`" if reference and reference != "HEAD"
                  else "- Comparado com: árvore de trabalho contra `HEAD`", ""]
    lines += [f"- {path}" for path in files] or ["- Nenhum arquivo alterado detectado."]
    if execution:
        lines += ["", "### Execução de testes", "",
            f"- Comando: `{execution.get('command', 'indisponivel')}`",
            f"- Saida resumida:",
            f"```",
            f"{execution.get('output', '')[-1500:]}",
            f"```",
        ]
    # O custo vai por ultimo porque nao sustenta o veredito: e' o preco de te-lo, e
    # so' faz sentido depois de ver o que foi entregue. Medir aqui tambem e' o que
    # permite ao relatorio dizer o proprio tamanho sem contar o bloco que o diz.
    lines += _cost_section("\n".join(lines) + "\n", git_change)
    return "\n".join(lines) + "\n"

def staleness(payload, head: str | None) -> str | None:
    """Acusação a emitir antes de exibir um relatório cujo commit não é mais o HEAD.

    O relatório é evidência datada, e o único artefato versionado (`latest.md`) é
    justamente o que mais engana quando desatualiza: exibi-lo sem ressalva afirma um
    veredito sobre código que já mudou.

    None quando não há o que acusar — inclusive fora de repositório Git, onde não há
    HEAD com que comparar. Ausência de commit é limitação declarada no cabeçalho, não
    licença para acusar desatualização que não se pode comprovar.
    """
    commit = (payload.get("data") or {}).get("commit")
    if not commit or not head or commit == head:
        return None
    return (f"Relatório desatualizado: analisado em {commit[:12]}, o HEAD atual é "
            f"{head[:12]}. Não é o veredito do código atual — rode sentry run de novo.")

def write_reports(root: Path, payload):
    reports = root / ".sentry" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    run_id = payload["data"]["id"]
    markdown = markdown_report(payload)
    (reports / "latest.md").write_text(markdown, encoding="utf-8")
    (reports / f"{run_id}.md").write_text(markdown, encoding="utf-8")
    (reports / f"{run_id}.json").write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    return markdown

def _delta(current, previous):
    if current is None or previous is None:
        return None
    return round(current - previous, 2)

def compare(first, second):
    a = {item.get("rule") for item in first["data"].get("findings", [])}
    b = {item.get("rule") for item in second["data"].get("findings", [])}
    result = {"new": sorted(b - a), "resolved": sorted(a - b), "persistent": sorted(a & b)}

    config_a = first["data"].get("configuration") or {}
    config_b = second["data"].get("configuration") or {}
    coverage_a = config_a.get("coverage") or {}
    coverage_b = config_b.get("coverage") or {}
    execution_a = config_a.get("test_execution") or {}
    execution_b = config_b.get("test_execution") or {}

    reasons = []
    if bool(config_a.get("run_tests")) != bool(config_b.get("run_tests")):
        reasons.append("execução de testes habilitada em apenas uma das execuções")
    if bool(coverage_a.get("error")) != bool(coverage_b.get("error")):
        reasons.append("base de cobertura indisponível em uma das execuções")
    comparable = not reasons
    result["comparable"] = comparable
    result["incomparable_reasons"] = reasons

    result["coverage"] = {
        "global_percent_delta": _delta(coverage_b.get("global_percent"), coverage_a.get("global_percent")),
        "changed_percent_delta": _delta(coverage_b.get("changed_percent"), coverage_a.get("changed_percent")),
    } if comparable else None

    result["tests"] = {
        "passed_delta": execution_b.get("passed", 0) - execution_a.get("passed", 0),
        "failed_delta": execution_b.get("failed", 0) - execution_a.get("failed", 0),
        "skipped_delta": execution_b.get("skipped", 0) - execution_a.get("skipped", 0),
        "not_run_delta": execution_b.get("not_run", 0) - execution_a.get("not_run", 0),
    } if comparable else None

    verdict_a = (first["data"].get("verdict") or {}).get("status")
    verdict_b = (second["data"].get("verdict") or {}).get("status")
    result["verdict"] = {"from": verdict_a, "to": verdict_b, "changed": verdict_a != verdict_b}
    return result
