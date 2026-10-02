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
GARANTIR_NAVEGADOR = training.navegador_instalado
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
    monkeypatch.setattr(training, "navegador_instalado", lambda **kwargs: True)
    # O pacote do Playwright pode não estar instalado (o CI só instala pytest e coverage): aqui ele é
    # só "presente", porque a gravação real é trocada logo abaixo.
    monkeypatch.setattr(training, "sync_playwright", object())
    monkeypatch.setattr(training, "gravar", gravar)
    monkeypatch.chdir(projeto)
    return {"projeto": projeto, "home": home, "chamadas": chamadas, "gravacoes": gravacoes,
            "which": which, "instalacoes": instalacoes, "run": run}


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


def exigir_navegador() -> None:
    """Os testes que gravam de verdade precisam do pacote do Playwright e do Chromium."""
    if training.sync_playwright is None:
        pytest.skip("o pacote playwright não está instalado")
    if not GARANTIR_NAVEGADOR():
        pytest.skip("o Chromium do Playwright não está instalado")


# cenario: training grava os passos no navegador e marca o tempo de cada um
def test_training_grava_os_passos_no_navegador_e_marca_o_tempo_de_cada_um(tmp_path):
    exigir_navegador()
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


@pytest.mark.parametrize("ausente", ["claude", "ffmpeg"])
# cenario: training para quando falta uma dependencia
def test_training_para_quando_falta_uma_dependencia(ambiente, monkeypatch, capsys, ausente):
    original = ambiente["which"]
    monkeypatch.setattr(promo.shutil, "which", lambda nome: None if nome == ausente else original(nome))
    codigo = cli.main(["training", "cadastro"])
    assert codigo == cli.EXIT_INFRA
    assert ausente.lower() in capsys.readouterr().out.lower()
    assert ambiente["gravacoes"] == []
    assert ambiente["chamadas"] == []
    assert not (ambiente["projeto"] / ".sentry" / "video").exists()


# cenario: training monta o video em portugues por padrao
def test_training_monta_o_video_em_portugues_por_padrao(ambiente, capsys):
    codigo = cli.main(["training", "cadastro"])
    assert codigo == cli.EXIT_OK
    assert len(ambiente["chamadas"]) == 1
    prompt = ambiente["chamadas"][0][2]
    assert prompt.startswith("/brag")
    assert "português" in prompt
    assert "Esta é a tela de cadastro." in prompt and "inicio_s" in prompt
    video = ambiente["projeto"] / ".sentry" / "video" / "training-cadastro-pt.mp4"
    assert video.read_bytes().startswith(b"video-")
    assert ".sentry/video/training-cadastro-pt.mp4" in capsys.readouterr().out


# cenario: training com lang en roda o brag de novo em ingles
def test_training_com_lang_en_roda_o_brag_de_novo_em_ingles(ambiente):
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    assert cli.main(["training", "cadastro", "--lang", "en"]) == cli.EXIT_OK
    assert len(ambiente["chamadas"]) == 2
    assert "English" in ambiente["chamadas"][1][2]
    pasta = ambiente["projeto"] / ".sentry" / "video"
    assert (pasta / "training-cadastro-pt.mp4").read_bytes() != (pasta / "training-cadastro-en.mp4").read_bytes()


# cenario: training propaga a falha do claude sem deixar video parcial
def test_training_propaga_a_falha_do_claude_sem_deixar_video_parcial(ambiente, monkeypatch, capsys):
    def falha(comando, **kwargs):
        return subprocess.CompletedProcess(comando, 7, stdout="", stderr="sessão expirada")
    monkeypatch.setattr(promo.subprocess, "run", falha)
    codigo = cli.main(["training", "cadastro"])
    assert codigo == cli.EXIT_INFRA
    assert "sessão expirada" in capsys.readouterr().out
    assert not list((ambiente["projeto"] / ".sentry" / "video").glob("*.mp4"))


def test_gravacao_que_nao_acha_o_seletor_diz_qual_passo_falhou(tmp_path):
    exigir_navegador()
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
    exigir_navegador()
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
    prompt = training.montar_prompt(ROTEIRO, gravacao, "pt", tmp_path / "projeto",
                                    Path("brag-output/training-x-pt.mp4"))
    assert "g.webm" in prompt and "inicio_s" in prompt
    assert "exatamente em brag-output/training-x-pt.mp4" in prompt


