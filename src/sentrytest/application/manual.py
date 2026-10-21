"""`sentry manual`: o manual em PDF de um módulo, do roteiro ao arquivo.

É o `training` sem o vídeo: o fluxo vem do mesmo roteiro (`.sentry/training/<modulo>.json`) e
o resultado é só texto, um passo por cartão. Não chama agente nem gasta token. O fluxo não é
reproduzido: do app o Sentry lê só a identidade (nome, cor e logo), na página de `base`, e ela
vira o cabeçalho padrão de toda página do PDF. Por isso o app de `base` precisa estar no ar.
"""
import struct
import urllib.request
import zlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from fpdf import FPDF
from fpdf.enums import Align

from . import training
from .promo import IDIOMA_PADRAO, validar_idioma

PASTA_DE_MANUAIS = Path(".sentry") / "manual"

TEXTOS = {
    "pt": {"manual": "MANUAL DO USUÁRIO", "passos": "Passo a passo", "pagina": "Página", "de": "de"},
    "en": {"manual": "USER MANUAL", "passos": "Step by step", "pagina": "Page", "de": "of"},
}

# As fontes embutidas do PDF só têm latin-1 (o suficiente para PT e EN); a pontuação tipográfica
# que o latin-1 não tem vira o equivalente simples, e o resto, `?`.
_EQUIVALENTES = str.maketrans({
    "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "…": "...", "•": "-", " ": " ",
})

COR_PADRAO = (34, 34, 34)
TEXTO_ESCURO = (31, 41, 55)
CINZA_DO_TEXTO = (75, 85, 99)
CINZA_DA_LINHA = (209, 213, 219)
RECUO_DO_CARTAO = 15
DIAMETRO_DO_SELO = 9
ESPACO_ENTRE_PASSOS = 5
MARCA_DAGUA_OPACIDADE = 0.14
MARCA_DAGUA_ESCALA = 2.3
TEMPO_DO_LOGO_S = 5
LIMITE_DO_LOGO = 2_000_000
_FORMATOS_DE_LOGO = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")

# O nome vem de `application-name`, depois `og:site_name`, depois <title>. A cor vem de
# `theme-color` ou, sem ele, do fundo do primeiro botão ou link colorido (nem branco nem
# transparente). O canvas converte qualquer sintaxe de cor do CSS (hex, hsl, oklch) para RGB.
IDENTIDADE_JS = """
() => {
  const meta = (nome) => ((document.querySelector(`meta[name="${nome}"], meta[property="${nome}"]`) || {}).content || "").trim();
  const rgb = (css) => {
    const tela = document.createElement("canvas");
    tela.width = tela.height = 1;
    const ctx = tela.getContext("2d");
    ctx.fillStyle = css;
    ctx.fillRect(0, 0, 1, 1);
    const d = ctx.getImageData(0, 0, 1, 1).data;
    return d[3] === 255 ? [d[0], d[1], d[2]] : null;
  };
  let cor = meta("theme-color") ? rgb(meta("theme-color")) : null;
  if (!cor) {
    for (const el of document.querySelectorAll("button, input[type=submit], a")) {
      const candidata = rgb(getComputedStyle(el).backgroundColor);
      if (candidata && !candidata.every(c => c > 235)) { cor = candidata; break; }
    }
  }
  const icone = document.querySelector('link[rel="apple-touch-icon"], link[rel~="icon"]');
  return {
    nome: meta("application-name") || meta("og:site_name") || document.title.trim(),
    cor,
    logo: icone && icone.getAttribute("href") ? new URL(icone.getAttribute("href"), document.baseURI).href : "",
  };
}
"""


@dataclass
class Identidade:
    nome: str
    cor: tuple[int, int, int] = COR_PADRAO
    logo: bytes | None = None


def _baixar_logo(url: str) -> bytes | None:
    """O logo é enfeite: só PNG e JPEG (o que o PDF embute); qualquer outra coisa, ou falha, fica sem logo."""
    if not url.startswith(("http://", "https://")):
        return None
    try:
        with urllib.request.urlopen(url, timeout=TEMPO_DO_LOGO_S) as resposta:
            dados = resposta.read(LIMITE_DO_LOGO + 1)
    except (OSError, ValueError):
        return None
    return dados if len(dados) <= LIMITE_DO_LOGO and dados.startswith(_FORMATOS_DE_LOGO) else None


def _identidade(pagina, base: str) -> Identidade:
    lida = pagina.evaluate(IDENTIDADE_JS)
    return Identidade(nome=lida.get("nome") or urlparse(base).hostname or base,
                      cor=tuple(lida["cor"]) if lida.get("cor") else COR_PADRAO,
                      logo=_baixar_logo(lida.get("logo") or ""))


