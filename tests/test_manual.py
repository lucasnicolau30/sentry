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
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from sentrytest import cli
from sentrytest.application import manual, manual_md, promo, training
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


from sentrytest.application.manual_md import Passo, Secao

PASSOS = [Passo(p["titulo"], p["fala"]) for p in ROTEIRO["passos"]]


def passos_longos(quantos: int = 30) -> list[Passo]:
    return [Passo(f"Passo {n}", "Faça isto. " * 12) for n in range(1, quantos + 1)]


def secao(n: int = 1, titulo: str = "Como criar uma conta", blocos=None) -> Secao:
    return Secao(modulo=f"modulo{n}", titulo=titulo, ordem=n, blocos=blocos if blocos is not None else [("passos", PASSOS)])


def pdf_de(tmp_path, secoes=None, idioma="pt", identidade=None):
    pypdf = pytest.importorskip("pypdf")
    dados = manual.conteudo(secoes or [secao()], idioma, identidade or Identidade(nome="Loja", cor=VERDE),
                            hoje=date(2026, 10, 22))
    return pypdf.PdfReader(str(manual.montar_pdf(dados, tmp_path / f"{idioma}.pdf")))


def texto_de(leitor) -> str:
    return "\n".join(pagina.extract_text() for pagina in leitor.pages)


def destinos_dos_links(leitor) -> list[int]:
    """A página (1-based) para onde cada link interno do PDF aponta, na ordem do documento."""
    paginas = [pagina.indirect_reference for pagina in leitor.pages]
    return [paginas.index(anotacao.get_object()["/Dest"][0]) + 1
            for pagina in leitor.pages for anotacao in pagina.get("/Annots", []) if "/Dest" in anotacao.get_object()]


def manual_do(ambiente, nome="manual-pt.pdf") -> Path:
    return ambiente["projeto"] / ".sentry" / "manual" / nome


def secao_do(ambiente, modulo="cadastro") -> Path:
    return ambiente["projeto"] / ".sentry" / "manual" / "secoes" / f"{modulo}.md"


# cenario: manual de roteiro valido e gravado em pdf
def test_manual_de_roteiro_valido_e_gravado_em_pdf(ambiente, capsys):
    codigo = cli.main(["manual", "cadastro"])
    saida = capsys.readouterr().out
    assert codigo == cli.EXIT_OK
    assert manual_do(ambiente).read_bytes().startswith(b"%PDF")
    assert "seção cadastro criada em .sentry/manual/secoes/cadastro.md" in saida
    assert ".sentry/manual/manual-pt.pdf" in saida


# cenario: manual traz titulo e os passos na ordem do roteiro
def test_manual_traz_titulo_e_os_passos_na_ordem_do_roteiro(ambiente):
    cli.main(["manual", "cadastro"])
    texto = secao_do(ambiente).read_text(encoding="utf-8")
    assert texto.startswith("---\nmodulo: cadastro\nordem: 1\n---\n# Como criar uma conta\n")
    assert ":::passos\n1. Abrir o cadastro\n   Esta é a tela de cadastro.\n2. Informar o nome\n" in texto
    pdf = texto_do_pdf(manual_do(ambiente))
    assert "Antes de começar" not in pdf and "Ana Souza" not in pdf          # o fluxo não é reproduzido
    posicoes = [pdf.index(passo["titulo"]) for passo in ROTEIRO["passos"]]
    assert posicoes == sorted(posicoes)


# cenario: secao nova nasce do roteiro com a ordem seguinte
def test_secao_nova_nasce_do_roteiro_com_a_ordem_seguinte(ambiente):
    segundo = {**ROTEIRO, "titulo": "Como entrar", "passos": ROTEIRO["passos"][:2]}
    escrever(ambiente["projeto"], "entrada", segundo)
    cli.main(["manual", "cadastro"])
    cli.main(["manual", "entrada"])
    assert "ordem: 1" in secao_do(ambiente).read_text(encoding="utf-8")
    nova = secao_do(ambiente, "entrada").read_text(encoding="utf-8")
    assert "ordem: 2" in nova and "# Como entrar" in nova and "<!--" in nova      # com as dicas de como escrever


