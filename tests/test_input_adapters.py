from pathlib import Path
from sentrytest.adapters.local_tools import CoverageAdapter

def test_coverage_adapter_reports_missing_evidence(tmp_path:Path):
    result=CoverageAdapter().read(tmp_path/'coverage.xml')
    assert result.error=='arquivo de cobertura ausente'
