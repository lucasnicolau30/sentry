"""Os documentos dizem que promo e training gastam tokens, só quando o usuário pede."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from sentrytest.skills import AGENT_GUIDE

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"

# (documento, frase que diz que o comando roda o agente e gasta tokens, só quando se pede)
FRASES = {
    "README.md": "spends tokens, only when you ask",
    "README.pt.md": "gasta tokens, só quando você pede",
    "AGENT-SENTRY.md": "gasta tokens, só quando o usuário pede",
    "guia do skills.py": "gasta tokens, só quando o usuário pede",
}


def _linha_do_comando(texto: str, comando: str) -> str:
    """O trecho que descreve o comando: da linha que o abre até a linha do próximo."""
    linhas = texto.splitlines()
    inicio = next(i for i, linha in enumerate(linhas) if f"sentry {comando} " in linha and linha.lstrip("-| ").startswith("`sentry"))
    fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].lstrip("-| ").startswith("`sentry")), len(linhas))
    return " ".join(" ".join(linhas[inicio:fim]).split())


def _texto(nome: str) -> str:
    if nome == "guia do skills.py":
        return AGENT_GUIDE
    return (ROOT / nome).read_text(encoding="utf-8")


def _entradas_do_docs_page(comando: str) -> list[str]:
    texto = DOCS_PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")
    blocos = re.findall(rf'command: "sentry {comando} .*?(?=\n\s+command:|\n\s+icon:|\n\];)', texto, flags=re.S)
    return [" ".join(bloco.split()) for bloco in blocos]


@pytest.mark.parametrize("nome", FRASES)
# cenario: documentos dizem que o promo gasta tokens so quando o usuario pede
def test_documentos_dizem_que_o_promo_gasta_tokens(nome: str):
    assert FRASES[nome] in _linha_do_comando(_texto(nome), "promo"), f"{nome} não diz que o promo gasta tokens"


@pytest.mark.parametrize("nome", FRASES)
# cenario: documentos dizem que o training gasta tokens so quando o usuario pede
def test_documentos_dizem_que_o_training_gasta_tokens(nome: str):
    assert FRASES[nome] in _linha_do_comando(_texto(nome), "training"), f"{nome} não diz que o training gasta tokens"


@pytest.mark.parametrize("comando", ["promo", "training"])
# cenario: documentos dizem que o promo gasta tokens so quando o usuario pede
# cenario: documentos dizem que o training gasta tokens so quando o usuario pede
def test_docs_page_diz_que_o_comando_gasta_tokens_em_pt_e_em_en(comando: str):
    entradas = _entradas_do_docs_page(comando)
    assert len(entradas) == 2, f"DocsPage.tsx deveria ter uma entrada de {comando} por idioma"
    pt, en = entradas
    assert "gasta tokens, só quando você pede" in pt
    assert "spends tokens, only when you ask" in en