# cenario: atualizar os passos preserva o que foi escrito a mao
def test_atualizar_os_passos_preserva_o_que_foi_escrito_a_mao(ambiente):
    cli.main(["manual", "cadastro"])
    arquivo = secao_do(ambiente)
    escrito = arquivo.read_text(encoding="utf-8").replace(
        "# Como criar uma conta\n", "# Como criar uma conta\n\nMinha introdução com **destaque**.\n\n> [!INFO] Atenção ao e-mail\n> Use o do trabalho.\n")
    arquivo.write_text(escrito, encoding="utf-8")
    novo = json.loads(json.dumps(ROTEIRO))
    novo["passos"][1]["fala"] = "Digite o nome completo."
    novo["passos"].append({"titulo": "Conferir", "fala": "Veja a lista.", "acao": {"apontar": "#lista"}})
    escrever(ambiente["projeto"], "cadastro", novo)
    cli.main(["manual", "cadastro"])
    atual = arquivo.read_text(encoding="utf-8")
    assert "Minha introdução com **destaque**." in atual and "> [!INFO] Atenção ao e-mail" in atual       # intacto
    assert "Digite o nome completo." in atual and "5. Conferir\n   Veja a lista." in atual                 # atualizado
    assert "Digite o seu nome." not in atual
    assert atual.splitlines().count(":::passos") == 1       # o bloco é trocado, não duplicado


# cenario: manual sem modulo atualiza todas as secoes
def test_manual_sem_modulo_atualiza_todas_as_secoes(ambiente, capsys):
    escrever(ambiente["projeto"], "entrada", {**ROTEIRO, "titulo": "Como entrar", "passos": ROTEIRO["passos"][:1]})
    cli.main(["manual", "cadastro"])
    cli.main(["manual", "entrada"])
    novo = json.loads(json.dumps(ROTEIRO))
    novo["passos"][0]["titulo"] = "Abrir a tela de cadastro"
    escrever(ambiente["projeto"], "cadastro", novo)
    capsys.readouterr()
    assert cli.main(["manual"]) == cli.EXIT_OK
    assert "Abrir a tela de cadastro" in secao_do(ambiente).read_text(encoding="utf-8")
    saida = capsys.readouterr().out
    assert "seção" not in saida and ".sentry/manual/manual-pt.pdf" in saida
    assert "Abrir a tela de cadastro" in texto_do_pdf(manual_do(ambiente))


# cenario: secao so de texto convive com as secoes de roteiro
def test_secao_so_de_texto_convive_com_as_secoes_de_roteiro(ambiente, capsys):
    cli.main(["manual", "cadastro"])
    texto = ambiente["projeto"] / ".sentry" / "manual" / "secoes" / "comandos.md"
    texto.write_text("---\nmodulo: comandos\nordem: 2\n---\n# Os comandos\n\nUse **sentry init --install** para começar.\n\n"
                     "> [!INFO] Sem roteiro\n> Esta seção não tem passos.\n", encoding="utf-8")
    antes = texto.read_text(encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["manual"]) == cli.EXIT_OK
    assert texto.read_text(encoding="utf-8") == antes                              # sem roteiro, nada é sincronizado
    pdf = texto_do_pdf(manual_do(ambiente))
    assert "Os comandos" in pdf and "Esta seção não tem passos." in pdf and "Digite o seu nome." in pdf
    assert "sentry init --install" in pdf                                          # os dois traços aparecem
    assert cli.main(["manual", "comandos"]) == cli.EXIT_INFRA                      # pedir o módulo sem roteiro segue sendo erro
    assert "roteiro não encontrado" in capsys.readouterr().out


# cenario: passo marcado como so do video fica fora do manual
def test_passo_marcado_como_so_do_video_fica_fora_do_manual(ambiente, capsys):
    dados = json.loads(json.dumps(ROTEIRO))
    dados["passos"][0]["manual"] = False                      # preparo que só o vídeo precisa, como entrar no sistema
    escrever(ambiente["projeto"], "cadastro", dados)
    assert cli.main(["manual", "cadastro"]) == cli.EXIT_OK
    secao_md = secao_do(ambiente).read_text(encoding="utf-8")
    assert "Abrir o cadastro" not in secao_md and ":::passos\n1. Informar o nome\n" in secao_md      # numeração recomeça
    assert "Abrir o cadastro" not in texto_do_pdf(manual_do(ambiente))
    assert training.validar_roteiro(dados) == []              # o roteiro, que o vídeo usa, continua válido
    dados["passos"][1]["manual"] = "nao"
    assert training.validar_roteiro(dados) == ["passo 2: campo 'manual' deve ser true ou false"]
    for passo in dados["passos"]:
        passo["manual"] = False
    escrever(ambiente["projeto"], "cadastro", dados)
    capsys.readouterr()
    assert cli.main(["manual", "cadastro"]) == cli.EXIT_INFRA
    assert 'todos os passos do roteiro têm "manual": false' in capsys.readouterr().out


