"""A documentação tem uma aba própria para os vídeos, entre o fluxo de trabalho e os comandos."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"


def _pagina() -> str:
    return DOCS_PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")


def _aba() -> str:
    pagina = _pagina()
    inicio = pagina.index("function VideosContent(")
    return pagina[inicio:pagina.index("\nconst TrashIcon", inicio)]


def _plano(trecho: str) -> str:
    """O texto corrido de um trecho JSX, sem marcas, chaves de string nem quebras de linha."""
    trecho = re.sub(r"<[^>]+>|\{\" \"\}|\{'|'\}|\{\"|\"\}", " ", trecho)
    return " ".join(trecho.split())


def _idiomas(trecho: str) -> tuple[str, str]:
    """O texto de cada idioma de todos os `lang === "pt" ? (<>...</>) : (<>...</>)` do trecho."""
    pares = re.findall(r"\? \(\s*<>(.*?)</>\s*\) : \(\s*<>(.*?)</>", trecho, flags=re.S)
    assert pares, "nenhum par pt/en no trecho"
    return _plano(" ".join(pt for pt, _ in pares)), _plano(" ".join(en for _, en in pares))


def _secao(aba: str, id_: str) -> str:
    inicio = aba.index(f'id="{id_}"')
    fim = aba.find("</Reveal>", inicio)
    return aba[inicio:fim]


# cenario: a aba de videos entra na navegacao entre o fluxo e os comandos
def test_a_aba_de_videos_entra_na_navegacao_entre_o_fluxo_e_os_comandos():
    pagina = _pagina()
    ordem = re.findall(r'\{ id: "(\w+)", pt: "[^"]+", en: "[^"]+" \}', pagina[pagina.index("const tabs = ["):])
    assert ordem[:6] == ["start", "setup", "workflow", "videos", "commands", "papers"]
    assert '{ id: "videos", pt: "Vídeos", en: "Videos" }' in pagina
    # os botões de anterior e próximo das três abas apontam uns para os outros
    assert 'onNextClick={() => goToTab("videos")}' in pagina
    assert re.search(r'<VideosContent\s+onPrevClick=\{\(\) => goToTab\("workflow"\)\}\s+onNextClick=\{\(\) => goToTab\("commands"\)\}', pagina)
    assert re.search(r'<CommandsContent\s+onPrevClick=\{\(\) => goToTab\("videos"\)\}', pagina)
    rodape = _aba()[_aba().index("<PageFooter"):]
    assert 'prevLabel={t("O fluxo de trabalho", "The workflow")}' in rodape
    assert 'nextLabel={t("Comandos e Habilidades", "Commands & Skills")}' in rodape
    assert 'nextLabel={t("Vídeos", "Videos")}' in pagina
    assert 'prevLabel={t("Vídeos", "Videos")}' in pagina


# cenario: a aba explica promo e training e que gastam tokens so quando o usuario pede
def test_a_aba_explica_promo_e_training_e_que_gastam_tokens_so_quando_o_usuario_pede():
    pt, en = _idiomas(_secao(_aba(), "visao-geral"))
    assert "gastam tokens, só quando você pede" in pt
    assert "zero IA vale só para ele" in pt
    assert "não certifica nada" in pt and "só o veredito certifica" in pt
    assert "spend tokens, only when you ask" in en
    assert "the zero-AI claim holds for it alone" in en
    assert "certifies nothing" in en and "only the verdict certifies" in en
    aba = _plano(_aba())
    assert "sentry promo gera o vídeo do projeto e o sentry training grava o treinamento de um módulo" in aba
    assert "sentry promo builds the project video and sentry training records a module's training" in aba


# cenario: a aba mostra o formato do roteiro do training
def test_a_aba_mostra_o_formato_do_roteiro_do_training():
    secao = _secao(_aba(), "training")
    for campo in ('"base"', '"titulo"', '"passos"', '"fala"', '"acao"', '"ir"', '"digitar"', '"valor"'):
        assert campo in secao
    pt, en = _idiomas(secao[secao.index("<p className=\"mt-4"):])
    for acao in ("ir", "digitar", "clicar", "apontar"):
        assert acao in pt and acao in en
    assert "A ação é uma só" in pt and "The action is exactly one of" in en
    assert ".sentry/training/&lt;módulo&gt;.json" in secao and ".sentry/training/&lt;module&gt;.json" in secao


# cenario: a aba diz onde ficam os videos como versionar e como altera-los
def test_a_aba_diz_onde_ficam_os_videos_como_versionar_e_como_altera_los():
    aba = _aba()
    pt, en = _idiomas(_secao(aba, "onde-ficam"))
    assert ".sentry/video/" in pt and "composition/" in pt and "brag-output/ , fica vazia" in pt.replace("brag-output/,", "brag-output/ ,")
    assert "!.sentry/video/ no .gitignore" in pt and "o init respeita essa escolha" in pt
    assert "!.sentry/video/ in .gitignore" in en and "init respects that choice" in en
    assert "sentry clear não toca na pasta de vídeos" in pt and "sentry clear doesn't touch the videos folder" in en
    pt, en = _idiomas(_secao(aba, "alterar"))
    assert "Você não precisa rodar o comando de novo. Peça ao agente para mudar o script" in pt
    assert "You don't need to run the command again. Ask the agent to change the script" in en
