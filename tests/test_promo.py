"""`sentry promo`: o brag acionado por `claude -p`, sem gastar token nem exigir login.

O `claude` é simulado: o que importa aqui é o que o Sentry decide antes e depois
dele (pré-requisitos, idioma, onde o vídeo cai, quando recusa afirmar sucesso).
"""
import os
import subprocess
import time
from pathlib import Path

import pytest

from sentrytest import cli
from sentrytest.application import promo


@pytest.fixture
def ambiente(tmp_path: Path, monkeypatch):
    """Projeto com tudo instalado e um `claude` que grava um .mp4 em brag-output/."""
    home = tmp_path / "home"
    skill = home / ".claude" / "skills" / "brag"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: brag\n---\n", encoding="utf-8")
    projeto = tmp_path / "projeto"
    projeto.mkdir()
    chamadas = []
    instalacoes = []

    def which(nome):
        return f"/bin/{nome}"

    def run(comando, **kwargs):
        if comando[1] == "plugin":  # a instalação do brag pelo Claude Code
            instalacoes.append(comando[2:])
            if comando[2] == "install":
                skill.mkdir(parents=True, exist_ok=True)
                (skill / "SKILL.md").write_text("---\nname: brag\n---\n", encoding="utf-8")
            return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
        chamadas.append(comando)
        saida = projeto / "brag-output"
        saida.mkdir(exist_ok=True)
        arquivo = saida / "brag.mp4"
        arquivo.write_bytes(b"video-" + comando[2].encode())
        # Duas chamadas seguidas regravam o mesmo arquivo e podem cair no mesmo tick do
        # relógio do sistema; o promo reconhece vídeo novo pela mudança da hora de
        # modificação. Cada gravação ganha uma hora distinta, para o teste não depender
        # da granularidade do relógio.
        hora = time.time_ns() + len(chamadas) * 1_000_000_000
        os.utime(arquivo, ns=(hora, hora))
        return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")

    monkeypatch.setattr(promo.Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(promo.shutil, "which", which)
    monkeypatch.setattr(promo.subprocess, "run", run)
    monkeypatch.chdir(projeto)
    return {"projeto": projeto, "home": home, "chamadas": chamadas, "which": which, "run": run,
            "instalacoes": instalacoes}


def sem(ambiente, monkeypatch, ausente):
    original = ambiente["which"]
    monkeypatch.setattr(promo.shutil, "which", lambda nome: None if nome == ausente else original(nome))


# cenario: promo gera o video em portugues por padrao
def test_promo_gera_o_video_em_portugues_por_padrao(ambiente, capsys):
    codigo = cli.main(["promo"])
    assert codigo == cli.EXIT_OK
    assert len(ambiente["chamadas"]) == 1
    comando = ambiente["chamadas"][0]
    assert comando[1] == "-p"
    assert comando[2].startswith("/brag")
    assert "português" in comando[2]
    video = ambiente["projeto"] / ".sentry" / "video" / "promo-pt.mp4"
    assert video.read_bytes().startswith(b"video-")
    # o brag não deixa nada para trás: o vídeo foi movido e a pasta dele sumiu
    assert not (ambiente["projeto"] / "brag-output").exists()
    assert ".sentry/video/promo-pt.mp4" in capsys.readouterr().out


def test_promo_acha_o_video_na_pasta_com_data_que_o_brag_cria(ambiente, monkeypatch):
    """Com `brag-output/` já existente, o brag grava em `brag-output-<data>/`."""
    (ambiente["projeto"] / "brag-output").mkdir()
    (ambiente["projeto"] / "brag-output" / "antigo.mp4").write_bytes(b"ANTIGO")

    def run(comando, **kwargs):
        if comando[1] == "plugin":
            return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
        nova = ambiente["projeto"] / "brag-output-2026-10-01-110000"
        nova.mkdir()
        (nova / "brag.mp4").write_bytes(b"NOVO")
        return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
    monkeypatch.setattr(promo.subprocess, "run", run)
    assert cli.main(["promo"]) == cli.EXIT_OK
    assert (ambiente["projeto"] / ".sentry" / "video" / "promo-pt.mp4").read_bytes() == b"NOVO"


def _brag_que_deixa_a_composicao(ambiente, monkeypatch, *, texto="primeira"):
    """Um `claude` que, além do .mp4, deixa a composição e o texto de divulgação do brag."""
    def run(comando, **kwargs):
        if comando[1] == "plugin":
            return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
        saida = ambiente["projeto"] / "brag-output"
        (saida / "composition").mkdir(parents=True, exist_ok=True)
        (saida / "composition" / "index.html").write_text(f"<html>{texto}</html>", encoding="utf-8")
        (saida / "share-copy.txt").write_text(texto, encoding="utf-8")
        (saida / "brag.mp4").write_bytes(b"video-" + texto.encode())
        hora = time.time_ns() + int(texto == "segunda") * 5_000_000_000
        os.utime(saida / "brag.mp4", ns=(hora, hora))
        return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
    monkeypatch.setattr(promo.subprocess, "run", run)


# cenario: promo leva a pasta inteira do brag para o sentry
def test_promo_leva_a_pasta_inteira_do_brag_para_o_sentry(ambiente, monkeypatch):
    _brag_que_deixa_a_composicao(ambiente, monkeypatch)
    assert cli.main(["promo"]) == cli.EXIT_OK
    video = ambiente["projeto"] / ".sentry" / "video"
    assert (video / "promo-pt.mp4").read_bytes() == b"video-primeira"
    assert (video / "composition" / "index.html").read_text(encoding="utf-8") == "<html>primeira</html>"
    assert (video / "share-copy.txt").read_text(encoding="utf-8") == "primeira"
    assert not (ambiente["projeto"] / "brag-output").exists()


# cenario: uma rodada nova do promo refaz a composicao da anterior
def test_uma_rodada_nova_do_promo_refaz_a_composicao_da_anterior(ambiente, monkeypatch):
    _brag_que_deixa_a_composicao(ambiente, monkeypatch, texto="primeira")
    assert cli.main(["promo"]) == cli.EXIT_OK
    velho = ambiente["projeto"] / ".sentry" / "video" / "composition" / "so-da-primeira.txt"
    velho.write_text("sobra", encoding="utf-8")
    _brag_que_deixa_a_composicao(ambiente, monkeypatch, texto="segunda")
    assert cli.main(["promo"]) == cli.EXIT_OK
    video = ambiente["projeto"] / ".sentry" / "video"
    assert (video / "promo-pt.mp4").read_bytes() == b"video-segunda"
    assert (video / "composition" / "index.html").read_text(encoding="utf-8") == "<html>segunda</html>"
    assert not velho.exists()


def test_promo_libera_a_powershell_e_a_pasta_de_plugins_para_o_brag(ambiente):
    (ambiente["home"] / ".claude" / "plugins").mkdir(parents=True)
    assert cli.main(["promo"]) == cli.EXIT_OK
    comando = ambiente["chamadas"][0]
    assert "PowerShell" in comando[comando.index("--allowedTools") + 1].split(",")
    assert comando[comando.index("--add-dir") + 1].endswith("plugins")


# cenario: promo com lang en roda o brag de novo em ingles
def test_promo_com_lang_en_roda_o_brag_de_novo_em_ingles(ambiente):
    assert cli.main(["promo"]) == cli.EXIT_OK
    assert cli.main(["promo", "--lang", "en"]) == cli.EXIT_OK
    assert len(ambiente["chamadas"]) == 2
    assert "English" in ambiente["chamadas"][1][2]
    pasta = ambiente["projeto"] / ".sentry" / "video"
    pt, en = (pasta / "promo-pt.mp4").read_bytes(), (pasta / "promo-en.mp4").read_bytes()
    assert pt != en


# cenario: promo recusa idioma desconhecido
def test_promo_recusa_idioma_desconhecido(ambiente, capsys):
    codigo = cli.main(["promo", "--lang", "fr"])
    assert codigo == cli.EXIT_INFRA
    saida = capsys.readouterr().out
    assert "pt" in saida and "en" in saida
    assert ambiente["chamadas"] == []


# cenario: promo para quando o claude nao esta no PATH
def test_promo_para_quando_o_claude_nao_esta_no_path(ambiente, monkeypatch, capsys):
    sem(ambiente, monkeypatch, "claude")
    codigo = cli.main(["promo"])
    assert codigo == cli.EXIT_INFRA
    assert "Claude Code" in capsys.readouterr().out
    assert not (ambiente["projeto"] / ".sentry" / "video").exists()
    assert ambiente["chamadas"] == []


# cenario: promo instala o brag quando ele esta ausente
def test_promo_instala_o_brag_quando_ele_esta_ausente(ambiente, capsys):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    codigo = cli.main(["promo"])
    assert codigo == cli.EXIT_OK
    assert ambiente["instalacoes"] == [["marketplace", "add", "latent-spaces/brag"],
                                       ["install", "brag@brag"]]
    assert len(ambiente["chamadas"]) == 1  # só depois de instalar o claude -p roda
    assert "instalando" in capsys.readouterr().out
    assert (ambiente["projeto"] / ".sentry" / "video" / "promo-pt.mp4").exists()


# cenario: promo para quando a instalacao do brag falha
def test_promo_para_quando_a_instalacao_do_brag_falha(ambiente, monkeypatch, capsys):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()

    def falha(comando, **kwargs):
        return subprocess.CompletedProcess(comando, 1, stdout="", stderr="marketplace inacessível")
    monkeypatch.setattr(promo.subprocess, "run", falha)
    codigo = cli.main(["promo"])
    assert codigo == cli.EXIT_INFRA
    saida = capsys.readouterr().out
    assert "marketplace inacessível" in saida and "latent-spaces/brag" in saida
    assert ambiente["chamadas"] == []


def registrar_plugins(home, conteudo):
    pasta = home / ".claude" / "plugins"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "installed_plugins.json").write_text(conteudo, encoding="utf-8")


