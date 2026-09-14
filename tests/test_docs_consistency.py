"""Os quatro documentos (README.md, README.pt.md, AGENT-SENTRY.md, DocsPage.tsx)
não podem divergir em silêncio da CLI real.

Sem isto, a próxima mudança de comando ou de catálogo volta a descolar a
documentação do código — exatamente o que aconteceu antes desta spec: AGENT-SENTRY.md
nunca mencionava `init`/`report`/`history`/`clear`, DocsPage.tsx nunca mencionava
`review`/`watch`/`context` e tinha um exemplo de `CASES.md` com `camada: unidade`
(valor de `TestType`, não de `Layer`). A fonte da verdade é sempre o código:
`cli.build_parser()` para os comandos, `FIELD_CLASSES`/`LAYERS` para o vocabulário.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pytest

from sentrytest.adapters.case_specs import LAYERS
from sentrytest.cli import build_parser
from sentrytest.domain.catalog import FIELD_CLASSES

ROOT = Path(__file__).resolve().parent.parent

DOCS = {
    "README.md": ROOT / "README.md",
    "README.pt.md": ROOT / "README.pt.md",
    "AGENT-SENTRY.md": ROOT / "AGENT-SENTRY.md",
    "DocsPage.tsx": ROOT / "frontend" / "src" / "components" / "DocsPage.tsx",
}

# DocsPage.tsx documenta tipos de campo em prosa (cpf, cnpj, ...), nao numa tabela
# fixa: so os tres arquivos que efetivamente listam o catalogo entram aqui.
CATALOG_DOCS = ("README.md", "README.pt.md", "DocsPage.tsx")


def _subcommands(parser: argparse.ArgumentParser | None = None) -> tuple[str, ...]:
    """Os nomes reais de subcomando de `cli.py`, direto do parser -- nunca uma
    lista copiada a mao, que divergiria da CLI do mesmo jeito que a doc diverge."""
    parser = parser or build_parser()
    if parser._subparsers is not None:
        for action in parser._subparsers._group_actions:
            if isinstance(action, argparse._SubParsersAction):
                return tuple(action.choices)
    raise AssertionError("nenhum subparser encontrado em build_parser()")


def test_subcommands_sem_subparser_e_erro_de_uso_e_nao_lista_vazia():
    """Caminho defensivo, sem cenário declarado: uma lista vazia se leria como
    "a CLI não tem comando nenhum", que esconderia o defeito em vez de acusá-lo."""
    with pytest.raises(AssertionError):
        _subcommands(argparse.ArgumentParser())


def _text(name: str) -> str:
    return DOCS[name].read_text(encoding="utf-8")


@pytest.mark.parametrize("doc", DOCS)
# cenario: todo comando do cli aparece no README.md
# cenario: todo comando do cli aparece no README.pt.md
# cenario: todo comando do cli aparece no AGENT-SENTRY.md
# cenario: todo comando do cli aparece no DocsPage.tsx
def test_todo_comando_do_cli_aparece_no_documento(doc: str):
    text = _text(doc)
    faltando = [command for command in _subcommands() if command not in text]
    assert not faltando, f"{doc} não menciona: {', '.join(faltando)}"


@pytest.mark.parametrize("doc", CATALOG_DOCS)
# cenario: todo tipo de campo do catalogo aparece na tabela do README.md
# cenario: todo tipo de campo do catalogo aparece na tabela do README.pt.md
# cenario: todo tipo de campo do catalogo aparece na tabela do DocsPage.tsx
def test_todo_tipo_de_campo_do_catalogo_aparece_no_documento(doc: str):
    text = _text(doc)
    faltando = [name for name in FIELD_CLASSES if name not in text]
    assert not faltando, f"{doc} não menciona os tipos: {', '.join(faltando)}"


_CAMADA_NO_EXEMPLO = re.compile(r'"camada",\s*"layer"\)\}\*\*:\s*([A-Za-zçãéí]+)')


# cenario: o valor de camada no exemplo do DocsPage.tsx e uma camada valida
def test_valor_de_camada_no_exemplo_do_docspage_e_valido():
    text = _text("DocsPage.tsx")
    match = _CAMADA_NO_EXEMPLO.search(text)
    assert match, "exemplo de CASES.md em DocsPage.tsx não declara `camada`"
    assert match.group(1) in LAYERS, (
        f"DocsPage.tsx mostra `camada: {match.group(1)}`, que não é um valor de Layer "
        f"({', '.join(LAYERS)}) — provavelmente um valor de Tipo (TestType) usado no lugar errado"
    )
