from __future__ import annotations
import json, sqlite3
from pathlib import Path
from ..domain.models import Run, to_dict

def load_runs(root:Path):
    db=root/'.sentry'/'sentry.db'
    if not db.exists(): return []
    with sqlite3.connect(db) as conn:
        rows=conn.execute('SELECT payload FROM runs ORDER BY rowid').fetchall()
    return [json.loads(row[0]) for row in rows]

def markdown_report(payload):
    data=payload['data']; verdict=data.get('verdict') or {}; status=verdict.get('status','inconclusivo')
    lines=[f"# Sentry Report",'',f"- Run: `{data.get('id')}`",f"- Projeto: `{data.get('project')}`",f"- Veredito: **{status}**",'', '## Métricas', '', f"- Achados: {len(data.get('findings',[]))}", '', '## Achados', '']
    findings=data.get('findings',[])
    lines += [f"- **{item.get('severity')}** — {item.get('message')} — Recomendação: {item.get('recommendation')}" for item in findings] or ['- Nenhum achado registrado.']
    return '\n'.join(lines)+'\n'

def write_reports(root:Path,payload):
    reports=root/'.sentry'/'reports'; reports.mkdir(parents=True,exist_ok=True); run_id=payload['data']['id']; md=markdown_report(payload)
    (reports/'latest.md').write_text(md,encoding='utf8'); (reports/f'{run_id}.md').write_text(md,encoding='utf8'); (reports/f'{run_id}.json').write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf8')
    return md

def compare(first,second):
    a={x.get('rule') for x in first['data'].get('findings',[])}; b={x.get('rule') for x in second['data'].get('findings',[])}
    return {'new':sorted(b-a),'resolved':sorted(a-b),'persistent':sorted(a&b)}