def test_brag_instalado_como_plugin_conta_como_instalado(ambiente):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    registrar_plugins(ambiente["home"], '{"plugins": {"brag@brag": [{"scope": "user"}]}}')
    assert cli.main(["promo"]) == cli.EXIT_OK
    assert ambiente["instalacoes"] == []


def test_cache_de_plugin_desinstalado_nao_conta_como_instalado(ambiente):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    cache = ambiente["home"] / ".claude" / "plugins" / "cache" / "brag" / "brag" / "0.4.0" / "skills" / "brag"
    cache.mkdir(parents=True)
    (cache / "SKILL.md").write_text("---\nname: brag\n---\n", encoding="utf-8")
    registrar_plugins(ambiente["home"], '{"plugins": {"outro@mercado": [{"scope": "user"}]}}')
    assert cli.main(["promo"]) == cli.EXIT_OK
    assert ["install", "brag@brag"] in ambiente["instalacoes"]


@pytest.mark.parametrize("conteudo", ["isto não é json", "[]", '{"plugins": {"brag@brag": []}}'])
def test_registro_de_plugins_ilegivel_ou_vazio_conta_como_brag_ausente(ambiente, conteudo):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    registrar_plugins(ambiente["home"], conteudo)
    assert cli.main(["promo"]) == cli.EXIT_OK
    assert ["install", "brag@brag"] in ambiente["instalacoes"]


