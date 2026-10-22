"""O `sentry init` grava o `.gitignore` em blocos comentados e ignora os roteiros e as seções do manual."""
from __future__ import annotations

from pathlib import Path

from sentrytest.adapters.local_tools import _is_untouched_init_file
from sentrytest.init_project import GITIGNORE_BLOCKS, GITIGNORE_COMMENTS, GITIGNORE_ENTRIES, initialize_project


def _linhas(raiz: Path) -> list[str]:
    return (raiz / ".gitignore").read_text(encoding="utf-8").splitlines()


# cenario: gitignore novo nasce em blocos comentados e ignora roteiros e secoes do manual
def test_gitignore_novo_nasce_em_blocos_comentados_e_ignora_roteiros_e_secoes_do_manual(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    antes = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    linhas = antes.splitlines()
    assert ".sentry/training/" in linhas and ".sentry/manual/secoes/" in linhas
    for comentario, entradas in GITIGNORE_BLOCKS:
        posicao = linhas.index(comentario)
        assert linhas[posicao + 1: posicao + 1 + len(entradas)] == list(entradas)      # o comentário vem logo acima do bloco
        if posicao:
            assert linhas[posicao - 1] == ""                                             # e uma linha em branco o separa do anterior
    assert initialize_project(tmp_path) == []
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == antes                # a segunda execução não muda nada


# cenario: gitignore existente ganha os blocos que faltam sem repetir comentario nem perder as linhas do usuario
def test_gitignore_existente_ganha_os_blocos_que_faltam_sem_repetir_comentario(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\nbrag-output/\n", encoding="utf-8")
    initialize_project(tmp_path)
    initialize_project(tmp_path)
    linhas = _linhas(tmp_path)
    assert linhas[:3] == ["node_modules/", "*.log", "brag-output/"]                     # o que era do usuário continua no lugar
    for entrada in GITIGNORE_ENTRIES:
        assert linhas.count(entrada) == 1
    comentario_dos_videos = GITIGNORE_BLOCKS[1][0]
    assert comentario_dos_videos not in linhas                                           # bloco parcial: só a linha que faltava
    assert linhas[3:5] == ["", GITIGNORE_BLOCKS[0][0]]                                   # os blocos novos vêm depois, separados
    assert all(linhas.count(comentario) == 1 for comentario in (GITIGNORE_BLOCKS[0][0], GITIGNORE_BLOCKS[2][0]))


# cenario: init respeita quem versiona roteiros e secoes do manual
def test_init_respeita_quem_versiona_roteiros_e_secoes_do_manual(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("*.log\n!.sentry/training/\n!.sentry/manual/secoes/\n", encoding="utf-8")
    initialize_project(tmp_path)
    initialize_project(tmp_path)
    linhas = _linhas(tmp_path)
    assert ".sentry/training/" not in linhas and ".sentry/manual/secoes/" not in linhas
    assert GITIGNORE_BLOCKS[2][0] not in linhas                                          # sem o bloco, sem o comentário dele
    assert linhas.count("!.sentry/training/") == 1 and linhas.count("!.sentry/manual/secoes/") == 1
    assert "brag-output/" in linhas                                                      # as outras entradas seguem chegando


# cenario: alteracao so com linhas e comentarios do init continua sendo do sentry
def test_alteracao_so_com_linhas_e_comentarios_do_init_continua_sendo_do_sentry(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    assert GITIGNORE_COMMENTS and _is_untouched_init_file(tmp_path, ".gitignore", [])    # arquivo novo: lê o conteúdo inteiro
    (tmp_path / ".gitignore").write_text(
        (tmp_path / ".gitignore").read_text(encoding="utf-8") + "meu-arquivo.txt\n", encoding="utf-8")
    assert not _is_untouched_init_file(tmp_path, ".gitignore", [])                       # uma linha do usuário muda o veredito
