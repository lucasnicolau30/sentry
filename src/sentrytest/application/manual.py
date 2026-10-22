"""`sentry manual`: o manual do usuário do projeto, um PDF só, com uma seção por módulo.

É o `training` sem o vídeo: os passos vêm do mesmo roteiro (`.sentry/training/<modulo>.json`) e o
resto de cada seção (introdução, avisos, cartões) está no Markdown dela, que o dev ou o agente
dele escreve (veja `manual_md`). Não chama agente nem gasta token. O fluxo não é reproduzido: do
app o Sentry lê só a identidade (nome, cor e logo), na página de `base` do primeiro módulo, e ela
vira o cabeçalho padrão de toda página do PDF. Por isso o app de `base` precisa estar no ar.
"""
import re
import struct
import urllib.request
import zlib
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from fpdf import FPDF
from fpdf.enums import Align

from ..adapters.toml_config import load_config
from . import manual_md, training
from .promo import IDIOMA_PADRAO, validar_idioma

PASTA_DE_MANUAIS = Path(".sentry") / "manual"

TEXTOS = {
    "pt": {"manual": "MANUAL DO USUÁRIO", "passos": "Passo a passo", "pagina": "Página", "de": "de",
           "gerado": "Gerado em {data}", "secao": "Seção", "sumario": "Sumário", "manual_curto": "Manual do usuário",
           "voltar_sumario": "Voltar ao sumário", "vigente": "Manual vigente · versão {versao}", "voltar_inicio": "Voltar ao início",
           "fim": "Fim do passo a passo", "idioma": "pt-BR", "data": "%d/%m/%Y"},
    "en": {"manual": "USER MANUAL", "passos": "Step by step", "pagina": "Page", "de": "of",
           "gerado": "Generated on {data}", "secao": "Section", "sumario": "Contents", "manual_curto": "User manual",
           "voltar_sumario": "Back to contents", "vigente": "Current manual · version {versao}", "voltar_inicio": "Back to top",
           "fim": "End of the step by step", "idioma": "en", "data": "%Y-%m-%d"},
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

# Escala tipográfica e de espaço: todo tamanho do PDF sai daqui (mm e pontos), nenhum número solto.
TAMANHO_CORPO = 10             # a fala: a leitura corrida
TAMANHO_PASSO = 11            # o título do passo
TAMANHO_PEQUENO = 8.5         # linha da data
TAMANHO_TEXTO = 10.5          # parágrafos da seção
LINHA_DO_TEXTO = 5.6
TAMANHO_TITULO_DA_SECAO = 24
ESPACO_ENTRE_BLOCOS = 4
ALTURA_DA_LINHA_DO_SUMARIO = 7.5
LARGURA_DO_NUMERO_DO_SUMARIO = 9
LARGURA_DA_PAGINA_DO_SUMARIO = 10
SUMARIO_MINIMO = 2            # com uma seção só o sumário não diz nada
DIAMETRO_DO_ICONE = 7
RECUO_DO_AVISO = 16
ESPACO_ENTRE_CARTOES = 5
COLUNAS_DOS_CARTOES = 2
# Cores de significado dos avisos, fixas: não dependem da cor do app (informar, concluir, atentar).
AVISOS = {
    "info": {"cor": (14, 116, 144), "fundo": (231, 246, 248)},
    "sucesso": {"cor": (21, 128, 61), "fundo": (234, 246, 237)},
    "atencao": {"cor": (180, 83, 9), "fundo": (254, 243, 231)},
}
CINZA_DO_PONTILHADO = (156, 163, 175)
VERSAO_PADRAO = "1.0"           # a versão do manual, quando o `sentry.toml` não declara `[manual] versao`
RODAPE_ESQUERDA = 0.35        # parte do rodapé que o app e "Manual do usuário" ocupam
LARGURA_DA_BARRA = 1.0        # a barra colorida na borda esquerda de avisos e cartões
LINHA_DO_CORPO = 4.8
LINHA_DO_PASSO = 5.5
DIAMETRO_DO_SELO = 8
RECUO_DO_SELO = 4              # o selo mora dentro do cartão do passo, a esta distância da borda
RECUO_DO_TEXTO_DO_PASSO = RECUO_DO_SELO + DIAMETRO_DO_SELO + 4
ESPACO_ENTRE_PASSOS = 3
TAMANHO_DO_NUMERO = 10.5         # o número dentro do selo
ALTURA_DO_ALGARISMO = 0.716    # altura dos algarismos da Helvetica, em fração do corpo
RESPIRO_DO_CARTAO = 3          # entre a borda do cartão e o texto, em cima e embaixo
ALTURA_DO_FIM = DIAMETRO_DO_SELO + 2
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


def _md(texto: str) -> str:
    """O texto pronto para o PDF: latin-1, com o `**negrito**` e sem os marcadores que o fpdf2
    leria como itálico (`__`) ou sublinhado (`--`). Os traços seguidos (`--install`) saem como estão:
    um hífen solto entre eles desfaz o marcador sem mudar o que se vê."""
    return re.sub(r"-{2,}", lambda achado: "-" + "\u00ad-" * (len(achado.group()) - 1), _latin1(texto)).replace("__", "_")


def _sem_negrito(texto: str) -> str:
    """Título já sai em negrito: o `**` dele só inverteria o estilo."""
    return texto.replace("**", "")


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


def conteudo(secoes: list, idioma: str, identidade: Identidade, hoje: date | None = None,
             versao: str = VERSAO_PADRAO) -> dict:
    """O que o manual diz, antes de virar PDF: identidade, seções (já na ordem), a data em que foi gerado e a versão."""
    textos = TEXTOS[idioma]
    gerado = textos["gerado"].format(data=(hoje or date.today()).strftime(textos["data"]))
    return {"identidade": identidade, "textos": textos, "secoes": secoes, "gerado_em": gerado, "versao": versao}


def _caber(pdf: FPDF, texto: str, largura: float) -> str:
    """O texto cortado com reticências para caber na largura, na fonte já escolhida."""
    if pdf.get_string_width(texto) <= largura:
        return texto
    while texto and pdf.get_string_width(texto + "...") > largura:
        texto = texto[:-1]
    return texto.rstrip() + "..."


class ManualPDF(FPDF):
    """O molde do manual: cabeçalho (logo, nome do app e filete na cor do app; dentro de uma seção,
    "Seção N" à direita) e rodapé (o app em negrito e "Manual do usuário" à esquerda, a página no meio e,
    da segunda página em diante, "Voltar ao sumário" à direita, com um link só do tamanho do texto)."""

    def __init__(self, identidade: Identidade, textos: dict, versao: str = VERSAO_PADRAO):
        super().__init__()
        self.identidade, self.textos, self.secao, self.versao = identidade, textos, "", versao
        self.volta, self.rotulo_de_volta = self.add_link(), textos["voltar_inicio"]
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=24)
        self.alias_nb_pages()
        # o que o leitor de PDF mostra na aba e lê em voz alta
        self.set_title(f"{identidade.nome} - {textos['manual']}")
        self.set_author(identidade.nome)
        self.set_subject(textos["manual"])
        self.set_creator("Sentry")
        self.set_lang(textos["idioma"])

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
        nome = _latin1(self.identidade.nome)
        self.cell(self.get_string_width(nome) + 2, 11, nome)
        livre = self.w - self.r_margin - self.get_x() - 6
        if self.secao and livre > 20:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*CINZA_DO_TEXTO)
            self.cell(livre + 6, 11, _caber(self, _latin1(self.secao), livre), align="R")
        self.set_draw_color(*self.identidade.cor)
        self.set_line_width(0.9)
        self.line(self.l_margin, 23, self.w - self.r_margin, 23)
        self.set_y(31)

    def footer(self):
        self.set_draw_color(*CINZA_DA_LINHA)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.h - 17, self.w - self.r_margin, self.h - 17)
        largura = self.w - self.l_margin - self.r_margin
        self.set_y(-13)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*CINZA_DO_TEXTO)
        identidade = f"{_latin1(_sem_negrito(self.identidade.nome))}"
        identidade = _caber(self, identidade, largura * RODAPE_ESQUERDA - self.get_string_width(f" · {self.textos['manual_curto']}"))
        self.cell(largura * RODAPE_ESQUERDA, 6, _md(f"**{identidade}** · {self.textos['manual_curto']}"), markdown=True)
        pagina = f"{self.textos['pagina']} {self.page_no()} {self.textos['de']} {{nb}}"
        self.set_x(self.l_margin + largura * RODAPE_ESQUERDA)
        self.cell(largura * (1 - 2 * RODAPE_ESQUERDA), 6, pagina, align="C")        # no meio da página
        if self.page_no() > 1:
            self._voltar(self.w - self.r_margin, self.get_y() + 3)
        else:
            self.set_x(self.l_margin + largura * (RODAPE_ESQUERDA + (1 - RODAPE_ESQUERDA) / 2))
            self.cell(largura * (1 - RODAPE_ESQUERDA) / 2, 6, _latin1(self.textos["vigente"].format(versao=self.versao)), align="R")

    def _voltar(self, borda: float, centro_y: float) -> None:
        """"Voltar ao sumário" na ponta direita: o texto sublinhado e um link só do tamanho do texto."""
        self.set_font("Helvetica", "U", 9)
        self.set_text_color(*cor_legivel(self.identidade.cor))
        texto = _latin1(self.rotulo_de_volta)
        largura = self.get_string_width(texto)
        self.set_xy(borda - largura, centro_y - 3)
        self.cell(largura, 6, texto, link=self.volta)