def test_training_pede_um_caminho_exato_e_apaga_o_video_velho_dele(ambiente):
    velho = ambiente["projeto"] / "brag-output" / "training-cadastro-pt.mp4"
    velho.parent.mkdir()
    velho.write_bytes(b"VELHO")
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    assert "exatamente em brag-output/training-cadastro-pt.mp4" in ambiente["chamadas"][0][2]
    assert not velho.exists()  # o velho saiu do caminho antes do claude rodar


def test_training_usa_o_video_do_caminho_pedido_quando_o_claude_o_grava(ambiente, monkeypatch):
    def run(comando, **kwargs):
        if comando[1] == "plugin":
            return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
        alvo = ambiente["projeto"] / "brag-output" / "training-cadastro-pt.mp4"
        alvo.parent.mkdir(exist_ok=True)
        alvo.write_bytes(b"NO-CAMINHO-PEDIDO")
        (alvo.parent / "outro.mp4").write_bytes(b"OUTRO")
        return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
    monkeypatch.setattr(promo.subprocess, "run", run)
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    video = ambiente["projeto"] / ".sentry" / "video" / "training-cadastro-pt.mp4"
    assert video.read_bytes() == b"NO-CAMINHO-PEDIDO"


def comando_de_playwright(ambiente, monkeypatch, *, pacote_ausente=False, navegador_ausente=False,
                          falha_em=None, excecao=None):
    """Troca o `run` para registrar as instalações do Playwright. `falha_em` é um trecho do
    comando que devolve código 1 (ou levanta `excecao`)."""
    instalados = {"navegador": not navegador_ausente}
    comandos = []
    original = ambiente["run"]

    def run(comando, **kwargs):
        texto = " ".join(str(parte) for parte in comando)
        if "-m pip" in texto or "-m playwright" in texto:
            comandos.append(comando)
            if falha_em and falha_em in texto:
                if excecao:
                    raise excecao
                return subprocess.CompletedProcess(comando, 1, stdout="", stderr="sem rede")
            if "install chromium" in texto and "--dry-run" not in texto:
                instalados["navegador"] = True
            return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")
        return original(comando, **kwargs)

    monkeypatch.setattr(promo.subprocess, "run", run)
    monkeypatch.setattr(training, "navegador_instalado", lambda **kwargs: instalados["navegador"])
    if pacote_ausente:
        monkeypatch.setattr(training, "sync_playwright", None)
        monkeypatch.setattr(training, "_carregar_playwright", lambda: True)
    return comandos


# cenario: training instala o playwright quando falta o pacote
def test_training_instala_o_playwright_quando_falta_o_pacote(ambiente, monkeypatch, capsys):
    comandos = comando_de_playwright(ambiente, monkeypatch, pacote_ausente=True)
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    assert comandos == [[sys.executable, "-m", "pip", "install", "playwright"]]
    assert "instalando com pip" in capsys.readouterr().out
    assert len(ambiente["gravacoes"]) == 1  # depois de instalar, segue para a gravação


# cenario: training instala o chromium quando falta so o navegador
def test_training_instala_o_chromium_quando_falta_so_o_navegador(ambiente, monkeypatch, capsys):
    comandos = comando_de_playwright(ambiente, monkeypatch, navegador_ausente=True)
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    assert comandos == [[sys.executable, "-m", "playwright", "install", "chromium"]]
    assert "150 MB" in capsys.readouterr().out
    assert len(ambiente["gravacoes"]) == 1