def test_promo_aceita_marketplace_ja_adicionado(ambiente, monkeypatch):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    original = ambiente["run"]

    def run(comando, **kwargs):
        if comando[2:4] == ["marketplace", "add"]:
            return subprocess.CompletedProcess(comando, 1, stdout="", stderr="Marketplace already exists")
        return original(comando, **kwargs)
    monkeypatch.setattr(promo.subprocess, "run", run)
    assert cli.main(["promo"]) == cli.EXIT_OK
    assert ambiente["instalacoes"] == [["install", "brag@brag"]]


@pytest.mark.parametrize("falha", [subprocess.TimeoutExpired("claude", 300), OSError("sem permissão")])
def test_promo_explica_quando_a_instalacao_nao_executa(ambiente, monkeypatch, capsys, falha):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()

    def quebra(comando, **kwargs):
        raise falha
    monkeypatch.setattr(promo.subprocess, "run", quebra)
    assert cli.main(["promo"]) == cli.EXIT_INFRA
    assert "latent-spaces/brag" in capsys.readouterr().out


def test_promo_avisa_quando_o_brag_nao_aparece_depois_de_instalar(ambiente, monkeypatch, capsys):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    monkeypatch.setattr(promo.subprocess, "run",
                        lambda comando, **kw: subprocess.CompletedProcess(comando, 0, stdout="", stderr=""))
    assert cli.main(["promo"]) == cli.EXIT_INFRA
    assert "não apareceu" in capsys.readouterr().out