def _garantir_espaco(pdf: FPDF, altura: float) -> None:
    """Um bloco não é cortado no meio: se não cabe no que resta da página, começa na seguinte."""
    if pdf.get_y() + altura > pdf.page_break_trigger:
        pdf.add_page()


def _linhas(pdf: FPDF, largura: float, altura_da_linha: float, texto: str) -> int:
    return len(pdf.multi_cell(largura, altura_da_linha, _md(texto), dry_run=True, output="LINES", markdown=True))


def _faixa_do_titulo(pdf: ManualPDF, dados: dict) -> None:
    """O título grande do manual, numa faixa na cor do app, com o nome do app embaixo."""
    cor, largura = pdf.identidade.cor, pdf.w - pdf.l_margin - pdf.r_margin
    sobre, miolo = texto_sobre(cor), largura - 16
    pdf.set_font("Helvetica", "", 15)
    altura = 8 + 13 + 3 + _linhas(pdf, miolo, 7, pdf.identidade.nome) * 7 + 8
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
    pdf.multi_cell(miolo, 7, _latin1(pdf.identidade.nome), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_y(y + altura + 4)


def _data(pdf: ManualPDF, dados: dict) -> None:
    """Uma linha miúda e centralizada sob a faixa: de quando é o manual."""
    pdf.set_font("Helvetica", "", TAMANHO_PEQUENO)
    pdf.set_text_color(*CINZA_DO_TEXTO)
    pdf.cell(0, 6, _latin1(dados["gerado_em"]), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)


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


def _subtitulo(pdf: ManualPDF, texto: str, destaque: tuple[int, int, int]) -> None:
    """O subtítulo em negrito, com um filete claro até a margem direita."""
    _garantir_espaco(pdf, 30)
    y = pdf.get_y()
    pdf.set_xy(pdf.l_margin, y)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*destaque)
    texto = _sem_negrito(texto)
    largura_do_texto = pdf.get_string_width(_latin1(texto))
    pdf.cell(largura_do_texto + 2, 9, _latin1(texto))
    pdf.set_draw_color(*tom_claro(pdf.identidade.cor, 0.25))
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin + largura_do_texto + 6, y + 4.5, pdf.w - pdf.r_margin, y + 4.5)
    pdf.set_y(y + 9 + 4)


