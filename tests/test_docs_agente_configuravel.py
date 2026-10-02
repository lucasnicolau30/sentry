"""Os documentos dizem que o vídeo roda no agente configurado, sem tratar uma marca como requisito."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from sentrytest.skills import AGENT_GUIDE

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"


def _pagina() -> str:
    return DOCS_PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")


def _plano(trecho: str) -> str:
    """O texto corrido de um trecho JSX, sem marcas, chaves de string nem quebras de linha."""
    return " ".join(re.sub(r"<[^>]+>|\{\" \"\}", " ", trecho).split())


def _aba_de_videos() -> str:
    pagina = _pagina()
    return pagina[pagina.index("function VideosContent("):pagina.index("\nconst TrashIcon")]


def _linha_do_comando(texto: str, comando: str) -> str:
    """O trecho que descreve o comando: da linha que o abre até a linha do próximo."""
    linhas = texto.splitlines()
    inicio = next(i for i, linha in enumerate(linhas) if f"sentry {comando} " in linha and linha.lstrip("-| ").startswith("`sentry"))
    fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].lstrip("-| ").startswith("`sentry")), len(linhas))
    return " ".join(" ".join(linhas[inicio:fim]).split())


def _documentos() -> dict[str, str]:
    docs = {nome: (ROOT / nome).read_text(encoding="utf-8") for nome in ("README.md", "README.pt.md", "AGENT-SENTRY.md")}
    docs["guia do skills.py"] = AGENT_GUIDE
    return docs


@pytest.mark.parametrize("comando", ["promo", "training"])
# cenario: os documentos dizem que promo e training precisam do agente configurado
def test_os_documentos_dizem_que_o_comando_precisa_do_agente_configurado(comando: str):
    for nome, texto in _documentos().items():
        descricao = _linha_do_comando(texto, comando)
        assert "Claude Code" not in descricao, f"{nome}: {comando} ainda exige o Claude Code"
        assert "agente" in descricao or "agent" in descricao, f"{nome}: {comando} não fala do agente"


# cenario: os documentos dizem que promo e training precisam do agente configurado
def test_o_promo_diz_onde_declarar_o_agente():
    for nome, texto in _documentos().items():
        assert "[video] agente" in _linha_do_comando(texto, "promo"), f"{nome}: promo não diz onde declarar o agente"


# cenario: os documentos dizem que promo e training precisam do agente configurado
def test_a_aba_de_videos_nao_trata_uma_marca_como_requisito():
    aba = _aba_de_videos()
    assert "Claude Code" not in aba
    texto = _plano(aba)
    assert "Os dois precisam de um agente de IA de linha de comando e do ffmpeg" in texto
    assert "Both need a command-line AI agent and ffmpeg" in texto


# cenario: a aba de videos ensina a declarar o agente
def test_a_aba_de_videos_ensina_a_declarar_o_agente():
    aba = _aba_de_videos()
    secao = aba[aba.index('id="agente"'):]
    secao = secao[:secao.index("</Reveal>")]
    assert "Qual agente roda o brag" in secao and "Which agent runs the brag" in secao
    assert "[video]" in secao and 'agente = ["meu-agente", "--rodar", "{prompt}"]' in secao
    texto = _plano(secao).replace('{"{prompt}"}', "{prompt}")
    assert "marca onde entra o pedido do vídeo" in texto and "marks where the video request goes" in texto
    assert "Um comando sem {prompt} é recusado antes de rodar" in texto
    assert "A command without {prompt} is refused before it runs" in texto
    assert "não procura nem instala a skill brag" in texto and "neither looks for nor installs the brag skill" in texto


# cenario: o exemplo de sentry toml dos documentos traz a secao video
def test_o_exemplo_de_sentry_toml_dos_documentos_traz_a_secao_video():
    for nome in ("README.md", "README.pt.md"):
        texto = (ROOT / nome).read_text(encoding="utf-8")
        assert re.search(r'\[video\] +# (optional|opcional): .*Claude\)\nagente = \["meu-agente", "--rodar", "\{prompt\}"\]', texto), nome
    pagina = _pagina()
    setup = pagina[pagina.index("function SetupContent("):pagina.index("function WorkflowContent(")]
    bloco = _plano(setup[setup.index('[video]{" "}'):])
    bloco = bloco.replace("{'", "").replace("'}", "")
    assert "opcional: o agente que roda o brag (padrão: Claude)" in bloco
    assert "optional: the agent that runs the brag (default: Claude)" in bloco
    assert 'agente = ["meu-agente", "--rodar", "{prompt}"]' in bloco
