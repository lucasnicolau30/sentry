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
    def percent(value):
        return f"{value:.2f}%".replace(".", ",") if value is not None else "indisponivel"
    files = git_change.get("files", [])
    status = verdict.get("status", "inconclusivo")
    lines = [
        "# Sentry Report", "",
        f"- Run: {data.get('id')}",
        f"- Projeto: {data.get('project')}",
        f"- Veredito: **{status}** — {_VERDICT_MEANING.get(status, '')}", "",
    ]
    # O achado e' o motivo do veredito: vem logo apos ele, antes de qualquer
    # evidencia bruta (arquivos, saida do pytest) que so sustenta o achado.
    lines += ["## Achados", ""]
    ordered_findings = sorted(findings, key=lambda item: _SEVERITY_ORDER.get(item.get("severity"), 9))
    lines += [f"- [{item.get('severity')}] `{item.get('rule')}` — {item.get('message')} — {item.get('recommendation')}" for item in ordered_findings] or ["- Nenhum achado registrado."]
    lines += ["", "## Contexto", "",
        f"- Arquivos alterados: {len(files)}",
        f"- Testes impactados: {len(impact.get('impacted', []))}",
        f"- Testes não relacionados: {len(impact.get('unrelated', []))}",
        f"- Cenários sem teste: {len(traceability.get('scenarios_without_tests', []))}",
        f"- Cobertura global (todo o projeto): {percent(coverage.get('global_percent'))}",
        f"- Cobertura alterada (só o código desta mudança): {percent(coverage.get('changed_percent'))}",
        f"- Testes: {execution.get('passed', 0)} passados, {execution.get('failed', 0)} falhos, {execution.get('skipped', 0)} ignorados, {execution.get('not_run', 0)} nao executados",
        f"- Duracao: {execution.get('duration_seconds', 'indisponivel')} s",
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
        for layer in ("backend", "integração"):
            in_layer = [case for case in test_cases if case.get("layer") == layer]
            if not in_layer:
                continue
            lines += ["", f"### {layer.capitalize()}", ""]
            for case in in_layer:
                related = case.get("related_test") or "sem teste associado"
                tag, name = _case_display(case)
                lines.append(f"- `{case.get('status')}` **{name}** ({tag}) — {case.get('expected_result')} ({case.get('priority')}, {case.get('test_type')}) — {related}")

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
    return "\n".join(lines) + "\n"

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
