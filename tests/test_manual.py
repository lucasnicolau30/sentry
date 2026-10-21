"""`sentry manual`: o manual em PDF de um módulo, a partir do roteiro do `training`.

Os testes de identidade leem uma página local de verdade, no Playwright; os demais trocam a
leitura do app por uma identidade pronta, para não abrir navegador. Nenhum deles aciona agente.
"""
import json
import re
import socket
import struct
import threading
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from sentrytest import cli
from sentrytest.application import manual, promo, training
from sentrytest.application.manual import Identidade

# As reais, guardadas antes de a fixture trocá-las.
NAVEGADOR_INSTALADO = training.navegador_instalado
APP_RESPONDE_REAL = training.app_responde

VERDE = (21, 128, 61)

ROTEIRO = {
    "base": "http://127.0.0.1:8100",
    "titulo": "Como criar uma conta",
    "passos": [
        {"titulo": "Abrir o cadastro", "fala": "Esta é a tela de cadastro.", "acao": {"ir": "/cadastro"}},
        {"titulo": "Informar o nome", "fala": "Digite o seu nome.",
         "acao": {"digitar": "#nome", "valor": "Ana Souza"}},
        {"titulo": "Informar o sobrenome", "fala": "Digite o seu sobrenome.",
         "acao": {"digitar": "#sobrenome", "valor": "Souza"}},
        {"titulo": "Salvar", "fala": "Clique em Salvar.", "acao": {"clicar": "#salvar"}},
    ],
}


def png_cru(tipo_de_cor: int, pixel: bytes, profundidade: int = 8, extras=()) -> bytes:
    """Um PNG de 1x1 montado à mão (com os trechos extras antes dos dados): o teste não depende de biblioteca de imagem."""
    def trecho(tipo: bytes, dados: bytes) -> bytes:
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))

    return (b"\x89PNG\r\n\x1a\n" + trecho(b"IHDR", struct.pack(">IIBBBBB", 1, 1, profundidade, tipo_de_cor, 0, 0, 0))
            + b"".join(trecho(tipo, dados) for tipo, dados in extras)
            + trecho(b"IDAT", zlib.compress(b"\x00" + pixel)) + trecho(b"IEND", b""))


def png_minimo(cor=(21, 128, 61), alfa=None) -> bytes:
    """Um PNG válido de 1x1: RGB, ou RGBA quando `alfa` é dado."""
    return png_cru(2, bytes(cor)) if alfa is None else png_cru(6, bytes(cor) + bytes([alfa]))


def escrever(projeto: Path, modulo: str, dados) -> Path:
    pasta = projeto / ".sentry" / "training"
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{modulo}.json"
    caminho.write_text(dados if isinstance(dados, str) else json.dumps(dados), encoding="utf-8")
    return caminho


def texto_do_pdf(caminho: Path) -> str:
    pypdf = pytest.importorskip("pypdf")
    return "\n".join(pagina.extract_text() for pagina in pypdf.PdfReader(str(caminho)).pages)


def cores_do_pdf(caminho: Path) -> set[tuple[int, ...]]:
    """As cores (RGB 0-255) que o PDF seleciona, lidas do conteúdo das páginas."""
    pypdf = pytest.importorskip("pypdf")
    achadas = set()
    for pagina in pypdf.PdfReader(str(caminho)).pages:
        conteudo = pagina.get_contents().get_data().decode("latin-1")
        for r, g, b in re.findall(r"([\d.]+) ([\d.]+) ([\d.]+) (?:rg|RG)\b", conteudo):
            achadas.add(tuple(round(float(canal) * 255) for canal in (r, g, b)))
    return achadas


def roteiro_longo() -> dict:
    return {**ROTEIRO, "passos": [{"titulo": f"Passo {n}", "fala": "Faça isto. " * 12, "acao": {"apontar": "#x"}}
                                  for n in range(1, 31)]}