def _luminosidade(cor: tuple[int, int, int]) -> float:
    return (0.299 * cor[0] + 0.587 * cor[1] + 0.114 * cor[2]) / 255


def cor_legivel(cor: tuple[int, int, int]) -> tuple[int, int, int]:
    """Escurece uma cor clara demais para servir de texto sobre o branco."""
    return cor if _luminosidade(cor) <= 0.55 else tuple(int(canal * 0.6) for canal in cor)


def texto_sobre(fundo: tuple[int, int, int]) -> tuple[int, int, int]:
    """Branco sobre fundo escuro, texto escuro sobre fundo claro: o que se escreve em cima da cor do app."""
    return (255, 255, 255) if _luminosidade(fundo) <= 0.6 else TEXTO_ESCURO


def tom_claro(cor: tuple[int, int, int], forca: float = 0.1) -> tuple[int, int, int]:
    """A cor do app diluída no branco: `forca` é a parte que resta da cor (0,1 = 10%)."""
    return tuple(round(255 - (255 - canal) * forca) for canal in cor)


def _latin1(texto: str) -> str:
    return texto.translate(_EQUIVALENTES).encode("latin-1", "replace").decode("latin-1")


def ler_identidade(roteiro: dict) -> Identidade:
    """Abre a página de `base` no Playwright e devolve a identidade do app (nome, cor e logo)."""
    if training.sync_playwright is None:
        raise ValueError(f"falta o Playwright do Python; instale com: {training.INSTALAR_PLAYWRIGHT}")
    base = roteiro["base"]
    try:
        with training.sync_playwright() as playwright:
            navegador = playwright.chromium.launch()
            try:
                page = navegador.new_context(viewport=training.VIEWPORT).new_page()
                page.goto(base, wait_until="networkidle")
                return _identidade(page, base)
            finally:
                navegador.close()
    except training.PlaywrightError as erro:
        raise ValueError(f"a leitura falhou: {training._traduzir_erro(erro, base)}") from None


def conteudo(roteiro: dict, idioma: str, identidade: Identidade | None = None) -> dict:
    """O que o manual diz, antes de virar PDF: identidade, título e passos numerados."""
    return {"identidade": identidade or Identidade(nome=urlparse(roteiro["base"]).hostname or roteiro["base"]),
            "titulo": roteiro["titulo"], "textos": TEXTOS[idioma],
            "passos": [(n, passo["titulo"], passo["fala"]) for n, passo in enumerate(roteiro["passos"], start=1)]}


class ManualPDF(FPDF):
    """O molde do manual: cabeçalho (logo, nome do app e filete na cor do app) e rodapé (página à
    esquerda, nome do app à direita) em toda página."""

    def __init__(self, identidade: Identidade, textos: dict):
        super().__init__()
        self.identidade, self.textos = identidade, textos
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=24)
        self.alias_nb_pages()

    def header(self):
        # o fundo branco explícito dá à mesclagem da marca d'água um branco sobre o qual somar
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, self.w, self.h, style="F")
        x = self.l_margin
        if self.identidade.logo:
            self.image(BytesIO(self.identidade.logo), x=x, y=9, h=11)
            x += 14
        self.set_xy(x, 9)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*TEXTO_ESCURO)
        self.cell(0, 11, _latin1(self.identidade.nome), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.identidade.cor)
        self.set_line_width(0.9)
        self.line(self.l_margin, 23, self.w - self.r_margin, 23)
        self.set_y(31)

    def footer(self):
        self.set_draw_color(*CINZA_DA_LINHA)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.h - 17, self.w - self.r_margin, self.h - 17)
        self.set_y(-13)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*CINZA_DO_TEXTO)
        metade = (self.w - self.l_margin - self.r_margin) / 2
        pagina = f"{self.textos['pagina']} {self.page_no()} {self.textos['de']} {{nb}}"
        self.cell(metade, 6, pagina, align="L")
        self.cell(metade, 6, _latin1(self.identidade.nome), align="R")


def _garantir_espaco(pdf: FPDF, altura: float) -> None:
    """Um bloco não é cortado no meio: se não cabe no que resta da página, começa na seguinte."""
    if pdf.get_y() + altura > pdf.page_break_trigger:
        pdf.add_page()


def _linhas(pdf: FPDF, largura: float, altura_da_linha: float, texto: str) -> int:
    return len(pdf.multi_cell(largura, altura_da_linha, _latin1(texto), dry_run=True, output="LINES"))


