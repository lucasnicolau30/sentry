"""A página de documentação mostra as pastas dos vídeos na árvore do .sentry e na seção de versionamento."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"


def _pagina() -> str:
    return " ".join(DOCS_PAGE.read_text(encoding="utf-8").split())


def _arvore() -> str:
    pagina = _pagina()
    inicio = pagina.index('<TerminalWindow title="tree">')
    return pagina[inicio:pagina.index("</TerminalWindow>", inicio)]


# cenario: a arvore do sentry mostra training e media
def test_arvore_do_sentry_mostra_training_e_media():
    arvore = _arvore()
    assert "├── training/" in arvore
    assert ".json" in arvore
    assert '{t("# o roteiro que gera o treinamento", "# the script that makes the training")}' in arvore
    assert '{t("# é aqui que se altera o promo", "# edit this to change the promo")}' in arvore
    assert "├── video/" in arvore
    assert "├── composition/" in arvore and "├── share-copy.txt" in arvore
    assert re.search(r"promo-\{t\(\"pt\", \"en\"\)\}\.mp4", arvore)
    assert re.search(r"training-\{t\(\"cadastro-de-cliente\", \"customer-registration\"\)\}-\{t\(\"pt\", \"en\"\)\}\.mp4", arvore)
    # ao lado dos .mp4, a nota de que podem ser versionados; a pasta de trabalho do brag não entra na árvore
    assert arvore.count('{t("# pode ser versionado", "# can be versioned")}') == 2
    assert "brag-output/" not in arvore
    # a ordem do que já existia não muda: specs, storage e reports continuam na árvore
    assert arvore.index("├── specs/") < arvore.index("├── training/") < arvore.index("├── storage/")
    assert arvore.index("├── storage/") < arvore.index("├── video/") < arvore.index("└── reports/")


# cenario: a secao o que fica versionado diz o que vai para o git
def test_secao_de_versionamento_diz_o_que_vai_para_o_git():
    pagina = _pagina()
    trecho = pagina[pagina.index('{t("O que fica versionado", "What gets versioned")}'):]
    trecho = trecho[:trecho.index("<PageFooter")]
    # sem as marcas JSX, o texto corrido de cada idioma
    texto = re.sub(r"<[^>]+>|\{\" \"\}", " ", trecho)
    texto = " ".join(texto.split())
    assert "Os roteiros de vídeo em .sentry/training/ também são versionados" in texto
    assert ".sentry/video/ , fora do Git" in texto or ".sentry/video/, fora do Git" in texto
    assert re.search(r"A pasta de trabalho do brag, brag-output/ ?, também fica fora do Git e fica vazia", texto)
    assert "!.sentry/video/ no .gitignore" in texto and "o init respeita essa escolha" in texto
    assert "sentry clear não toca nessa pasta" in texto
    assert re.search(r"Brag's working folder, brag-output/ ?, stays out of Git too and ends up empty", texto)
    assert "writes !.sentry/video/ in the .gitignore" in texto and "init respects that choice" in texto
    assert "sentry clear doesn't touch that folder" in texto
    assert ".sentry/media/" not in texto