@pytest.fixture
def ambiente(tmp_path: Path, monkeypatch):
    """Projeto com o roteiro `cadastro` e a leitura do app trocada por uma identidade pronta."""
    projeto = tmp_path / "projeto"
    projeto.mkdir()
    escrever(projeto, "cadastro", ROTEIRO)
    leituras = []

    def ler_identidade(roteiro):
        leituras.append(roteiro)
        return Identidade(nome="Loja Verde", cor=VERDE, logo=png_minimo())

    # O pacote do Playwright pode não estar instalado (o CI só instala pytest e coverage): aqui ele é
    # só "presente", porque a leitura é trocada logo abaixo.
    monkeypatch.setattr(training, "sync_playwright", object())
    monkeypatch.setattr(training, "navegador_instalado", lambda **kwargs: True)
    monkeypatch.setattr(training, "app_responde", lambda base, timeout=5: None)
    monkeypatch.setattr(manual, "ler_identidade", ler_identidade)
    monkeypatch.chdir(projeto)
    return {"projeto": projeto, "leituras": leituras}


# cenario: manual de roteiro valido e gravado em pdf
def test_manual_de_roteiro_valido_e_gravado_em_pdf(ambiente, capsys):
    codigo = cli.main(["manual", "cadastro"])
    pdf = ambiente["projeto"] / ".sentry" / "manual" / "cadastro-pt.pdf"
    assert codigo == cli.EXIT_OK
    assert pdf.read_bytes().startswith(b"%PDF")
    assert ".sentry/manual/cadastro-pt.pdf" in capsys.readouterr().out


# cenario: manual traz titulo e os passos na ordem do roteiro
def test_manual_traz_titulo_e_os_passos_na_ordem_do_roteiro(ambiente):
    dados = manual.conteudo(ROTEIRO, "pt")
    assert dados["titulo"] == "Como criar uma conta"
    assert dados["passos"] == [
        (1, "Abrir o cadastro", "Esta é a tela de cadastro."),
        (2, "Informar o nome", "Digite o seu nome."),
        (3, "Informar o sobrenome", "Digite o seu sobrenome."),
        (4, "Salvar", "Clique em Salvar."),
    ]
    cli.main(["manual", "cadastro"])
    texto = texto_do_pdf(ambiente["projeto"] / ".sentry" / "manual" / "cadastro-pt.pdf")
    assert "Antes de começar" not in texto and "Ana Souza" not in texto
    posicoes = [texto.index(titulo) for _, titulo, _ in dados["passos"]]
    assert posicoes == sorted(posicoes)


# Páginas com <head> próprio: é nele que o app declara nome, cor e ícone.
PAGINAS = {
    "/tema": ('<!doctype html><title>Início · Outro Nome</title><meta name="application-name" content="Loja Verde">'
              '<meta name="theme-color" content="#15803d"><link rel="icon" href="/logo.png"><body>oi</body>'),
    "/botao": ('<!doctype html><title>Sem Tema</title><body><a href="#" style="background:#fff">x</a>'
               '<button style="background:#0a66c2;color:#fff">Ir</button></body>'),
    "/nada": '<!doctype html><title>Só o Título</title><body>oi</body>',
    "/hsl": ('<!doctype html><title>HSL</title><meta name="theme-color" content="hsl(120, 100%, 25%)">'
             '<link rel="icon" href="/falso.png"><body>oi</body>'),
}


class PaginaDeTeste(BaseHTTPRequestHandler):
    def do_GET(self):
        tipo = "text/html; charset=utf-8"
        if self.path == "/logo.png":
            corpo, tipo = png_minimo(), "image/png"
        else:
            corpo = PAGINAS.get(self.path, "<html><body></body></html>").encode()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


@pytest.fixture
def http_local():
    http = HTTPServer(("127.0.0.1", 0), PaginaDeTeste)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{http.server_port}"
    http.shutdown()
    http.server_close()


@pytest.fixture
def servidor(http_local):
    if training.sync_playwright is None or not NAVEGADOR_INSTALADO():
        pytest.skip("o Playwright e o Chromium não estão instalados")
    return http_local