def _faixa_do_titulo(pdf: ManualPDF, dados: dict) -> None:
    """O título grande do manual, numa faixa na cor do app, com o título do roteiro embaixo."""
    cor, largura = pdf.identidade.cor, pdf.w - pdf.l_margin - pdf.r_margin
    sobre, miolo = texto_sobre(cor), largura - 16
    pdf.set_font("Helvetica", "", 15)
    altura = 8 + 13 + 3 + _linhas(pdf, miolo, 7, dados["titulo"]) * 7 + 8
    y = pdf.get_y()
    pdf.set_fill_color(*cor)
    pdf.rect(pdf.l_margin, y, largura, altura, style="F", round_corners=True, corner_radius=3)
    if pdf.identidade.logo:
        _marca_dagua(pdf, y, altura)
    pdf.set_xy(pdf.l_margin + 8, y + 8)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*sobre)
    pdf.cell(miolo, 13, _latin1(dados["textos"]["manual"]), align="C")
    pdf.set_xy(pdf.l_margin + 8, y + 8 + 13 + 3)
    pdf.set_font("Helvetica", "", 15)
    pdf.multi_cell(miolo, 7, _latin1(dados["titulo"]), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_y(y + altura + 10)


def _fundo_do_logo(logo: bytes) -> tuple[int, int, int] | None:
    """A cor do fundo sólido de um logo PNG (o pixel do canto); None se ele é transparente ou ilegível.

    No primeiro pixel da primeira linha nenhum filtro do PNG precisa de vizinho, então o valor
    cru já é a cor: dá para lê-la só com a biblioteca padrão.
    """
    if not logo.startswith(_FORMATOS_DE_LOGO[0]):
        return None
    try:
        pedacos, posicao, dados = {}, 8, b""
        while posicao + 8 <= len(logo):
            tamanho, tipo = struct.unpack(">I4s", logo[posicao:posicao + 8])
            corpo = logo[posicao + 8:posicao + 8 + tamanho]
            posicao += 12 + tamanho
            if tipo == b"IDAT":
                dados += corpo
            else:
                pedacos[tipo] = corpo
        profundidade, tipo_de_cor = struct.unpack(">BB", pedacos[b"IHDR"][8:10])
        pixel = zlib.decompressobj().decompress(dados, 8)[1:]          # tira o byte de filtro
        if b"tRNS" in pedacos or profundidade != 8:
            return None
        if tipo_de_cor in (0, 4):
            cor, alfa = (pixel[0],) * 3, pixel[1] if tipo_de_cor == 4 else 255
        elif tipo_de_cor in (2, 6):
            cor, alfa = tuple(pixel[:3]), pixel[3] if tipo_de_cor == 6 else 255
        elif tipo_de_cor == 3:
            cor, alfa = tuple(pedacos[b"PLTE"][3 * pixel[0]:3 * pixel[0] + 3]), 255
        else:
            return None
    except (struct.error, zlib.error, KeyError, IndexError):
        return None
    return cor if len(cor) == 3 and alfa >= 250 else None


def _marca_dagua(pdf: ManualPDF, y: float, altura: float) -> None:
    """A logo do app como marca d'água: enorme, tom sobre tom, cortada pelas bordas da faixa.

    Logo de fundo sólido escuro entra com `Screen` e de fundo claro com `Multiply`: assim o fundo
    some e só o desenho aparece, como num brasão sem moldura. Logo transparente entra como está.
    """
    largura, lado = pdf.w - pdf.l_margin - pdf.r_margin, altura * MARCA_DAGUA_ESCALA
    estilo = {"fill_opacity": MARCA_DAGUA_OPACIDADE}
    fundo = _fundo_do_logo(pdf.identidade.logo)
    if fundo:
        estilo["blend_mode"] = "Screen" if _luminosidade(fundo) <= 0.5 else "Multiply"
    margem = pdf.r_margin
    pdf.set_right_margin(margem - 0.05 * lado)          # a ponta direita da logo passa da borda e é cortada
    with pdf.rect_clip(pdf.l_margin, y, largura, altura), pdf.local_context(**estilo):
        pdf.image(BytesIO(pdf.identidade.logo), x=Align.R, y=y + (altura - lado) / 2, h=lado)
    pdf.set_right_margin(margem)


def _titulo_de_secao(pdf: ManualPDF, texto: str, destaque: tuple[int, int, int]) -> None:
    """O título da seção em negrito, com um filete claro até a margem direita."""
    _garantir_espaco(pdf, 30)
    y = pdf.get_y()
    pdf.set_xy(pdf.l_margin, y)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*destaque)
    largura_do_texto = pdf.get_string_width(_latin1(texto))
    pdf.cell(largura_do_texto + 2, 9, _latin1(texto))
    pdf.set_draw_color(*tom_claro(pdf.identidade.cor, 0.25))
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin + largura_do_texto + 6, y + 4.5, pdf.w - pdf.r_margin, y + 4.5)
    pdf.set_y(y + 9 + 5)