# cenario: secoes saem na ordem declarada
def test_secoes_saem_na_ordem_declarada(ambiente):
    for modulo in ("a", "b", "c"):
        escrever(ambiente["projeto"], modulo, {**ROTEIRO, "titulo": f"Título {modulo.upper()}"})
        cli.main(["manual", modulo])
    arquivo = secao_do(ambiente, "a")
    arquivo.write_text(arquivo.read_text(encoding="utf-8").replace("ordem: 1", "ordem: 9"), encoding="utf-8")
    sem_ordem = secao_do(ambiente, "c")
    sem_ordem.write_text(sem_ordem.read_text(encoding="utf-8").replace("ordem: 3\n", ""), encoding="utf-8")
    assert [s.modulo for s in manual_md.listar_secoes(ambiente["projeto"])] == ["b", "a", "c"]   # com ordem primeiro, o resto pelo nome
    cli.main(["manual"])
    pdf = texto_do_pdf(manual_do(ambiente))
    assert pdf.index("Título B") < pdf.index("Título A") < pdf.index("Título C")


# cenario: sumario lista as secoes com a pagina sem pintar link na linha
def test_sumario_lista_as_secoes_com_a_pagina_sem_pintar_link_na_linha(tmp_path):
    comprido = "Uma seção com um título tão comprido que não cabe numa linha do sumário e precisa ser cortado"
    secoes = [secao(1, "Primeira"), secao(2, "Segunda", [("passos", passos_longos(12))]), secao(3, "Terceira"),
              secao(4, comprido)]
    leitor = pdf_de(tmp_path, secoes)
    paginas = manual._montar(manual.conteudo(secoes, "pt", Identidade(nome="Loja")), {})[1]
    primeira = leitor.pages[0].extract_text()
    assert "Sumário" in primeira
    for n, nome in enumerate(("Primeira", "Segunda", "Terceira"), start=1):
        assert re.search(rf"\n{n}\. {nome} [. ]+ {paginas[n]}\n", primeira)          # o número impresso é a página real
    assert "Uma seção com um título tão comprido" in primeira and "..." in primeira        # o título longo é cortado
    assert paginas[3] > paginas[2] > paginas[1] > 1 and paginas[3] - paginas[2] >= 1    # cada seção em página nova
    # o leitor de PDF pinta a área de todo link ao passar o mouse: na capa não há nenhum, e o único de cada
    # página é o "Voltar ao sumário" do rodapé, que leva à capa
    assert destinos_dos_links(leitor) == [1] * (len(leitor.pages) - 1)


# cenario: manual com uma secao so nao tem sumario
def test_manual_com_uma_secao_so_nao_tem_sumario(tmp_path):
    leitor = pdf_de(tmp_path, [secao()])
    texto = texto_de(leitor)
    assert "Sumário" not in texto and destinos_dos_links(leitor) == []
    assert "SEÇÃO 1" in leitor.pages[0].extract_text()       # a seção segue na própria capa


# cenario: rodape traz o app o manual e a volta ao sumario
def test_rodape_traz_o_app_o_manual_e_a_volta_ao_sumario(tmp_path):
    secoes = [secao(1, "Primeira", [("passos", passos_longos(12))]), secao(2, "Segunda")]
    pt, en = pdf_de(tmp_path, secoes), pdf_de(tmp_path, secoes, "en")
    capa, segunda = pt.pages[0].extract_text(), pt.pages[1].extract_text()
    assert "Loja · Manual do usuário" in capa and "Voltar" not in capa             # a capa já é o topo
    assert "Loja · Manual do usuário" in segunda and "Voltar ao sumário" in segunda
    assert "Loja · User manual" in en.pages[1].extract_text() and "Back to contents" in en.pages[1].extract_text()
    sem_sumario = pdf_de(tmp_path, [secao(blocos=[("passos", passos_longos(12))])])
    assert "Voltar ao início" in sem_sumario.pages[1].extract_text()               # sem sumário, volta ao início
    # o link tem o tamanho do texto, não o da linha: sem uma faixa larga pintada ao passar o mouse
    anotacao = pt.pages[1]["/Annots"][0].get_object()
    x0, _, x1, _ = (float(v) for v in anotacao["/Rect"])
    assert x1 - x0 < 100


