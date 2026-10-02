"""A aba Vídeos é a fonte do assunto; as outras abas resumem e remetem a ela."""
from __future__ import annotations

import re
from pathlib import Path

from sentrytest import cli

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"


def _pagina() -> str:
    return DOCS_PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")


def _plano(trecho: str) -> str:
    """O texto corrido de um trecho JSX, sem marcas, chaves de string nem quebras de linha."""
    return " ".join(re.sub(r"<[^>]+>|\{\" \"\}", " ", trecho).split())


def _versionamento() -> str:
    pagina = _pagina()
    trecho = pagina[pagina.index('{t("O que fica versionado", "What gets versioned")}'):]
    return _plano(trecho[:trecho.index("<PageFooter")])


def _entradas(comando: str) -> tuple[str, str]:
    """As entradas `command: "sentry <comando> ..."` da página, a de português e a de inglês."""
    blocos = re.findall(rf'command: "sentry {comando} .*?(?=\n\s+command:|\n\s+icon:|\n\];|\n  \],)', _pagina(), flags=re.S)
    assert len(blocos) == 2, f"deveria haver uma entrada de {comando} por idioma"
    return _plano(blocos[0]), _plano(blocos[1])


# cenario: o setup diz em poucas palavras onde ficam os videos e remete a aba de videos
def test_o_setup_diz_em_poucas_palavras_onde_ficam_os_videos_e_remete_a_aba_de_videos():
    texto = _versionamento()
    assert "Os roteiros de vídeo em .sentry/training/ também são versionados" in texto
    assert "para versionar, veja a aba Vídeos" in texto
    assert "to version them, see the Videos tab" in texto
    # o detalhe mora na aba Vídeos: não se repete aqui
    for repetido in ("!.sentry/video/", "brag-output/", "sentry clear", "respeita essa escolha", "respects that choice"):
        assert repetido not in texto, f"o setup ainda repete {repetido}"


# cenario: as entradas de promo e training em comandos sao curtas e remetem a aba de videos
def test_as_entradas_de_promo_e_training_em_comandos_sao_curtas_e_remetem_a_aba_de_videos():
    for comando in ("promo", "training"):
        pt, en = _entradas(comando)
        assert "gasta tokens, só quando você pede" in pt and "spends tokens, only when you ask" in en
        assert "Detalhes na aba Vídeos" in pt and "Details in the Videos tab" in en
        # o que a aba Vídeos explica não se repete na entrada
        for repetido in ("ffmpeg", "peça ao agente", "ask the agent", "brag em", "brag project"):
            assert repetido not in pt and repetido not in en, f"{comando} ainda repete {repetido}"
    _, en_training = _entradas("training")
    pt_training, _ = _entradas("training")
    assert "só o veredito certifica" in pt_training and "only the verdict certifies" in en_training


# cenario: a aba de comandos conta os catorze comandos da cli
def test_a_aba_de_comandos_conta_os_catorze_comandos_da_cli():
    pagina = _pagina()
    lista = pagina[pagina.index("const ALL_COMMANDS = ["):]
    lista = re.findall(r'"(\w+)",', lista[:lista.index("];")])
    assert len(lista) == 14
    assert "Catorze comandos, um ciclo só:" in pagina
    assert "Fourteen commands, one single cycle:" in pagina
    assert "Doze comandos" not in pagina and "Twelve commands" not in pagina
    # o mesmo conjunto de comandos da própria CLI
    assert set(lista) == set(cli.build_parser()._subparsers._group_actions[0].choices)


# cenario: o card dos videos em comece aqui remete a aba de videos
def test_o_card_dos_videos_em_comece_aqui_remete_a_aba_de_videos():
    pagina = _pagina()
    card = pagina[pagina.index('title: "Gere os vídeos"'):]
    pt = _plano(card[:card.index("],")])
    assert "gastam tokens, só quando você pede; o veredito não muda. Detalhes na aba Vídeos." in pt
    card = pagina[pagina.index('title: "Make the videos"'):]
    en = _plano(card[:card.index("],")])
    assert "spend tokens, only when you ask; the verdict doesn't change. Details in the Videos tab." in en