def _medir_passo(pdf: ManualPDF, titulo: str, fala: str) -> float:
    """A altura do cartão do passo: o respiro, o título, a fala e o respiro."""
    largura = pdf.w - pdf.l_margin - pdf.r_margin - RECUO_DO_TEXTO_DO_PASSO - 4
    pdf.set_font("Helvetica", "B", TAMANHO_PASSO)
    linhas_do_titulo = _linhas(pdf, largura, LINHA_DO_PASSO, _sem_negrito(titulo))
    pdf.set_font("Helvetica", "", TAMANHO_CORPO)
    return (RESPIRO_DO_CARTAO + linhas_do_titulo * LINHA_DO_PASSO + 1
            + _linhas(pdf, largura, LINHA_DO_CORPO, fala) * LINHA_DO_CORPO + RESPIRO_DO_CARTAO)


def _selo(pdf: ManualPDF, centro_y: float) -> None:
    pdf.set_fill_color(*pdf.identidade.cor)
    pdf.ellipse(pdf.l_margin + RECUO_DO_SELO, centro_y - DIAMETRO_DO_SELO / 2, DIAMETRO_DO_SELO, DIAMETRO_DO_SELO, style="F")


def _texto_centrado(pdf: ManualPDF, texto: str, centro_x: float, centro_y: float, tamanho: float,
                    cor: tuple[int, int, int]) -> None:
    """Um texto curto no meio exato de um ponto: na horizontal pela largura do texto e na vertical
    pela altura das letras (e não pela caixa da linha, que deixa o texto mais baixo)."""
    pdf.set_font("Helvetica", "B", tamanho)
    pdf.set_text_color(*cor)
    altura_da_letra = ALTURA_DO_ALGARISMO * tamanho * 25.4 / 72      # pontos para mm
    pdf.text(centro_x - pdf.get_string_width(texto) / 2, centro_y + altura_da_letra / 2, texto)


