"""Caminhos de erro alterados que nenhum teste executou.

Em Python a deteccao e por AST: um `raise` ou um `except` e caminho de erro por
estrutura, sem depender de convencao de nomenclatura. Nas demais stacks nao ha
parser na biblioteca padrao, entao a deteccao e por padrao sintatico ancorado no
inicio da linha -- menos preciso, e por isso registrado como limitacao no
relatorio em vez de passar por evidencia da mesma qualidade.

Quem responde se existe teste e a cobertura: se a linha do `throw` nunca
executou, nenhum teste passou por ali. Sem dados de cobertura a regra nao dispara
e registra limitacao, em vez de afirmar ausencia de teste sem evidencia.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

# Ancorados no inicio da linha: um `// pode dar throw` ou uma string contendo
# "throw" nao comecam a linha com a palavra, entao nao viram falso caminho.
_CLIKE = (
    (re.compile(r"^\s*throw\b"), "throw"),
    (re.compile(r"^\s*\}?\s*catch\s*[({]"), "catch"),
)
_GO = (
    (re.compile(r"^\s*panic\s*\("), "panic"),
    # O idioma de erro do Go nao e' excecao: e' o if err != nil.
    (re.compile(r"^\s*if\s+err\s*!=\s*nil\b"), "if err != nil"),
    (re.compile(r"^\s*(?:defer\s+)?.*\brecover\s*\(\s*\)"), "recover"),
)
_RUBY = (
    (re.compile(r"^\s*raise\b"), "raise"),
    (re.compile(r"^\s*rescue\b"), "rescue"),
)
_RUST = (
    (re.compile(r"^\s*panic!\s*\("), "panic!"),
    (re.compile(r"^\s*return\s+Err\s*\("), "return Err"),
)

ERROR_PATTERNS = {
    ".js": _CLIKE, ".jsx": _CLIKE, ".ts": _CLIKE, ".tsx": _CLIKE, ".mjs": _CLIKE, ".cjs": _CLIKE,
    ".java": _CLIKE, ".kt": _CLIKE, ".kts": _CLIKE, ".cs": _CLIKE, ".php": _CLIKE,
    ".go": _GO,
    ".rb": _RUBY,
    ".rs": _RUST,
}


def _error_lines(tree: ast.AST) -> dict[int, str]:
    """Linha -> tipo do caminho de erro que comeca nela."""
    found: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            found[node.lineno] = "raise"
        elif isinstance(node, ast.ExceptHandler):
            found.setdefault(node.lineno, "except")
    return found


def _error_lines_by_pattern(text: str, patterns) -> dict[int, str]:
    found: dict[int, str] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern, label in patterns:
            if pattern.search(line):
                found.setdefault(number, label)
                break
    return found


def select_error_paths(
    root: Path,
    changed_lines: dict[str, tuple[int, ...]] | None,
    executed_lines: dict[str, tuple[int, ...]] | None = None,
    excluded_lines: dict[str, tuple[int, ...]] | None = None,
) -> dict:
    """Caminhos de erro nas linhas alteradas, separados por cobertura de execucao.

    Linha marcada `# pragma: no cover` sai da medicao por decisao do projeto: nao
    esta em executed_lines nem em missing_lines. Trata-la como nao executada
    acusaria falta de teste onde houve exclusao declarada -- o mesmo erro que
    'classe nao aplicavel' evita do lado do catalogo. A exclusao e' honrada, mas
    fica registrada: nada some do relatorio em silencio.
    """
    uncovered: list[str] = []
    covered: list[str] = []
    limitations: list[str] = []

    heuristic: list[str] = []
    excluded_found: list[str] = []

    for filename, lines in sorted((changed_lines or {}).items()):
        suffix = Path(filename).suffix.lower()
        if suffix != ".py" and suffix not in ERROR_PATTERNS:
            continue
        path = root / filename
        try:
            text = path.read_text(encoding="utf-8")
            error_lines = _error_lines(ast.parse(text)) if suffix == ".py" else _error_lines_by_pattern(text, ERROR_PATTERNS[suffix])
        except (OSError, SyntaxError, ValueError, UnicodeDecodeError) as error:
            limitations.append(f"{filename}: caminhos de erro nao analisados ({error})")
            continue
        touched = sorted(set(lines) & set(error_lines))
        if not touched:
            continue
        if suffix != ".py":
            heuristic.append(filename)

        if executed_lines is None:
            limitations.append(
                f"{filename}: {len(touched)} caminho(s) de erro alterado(s) sem dados de "
                "cobertura para confirmar execucao"
            )
            continue

        executed = set(executed_lines.get(filename, ()))
        excluded = set((excluded_lines or {}).get(filename, ()))
        for line in touched:
            label = f"{filename}:{line} ({error_lines[line]})"
            if line in excluded:
                excluded_found.append(label)
            elif line in executed:
                covered.append(label)
            else:
                uncovered.append(label)

    if excluded_found:
        limitations.append(
            "caminho(s) de erro excluido(s) da medicao pelo projeto (`# pragma: no cover`): "
            + ", ".join(excluded_found)
        )
    if heuristic:
        # A diferenca de metodo precisa aparecer: fora de Python a deteccao e' por
        # padrao sintatico, que pode passar batido num caminho de erro escrito de
        # forma incomum. Dizer isso e' mais honesto que equiparar as evidencias.
        limitations.append(
            "deteccao de caminho de erro por padrao sintatico (sem AST) em: "
            + ", ".join(sorted(set(heuristic)))
        )
    return {"uncovered": tuple(uncovered), "covered": tuple(covered), "limitations": limitations}
