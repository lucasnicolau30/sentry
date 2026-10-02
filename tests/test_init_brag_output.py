"""O `sentry init` ignora a pasta de trabalho do brag, `brag-output/`."""
from __future__ import annotations

from pathlib import Path

from sentrytest.adapters.local_tools import _is_untouched_init_file
from sentrytest.init_project import GITIGNORE_ENTRIES, initialize_project


def _linhas(raiz: Path) -> list[str]:
    return (raiz / ".gitignore").read_text(encoding="utf-8").splitlines()


# cenario: gitignore novo nasce ignorando a pasta de trabalho do brag
def test_gitignore_novo_ignora_a_pasta_de_trabalho_do_brag(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    linhas = _linhas(tmp_path)
    assert "brag-output/" in linhas
    assert ".sentry/video/" in linhas
    assert ".sentry/media/" not in linhas
    # o que já valia continua valendo: spec não é ignorada e o relatório atual segue rastreável
    assert ".sentry/specs/" not in linhas
    assert "!.sentry/reports/latest-*.md" in linhas


# cenario: gitignore existente ganha a linha sem duplicar e sem perder as do usuario
def test_gitignore_existente_ganha_a_linha_sem_duplicar_nem_perder_as_do_usuario(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n", encoding="utf-8")
    initialize_project(tmp_path)
    initialize_project(tmp_path)
    linhas = _linhas(tmp_path)
    assert linhas.count("brag-output/") == 1
    assert "node_modules/" in linhas and "*.log" in linhas


# cenario: alteracao so com linhas do init continua sendo do sentry
def test_alteracao_so_com_linhas_do_init_continua_sendo_do_sentry(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    assert "brag-output/" in GITIGNORE_ENTRIES
    assert _is_untouched_init_file(tmp_path, ".gitignore", list(GITIGNORE_ENTRIES))


# cenario: init remove a linha obsoleta do pool media
def test_init_remove_a_linha_obsoleta_do_pool_media(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("*.log\n.sentry/media/\n", encoding="utf-8")
    initialize_project(tmp_path)
    linhas = _linhas(tmp_path)
    assert ".sentry/media/" not in linhas
    assert ".sentry/video/" in linhas
    assert "*.log" in linhas