def _numero_no_selo(pdf: ManualPDF, n: int, centro_y: float) -> None:
    _texto_centrado(pdf, str(n), pdf.l_margin + RECUO_DO_SELO + DIAMETRO_DO_SELO / 2, centro_y, TAMANHO_DO_NUMERO,
                    texto_sobre(pdf.identidade.cor))


def _passo(pdf: ManualPDF, n: int, titulo: str, fala: str, altura: float, reservar: float = 0) -> None:
    """Um passo: o cartão claro com o selo redondo numerado dentro, o título em negrito e a fala. Vira também um marcador do PDF (o painel de
    navegação do leitor). `reservar` é o espaço que deve sobrar logo abaixo (o fecho, para o
    último passo não ficar sem ele na página)."""
    cor = pdf.identidade.cor
    largura = pdf.w - pdf.l_margin - pdf.r_margin
    _garantir_espaco(pdf, altura + ESPACO_ENTRE_PASSOS + reservar)
    y = pdf.get_y()
    pdf.start_section(f"{n}. {_sem_negrito(titulo)}", level=1)
    centro_y = y + altura / 2
    pdf.set_fill_color(*tom_claro(cor, 0.06))
    pdf.set_draw_color(*tom_claro(cor, 0.22))
    pdf.set_line_width(0.25)
    pdf.rect(pdf.l_margin, y, largura, altura, style="DF", round_corners=True, corner_radius=3)
    _selo(pdf, centro_y)
    _numero_no_selo(pdf, n, centro_y)
    miolo = largura - RECUO_DO_TEXTO_DO_PASSO - 4
    recuo = pdf.l_margin + RECUO_DO_TEXTO_DO_PASSO
    pdf.set_xy(recuo, y + RESPIRO_DO_CARTAO)
    pdf.set_font("Helvetica", "B", TAMANHO_PASSO)
    pdf.set_text_color(*TEXTO_ESCURO)
    pdf.multi_cell(miolo, LINHA_DO_PASSO, _md(_sem_negrito(titulo)), new_x="LEFT", new_y="NEXT", align="L")
    pdf.set_font("Helvetica", "", TAMANHO_CORPO)
    pdf.set_text_color(*CINZA_DO_TEXTO)
    pdf.set_xy(recuo, pdf.get_y() + 1)
    pdf.multi_cell(miolo, LINHA_DO_CORPO, _md(fala), new_x="LEFT", new_y="NEXT", align="L", markdown=True)
    pdf.set_y(y + altura + ESPACO_ENTRE_PASSOS)


