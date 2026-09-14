from __future__ import annotations
from ..ports.inputs import CoverageData, GitChange

def calculate_changed_coverage(change: GitChange, coverage: CoverageData) -> CoverageData:
    if coverage.error or not coverage.executed_lines:
        return CoverageData(coverage.global_percent, coverage.files, error=coverage.error or "dados de linhas ausentes", executed_lines=coverage.executed_lines or {}, excluded_lines=coverage.excluded_lines or {}, measured_lines=coverage.measured_lines or {})
    # O denominador e' linha que a ferramenta mediu, nao linha que o diff tocou.
    # Contando tudo, comentario, linha em branco e arquivo sem cobertura (um YAML de
    # workflow, um Markdown) entravam como descobertos: neste codigo, cuja convencao
    # e' registrar o porque de cada decisao, escrever o comentario derrubava a nota
    # da propria mudanca e produzia um `coverage-below-threshold` falso.
    #
    # Statement medido e' o que sobra depois disso -- executado ou nao. Tirar do
    # denominador o que nao foi executado esconderia ausencia de teste, que e'
    # exatamente o que esta medida existe para acusar.
    changed = []
    covered = []
    measured_by_file = coverage.measured_lines or {}
    for filename, lines in (change.changed_lines or {}).items():
        countable = set(lines) & set(measured_by_file.get(filename, ()))
        changed.extend(countable)
        covered.extend(countable & set(coverage.executed_lines.get(filename, ())))
    # Sem linha mensuravel alterada nao ha percentual a afirmar. `None` aqui e'
    # "nao havia o que medir", e quem le as regras precisa distingui-lo de zero.
    percent = (len(set(covered)) / len(set(changed)) * 100) if changed else None
    return CoverageData(coverage.global_percent, coverage.files, changed_percent=percent, error=coverage.error, executed_lines=coverage.executed_lines, excluded_lines=coverage.excluded_lines, measured_lines=coverage.measured_lines)