# cenario: rodape da capa traz a versao do manual
def test_rodape_da_capa_traz_a_versao_do_manual(ambiente, tmp_path):
    secoes = [secao(1, "Primeira", [("passos", passos_longos(12))]), secao(2, "Segunda")]
    capa = pdf_de(tmp_path, secoes).pages[0].extract_text()
    assert "Manual vigente · versão 1.0" in capa                                   # sem `[manual]`, a versão é 1.0
    assert "Manual vigente" not in pdf_de(tmp_path, secoes).pages[1].extract_text()  # só a capa, onde está o sumário
    assert "Current manual · version 1.0" in pdf_de(tmp_path, secoes, "en").pages[0].extract_text()
    (ambiente["projeto"] / "sentry.toml").write_text('[manual]\nversao = "2.3"\n', encoding="utf-8")
    assert cli.main(["manual", "cadastro"]) == cli.EXIT_OK
    assert "Manual vigente · versão 2.3" in texto_do_pdf(manual_do(ambiente))      # a versão que o projeto declara


# cenario: introducao e negrito aparecem na secao
def test_introducao_e_negrito_aparecem_na_secao(tmp_path):
    blocos = [("paragrafo", "A tela reúne as empresas. Crie a empresa **antes** do usuário."),
              ("subtitulo", "Como funciona"), ("passos", PASSOS)]
    leitor = pdf_de(tmp_path, [secao(blocos=blocos)])
    texto = texto_de(leitor).replace("\n", " ")
    assert "A tela reúne as empresas. Crie a empresa antes do usuário." in texto and "Como funciona" in texto
    fontes = {fonte["/BaseFont"] for pagina in leitor.pages for fonte in
              (f.get_object() for f in pagina["/Resources"]["/Font"].values())}
    assert "/Helvetica-Bold" in fontes


# cenario: aviso tem icone e cor do tipo
def test_aviso_tem_icone_e_cor_do_tipo(tmp_path):
    for tipo in ("info", "sucesso", "atencao"):
        leitor = pdf_de(tmp_path, [secao(blocos=[("aviso", tipo, "Título do aviso", "Texto do aviso.")])])
        assert "TÍTULO DO AVISO" in texto_de(leitor).replace("\n", " ") or "TÍTULO DO AVISO" in texto_de(leitor)
        assert "Texto do aviso." in texto_de(leitor)
        assert manual.AVISOS[tipo]["cor"] in cores_do_pdf(tmp_path / "pt.pdf")
    sem_titulo = pdf_de(tmp_path, [secao(blocos=[("aviso", "info", "", "Só o texto.")])])
    assert "Só o texto." in texto_de(sem_titulo)