def _fim(pdf: ManualPDF, textos: dict) -> None:
    """O fecho da linha do tempo: um selo com um visto e "Fim do passo a passo". O leitor sabe que acabou."""
    _garantir_espaco(pdf, ALTURA_DO_FIM)
    y = pdf.get_y()
    centro_y = y + ALTURA_DO_FIM / 2
    _selo(pdf, centro_y)
    cx = pdf.l_margin + RECUO_DO_SELO + DIAMETRO_DO_SELO / 2
    pdf.set_draw_color(*texto_sobre(pdf.identidade.cor))
    pdf.set_line_width(0.7)
    with pdf.local_context(stroke_cap_style="round", stroke_join_style="round"):
        pdf.polyline([(cx - 1.8, centro_y + 0.1), (cx - 0.5, centro_y + 1.4), (cx + 1.9, centro_y - 1.4)])
    pdf.set_xy(pdf.l_margin + RECUO_DO_TEXTO_DO_PASSO, centro_y - LINHA_DO_PASSO / 2)
    pdf.set_font("Helvetica", "B", TAMANHO_CORPO)
    pdf.set_text_color(*cor_legivel(pdf.identidade.cor))
    pdf.cell(0, LINHA_DO_PASSO, _latin1(textos["fim"]))
    pdf.set_y(y + ALTURA_DO_FIM)


def _linha_do_sumario(pdf: ManualPDF, n: int, titulo: str, pagina: int) -> None:
    """Uma linha do sumário: o número da seção, o título, o pontilhado e a página. Não é um link: o
    leitor de PDF pinta a área de todo link ao passar o mouse, e numa linha larga isso pesa; a
    navegação fica nos marcadores do painel lateral e no "Voltar ao sumário" do rodapé."""
    largura = pdf.w - pdf.l_margin - pdf.r_margin
    _garantir_espaco(pdf, ALTURA_DA_LINHA_DO_SUMARIO)
    y = pdf.get_y()
    pdf.set_xy(pdf.l_margin, y)
    pdf.set_font("Helvetica", "B", TAMANHO_TEXTO)
    pdf.set_text_color(*cor_legivel(pdf.identidade.cor))
    pdf.cell(LARGURA_DO_NUMERO_DO_SUMARIO, ALTURA_DA_LINHA_DO_SUMARIO, f"{n}.")
    pdf.set_font("Helvetica", "", TAMANHO_TEXTO)
    pdf.set_text_color(*TEXTO_ESCURO)
    texto = _caber(pdf, _latin1(_sem_negrito(titulo)),
                   largura - LARGURA_DO_NUMERO_DO_SUMARIO - LARGURA_DA_PAGINA_DO_SUMARIO - 8)
    pdf.cell(pdf.get_string_width(texto) + 3, ALTURA_DA_LINHA_DO_SUMARIO, texto)
    fim_do_pontilhado = pdf.w - pdf.r_margin - LARGURA_DA_PAGINA_DO_SUMARIO
    pontos = int((fim_do_pontilhado - pdf.get_x()) / pdf.get_string_width(". "))
    pdf.set_text_color(*CINZA_DO_PONTILHADO)
    pdf.cell(fim_do_pontilhado - pdf.get_x(), ALTURA_DA_LINHA_DO_SUMARIO, ". " * pontos, align="R")
    pdf.set_text_color(*TEXTO_ESCURO)
    pdf.cell(LARGURA_DA_PAGINA_DO_SUMARIO, ALTURA_DA_LINHA_DO_SUMARIO, str(pagina), align="R")
    pdf.set_y(y + ALTURA_DA_LINHA_DO_SUMARIO)


def _paragrafo(pdf: ManualPDF, texto: str) -> None:
    pdf.set_font("Helvetica", "", TAMANHO_TEXTO)
    pdf.set_text_color(*TEXTO_ESCURO)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, LINHA_DO_TEXTO, _md(texto), new_x="LMARGIN", new_y="NEXT", align="L", markdown=True)
    pdf.ln(ESPACO_ENTRE_BLOCOS)


