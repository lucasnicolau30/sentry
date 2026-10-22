"""O Markdown do manual, sem PDF: o que a seção entende, o que recusa e como os passos são trocados.

Os cenários do que o usuário vê (a seção nasce, preserva o que foi escrito, o PDF segue a ordem) estão
em `test_manual.py`; aqui ficam os ramos do leitor, um a um.
"""
import json
from pathlib import Path

import pytest

from sentrytest.application import manual_md as md
from sentrytest.application.manual_md import Passo

CABECALHO = "---\nmodulo: m\nordem: 2\n---\n# Título\n"
ROTEIRO = {"base": "http://127.0.0.1:1", "titulo": "Como fazer", "passos": [
    {"titulo": "Abrir", "fala": "Acesse\n a tela.", "acao": {"ir": "/"}},
    {"titulo": "Salvar", "fala": "Clique em **Salvar**.", "acao": {"clicar": "#s"}}]}


def lido(corpo: str, cabecalho: str = CABECALHO):
    return md.ler_secao(cabecalho + corpo, "m.md")


def recusa(texto: str, *trechos: str) -> None:
    with pytest.raises(ValueError) as erro:
        md.ler_secao(texto, "m.md")
    assert all(trecho in str(erro.value) for trecho in trechos), str(erro.value)


def test_secao_le_cada_bloco_na_ordem():
    secao = lido(
        "<!-- um comentário não aparece -->\n\nPrimeira linha\ncontinua aqui.\n\n## Subtítulo\n\n"
        "> [!SUCESSO] Concluído\n> Tudo certo.\n>\n> E mais isto.\n\n"
        ":::cartoes\n### A\ntexto a\ncontinua\n\n### B\ntexto b\n:::\n\n"
        ":::passos\n1. Abrir\n   Acesse\n   a tela.\n\n2. Salvar\n   Clique.\n:::\n\nFim.\n")
    assert (secao.modulo, secao.ordem, secao.titulo) == ("m", 2, "Título")
    assert secao.blocos == [
        ("paragrafo", "Primeira linha continua aqui."),
        ("subtitulo", "Subtítulo"),
        ("aviso", "sucesso", "Concluído", "Tudo certo. E mais isto."),
        ("cartoes", [("A", "texto a continua"), ("B", "texto b")]),
        ("passos", [Passo("Abrir", "Acesse a tela."), Passo("Salvar", "Clique.")]),
        ("paragrafo", "Fim."),
    ]


def test_aviso_aceita_os_nomes_em_portugues_e_em_ingles_sem_titulo():
    tipos = [lido(f"> [!{nome}]\n> texto\n").blocos[0][1] for nome in ("INFO", "note", "Sucesso", "SUCCESS", "ATENCAO", "warning")]
    assert tipos == ["info", "info", "sucesso", "sucesso", "atencao", "atencao"]
    assert lido("> [!INFO]\n").blocos == [("aviso", "info", "", "")]


def test_secao_sem_ordem_e_com_crlf():
    secao = md.ler_secao("---\r\nmodulo: m\r\n---\r\n# T\r\n\r\ntexto\r\n", "m.md")
    assert secao.ordem is None and secao.blocos == [("paragrafo", "texto")]


def test_secao_recusa_o_que_nao_entende_dizendo_a_linha():
    recusa("# T\n", "m.md:1:", "bloco \"---\"")
    recusa("---\nmodulo: m\n# T\n", "m.md:3:", "esperava", "chave: valor")
    recusa("---\n: x\n---\n# T\n", "m.md:2:", "chave: valor")
    recusa("---\nmodulo: m\n", "m.md:3:", "não foi fechado")
    recusa("---\nordem: 1\n---\n# T\n", "m.md:1:", "falta a chave modulo")
    recusa("---\nmodulo: m\nordem: x\n---\n# T\n", "m.md:1:", "ordem precisa ser um número", '"x"')
    recusa("---\nmodulo: m\n---\ntexto\n", "m.md:4:", "falta o título")
    recusa(CABECALHO + "# Outro\n", "m.md:6:", "só um título")
    recusa(CABECALHO + "> sem tipo\n", "m.md:6:", "o aviso começa com")
    recusa(CABECALHO + "> [!INFO] ok\n\n> [!NADA] x\n", "m.md:8:", "o aviso começa com")
    recusa(CABECALHO + ":::outro\n", "m.md:6:", "bloco desconhecido", ":::passos e :::cartoes")
    recusa(CABECALHO + ":::\n", "m.md:6:", "bloco desconhecido")


