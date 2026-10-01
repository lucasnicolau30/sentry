"""`sentry training`: do roteiro declarado ao vídeo montado pelo brag.

O `claude` é simulado e a gravação só roda de verdade no teste que a verifica
(contra uma página local); nos demais ela é trocada por uma gravação pronta,
para não abrir navegador nem gastar token.
"""
import importlib
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from sentrytest import cli
from sentrytest.application import promo, training

REPO = Path(__file__).resolve().parent.parent
# As reais, guardadas antes de a fixture trocá-las.
GRAVAR_REAL = training.gravar
APP_RESPONDE_REAL = training.app_responde

ROTEIRO = {
    "base": "http://127.0.0.1:8100",
    "titulo": "Como criar uma conta",
    "passos": [
        {"titulo": "Abrir o cadastro", "fala": "Esta é a tela de cadastro.", "acao": {"ir": "/cadastro"}},
        {"titulo": "Informar o nome", "fala": "Digite o seu nome.",
         "acao": {"digitar": "#nome", "valor": "Ana Souza"}},
        {"titulo": "Ler o erro", "fala": "O sistema explica o que falta.", "acao": {"apontar": "#erro"}},
    ],
}


def escrever(projeto: Path, modulo: str, dados) -> Path:
    pasta = projeto / ".sentry" / "training"
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{modulo}.json"
    caminho.write_text(dados if isinstance(dados, str) else json.dumps(dados), encoding="utf-8")
    return caminho