def roteiro_em(base: str) -> dict:
    """O passo aponta para um elemento que não existe: se o fluxo fosse reproduzido, a leitura falharia."""
    return {"base": base, "titulo": "Só olhar", "passos": [
        {"titulo": "Clicar", "fala": "Clique.", "acao": {"clicar": "#nao-existe"}}]}


# cenario: so a pagina de base e lida e o fluxo nao e reproduzido
def test_so_a_pagina_de_base_e_lida_e_o_fluxo_nao_e_reproduzido(servidor):
    identidade = manual.ler_identidade(roteiro_em(servidor + "/tema"))
    assert identidade.nome == "Loja Verde"


# cenario: identidade vem de application-name theme-color e icone
def test_identidade_vem_de_application_name_theme_color_e_icone(servidor):
    identidade = manual.ler_identidade(roteiro_em(servidor + "/tema"))
    assert identidade.nome == "Loja Verde"
    assert identidade.cor == VERDE
    assert identidade.logo.startswith(b"\x89PNG")


# cenario: cor cai no fundo do primeiro botao colorido
def test_cor_cai_no_fundo_do_primeiro_botao_colorido(servidor):
    identidade = manual.ler_identidade(roteiro_em(servidor + "/botao"))
    assert identidade.cor == (10, 102, 194)
    assert identidade.nome == "Sem Tema"


def test_theme_color_em_qualquer_sintaxe_do_css_vira_rgb(servidor):
    assert manual.ler_identidade(roteiro_em(servidor + "/hsl")).cor == (0, 128, 0)


# cenario: app sem identidade declarada usa titulo e cor padrao
def test_app_sem_identidade_declarada_usa_titulo_e_cor_padrao(servidor):
    identidade = manual.ler_identidade(roteiro_em(servidor + "/nada"))
    assert identidade == Identidade(nome="Só o Título", cor=manual.COR_PADRAO, logo=None)


# cenario: logo que nao e png nem jpeg fica de fora
def test_logo_que_nao_e_png_nem_jpeg_fica_de_fora(http_local):
    assert manual._baixar_logo(http_local + "/logo.png").startswith(b"\x89PNG")
    assert manual._baixar_logo(http_local + "/botao") is None       # responde HTML, não imagem
    assert manual._baixar_logo("javascript:alert(1)") is None        # só http(s)
    assert manual._baixar_logo("") is None
    with socket.socket() as livre:
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
    assert manual._baixar_logo(f"http://127.0.0.1:{porta}/logo.png") is None   # ninguém na porta


# cenario: cabecalho com logo e nome do app em toda pagina
def test_cabecalho_com_logo_e_nome_do_app_em_toda_pagina(tmp_path):
    destino = manual.montar_pdf(
        manual.conteudo(roteiro_longo(), "pt", Identidade(nome="Loja Verde", cor=VERDE, logo=png_minimo())),
        tmp_path / "m.pdf")
    pypdf = pytest.importorskip("pypdf")
    paginas = pypdf.PdfReader(str(destino)).pages
    assert len(paginas) >= 2
    for pagina in paginas:
        assert "Loja Verde" in pagina.extract_text()
        assert len(pagina["/Resources"]["/XObject"]) == 1    # a logo
    assert VERDE in cores_do_pdf(destino)


# cenario: cor clara demais e escurecida para o texto
def test_cor_clara_demais_e_escurecida_para_o_texto(tmp_path):
    assert manual.cor_legivel(VERDE) == VERDE
    assert manual.cor_legivel((57, 255, 20)) == (34, 153, 12)
    assert manual.tom_claro((0, 0, 0)) == (230, 230, 230)
    destino = manual.montar_pdf(
        manual.conteudo(ROTEIRO, "pt", Identidade(nome="Neon", cor=(57, 255, 20))), tmp_path / "n.pdf")
    cores = cores_do_pdf(destino)
    assert (57, 255, 20) in cores          # o filete do cabeçalho mantém a cor do app
    assert (34, 153, 12) in cores          # o título da seção usa a versão legível