def test_bloco_de_passos_recusa_linha_solta_e_bloco_vazio_ou_aberto():
    recusa(CABECALHO + ":::passos\nnão é passo\n:::\n", "m.md:7:", "esperava", "1. Título")
    recusa(CABECALHO + ":::passos\n   fala sem passo\n:::\n", "m.md:7:", "esperava")
    recusa(CABECALHO + ":::passos\n\n:::\n", "m.md:6:", "vazio")
    recusa(CABECALHO + ":::passos\n:::\n", "m.md:6:", "vazio")
    recusa(CABECALHO + ":::passos\n1. A\n   b\n", "não foi fechado", ":::")
    recusa(CABECALHO + ":::cartoes\n### A\n:::passos\n1. A\n   b\n:::\n", "m.md:", "não foi fechado")      # outro bloco começou


def test_bloco_de_cartoes_recusa_texto_antes_do_titulo_e_bloco_vazio():
    recusa(CABECALHO + ":::cartoes\ntexto solto\n:::\n", "m.md:7:", "### Título")
    recusa(CABECALHO + ":::cartoes\n:::\n", "m.md:6:", "vazio")


def test_listar_secoes_sem_pasta_e_ordenadas(tmp_path):
    assert md.listar_secoes(tmp_path) == []
    pasta = tmp_path / md.PASTA_DAS_SECOES
    pasta.mkdir(parents=True)
    for modulo, ordem in (("zeta", "1"), ("beta", ""), ("alfa", ""), ("meio", "5")):
        extra = f"ordem: {ordem}\n" if ordem else ""
        (pasta / f"{modulo}.md").write_text(f"---\nmodulo: {modulo}\n{extra}---\n# {modulo}\n", encoding="utf-8")
    assert [s.modulo for s in md.listar_secoes(tmp_path)] == ["zeta", "meio", "alfa", "beta"]


def test_listar_secoes_diz_qual_arquivo_esta_torto(tmp_path):
    pasta = tmp_path / md.PASTA_DAS_SECOES
    pasta.mkdir(parents=True)
    (pasta / "torta.md").write_text("sem nada", encoding="utf-8")
    with pytest.raises(ValueError, match=r"\.sentry/manual/secoes/torta\.md:1:"):
        md.listar_secoes(tmp_path)


def test_com_passos_troca_o_bloco_e_acrescenta_quando_nao_ha():
    texto = CABECALHO + "\nIntro.\n\n:::passos\n1. Velho\n   texto\n:::\n\nDepois.\n"
    novo = md.com_passos(texto, ROTEIRO)
    assert "Velho" not in novo and "1. Abrir\n   Acesse a tela.\n2. Salvar\n   Clique em **Salvar**.\n:::" in novo
    assert novo.startswith(CABECALHO) and "Intro." in novo and novo.rstrip().endswith("Depois.")
    assert md.com_passos(novo, ROTEIRO) == novo                               # idempotente
    sem_bloco = md.com_passos(CABECALHO + "\nSó intro.\n", ROTEIRO)
    assert sem_bloco.endswith("   Clique em **Salvar**.\n:::\n") and "Só intro." in sem_bloco
    with pytest.raises(ValueError, match="não foi fechado"):
        md.com_passos(CABECALHO + ":::passos\n1. A\n   b\n", ROTEIRO)


def projeto_com_roteiro(tmp_path: Path, modulo: str = "m") -> Path:
    pasta = tmp_path / ".sentry" / "training"
    pasta.mkdir(parents=True)
    (pasta / f"{modulo}.json").write_text(json.dumps(ROTEIRO), encoding="utf-8")
    return tmp_path


def test_sincronizar_cria_e_depois_so_troca_os_passos(tmp_path):
    root = projeto_com_roteiro(tmp_path)
    arquivo, criada = md.sincronizar(root, "m")
    assert criada and arquivo == md.caminho_da_secao(root, "m")
    primeira = arquivo.read_text(encoding="utf-8")
    assert md.ler_secao(primeira).blocos == [("passos", [Passo("Abrir", "Acesse a tela."),
                                                         Passo("Salvar", "Clique em **Salvar**.")])]
    assert md.sincronizar(root, "m") == (arquivo, False)
    assert arquivo.read_text(encoding="utf-8") == primeira                    # nada mudou, nada se perdeu


def test_sincronizar_nao_grava_o_que_ficaria_invalido(tmp_path):
    root = projeto_com_roteiro(tmp_path)
    arquivo = md.caminho_da_secao(root, "m")
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text(CABECALHO + "\n> [!NADA] x\n", encoding="utf-8")
    antes = arquivo.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="o aviso começa com"):
        md.sincronizar(root, "m")
    assert arquivo.read_text(encoding="utf-8") == antes


def test_sincronizar_recusa_modulo_inseguro_ou_sem_roteiro(tmp_path):
    with pytest.raises(ValueError, match="inválido"):
        md.caminho_da_secao(tmp_path, "../fora")
    with pytest.raises(ValueError, match=r"\.sentry/training/nada\.json"):
        md.sincronizar(tmp_path, "nada")