@pytest.fixture
def ambiente(tmp_path: Path, monkeypatch):
    """Projeto com tudo instalado, um roteiro `cadastro` e um `claude` que grava o .mp4."""
    home = tmp_path / "home"
    skill = home / ".claude" / "skills" / "brag"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: brag\n---\n", encoding="utf-8")
    projeto = tmp_path / "projeto"
    projeto.mkdir()
    escrever(projeto, "cadastro", ROTEIRO)
    chamadas = []
    instalacoes = []
    gravacoes = []

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
        (saida / "treino.mp4").write_bytes(b"video-" + comando[2].encode())
        return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")

    def gravar(root, roteiro, destino):
        gravacoes.append(roteiro)
        destino.mkdir(parents=True, exist_ok=True)
        webm = destino / "gravacao.webm"
        webm.write_bytes(b"webm")
        return {"webm": str(webm), "duracao": 12.5,
                "passos": [{"n": i, "titulo": p["titulo"], "fala": p["fala"],
                            "inicio": 2.0 * i, "fim": 2.0 * i + 1.8}
                           for i, p in enumerate(roteiro["passos"], start=1)]}

    monkeypatch.setattr(promo.Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(promo.shutil, "which", which)
    monkeypatch.setattr(promo.subprocess, "run", run)
    monkeypatch.setattr(training, "app_responde", lambda base, timeout=5: None)
    monkeypatch.setattr(training, "gravar", gravar)
    monkeypatch.chdir(projeto)
    return {"projeto": projeto, "home": home, "chamadas": chamadas, "gravacoes": gravacoes,
            "which": which, "instalacoes": instalacoes}


# cenario: roteiro valido e aceito
def test_roteiro_valido_e_aceito(ambiente):
    roteiro = training.carregar_roteiro(ambiente["projeto"], "cadastro")
    assert [p["titulo"] for p in roteiro["passos"]] == ["Abrir o cadastro", "Informar o nome", "Ler o erro"]
    assert roteiro["base"] == "http://127.0.0.1:8100"


# cenario: modulo com nome simples localiza o roteiro
def test_modulo_com_nome_simples_localiza_o_roteiro(tmp_path):
    caminho = training.caminho_do_roteiro(tmp_path, "login-de-usuario")
    assert caminho == tmp_path / ".sentry" / "training" / "login-de-usuario.json"


# cenario: modulo com separador de caminho e recusado
def test_modulo_com_separador_de_caminho_e_recusado(ambiente, capsys):
    (ambiente["projeto"] / "segredo.json").write_text(json.dumps(ROTEIRO), encoding="utf-8")
    codigo = cli.main(["training", "../../segredo"])
    assert codigo == cli.EXIT_INFRA
    assert "inválido" in capsys.readouterr().out
    assert ambiente["gravacoes"] == []
    with pytest.raises(ValueError):
        training.validar_modulo("pasta/outra")
    with pytest.raises(ValueError):
        training.validar_modulo("pasta\\outra")


# cenario: modulo com nome longo demais e recusado
def test_modulo_com_nome_longo_demais_e_recusado(ambiente, capsys):
    codigo = cli.main(["training", "a" * 300])
    assert codigo == cli.EXIT_INFRA
    assert "longo demais" in capsys.readouterr().out
    assert ambiente["gravacoes"] == []


# cenario: modulo sem roteiro e recusado
def test_modulo_sem_roteiro_e_recusado(ambiente, capsys):
    codigo = cli.main(["training", "inexistente"])
    assert codigo == cli.EXIT_INFRA
    assert ".sentry/training/inexistente.json" in capsys.readouterr().out
    assert ambiente["gravacoes"] == []


# cenario: roteiro com json invalido aponta o erro
def test_roteiro_com_json_invalido_aponta_o_erro(ambiente, capsys):
    escrever(ambiente["projeto"], "quebrado",
             '{"passos": [\n  {"titulo": "a" "fala": "b"}\n]}')
    codigo = cli.main(["training", "quebrado"])
    assert codigo == cli.EXIT_INFRA
    saida = capsys.readouterr().out
    assert "quebrado.json" in saida and "linha 2" in saida and "coluna" in saida


# cenario: passo sem fala e recusado
def test_passo_sem_fala_e_recusado(ambiente, capsys):
    dados = json.loads(json.dumps(ROTEIRO))
    del dados["passos"][2]["fala"]
    escrever(ambiente["projeto"], "semfala", dados)
    codigo = cli.main(["training", "semfala"])
    assert codigo == cli.EXIT_INFRA
    assert "passo 3: campo 'fala'" in capsys.readouterr().out
    assert ambiente["gravacoes"] == []


# cenario: acao desconhecida e recusada
def test_acao_desconhecida_e_recusada(ambiente, capsys):
    dados = json.loads(json.dumps(ROTEIRO))
    dados["passos"][1]["acao"] = {"executar": "alert(1)"}
    escrever(ambiente["projeto"], "perigoso", dados)
    codigo = cli.main(["training", "perigoso"])
    assert codigo == cli.EXIT_INFRA
    saida = capsys.readouterr().out
    assert "ação desconhecida 'executar'" in saida
    assert "ir, digitar, clicar, apontar" in saida
    assert ambiente["gravacoes"] == []


# cenario: acao com seletor vazio e recusada
def test_acao_com_seletor_vazio_e_recusada(ambiente, capsys):
    dados = json.loads(json.dumps(ROTEIRO))
    dados["passos"][1]["acao"] = {"clicar": ""}
    escrever(ambiente["projeto"], "vazio", dados)
    codigo = cli.main(["training", "vazio"])
    assert codigo == cli.EXIT_INFRA
    assert "passo 2" in capsys.readouterr().out
    # digitar sem valor e roteiro que nem e' objeto tambem sao recusados
    assert training.validar_roteiro({**ROTEIRO, "passos": [
        {"titulo": "t", "fala": "f", "acao": {"digitar": "#a"}}]})
    assert training.validar_roteiro([]) == ["o roteiro deve ser um objeto JSON"]
    assert training.validar_roteiro({"base": "x", "titulo": "t", "passos": ["texto"]})
    assert training.validar_roteiro({**ROTEIRO, "passos": [
        {"titulo": "t", "fala": "f", "acao": {"ir": "/", "clicar": "#a"}}]})


class PaginaDeTeste(BaseHTTPRequestHandler):
    def do_GET(self):
        corpo = ('<html><body><h1>Cadastro</h1><input id="nome">'
                 '<p id="erro">falta o nome</p></body></html>').encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


# cenario: training grava os passos no navegador e marca o tempo de cada um
def test_training_grava_os_passos_no_navegador_e_marca_o_tempo_de_cada_um(tmp_path):
    servidor = HTTPServer(("127.0.0.1", 0), PaginaDeTeste)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        roteiro = {**ROTEIRO, "base": f"http://127.0.0.1:{servidor.server_port}"}
        gravacao = GRAVAR_REAL(tmp_path, roteiro, tmp_path / "saida")
    finally:
        servidor.shutdown()
    assert Path(gravacao["webm"]).stat().st_size > 0
    passos = gravacao["passos"]
    assert [p["n"] for p in passos] == [1, 2, 3]
    assert all(p["inicio"] < p["fim"] for p in passos)
    assert all(a["fim"] <= b["inicio"] + 0.05 for a, b in zip(passos, passos[1:]))
    assert gravacao["duracao"] >= passos[-1]["fim"]


# cenario: training para quando o app da base nao responde
def test_training_para_quando_o_app_da_base_nao_responde(ambiente, monkeypatch, capsys):
    monkeypatch.setattr(training, "app_responde", APP_RESPONDE_REAL)
    escrever(ambiente["projeto"], "fora", {**ROTEIRO, "base": "http://127.0.0.1:9"})
    codigo = cli.main(["training", "fora"])
    assert codigo == cli.EXIT_INFRA
    assert "não respondeu" in capsys.readouterr().out
    assert ambiente["chamadas"] == []
    assert ambiente["gravacoes"] == []


@pytest.mark.parametrize("ausente", ["claude", "ffmpeg", "playwright"])
# cenario: training para quando falta uma dependencia
def test_training_para_quando_falta_uma_dependencia(ambiente, monkeypatch, capsys, ausente):
    if ausente == "playwright":
        monkeypatch.setattr(training, "sync_playwright", None)
    else:
        original = ambiente["which"]
        monkeypatch.setattr(promo.shutil, "which", lambda nome: None if nome == ausente else original(nome))
    codigo = cli.main(["training", "cadastro"])
    assert codigo == cli.EXIT_INFRA
    assert ausente.lower() in capsys.readouterr().out.lower()
    assert ambiente["gravacoes"] == []
    assert ambiente["chamadas"] == []
    assert not (ambiente["projeto"] / ".sentry" / "media").exists()


# cenario: training monta o video em portugues por padrao
def test_training_monta_o_video_em_portugues_por_padrao(ambiente, capsys):
    codigo = cli.main(["training", "cadastro"])
    assert codigo == cli.EXIT_OK
    assert len(ambiente["chamadas"]) == 1
    prompt = ambiente["chamadas"][0][2]
    assert prompt.startswith("/brag")
    assert "português" in prompt
    assert "Esta é a tela de cadastro." in prompt and "inicio_s" in prompt
    video = ambiente["projeto"] / ".sentry" / "media" / "training-cadastro-pt.mp4"
    assert video.read_bytes().startswith(b"video-")
    assert ".sentry/media/training-cadastro-pt.mp4" in capsys.readouterr().out


# cenario: training com lang en roda o brag de novo em ingles
def test_training_com_lang_en_roda_o_brag_de_novo_em_ingles(ambiente):
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    assert cli.main(["training", "cadastro", "--lang", "en"]) == cli.EXIT_OK
    assert len(ambiente["chamadas"]) == 2
    assert "English" in ambiente["chamadas"][1][2]
    media = ambiente["projeto"] / ".sentry" / "media"
    assert (media / "training-cadastro-pt.mp4").read_bytes() != (media / "training-cadastro-en.mp4").read_bytes()


# cenario: training propaga a falha do claude sem deixar video parcial
def test_training_propaga_a_falha_do_claude_sem_deixar_video_parcial(ambiente, monkeypatch, capsys):
    def falha(comando, **kwargs):
        return subprocess.CompletedProcess(comando, 7, stdout="", stderr="sessão expirada")
    monkeypatch.setattr(promo.subprocess, "run", falha)
    codigo = cli.main(["training", "cadastro"])
    assert codigo == cli.EXIT_INFRA
    assert "sessão expirada" in capsys.readouterr().out
    assert not list((ambiente["projeto"] / ".sentry" / "media").glob("*.mp4"))


def test_gravacao_que_nao_acha_o_seletor_diz_qual_passo_falhou(tmp_path):
    servidor = HTTPServer(("127.0.0.1", 0), PaginaDeTeste)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        roteiro = {**ROTEIRO, "base": f"http://127.0.0.1:{servidor.server_port}",
                   "passos": [ROTEIRO["passos"][0],
                              {"titulo": "Clicar no que não existe", "fala": "Sem botão.",
                               "acao": {"clicar": "#nao-existe"}}]}
        with pytest.raises(ValueError, match="passo 2 .Clicar no que não existe."):
            GRAVAR_REAL(tmp_path, roteiro, tmp_path / "saida", timeout_ms=800)
    finally:
        servidor.shutdown()


class PaginaQueFalha:
    def locator(self, seletor):
        raise training.PlaywrightError("Timeout 800ms exceeded.\nwaiting for locator")


def test_passo_que_falha_diz_o_numero_e_o_titulo():
    passo = {"titulo": "Clicar", "fala": "f", "acao": {"clicar": "#x"}}
    with pytest.raises(ValueError, match="passo 4 .Clicar.: Timeout 800ms exceeded"):
        training._executar_passo(PaginaQueFalha(), 4, passo, "http://x", 800)


def test_sem_o_pacote_playwright_o_modulo_ainda_carrega(monkeypatch):
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    try:
        recarregado = importlib.reload(training)
        assert recarregado.sync_playwright is None
        assert recarregado.PlaywrightError is Exception
    finally:
        monkeypatch.undo()
        importlib.reload(training)


def test_gravacao_com_app_fora_do_ar_diz_que_nao_conectou(tmp_path):
    roteiro = {**ROTEIRO, "base": "http://127.0.0.1:9"}
    with pytest.raises(ValueError, match="não foi possível conectar"):
        GRAVAR_REAL(tmp_path, roteiro, tmp_path / "saida")


class NavegadorAusente:
    def __enter__(self):
        raise training.PlaywrightError("BrowserType.launch: Executable doesn't exist at /x/chrome.exe")

    def __exit__(self, *args):
        return False


def test_gravacao_sem_o_navegador_do_playwright_diz_como_instalar(tmp_path, monkeypatch):
    monkeypatch.setattr(training, "sync_playwright", lambda: NavegadorAusente())
    with pytest.raises(ValueError, match="playwright install chromium"):
        GRAVAR_REAL(tmp_path, ROTEIRO, tmp_path / "saida")


def test_gravar_sem_o_pacote_playwright_diz_como_instalar(tmp_path, monkeypatch):
    monkeypatch.setattr(training, "sync_playwright", None)
    with pytest.raises(ValueError, match="pip install playwright"):
        GRAVAR_REAL(tmp_path, ROTEIRO, tmp_path / "saida")


def test_prompt_aceita_gravacao_fora_do_projeto(tmp_path):
    gravacao = {"webm": str(tmp_path / "fora" / "g.webm"), "duracao": 3.0,
                "passos": [{"n": 1, "titulo": "t", "fala": "f", "inicio": 0.5, "fim": 2.0}]}
    prompt = training.montar_prompt(ROTEIRO, gravacao, "pt", tmp_path / "projeto")
    assert "g.webm" in prompt and "inicio_s" in prompt


# cenario: training instala o brag quando ele esta ausente
def test_training_instala_o_brag_quando_ele_esta_ausente(ambiente):
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    assert ambiente["instalacoes"][-1] == ["install", "brag@brag"]
    assert len(ambiente["chamadas"]) == 1


# cenario: check valida os roteiros declarados
def test_check_valida_os_roteiros_declarados(ambiente, capsys):
    dados = json.loads(json.dumps(ROTEIRO))
    del dados["passos"][0]["fala"]
    escrever(ambiente["projeto"], "ruim", dados)
    spec = ambiente["projeto"] / ".sentry" / "specs" / "x"
    spec.mkdir(parents=True)
    (spec / "CASES.md").write_text(
        "# X\n\n## Prompt\n\np\n\n## Campos\n\n- **a**: livre — a\n\n"
        "## Caso: c\n\n- **Requisito:** r\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Classe:** a/valido\n- **Dado:** d\n- **Quando:** q\n"
        "- **Então:** e\n", encoding="utf-8")
    codigo = cli.main(["check", "x"])
    assert codigo == 1
    assert "passo 1: campo 'fala'" in capsys.readouterr().out
