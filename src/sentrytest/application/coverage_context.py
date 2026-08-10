from __future__ import annotations
from ..ports.inputs import CoverageData, GitChange

def calculate_changed_coverage(change: GitChange, coverage: CoverageData) -> CoverageData:
    if coverage.error or not coverage.executed_lines:
        return CoverageData(coverage.global_percent, coverage.files, error=coverage.error or "dados de linhas ausentes", executed_lines=coverage.executed_lines or {}, excluded_lines=coverage.excluded_lines or {})
    changed = []
    covered = []
    for filename, lines in (change.changed_lines or {}).items():
        changed.extend(lines)
        covered.extend(set(lines) & set(coverage.executed_lines.get(filename, ())))
    percent = (len(set(covered)) / len(set(changed)) * 100) if changed else None
    return CoverageData(coverage.global_percent, coverage.files, changed_percent=percent, error=coverage.error, executed_lines=coverage.executed_lines, excluded_lines=coverage.excluded_lines)
