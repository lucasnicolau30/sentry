"""Os documentos limitam o "zero IA" ao veredito e dizem que o `training` não certifica."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from sentrytest.skills import AGENT_GUIDE

ROOT = Path(__file__).resolve().parent.parent
COMPONENTS = ROOT / "frontend" / "src" / "components"


def _texto(rel: str) -> str:
    return " ".join((ROOT / rel).read_text(encoding="utf-8").split())


# (arquivo, trecho que limita ao veredito, trecho que diz que os vídeos usam o agente)
RESSALVAS = {
    "README.md": ("never calls a model to reach a verdict", "hand the work to the agent"),
    "README.pt.md": ("nunca chama um modelo para chegar ao veredito", "entregam o trabalho ao agente"),
    "frontend/src/components/DocsPage.tsx": ("nunca chama um modelo para chegar ao veredito", "usam o agente"),
    "frontend/src/components/FeatureGrid.tsx": ("Zero chamada de IA no veredito", "usam o agente"),
}


@pytest.mark.parametrize("rel", RESSALVAS)
# cenario: documentos limitam o zero IA ao veredito e dizem que os videos usam o agente
def test_documentos_limitam_o_zero_ia_ao_veredito_e_dizem_que_os_videos_usam_o_agente(rel: str):
    limite, agente = RESSALVAS[rel]
    texto = _texto(rel)
    assert limite in texto, f"{rel} não limita o zero IA ao veredito"
    assert agente in texto, f"{rel} não diz que os vídeos usam o agente"


def test_ressalva_nao_cita_claude_code():
    """Sem cenário declarado: a ressalva fala em "o agente"; Claude Code só aparece como
    pré-requisito técnico de promo/training, nunca na frase que explica o zero IA."""
    marcas = {"README.md": "optional video commands", "README.pt.md": "comandos de vídeo opcionais"}
    for rel, marca in marcas.items():
        paragrafo = next(p for p in (ROOT / rel).read_text(encoding="utf-8").splitlines() if marca in p)
        assert "Claude Code" not in paragrafo, f"{rel}: a ressalva cita Claude Code"


@pytest.mark.parametrize("nome", ["README.md", "README.pt.md", "AGENT-SENTRY.md", "guia do skills.py", "DocsPage.tsx"])
# cenario: documentos dizem que o training nao certifica
def test_documentos_dizem_que_o_training_nao_certifica(nome: str):
    texto = " ".join(AGENT_GUIDE.split()) if nome == "guia do skills.py" else _texto(
        "frontend/src/components/DocsPage.tsx" if nome == "DocsPage.tsx" else nome)
    assert re.search(r"only the verdict certifies|só o veredito certifica|verdict certifies", texto),         f"{nome} não diz que o training não certifica"
