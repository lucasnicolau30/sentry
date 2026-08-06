from __future__ import annotations
import json
import sqlite3
from pathlib import Path

def load_runs(root: Path):
    db = root / ".sentry" / "sentry.db"
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT payload FROM runs ORDER BY rowid").fetchall()
    return [json.loads(row[0]) for row in rows]

def markdown_report(payload):
    data = payload["data"]
    verdict = data.get("verdict") or {}
    config = data.get("configuration") or {}
    git_change = config.get("git_change") or {}
    traceability = config.get("traceability") or {}
    impact = config.get("impact") or {}
    coverage = config.get("coverage") or {}
    execution = config.get("test_execution") or {}
    def percent(value):
        return f"{value:.2f}%".replace(".", ",") if value is not None else "indisponivel"
    files = git_change.get("files", [])
    changed_lines = git_change.get("changed_lines", {})
    lines = [
        "# Sentry Report", "",
        f"- Run: {data.get('id')}",
        f"- Projeto: {data.get('project')}",
        f"- Veredito: **{verdict.get('status', 'inconclusivo')}**", "",
        "## Contexto", "",
        f"- Arquivos alterados: {len(files)}",
        f"- Testes impactados: {len(impact.get('impacted', []))}",
        f"- Testes n\u00e3o relacionados: {len(impact.get('unrelated', []))}",
        f"- Cen\u00e1rios sem teste: {len(traceability.get('scenarios_without_tests', []))}",
        f"- Cobertura global: {percent(coverage.get('global_percent'))}",
        f"- Cobertura alterada: {percent(coverage.get('changed_percent'))}",
        f"- Testes: {execution.get('passed', 0)} passados, {execution.get('failed', 0)} falhos, {execution.get('skipped', 0)} ignorados, {execution.get('not_run', 0)} nao executados",
        f"- Duracao: {execution.get('duration_seconds', 'indisponivel')} s",
        "", "### Execucao de testes", "",
    ]
    if execution:
        lines += [
            f"- Comando: `{execution.get('command', 'indisponivel')}`",
            f"- Saida resumida:",
            f"```",
            f"{execution.get('output', '')[-1500:]}",
            f"```",
        ]
    lines += ["", "### Arquivos alterados", "",]
    lines += [f"- {path}" for path in files] or ["- Nenhum arquivo alterado detectado."]
    lines += ["", "## Limita\u00e7\u00f5es", ""]
    limitations = impact.get("limitations", [])
    lines += [f"- {item}" for item in limitations] or ["- Nenhuma limita\u00e7\u00e3o registrada."]
    lines += ["", "## M\u00e9tricas", "", f"- Achados: {len(data.get('findings', []))}", "", "## Achados", ""]
    findings = data.get("findings", [])
    lines += [f"- [{item.get('severity')}] {item.get('message')} - Recomendacao: {item.get('recommendation')}" for item in findings] or ["- Nenhum achado registrado."]
    return "\n".join(lines) + "\n"

def write_reports(root: Path, payload):
    reports = root / ".sentry" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    run_id = payload["data"]["id"]
    markdown = markdown_report(payload)
    (reports / "latest.md").write_text(markdown, encoding="utf8")
    (reports / f"{run_id}.md").write_text(markdown, encoding="utf8")
    (reports / f"{run_id}.json").write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf8")
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