def _icone_do_aviso(pdf: ManualPDF, tipo: str, x: float, y: float) -> None:
    """O ícone do aviso, desenhado: um círculo na cor do tipo com um "i", um visto ou um "!" dentro."""
    cor, centro_x, centro_y = AVISOS[tipo]["cor"], x + DIAMETRO_DO_ICONE / 2, y + DIAMETRO_DO_ICONE / 2
    pdf.set_fill_color(*cor)
    pdf.ellipse(x, y, DIAMETRO_DO_ICONE, DIAMETRO_DO_ICONE, style="F")
    if tipo == "sucesso":
        pdf.set_draw_color(255, 255, 255)
        pdf.set_line_width(0.6)
        with pdf.local_context(stroke_cap_style="round", stroke_join_style="round"):
            pdf.polyline([(centro_x - 1.6, centro_y + 0.1), (centro_x - 0.4, centro_y + 1.3),
                          (centro_x + 1.7, centro_y - 1.3)])
    else:
        _texto_centrado(pdf, "i" if tipo == "info" else "!", centro_x, centro_y, 10, (255, 255, 255))


def _barra_lateral(pdf: ManualPDF, x: float, y: float, largura: float, altura: float, cor: tuple) -> None:
    """A barra colorida na borda esquerda de uma caixa: o contorno arredondado da própria caixa, recortado
    na faixa da esquerda, então ela acompanha os cantos."""
    pdf.set_fill_color(*cor)
    with pdf.rect_clip(x, y, LARGURA_DA_BARRA, altura):
        pdf.rect(x, y, largura, altura, style="F", round_corners=True, corner_radius=3)


def _aviso(pdf: ManualPDF, tipo: str, titulo: str, texto: str) -> None:
    """Um aviso: caixa na cor do tipo com o ícone, o título em maiúsculas e o texto."""
    cores, largura = AVISOS[tipo], pdf.w - pdf.l_margin - pdf.r_margin
    miolo = largura - RECUO_DO_AVISO - 5
    pdf.set_font("Helvetica", "", TAMANHO_CORPO)
    altura = max(RESPIRO_DO_CARTAO * 2 + DIAMETRO_DO_ICONE,
                 2 * RESPIRO_DO_CARTAO + (LINHA_DO_PASSO + 1 if titulo else 0)
                 + (_linhas(pdf, miolo, LINHA_DO_CORPO, texto) * LINHA_DO_CORPO if texto else 0))
    _garantir_espaco(pdf, altura + ESPACO_ENTRE_BLOCOS)
    y = pdf.get_y()
    pdf.set_fill_color(*cores["fundo"])
    pdf.set_draw_color(*tom_claro(cores["cor"], 0.3))
    pdf.set_line_width(0.25)
    pdf.rect(pdf.l_margin, y, largura, altura, style="DF", round_corners=True, corner_radius=3)
    _barra_lateral(pdf, pdf.l_margin, y, largura, altura, cores["cor"])
    _icone_do_aviso(pdf, tipo, pdf.l_margin + 4.5, y + RESPIRO_DO_CARTAO + 0.5)
    recuo = pdf.l_margin + RECUO_DO_AVISO
    pdf.set_xy(recuo, y + RESPIRO_DO_CARTAO)
    if titulo:
        pdf.set_font("Helvetica", "B", TAMANHO_CORPO)
        pdf.set_text_color(*TEXTO_ESCURO)
        with pdf.local_context():
            pdf.set_char_spacing(0.4)
            pdf.cell(miolo, LINHA_DO_PASSO, _latin1(_sem_negrito(titulo)).upper(), new_x="LEFT", new_y="NEXT")
        pdf.set_xy(recuo, pdf.get_y() + 1)
    if texto:
        pdf.set_font("Helvetica", "", TAMANHO_CORPO)
        pdf.set_text_color(*TEXTO_ESCURO)
        pdf.multi_cell(miolo, LINHA_DO_CORPO, _md(texto), new_x="LEFT", new_y="NEXT", align="L", markdown=True)
    pdf.set_y(y + altura + ESPACO_ENTRE_BLOCOS)


