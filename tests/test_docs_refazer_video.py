"""Os documentos avisam que, para alterar o vídeo do `promo` ou do `training`, o usuário
pede ao agente que mude o script, em vez de rodar o comando de novo."""
from __future__ import annotations

from pathlib import Path

import pytest

from sentrytest.skills import AGENT_GUIDE

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"

# Cada documento tem seu idioma, então cada um tem a sua frase-chave.
AVISO = {
    "README.md": "ask the agent",
    "README.pt.md": "peça ao agente",
    "AGENT-SENTRY.md": "pede ao agente",
}


def _linha_do_comando(texto: str, comando: str) -> str:
    """O trecho que descreve o comando: da linha que o abre até a linha do próximo."""
    linhas = texto.splitlines()
    inicio = next(i for i, linha in enumerate(linhas) if f"sentry {comando} " in linha and linha.lstrip("-| ").startswith("`sentry"))
    fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].lstrip("-| ").startswith("`sentry")), len(linhas))
    return " ".join(linhas[inicio:fim])


def _documentos() -> dict[str, tuple[str, str]]:
    docs = {nome: ((ROOT / nome).read_text(encoding="utf-8"), frase) for nome, frase in AVISO.items()}
    docs["guia do skills.py"] = (AGENT_GUIDE, AVISO["AGENT-SENTRY.md"])
    return docs


@pytest.mark.parametrize("nome", _documentos())
# cenario: documentos dizem para pedir ao agente em vez de rodar promo de novo
def test_documentos_dizem_para_pedir_ao_agente_em_vez_de_rodar_promo_de_novo(nome: str):
    texto, frase = _documentos()[nome]
    assert frase in _linha_do_comando(texto, "promo"), f"{nome} não traz o aviso no promo"


@pytest.mark.parametrize("nome", _documentos())
# cenario: documentos dizem para pedir ao agente em vez de rodar training de novo
def test_documentos_dizem_para_pedir_ao_agente_em_vez_de_rodar_training_de_novo(nome: str):
    texto, frase = _documentos()[nome]
    assert frase in _linha_do_comando(texto, "training"), f"{nome} não traz o aviso no training"


# cenario: documentos dizem para pedir ao agente em vez de rodar promo de novo
# cenario: documentos dizem para pedir ao agente em vez de rodar training de novo
def test_aba_de_videos_tem_o_aviso_em_pt_e_em_en():
    """A aba Vídeos é a fonte do aviso; as entradas dos comandos remetem a ela."""
    texto = " ".join(DOCS_PAGE.read_text(encoding="utf-8").split())
    secao = texto[texto.index('id="alterar"'):]
    secao = secao[:secao.index("<PageFooter")]
    assert "Peça ao agente para mudar o script" in secao
    assert "Ask the agent to change the script" in secao
    # o que se altera em cada comando: o projeto do brag (promo) e o roteiro (training)
    assert "o projeto do brag em" in secao and "the brag project in" in secao
    assert ".sentry/training/&lt;módulo&gt;.json" in secao and ".sentry/training/&lt;module&gt;.json" in secao


def test_guia_do_skills_py_e_o_agent_sentry_md_nao_divergem():
    """Sem cenário declarado: o `init` regrava o AGENT-SENTRY.md a partir do guia, então os
    dois precisam ser o mesmo texto, senão o aviso some na próxima regravação."""
    arquivo = (ROOT / "AGENT-SENTRY.md").read_text(encoding="utf-8")
    assert arquivo.replace("\r\n", "\n") == AGENT_GUIDE.replace("\r\n", "\n")