# cenario: promo para quando o ffmpeg esta ausente
def test_promo_para_quando_o_ffmpeg_esta_ausente(ambiente, monkeypatch, capsys):
    sem(ambiente, monkeypatch, "ffmpeg")
    codigo = cli.main(["promo"])
    assert codigo == cli.EXIT_INFRA
    assert "ffmpeg" in capsys.readouterr().out
    assert ambiente["chamadas"] == []


# cenario: promo propaga a falha do claude sem deixar video parcial
def test_promo_propaga_a_falha_do_claude_sem_deixar_video_parcial(ambiente, monkeypatch, capsys):
    def falha(comando, **kwargs):
        return subprocess.CompletedProcess(comando, 7, stdout="", stderr="sessão expirada")
    monkeypatch.setattr(promo.subprocess, "run", falha)
    codigo = cli.main(["promo"])
    assert codigo == cli.EXIT_INFRA
    saida = capsys.readouterr().out
    assert "sessão expirada" in saida
    assert not list((ambiente["projeto"] / ".sentry" / "video").glob("*.mp4")) \
        if (ambiente["projeto"] / ".sentry" / "video").exists() else True


# cenario: promo nao afirma sucesso quando o claude nao gerou o video
def test_promo_nao_afirma_sucesso_quando_o_claude_nao_gerou_o_video(ambiente, monkeypatch, capsys):
    def sem_video(comando, **kwargs):
        return subprocess.CompletedProcess(comando, 0, stdout="pronto!", stderr="")
    monkeypatch.setattr(promo.subprocess, "run", sem_video)
    codigo = cli.main(["promo"])
    assert codigo == cli.EXIT_INFRA
    saida = capsys.readouterr().out
    assert "não foi gerado" in saida
    assert "pronto!" in saida  # o que o claude disse, para o usuário entender por que parou
    assert not (ambiente["projeto"] / ".sentry" / "video" / "promo-pt.mp4").exists()


# cenario: promo propaga a falha do claude sem deixar video parcial
def test_promo_explica_quando_o_claude_estoura_o_tempo(ambiente, monkeypatch, capsys):
    def demora(comando, **kwargs):
        raise subprocess.TimeoutExpired(comando, kwargs["timeout"])
    monkeypatch.setattr(promo.subprocess, "run", demora)
    assert cli.main(["promo"]) == cli.EXIT_INFRA
    assert "sem terminar" in capsys.readouterr().out
    assert not (ambiente["projeto"] / ".sentry" / "video" / "promo-pt.mp4").exists()


# cenario: promo propaga a falha do claude sem deixar video parcial
def test_promo_explica_quando_o_claude_nao_executa(ambiente, monkeypatch, capsys):
    def quebra(comando, **kwargs):
        raise OSError("acesso negado")
    monkeypatch.setattr(promo.subprocess, "run", quebra)
    assert cli.main(["promo"]) == cli.EXIT_INFRA
    assert "acesso negado" in capsys.readouterr().out