# cenario: cartoes ficam lado a lado
def test_cartoes_ficam_lado_a_lado(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    itens = [("Primeiro", "Texto um."), ("Segundo", "Texto dois."), ("Terceiro", "Texto três.")]
    leitor = pdf_de(tmp_path, [secao(blocos=[("cartoes", itens)])])
    posicoes = {}
    leitor.pages[0].extract_text(visitor_text=lambda texto, cm, tm, fonte, tamanho: posicoes.update(
        {texto.strip(): (round(tm[4]), round(tm[5]))} if texto.strip() in ("Primeiro", "Segundo", "Terceiro") else {}))
    assert posicoes["Primeiro"][1] == posicoes["Segundo"][1] and posicoes["Primeiro"][0] < posicoes["Segundo"][0]
    assert posicoes["Terceiro"][1] < posicoes["Primeiro"][1] and posicoes["Terceiro"][0] == posicoes["Primeiro"][0]


# cenario: markdown invalido e recusado dizendo o arquivo e a linha
def test_markdown_invalido_e_recusado_dizendo_o_arquivo_e_a_linha(ambiente, capsys):
    cli.main(["manual", "cadastro"])
    arquivo = secao_do(ambiente)
    original = arquivo.read_text(encoding="utf-8")
    casos = {
        "sem front matter": ("# Só título\n", ":1:", "bloco \"---\""),
        "sem título": ("---\nmodulo: cadastro\n---\ntexto\n", ":4:", "falta o título"),
        "aviso torto": (original.replace("# Como criar uma conta\n", "# Como criar uma conta\n> [!XYZ] oi\n"), ":6:", "o aviso começa com"),
        "bloco desconhecido": (original.replace("# Como criar uma conta\n", "# Como criar uma conta\n:::foo\n"), ":::foo", "bloco desconhecido"),
        "bloco aberto": (original.replace("# Como criar uma conta\n", "# Como criar uma conta\n:::cartoes\n### A\n"), "não foi fechado", ":::"),
        "ordem torta": (original.replace("ordem: 1", "ordem: um"), ":1:", "ordem precisa ser um número"),
    }
    for nome, (texto, *esperado) in casos.items():
        arquivo.write_text(texto, encoding="utf-8")
        assert cli.main(["manual"]) == cli.EXIT_INFRA, nome
        saida = capsys.readouterr().out
        assert "secoes/cadastro.md" in saida and all(trecho in saida for trecho in esperado), (nome, saida)


# cenario: manual sem secoes pede a primeira
def test_manual_sem_secoes_pede_a_primeira(ambiente, capsys):
    assert cli.main(["manual"]) == cli.EXIT_INFRA
    assert "sentry manual <modulo>" in capsys.readouterr().out
    assert not manual_do(ambiente).exists()


# cenario: secao com roteiro apagado e recusada
def test_secao_com_roteiro_apagado_e_recusada(ambiente, capsys):
    cli.main(["manual", "cadastro"])
    (ambiente["projeto"] / ".sentry" / "training" / "cadastro.json").unlink()
    assert cli.main(["manual"]) == cli.EXIT_INFRA
    assert "nenhuma seção tem roteiro em .sentry/training/" in capsys.readouterr().out      # sem app para ler a identidade


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
    leitor = pdf_de(tmp_path, [secao(blocos=[("passos", passos_longos())])],
                    identidade=Identidade(nome="Loja Verde", cor=VERDE, logo=png_minimo()))
    paginas = leitor.pages
    assert len(paginas) >= 2
    for pagina in paginas:
        assert "Loja Verde" in pagina.extract_text()
        assert len(pagina["/Resources"]["/XObject"]) == 1    # a logo
    assert VERDE in cores_do_pdf(tmp_path / "pt.pdf")


# cenario: cor clara demais e escurecida para o texto
def test_cor_clara_demais_e_escurecida_para_o_texto(tmp_path):
    assert manual.cor_legivel(VERDE) == VERDE
    assert manual.cor_legivel((57, 255, 20)) == (34, 153, 12)
    assert manual.tom_claro((0, 0, 0)) == (230, 230, 230)
    pdf_de(tmp_path, identidade=Identidade(nome="Neon", cor=(57, 255, 20)))
    cores = cores_do_pdf(tmp_path / "pt.pdf")
    assert (57, 255, 20) in cores          # o filete do cabeçalho mantém a cor do app
    assert (34, 153, 12) in cores          # o subtítulo usa a versão legível


# cenario: capa traz MANUAL DO USUARIO e o nome do app
def test_capa_traz_manual_do_usuario_e_o_nome_do_app(tmp_path):
    pt, en = pdf_de(tmp_path), pdf_de(tmp_path, idioma="en")
    capa_pt, capa_en = pt.pages[0].extract_text(), en.pages[0].extract_text()
    assert "MANUAL DO USUÁRIO" in capa_pt and capa_pt.count("Loja") >= 3           # cabeçalho, faixa e rodapé
    assert "USER MANUAL" in capa_en and "MANUAL DO USUÁRIO" not in capa_en
    assert "Como criar uma conta" in capa_pt                                       # o título da seção
    assert manual.texto_sobre(VERDE) == (255, 255, 255)
    assert manual.texto_sobre((255, 255, 0)) == manual.TEXTO_ESCURO


# cenario: titulo da capa e centralizado e a logo vira marca d'agua na faixa
def test_titulo_da_capa_e_centralizado_e_a_logo_vira_marca_dagua_na_faixa(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    com_logo = pdf_de(tmp_path / "a", identidade=Identidade(nome="Loja", cor=VERDE, logo=png_minimo()))
    sem_logo = pdf_de(tmp_path / "b", identidade=Identidade(nome="Loja", cor=VERDE))

    def opacidades(leitor):
        estados = leitor.pages[0]["/Resources"].get("/ExtGState", {})
        return {round(float(estado.get_object()["/ca"]), 2) for estado in estados.values() if "/ca" in estado.get_object()}

    assert manual.MARCA_DAGUA_OPACIDADE in opacidades(com_logo)
    assert manual.MARCA_DAGUA_OPACIDADE not in opacidades(sem_logo)

    posicoes = []
    com_logo.pages[0].extract_text(
        visitor_text=lambda texto, cm, tm, fonte, tamanho: posicoes.append(tm[4]) if "MANUAL DO" in texto else None)
    assert 100 < posicoes[0] < 200          # à esquerda, o título começaria em ~80 pt


# cenario: marca d'agua tira o fundo solido do logo
def test_marca_dagua_tira_o_fundo_solido_do_logo(tmp_path):
    def modos(logo):
        leitor = pdf_de(tmp_path, identidade=Identidade(nome="L", cor=VERDE, logo=logo))
        estados = leitor.pages[0]["/Resources"].get("/ExtGState", {})
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
    secoes = [secao(blocos=[("passos", passos_longos())])]
    pt, en = pdf_de(tmp_path, secoes), pdf_de(tmp_path, secoes, "en")
    total = len(pt.pages)
    assert total >= 2
    for n, pagina in enumerate(pt.pages, start=1):
        texto = pagina.extract_text()
        assert f"Página {n} de {total}" in texto
        assert texto.count("Loja") == (3 if n == 1 else 2)      # cabeçalho e rodapé; na capa, também a faixa
    assert f"Page 1 of {total}" in en.pages[0].extract_text()


# cenario: numero do passo fica no centro exato do selo
def test_numero_do_passo_fica_no_centro_exato_do_selo(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    mm = 72 / 25.4
    for n in (1, 7, 10, 11):
        pdf = manual.ManualPDF(Identidade(nome="Loja", cor=VERDE), manual.TEXTOS["pt"])
        pdf.add_page()
        manual._numero_no_selo(pdf, n, centro_y=100)
        largura = pdf.get_string_width(str(n))        # antes do output, cujo rodapé troca a fonte
        destino = tmp_path / f"n{n}.pdf"
        pdf.output(str(destino))
        achados = []
        pypdf.PdfReader(str(destino)).pages[0].extract_text(
            visitor_text=lambda texto, cm, tm, fonte, tamanho: achados.append((texto, tm[4], tm[5])) if texto.strip() == str(n) else None)
        _, x, y = achados[0]
        centro_x_esperado = (pdf.l_margin + manual.RECUO_DO_SELO + manual.DIAMETRO_DO_SELO / 2) * mm
        assert x + largura * mm / 2 == pytest.approx(centro_x_esperado, abs=0.3)           # no meio na horizontal
        altura = manual.ALTURA_DO_ALGARISMO * manual.TAMANHO_DO_NUMERO
        assert y + altura / 2 == pytest.approx((pdf.h - 100) * mm, abs=0.3)               # e na vertical, pelos algarismos


# cenario: capa traz so a data de geracao sob a faixa
def test_capa_traz_so_a_data_de_geracao_sob_a_faixa(tmp_path):
    identidade = Identidade(nome="Loja")
    assert manual.conteudo([secao()], "pt", identidade, hoje=date(2026, 10, 22))["gerado_em"] == "Gerado em 22/10/2026"
    assert manual.conteudo([secao()], "en", identidade, hoje=date(2026, 10, 22))["gerado_em"] == "Generated on 2026-10-22"
    capa = pdf_de(tmp_path).pages[0].extract_text()
    assert "Gerado em 22/10/2026" in capa and "passos  ·" not in capa      # nada de contagem de passos


# cenario: cada passo vira marcador do pdf
def test_cada_passo_vira_marcador_do_pdf(tmp_path):
    leitor = pdf_de(tmp_path, [secao(1, "Primeira"), secao(2, "Segunda")])
    def titulos(itens):          # o outline do pypdf: cada seção, seguida da lista dos passos dela
        return [titulos(item) if isinstance(item, list) else item.title for item in itens]

    passos = ["1. Abrir o cadastro", "2. Informar o nome", "3. Informar o sobrenome", "4. Salvar"]
    assert titulos(leitor.outline) == ["1. Primeira", passos, "2. Segunda", passos]


# cenario: linha do tempo fecha com fim do passo a passo junto do ultimo passo
def test_linha_do_tempo_fecha_com_fim_do_passo_a_passo_junto_do_ultimo_passo(tmp_path):
    for quantos in range(1, 31):
        ultima = pdf_de(tmp_path, [secao(blocos=[("passos", passos_longos(quantos))])]).pages[-1].extract_text()
        assert "Fim do passo a passo" in ultima and f"Passo {quantos}" in ultima      # nunca sozinho numa página
    assert "End of the step by step" in pdf_de(tmp_path, idioma="en").pages[-1].extract_text()


# cenario: cabecalho mostra a secao da pagina
def test_cabecalho_mostra_a_secao_da_pagina(tmp_path):
    secoes = [secao(1, "Primeira", [("passos", passos_longos(12))]), secao(2, "Segunda")]
    paginas = pdf_de(tmp_path, secoes).pages
    assert "Seção" not in paginas[0].extract_text().replace("SEÇÃO", "")        # a capa não tem seção
    textos = [pagina.extract_text() for pagina in paginas]
    assert any("Seção 1" in texto for texto in textos[1:-1]) and "Seção 2" in textos[-1]
    assert "Section 2" in pdf_de(tmp_path, secoes, "en").pages[-1].extract_text()


# cenario: pdf declara titulo autor e idioma
def test_pdf_declara_titulo_autor_e_idioma(tmp_path):
    pt, en = pdf_de(tmp_path), pdf_de(tmp_path, idioma="en")
    assert pt.metadata.title == "Loja - MANUAL DO USUÁRIO" and pt.metadata.author == "Loja"
    assert pt.trailer["/Root"]["/Lang"] == "pt-BR" and en.trailer["/Root"]["/Lang"] == "en"


# cenario: app fora do ar e recusado
def test_app_fora_do_ar_e_recusado(ambiente, monkeypatch, capsys):
    with socket.socket() as livre:
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
    escrever(ambiente["projeto"], "fora", {**ROTEIRO, "base": f"http://127.0.0.1:{porta}"})
    monkeypatch.setattr(training, "app_responde", APP_RESPONDE_REAL)
    assert cli.main(["manual", "fora"]) == cli.EXIT_INFRA
    assert "suba o app" in capsys.readouterr().out
    assert not manual_do(ambiente).exists()


# cenario: manual nao aciona agente nem ffmpeg
def test_manual_nao_aciona_agente_nem_ffmpeg(ambiente, monkeypatch):
    monkeypatch.setattr(promo.shutil, "which", lambda nome: None)
    monkeypatch.setattr(promo.subprocess, "run", lambda *args, **kwargs: pytest.fail("o manual não executa subprocesso"))
    assert cli.main(["manual", "cadastro"]) == cli.EXIT_OK
    assert manual_do(ambiente).is_file()


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
    assert not (ambiente["projeto"] / ".sentry" / "manual").exists()


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
    texto = texto_do_pdf(manual_do(ambiente, "manual-en.pdf"))
    assert "USER MANUAL" in texto and "Step by step" in texto and "SECTION 1" in texto
    assert "Passo a passo" not in texto
    assert "Digite o seu nome." in texto


# cenario: texto fora do latin-1 nao derruba o pdf
def test_texto_fora_do_latin_1_nao_derruba_o_pdf(ambiente):
    dados = json.loads(json.dumps(ROTEIRO))
    dados["passos"][0]["fala"] = "Clique — “Salvar”… 🙂 e --risque-- __assim__"
    escrever(ambiente["projeto"], "estranho", dados)
    assert cli.main(["manual", "estranho"]) == cli.EXIT_OK
    texto = texto_do_pdf(manual_do(ambiente))
    assert 'Clique - "Salvar"... ? e --risque-- _assim_' in texto


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