# cenario: capa traz MANUAL DO USUARIO e o titulo do roteiro
def test_capa_traz_manual_do_usuario_e_o_titulo_do_roteiro(ambiente):
    assert cli.main(["manual", "cadastro"]) == cli.EXIT_OK
    assert cli.main(["manual", "cadastro", "--lang", "en"]) == cli.EXIT_OK
    pasta = ambiente["projeto"] / ".sentry" / "manual"
    pt, en = texto_do_pdf(pasta / "cadastro-pt.pdf"), texto_do_pdf(pasta / "cadastro-en.pdf")
    assert "MANUAL DO USUÁRIO" in pt and "Como criar uma conta" in pt
    assert "USER MANUAL" in en and "MANUAL DO USUÁRIO" not in en
    assert manual.texto_sobre(VERDE) == (255, 255, 255)
    assert manual.texto_sobre((255, 255, 0)) == manual.TEXTO_ESCURO


# cenario: titulo da capa e centralizado e a logo vira marca d'agua na faixa
def test_titulo_da_capa_e_centralizado_e_a_logo_vira_marca_dagua_na_faixa(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    com_logo = manual.montar_pdf(manual.conteudo(ROTEIRO, "pt", Identidade(nome="Loja", cor=VERDE, logo=png_minimo())),
                                 tmp_path / "com.pdf")
    sem_logo = manual.montar_pdf(manual.conteudo(ROTEIRO, "pt", Identidade(nome="Loja", cor=VERDE)), tmp_path / "sem.pdf")

    def opacidades(caminho):
        pagina = pypdf.PdfReader(str(caminho)).pages[0]
        estados = pagina["/Resources"].get("/ExtGState", {})
        return {round(float(estado.get_object()["/ca"]), 2) for estado in estados.values()}

    assert manual.MARCA_DAGUA_OPACIDADE in opacidades(com_logo)
    assert manual.MARCA_DAGUA_OPACIDADE not in opacidades(sem_logo)

    posicoes = []
    pypdf.PdfReader(str(com_logo)).pages[0].extract_text(
        visitor_text=lambda texto, cm, tm, fonte, tamanho: posicoes.append(tm[4]) if "MANUAL DO" in texto else None)
    assert 100 < posicoes[0] < 200          # à esquerda, o título começaria em ~80 pt


# cenario: marca d'agua tira o fundo solido do logo
def test_marca_dagua_tira_o_fundo_solido_do_logo(tmp_path):
    pypdf = pytest.importorskip("pypdf")

    def modos(logo):
        destino = manual.montar_pdf(
            manual.conteudo(ROTEIRO, "pt", Identidade(nome="L", cor=VERDE, logo=logo)), tmp_path / "x.pdf")
        estados = pypdf.PdfReader(str(destino)).pages[0]["/Resources"].get("/ExtGState", {})
        return {estado.get_object().get("/BM") for estado in estados.values()}

    assert "/Screen" in modos(png_minimo((0, 0, 0)))                 # fundo escuro sólido
    assert "/Screen" in modos(png_minimo((0, 0, 0), alfa=255))       # RGBA opaco, como o ícone do Sentry
    assert "/Multiply" in modos(png_minimo((255, 255, 255)))         # fundo claro sólido
    assert not modos(png_minimo((0, 0, 0), alfa=0)) & {"/Screen", "/Multiply"}   # transparente entra como está


def test_fundo_do_logo_so_e_lido_em_png_de_fundo_solido():
    paleta = (b"PLTE", bytes([0, 0, 0, 9, 8, 7]))
    assert manual._fundo_do_logo(png_minimo((10, 20, 30))) == (10, 20, 30)
    assert manual._fundo_do_logo(png_minimo((10, 20, 30), alfa=255)) == (10, 20, 30)
    assert manual._fundo_do_logo(png_minimo((10, 20, 30), alfa=0)) is None
    assert manual._fundo_do_logo(png_cru(0, b"\x10")) == (16, 16, 16)                     # cinza
    assert manual._fundo_do_logo(png_cru(4, b"\x10\xff")) == (16, 16, 16)                 # cinza com alfa opaco
    assert manual._fundo_do_logo(png_cru(4, b"\x10\x00")) is None                        # cinza transparente
    assert manual._fundo_do_logo(png_cru(3, b"\x01", extras=[paleta])) == (9, 8, 7)       # paleta
    assert manual._fundo_do_logo(png_cru(3, b"\x01", extras=[paleta, (b"tRNS", b"\x00\x00")])) is None
    assert manual._fundo_do_logo(png_cru(2, bytes(6), profundidade=16)) is None            # 16 bits não é lido
    assert manual._fundo_do_logo(png_cru(5, b"\x00")) is None                             # tipo de cor desconhecido
    assert manual._fundo_do_logo(b"\xff\xd8\xff\xe0jpeg") is None                        # JPEG não é lido
    assert manual._fundo_do_logo(png_minimo()[:40]) is None                                # PNG cortado
    assert manual._fundo_do_logo(b"\x89PNG\r\n\x1a\n") is None                            # sem IHDR


# cenario: rodape traz pagina e nome do app em toda pagina
def test_rodape_traz_pagina_e_nome_do_app_em_toda_pagina(tmp_path):
    identidade = Identidade(nome="Loja Verde", cor=VERDE)
    pt = manual.montar_pdf(manual.conteudo(roteiro_longo(), "pt", identidade), tmp_path / "pt.pdf")
    en = manual.montar_pdf(manual.conteudo(roteiro_longo(), "en", identidade), tmp_path / "en.pdf")
    pypdf = pytest.importorskip("pypdf")
    paginas = pypdf.PdfReader(str(pt)).pages
    total = len(paginas)
    assert total >= 2
    for n, pagina in enumerate(paginas, start=1):
        texto = pagina.extract_text()
        assert f"Página {n} de {total}" in texto
        assert texto.count("Loja Verde") == 2           # o do cabeçalho e o do rodapé
    assert f"Page 1 of {total}" in pypdf.PdfReader(str(en)).pages[0].extract_text()


# cenario: app fora do ar e recusado
def test_app_fora_do_ar_e_recusado(ambiente, monkeypatch, capsys):
    with socket.socket() as livre:
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
    escrever(ambiente["projeto"], "fora", {**ROTEIRO, "base": f"http://127.0.0.1:{porta}"})
    monkeypatch.setattr(training, "app_responde", APP_RESPONDE_REAL)
    assert cli.main(["manual", "fora"]) == cli.EXIT_INFRA
    assert "suba o app" in capsys.readouterr().out
    assert not (ambiente["projeto"] / ".sentry" / "manual").exists()


# cenario: manual nao aciona agente nem ffmpeg
def test_manual_nao_aciona_agente_nem_ffmpeg(ambiente, monkeypatch):
    monkeypatch.setattr(promo.shutil, "which", lambda nome: None)
    monkeypatch.setattr(promo.subprocess, "run", lambda *args, **kwargs: pytest.fail("o manual não executa subprocesso"))
    assert cli.main(["manual", "cadastro"]) == cli.EXIT_OK
    assert (ambiente["projeto"] / ".sentry" / "manual" / "cadastro-pt.pdf").is_file()


# cenario: manual recusa modulo com separador de caminho
def test_manual_recusa_modulo_com_separador_de_caminho(ambiente, capsys):
    (ambiente["projeto"] / "segredo.json").write_text(json.dumps(ROTEIRO), encoding="utf-8")
    codigo = cli.main(["manual", "../../segredo"])
    assert codigo == cli.EXIT_INFRA
    assert "inválido" in capsys.readouterr().out
    assert ambiente["leituras"] == []
    assert not (ambiente["projeto"] / ".sentry" / "manual").exists()


# cenario: manual recusa modulo sem roteiro
def test_manual_recusa_modulo_sem_roteiro(ambiente, capsys):
    codigo = cli.main(["manual", "inexistente"])
    assert codigo == cli.EXIT_INFRA
    assert ".sentry/training/inexistente.json" in capsys.readouterr().out


# cenario: roteiro invalido e recusado dizendo o passo
def test_roteiro_invalido_e_recusado_dizendo_o_passo(ambiente, capsys):
    dados = json.loads(json.dumps(ROTEIRO))
    del dados["passos"][2]["fala"]
    escrever(ambiente["projeto"], "semfala", dados)
    codigo = cli.main(["manual", "semfala"])
    assert codigo == cli.EXIT_INFRA
    assert "passo 3: campo 'fala'" in capsys.readouterr().out
    assert not (ambiente["projeto"] / ".sentry" / "manual").exists()


# cenario: idioma desconhecido e recusado
def test_idioma_desconhecido_e_recusado(ambiente, capsys):
    codigo = cli.main(["manual", "cadastro", "--lang", "fr"])
    assert codigo == cli.EXIT_INFRA
    assert "pt, en" in capsys.readouterr().out
    assert not (ambiente["projeto"] / ".sentry" / "manual").exists()


# cenario: lang en gera o manual com titulos fixos em ingles
def test_lang_en_gera_o_manual_com_titulos_fixos_em_ingles(ambiente):
    assert cli.main(["manual", "cadastro", "--lang", "en"]) == cli.EXIT_OK
    texto = texto_do_pdf(ambiente["projeto"] / ".sentry" / "manual" / "cadastro-en.pdf")
    assert "USER MANUAL" in texto and "Step by step" in texto
    assert "Passo a passo" not in texto
    assert "Digite o seu nome." in texto


# cenario: texto fora do latin-1 nao derruba o pdf
def test_texto_fora_do_latin_1_nao_derruba_o_pdf(ambiente):
    dados = json.loads(json.dumps(ROTEIRO))
    dados["passos"][0]["fala"] = "Clique — “Salvar”… 🙂"
    escrever(ambiente["projeto"], "estranho", dados)
    assert cli.main(["manual", "estranho"]) == cli.EXIT_OK
    texto = texto_do_pdf(ambiente["projeto"] / ".sentry" / "manual" / "estranho-pt.pdf")
    assert 'Clique - "Salvar"... ?' in texto


class PaginaFalsa:
    def __init__(self, erro_ao_abrir=None):
        self.erro_ao_abrir = erro_ao_abrir

    def goto(self, url, **kwargs):
        if self.erro_ao_abrir:
            raise self.erro_ao_abrir

    def evaluate(self, js):
        return {"nome": "", "cor": None, "logo": ""}


def playwright_falso(monkeypatch, pagina):
    """Um Playwright que devolve `pagina`: os erros da leitura, sem navegador (o coverage não enxerga
    o que roda dentro do greenlet do Playwright, então estes caminhos só aparecem assim)."""
    class Contexto:
        def new_page(self):
            return pagina

    class Navegador:
        def new_context(self, **kwargs):
            return Contexto()

        def close(self):
            pass

    class Playwright:
        chromium = type("Chromium", (), {"launch": staticmethod(lambda: Navegador())})()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(training, "sync_playwright", Playwright)


def test_leitura_sem_playwright_pede_a_instalacao(monkeypatch):
    monkeypatch.setattr(training, "sync_playwright", None)
    with pytest.raises(ValueError, match="falta o Playwright"):
        manual.ler_identidade(ROTEIRO)


def test_leitura_com_app_inalcancavel_diz_para_subir_o_app(monkeypatch):
    erro = training.PlaywrightError("net::ERR_CONNECTION_REFUSED at http://127.0.0.1:8100/")
    playwright_falso(monkeypatch, PaginaFalsa(erro_ao_abrir=erro))
    with pytest.raises(ValueError, match="a leitura falhou: não foi possível conectar"):
        manual.ler_identidade(ROTEIRO)


def test_app_sem_nome_na_pagina_cai_no_host_da_base(monkeypatch):
    playwright_falso(monkeypatch, PaginaFalsa())
    assert manual.ler_identidade(ROTEIRO) == Identidade(nome="127.0.0.1", cor=manual.COR_PADRAO, logo=None)
