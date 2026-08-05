from pathlib import Path
from sentry.adapters.markdown_specs import MarkdownSpecAdapter
from sentry.adapters.local_tools import CoverageAdapter

def test_markdown_spec_adapter_reads_structured_scenario(tmp_path:Path):
    p=tmp_path/'SPEC.md'; p.write_text('### Cenário: acesso negado\n- Dado: usuário sem permissão\n- Quando: solicita recurso\n- Então: responde 403\n',encoding='utf8')
    scenario=MarkdownSpecAdapter(p).scenarios()[0]
    assert scenario.given=='usuário sem permissão' and scenario.then=='responde 403'

def test_coverage_adapter_reports_missing_evidence(tmp_path:Path):
    result=CoverageAdapter().read(tmp_path/'coverage.xml')
    assert result.error=='arquivo de cobertura ausente'