import json
from pathlib import Path
from sentry.application.reporting import compare, markdown_report

def payload(run_id, rules):
    return {'data': {'id':run_id,'project':'demo','verdict':{'status':'inconclusivo'},'findings':[{'rule':r,'severity':'alta','message':r,'recommendation':'corrigir'} for r in rules]}}

def test_markdown_and_comparison():
    report=markdown_report(payload('r1',['a']))
    assert '# Sentry Report' in report
    assert compare(payload('r1',['a']),payload('r2',['b'])) == {'new':['b'],'resolved':['a'],'persistent':[]}