def _cartoes(pdf: ManualPDF, itens: list[tuple[str, str]]) -> None:
    """Cartões lado a lado, em duas colunas; numa fileira todos têm a altura do maior."""
    largura = (pdf.w - pdf.l_margin - pdf.r_margin - ESPACO_ENTRE_CARTOES * (COLUNAS_DOS_CARTOES - 1)) / COLUNAS_DOS_CARTOES
    miolo = largura - 8
    for inicio in range(0, len(itens), COLUNAS_DOS_CARTOES):
        fileira = itens[inicio:inicio + COLUNAS_DOS_CARTOES]
        alturas = []
        for titulo, texto in fileira:
            pdf.set_font("Helvetica", "B", TAMANHO_PASSO)
            titulo_em_linhas = _linhas(pdf, miolo, LINHA_DO_PASSO, _sem_negrito(titulo))
            pdf.set_font("Helvetica", "", TAMANHO_CORPO)
            alturas.append(2 * RESPIRO_DO_CARTAO + titulo_em_linhas * LINHA_DO_PASSO + 1
                           + _linhas(pdf, miolo, LINHA_DO_CORPO, texto) * LINHA_DO_CORPO)
        altura = max(alturas)
        _garantir_espaco(pdf, altura + ESPACO_ENTRE_BLOCOS)
        y = pdf.get_y()
        for coluna, (titulo, texto) in enumerate(fileira):
            x = pdf.l_margin + coluna * (largura + ESPACO_ENTRE_CARTOES)
            pdf.set_fill_color(*tom_claro(pdf.identidade.cor, 0.06))
            pdf.set_draw_color(*tom_claro(pdf.identidade.cor, 0.22))
            pdf.set_line_width(0.25)
            pdf.rect(x, y, largura, altura, style="DF", round_corners=True, corner_radius=3)
            _barra_lateral(pdf, x, y, largura, altura, cor_legivel(pdf.identidade.cor))
            pdf.set_xy(x + 4, y + RESPIRO_DO_CARTAO)
            pdf.set_font("Helvetica", "B", TAMANHO_PASSO)
            pdf.set_text_color(*TEXTO_ESCURO)
            pdf.multi_cell(miolo, LINHA_DO_PASSO, _md(_sem_negrito(titulo)), new_x="LEFT", new_y="NEXT", align="L")
            pdf.set_xy(x + 4, pdf.get_y() + 1)
            pdf.set_font("Helvetica", "", TAMANHO_CORPO)
            pdf.set_text_color(*CINZA_DO_TEXTO)
            pdf.multi_cell(miolo, LINHA_DO_CORPO, _md(texto), new_x="LEFT", new_y="NEXT", align="L", markdown=True)
        pdf.set_y(y + altura + ESPACO_ENTRE_BLOCOS)


def _passos(pdf: ManualPDF, textos: dict, passos: list) -> None:
    """O "Passo a passo" da seção: um cartão por passo e o fecho."""
    _subtitulo(pdf, textos["passos"], cor_legivel(pdf.identidade.cor))
    for indice, passo in enumerate(passos, start=1):
        _passo(pdf, indice, passo.titulo, passo.fala, _medir_passo(pdf, passo.titulo, passo.fala),
               reservar=ALTURA_DO_FIM if indice == len(passos) else 0)
    _fim(pdf, textos)
    pdf.ln(ESPACO_ENTRE_BLOCOS * 2)


