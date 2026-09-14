"""Evidência de execução do Playwright, anexada por cenário.

Cobertura de linha não existe para o frontend: nenhum coverage.py, lcov ou
Cobertura mede TypeScript de UI. A prova de um caso de frontend é ter rodado e
passado — e o que sustenta essa prova é o trace e o screenshot que o próprio
Playwright grava por teste. Fingir um percentual aqui destruiria a única coisa
que diferencia este produto de um palpite: a disciplina de nunca afirmar o que
não foi medido.

O vínculo é o mesmo marcador `// cenario:` que a rastreabilidade já usa para
associar caso a arquivo de teste — aqui ele associa caso ao título exato do
`test()`/`it()` do Playwright, que é o nome que o relatório JUnit publica.
"""
from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

# Mesma ancora da rastreabilidade (comentario no inicio da linha), duplicada aqui
# em vez de importada: acoplar aos dois modulos por uma regex privada tornaria
# qualquer ajuste na rastreabilidade um risco silencioso para a evidencia de e2e.
_MARKER = re.compile(r"^[ \t]*(?://|--|\#|\*|/\*)[ \t]*(?:scenario|cenario)\s*[:=][ \t]*([^\n]+)",
                     re.IGNORECASE | re.MULTILINE)
_TEST_TITLE = re.compile(r"\b(?:it|test)\s*\(\s*[\"'`]([^\"'`]+)[\"'`]")
_ATTACHMENT = re.compile(r"\[\[ATTACHMENT\|([^\]]+)\]\]")


def _normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in stripped if not unicodedata.combining(char))


def marker_titles(paths: list[Path]) -> dict[str, str]:
    """Nome do caso (normalizado) -> título exato do teste Playwright que o marcador
    precede.

    Só conta o `test()`/`it()` das três linhas seguintes ao marcador: a mesma
    disciplina do `# cenario:` acima de `def test_...` em Python — o vínculo é a
    posição declarada, não a menção solta do nome em algum lugar do arquivo.
    """
    mapping: dict[str, str] = {}
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        for match in _MARKER.finditer(text):
            case_name = match.group(1).strip().strip("'\"")
            marker_line = text.count("\n", 0, match.start())
            for candidate in lines[marker_line + 1: marker_line + 4]:
                title_match = _TEST_TITLE.search(candidate)
                if title_match:
                    mapping[_normalize(case_name)] = title_match.group(1)
                    break
    return mapping


def junit_attachments(report_path: Path) -> dict[str, tuple[str, ...]]:
    """Título do teste (exato, como o Playwright publica) -> caminhos de anexo
    (trace, screenshot), lidos do `<system-out>` do relatório JUnit.

    O reporter `junit` do Playwright grava `[[ATTACHMENT|caminho]]` por anexo,
    tanto em teste que passou quanto no que falhou — é o mesmo formato de que o
    Sentry lê contagem, sem precisar de nenhum parser novo além do XML padrão.
    """
    if not report_path.exists():
        return {}
    try:
        root = ET.parse(report_path).getroot()
    except ET.ParseError:
        return {}
    result: dict[str, tuple[str, ...]] = {}
    for testcase in root.iter("testcase"):
        name = testcase.get("name")
        if not name:
            continue
        system_out = testcase.find("system-out")
        if system_out is None or not system_out.text:
            continue
        attachments = tuple(_ATTACHMENT.findall(system_out.text))
        if attachments:
            result[name] = attachments
    return result


def evidence_by_case(report_path: Path, e2e_paths: list[Path]) -> dict[str, tuple[str, ...]]:
    """Nome do caso (normalizado) -> caminhos de anexo, cruzando marcador e JUnit.

    Sem relatório JUnit (suíte não rodou, ou não declarou `junit_xml`) ou sem
    nenhum marcador nos arquivos declarados, devolve vazio — nunca inventa
    evidência para um caso que não tem prova de execução.
    """
    titles = marker_titles(e2e_paths)
    attachments = junit_attachments(report_path)
    return {case_name: attachments[title] for case_name, title in titles.items() if title in attachments}