def _medir_passo(pdf: ManualPDF, titulo: str, fala: str) -> float:
    """A altura do cartão do passo: o respiro, o título, a fala e o respiro."""
    largura = pdf.w - pdf.l_margin - pdf.r_margin - RECUO_DO_CARTAO - 8
    pdf.set_font("Helvetica", "B", 11.5)
    linhas_do_titulo = _linhas(pdf, largura, 5.5, titulo)
    pdf.set_font("Helvetica", "", 9.5)
    return max(DIAMETRO_DO_SELO + 3, 4 + linhas_do_titulo * 5.5 + 1 + _linhas(pdf, largura, 4.8, fala) * 4.8 + 4)


def _passo(pdf: ManualPDF, n: int, titulo: str, fala: str, altura: float, altura_seguinte: float | None) -> None:
    """Um passo na linha do tempo: o selo redondo numerado, a linha que o liga ao seguinte e o
    cartão claro com o título em negrito e a fala."""
    cor = pdf.identidade.cor
    largura = pdf.w - pdf.l_margin - pdf.r_margin - RECUO_DO_CARTAO
    _garantir_espaco(pdf, altura + ESPACO_ENTRE_PASSOS)
    y = pdf.get_y()
    centro_x, centro_y = pdf.l_margin + DIAMETRO_DO_SELO / 2, y + altura / 2
    if altura_seguinte is not None:
        # a linha só atravessa o vão se o passo seguinte cabe na mesma página
        proximo_topo = y + altura + ESPACO_ENTRE_PASSOS
        cabe = proximo_topo + altura_seguinte <= pdf.page_break_trigger
        fim = proximo_topo + altura_seguinte / 2 if cabe else y + altura
        pdf.set_draw_color(*tom_claro(cor, 0.25))
        pdf.set_line_width(0.6)
        pdf.line(centro_x, centro_y, centro_x, fim)
    pdf.set_fill_color(*tom_claro(cor, 0.06))
    pdf.set_draw_color(*tom_claro(cor, 0.22))
    pdf.set_line_width(0.25)
    pdf.rect(pdf.l_margin + RECUO_DO_CARTAO, y, largura, altura, style="DF", round_corners=True, corner_radius=3)
    pdf.set_fill_color(*cor)
    pdf.ellipse(pdf.l_margin, centro_y - DIAMETRO_DO_SELO / 2, DIAMETRO_DO_SELO, DIAMETRO_DO_SELO, style="F")
    pdf.set_xy(pdf.l_margin, centro_y - DIAMETRO_DO_SELO / 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*texto_sobre(cor))
    pdf.cell(DIAMETRO_DO_SELO, DIAMETRO_DO_SELO, str(n), align="C")
    miolo = largura - 8
    pdf.set_xy(pdf.l_margin + RECUO_DO_CARTAO + 4, y + 4)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(*TEXTO_ESCURO)
    pdf.multi_cell(miolo, 5.5, _latin1(titulo), new_x="LEFT", new_y="NEXT")
    pdf.set_x(pdf.l_margin + RECUO_DO_CARTAO + 4)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*CINZA_DO_TEXTO)
    pdf.multi_cell(miolo, 4.8, _latin1(fala), new_x="LEFT", new_y="NEXT")
    pdf.set_y(y + altura + ESPACO_ENTRE_PASSOS)


def montar_pdf(dados: dict, destino: Path) -> Path:
    identidade = dados["identidade"]
    pdf = ManualPDF(identidade, dados["textos"])
    pdf.add_page()
    _faixa_do_titulo(pdf, dados)
    _titulo_de_secao(pdf, dados["textos"]["passos"], cor_legivel(identidade.cor))
    alturas = [_medir_passo(pdf, titulo, fala) for _, titulo, fala in dados["passos"]]
    for indice, (n, titulo, fala) in enumerate(dados["passos"]):
        seguinte = alturas[indice + 1] if indice + 1 < len(alturas) else None
        _passo(pdf, n, titulo, fala, alturas[indice], seguinte)
    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destino))
    return destino


def gerar_manual(root: Path, modulo: str, idioma: str = IDIOMA_PADRAO, *, ler_identidade_fn=None) -> Path:
    """Valida, lê a identidade do app e grava `.sentry/manual/<modulo>-<idioma>.pdf`.

    Tudo que dá para recusar sem abrir navegador é recusado antes; e o app é testado antes do
    Playwright, para o erro dizer "suba o app" em vez de um net::ERR_CONNECTION_REFUSED.
    """
    validar_idioma(idioma)
    roteiro = training.carregar_roteiro(root, modulo)
    training.garantir_playwright()
    training.app_responde(roteiro["base"])
    identidade = (ler_identidade_fn or ler_identidade)(roteiro)
    return montar_pdf(conteudo(roteiro, idioma, identidade), root / PASTA_DE_MANUAIS / f"{modulo}-{idioma}.pdf")
