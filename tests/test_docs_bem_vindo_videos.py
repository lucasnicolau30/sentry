"""A aba "Comece aqui" da documentação fala dos vídeos, como a home."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"


def _pagina() -> str:
    return DOCS_PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")


def _plano(trecho: str) -> str:
    """O texto corrido de um trecho JSX, sem marcas nem quebras de linha."""
    return " ".join(re.sub(r"<[^>]+>|\{\" \"\}", " ", trecho).split())


def _lista(nome: str) -> str:
    pagina = _pagina()
    inicio = pagina.index(f"const {nome}: Record")
    return pagina[inicio:pagina.index("\n};", inicio)]


# cenario: a frase de abertura do bem-vindo fala dos videos
def test_a_frase_de_abertura_do_bem_vindo_fala_dos_videos():
    pagina = _pagina()
    assert "Quando quiser, peça também o vídeo do projeto ou o treinamento de um módulo." in pagina
    assert "When you want, also ask for the project video or a module's training video." in pagina
    # continua sendo a frase do ciclo intenção -> veredito
    assert "rode o ciclo intenção → veredito direto do terminal." in pagina


# cenario: o que voce pode fazer tem um card dos videos que gastam tokens
def test_o_que_voce_pode_fazer_tem_um_card_dos_videos_que_gastam_tokens():
    lista = _lista("actionsByLang")
    pt, en = lista.split("  en: [")
    pt, en = _plano(pt), _plano(en)
    assert "Gere os vídeos" in pt and "Make the videos" in en
    assert "sentry promo gera o vídeo do projeto e sentry training grava o treinamento de um módulo" in pt
    assert "Usam o agente e gastam tokens, só quando você pede; o veredito não muda." in pt
    assert "sentry promo makes the project video and sentry training records a module's training" in en
    assert "Both use the agent and spend tokens, only when you ask; the verdict doesn't change." in en


# cenario: os cards de o que voce pode fazer fecham o grid de tres colunas
def test_os_cards_de_o_que_voce_pode_fazer_fecham_o_grid_de_tres_colunas():
    lista = _lista("actionsByLang")
    assert lista.count("<FilmIcon />") == 2
    pt, en = lista.split("  en: [")
    assert pt.count("icon: <") == 9 and en.count("icon: <") == 9
    uso = _pagina()
    uso = uso[uso.index("{actionsByLang[lang].map("):]
    uso = uso[:uso.index("))}")]
    assert "lg:col-span-2" not in uso