# cenario: training para quando a instalacao do playwright falha
@pytest.mark.parametrize("opcoes, trecho", [
    ({"pacote_ausente": True, "falha_em": "pip install"}, "sem rede"),
    ({"navegador_ausente": True, "falha_em": "install chromium"}, "sem rede"),
    ({"pacote_ausente": True, "falha_em": "pip install", "excecao": OSError("pip sumiu")}, "pip sumiu"),
    ({"navegador_ausente": True, "falha_em": "install chromium",
      "excecao": subprocess.TimeoutExpired("playwright", 900)}, "não foi possível instalar"),
])
def test_training_para_quando_a_instalacao_do_playwright_falha(ambiente, monkeypatch, capsys, opcoes, trecho):
    comando_de_playwright(ambiente, monkeypatch, **opcoes)
    assert cli.main(["training", "cadastro"]) == cli.EXIT_INFRA
    saida = capsys.readouterr().out
    assert trecho in saida
    assert "pip install playwright && playwright install chromium" in saida
    assert ambiente["gravacoes"] == [] and ambiente["chamadas"] == []


def test_training_avisa_quando_o_pip_instala_mas_o_pacote_nao_carrega(ambiente, monkeypatch, capsys):
    comando_de_playwright(ambiente, monkeypatch, pacote_ausente=True)
    monkeypatch.setattr(training, "_carregar_playwright", lambda: False)
    assert cli.main(["training", "cadastro"]) == cli.EXIT_INFRA
    assert "não o carregou" in capsys.readouterr().out


def test_training_avisa_quando_o_chromium_instala_mas_nao_aparece(ambiente, monkeypatch, capsys):
    comando_de_playwright(ambiente, monkeypatch, navegador_ausente=True)
    monkeypatch.setattr(training, "navegador_instalado", lambda **kwargs: False)
    assert cli.main(["training", "cadastro"]) == cli.EXIT_INFRA
    assert "não o encontrou" in capsys.readouterr().out


DRY_RUN = (
    "Chrome for Testing 151 (playwright chromium v1234)\n  Install location:    {a}\n"
    "  Download url:        https://x\n\nFFmpeg (playwright ffmpeg v1011)\n  Install location:    {b}\n"
)


@pytest.mark.parametrize("existem, esperado", [(("a", "b"), True), (("a",), False), ((), False)])
def test_navegador_instalado_exige_que_todos_os_locais_existam(tmp_path, existem, esperado):
    locais = {"a": tmp_path / "chromium-1", "b": tmp_path / "ffmpeg-1"}
    for nome in existem:
        locais[nome].mkdir()

    def run(comando, **kwargs):
        assert comando[1:5] == ["-m", "playwright", "install", "--dry-run"]
        return subprocess.CompletedProcess(comando, 0, stdout=DRY_RUN.format(a=locais["a"], b=locais["b"]), stderr="")
    assert GARANTIR_NAVEGADOR(run=run) is esperado


@pytest.mark.parametrize("resultado", [
    subprocess.CompletedProcess([], 1, stdout="", stderr="erro"),
    subprocess.CompletedProcess([], 0, stdout="sem locais", stderr=""),
])
def test_navegador_instalado_e_falso_quando_o_playwright_nao_informa_locais(resultado):
    assert GARANTIR_NAVEGADOR(run=lambda comando, **kwargs: resultado) is False


@pytest.mark.parametrize("falha", [OSError("sem python"), subprocess.TimeoutExpired("playwright", 60)])
def test_navegador_instalado_e_falso_quando_a_consulta_nao_executa(falha):
    def run(comando, **kwargs):
        raise falha
    assert GARANTIR_NAVEGADOR(run=run) is False


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


# cenario: training roda o agente declarado no sentry toml
def test_training_roda_o_agente_declarado_no_sentry_toml(ambiente):
    (ambiente["projeto"] / "sentry.toml").write_text(
        '[video]\nagente = ["meu-agente", "--rodar", "{prompt}"]\n', encoding="utf-8")
    (ambiente["home"] / ".claude" / "skills" / "brag" / "SKILL.md").unlink()
    assert cli.main(["training", "cadastro"]) == cli.EXIT_OK
    assert ambiente["instalacoes"] == []
    comando = ambiente["chamadas"][0]
    assert comando[:2] == ["/bin/meu-agente", "--rodar"] and len(comando) == 3
    assert "{prompt}" not in comando[2] and not comando[2].startswith("/brag")
    assert comando[2].startswith("Use a skill brag") and "TREINAMENTO" in comando[2]
    assert (ambiente["projeto"] / ".sentry" / "video" / "training-cadastro-pt.mp4").exists()