def _secao(pdf: ManualPDF, n: int, secao, textos: dict, nova_pagina: bool) -> int:
    """Uma seção: "SEÇÃO N", o título grande e os blocos do Markdown, na ordem em que foram escritos.
    Devolve a página onde ela começa."""
    pdf.secao = f"{textos['secao']} {n}"
    if nova_pagina:
        pdf.add_page()
    else:
        _garantir_espaco(pdf, 40)
    pdf.start_section(f"{n}. {_sem_negrito(secao.titulo)}")
    primeira_pagina = pdf.page_no()
    pdf.set_font("Helvetica", "B", TAMANHO_PEQUENO)
    pdf.set_text_color(*cor_legivel(pdf.identidade.cor))
    with pdf.local_context():
        pdf.set_char_spacing(1)
        pdf.cell(0, 6, f"{textos['secao']} {n}".upper(), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", TAMANHO_TITULO_DA_SECAO)
    pdf.set_text_color(*TEXTO_ESCURO)
    pdf.multi_cell(0, 10.5, _md(_sem_negrito(secao.titulo)), new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(ESPACO_ENTRE_BLOCOS + 1)
    for bloco in secao.blocos:
        tipo = bloco[0]
        if tipo == "paragrafo":
            _paragrafo(pdf, bloco[1])
        elif tipo == "subtitulo":
            _subtitulo(pdf, bloco[1], cor_legivel(pdf.identidade.cor))
        elif tipo == "aviso":
            _aviso(pdf, bloco[1], bloco[2], bloco[3])
        elif tipo == "cartoes":
            _cartoes(pdf, bloco[1])
        else:
            _passos(pdf, textos, bloco[1])
    return primeira_pagina


def _montar(dados: dict, paginas: dict[int, int]) -> tuple[ManualPDF, dict[int, int]]:
    """Monta o documento inteiro. `paginas` é a página de cada seção numa montagem anterior (o
    sumário as imprime); devolve a página de cada seção nesta."""
    identidade, textos, secoes = dados["identidade"], dados["textos"], dados["secoes"]
    pdf = ManualPDF(identidade, textos, dados["versao"])
    pdf.add_page()
    _faixa_do_titulo(pdf, dados)
    _data(pdf, dados)
    com_sumario = len(secoes) >= SUMARIO_MINIMO
    pdf.set_link(pdf.volta, page=1, y=pdf.get_y() if com_sumario else 0)       # o "Voltar" do rodapé
    if com_sumario:
        pdf.rotulo_de_volta = textos["voltar_sumario"]
        _subtitulo(pdf, textos["sumario"], cor_legivel(identidade.cor))
        for n, secao in enumerate(secoes, start=1):
            _linha_do_sumario(pdf, n, secao.titulo, paginas.get(n, 0))
    achadas = {}
    for n, secao in enumerate(secoes, start=1):
        achadas[n] = _secao(pdf, n, secao, textos, nova_pagina=com_sumario)
    return pdf, achadas


def montar_pdf(dados: dict, destino: Path) -> Path:
    """Monta duas vezes: na primeira descobre em que página cai cada seção, na segunda o sumário já
    imprime esses números (o sumário tem o mesmo tamanho nas duas, então nada se move)."""
    pdf, paginas = _montar(dados, {})
    if len(dados["secoes"]) >= SUMARIO_MINIMO:
        pdf, _ = _montar(dados, paginas)
    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destino))
    return destino


@dataclass
class Resultado:
    pdf: Path
    secao: Path | None = None       # a seção que `sentry manual <modulo>` criou ou atualizou
    criada: bool = False


def gerar_manual(root: Path, modulo: str | None = None, idioma: str = IDIOMA_PADRAO, *,
                 ler_identidade_fn=None) -> Resultado:
    """Sincroniza as seções com os roteiros, lê a identidade do app e grava `.sentry/manual/manual-<idioma>.pdf`.

    Com `modulo`, cria a seção dele ou atualiza os passos dela; sem, atualiza os passos de todas as
    seções que já existem. Tudo que dá para recusar sem abrir navegador é recusado antes; e o app é
    testado antes do Playwright, para o erro dizer "suba o app" em vez de um net::ERR_CONNECTION_REFUSED.
    """
    validar_idioma(idioma)
    arquivo, criada = manual_md.sincronizar(root, modulo) if modulo is not None else (None, False)
    if modulo is None:
        for secao in manual_md.listar_secoes(root):
            if training.caminho_do_roteiro(root, secao.modulo).is_file():      # sem roteiro a seção é só texto
                manual_md.sincronizar(root, secao.modulo)
    secoes = manual_md.listar_secoes(root)
    if not secoes:
        raise ValueError("o manual ainda não tem seções: crie a primeira com `sentry manual <modulo>`")
    com_roteiro = [secao for secao in secoes if training.caminho_do_roteiro(root, secao.modulo).is_file()]
    if not com_roteiro:
        raise ValueError("nenhuma seção tem roteiro em .sentry/training/: o nome, a cor e a logo do app vêm "
                         "da página de `base` do roteiro de uma seção")
    roteiro = training.carregar_roteiro(root, com_roteiro[0].modulo)
    training.garantir_playwright()
    training.app_responde(roteiro["base"])
    identidade = (ler_identidade_fn or ler_identidade)(roteiro)
    versao = str(load_config(root).get("manual", {}).get("versao", VERSAO_PADRAO))
    pdf = montar_pdf(conteudo(secoes, idioma, identidade, versao=versao), root / PASTA_DE_MANUAIS / f"manual-{idioma}.pdf")
    return Resultado(pdf=pdf, secao=arquivo, criada=criada)
