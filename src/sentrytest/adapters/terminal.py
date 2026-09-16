"""Cor ANSI crua para o terminal, sem dependência de runtime nova -- o mesmo
princípio de `application/watch.py`, que não puxa uma biblioteca de watch só para
o comando mais leve do produto. Aqui a lógica é a mesma: colorama e rich resolvem
isto, mas exigi-los para o comando mais visível (o veredito na tela) trocaria
fricção de instalação por embelezamento.

Regra única: cor é sempre para o terminal, nunca para o que é persistido ou
parseado por máquina. `.sentry/reports/latest.md` e o payload de `--json` nunca
passam por aqui -- só a cópia impressa em stdout.
"""
from __future__ import annotations

import itertools
import os
import re
import shutil
import sys
import threading
import time
from typing import TextIO

RESET = "\x1b[0m"
_CODES = {"red": "31", "yellow": "33", "green": "32", "gray": "90", "blue": "34", "magenta": "35",
         "bright_green": "92", "dim_green": "2;32"}

_ANSI = re.compile(r"\x1b\[[0-9;]*m")

VERDICT_COLOR = {
    "aprovado": "green",
    "aprovado com ressalvas": "yellow",
    "reprovado": "red",
    "inconclusivo": "gray",
}

# Simbolo e' texto, nao codigo de escape: aparece igual com ou sem suporte a
# cor, e sobrevive a redirecionamento para arquivo/CI sem sujar nada -- por
# isso nao tem gate de `enabled` como `paint()` tem.
VERDICT_SYMBOL = {"aprovado": "✓", "aprovado com ressalvas": "⚠", "reprovado": "✗", "inconclusivo": "○"}

# `alta` entra junto de `crítica`: o próprio catálogo de regras já trata as duas
# como "revise antes de seguir" (warning) vs. "não deveria seguir" (crítica) --
# aqui a cor marca as duas como o que precisa de atenção imediata, e só `média`
# ganha um tom mais brando.
SEVERITY_COLOR = {"crítica": "red", "alta": "red", "média": "yellow", "baixa": "gray"}
SEVERITY_SYMBOL = {"crítica": "✗", "alta": "✗", "média": "⚠", "baixa": "○"}

# So' para os comandos cuja saida nao ja' carrega um simbolo de veredito
# (masthead/resumo compacto): `run`/`review`/`status` ficariam com dois
# simbolos competindo pela mesma linha.
COMMAND_ICON = {
    "clear": "✂", "history": "↺",
}


def supports_color(stream: TextIO | None = None) -> bool:
    """NO_COLOR sempre desliga; FORCE_COLOR sempre liga, mesmo sem terminal
    interativo -- é o que permite `sentry review | less -R` continuar colorido.
    Sem nenhuma das duas, decide o próprio stream: pipe e arquivo não são tty."""
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    stream = stream if stream is not None else sys.stdout
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def paint(text: str, color: str, *, enabled: bool | None = None) -> str:
    """Envolve `text` no código ANSI de `color`. Sem cor habilitada, devolve o
    texto intocado -- nunca um código vazio, que ainda seria bytes a mais em
    quem redireciona a saída para arquivo."""
    if enabled is None:
        enabled = supports_color()
    if not enabled or not text:
        return text
    return f"\x1b[{_CODES[color]}m{text}{RESET}"


def strip_ansi(text: str) -> str:
    """O inverso de `paint`, para provar que o que vai para disco está limpo."""
    return _ANSI.sub("", text)


_VERDICT_LINE = re.compile(r"(- Veredito: \*\*)([^*]+)(\*\*)")
_SEVERITY_TAG = re.compile(r"\[(crítica|alta|média|baixa)\]")


def colorize_report(markdown: str, *, enabled: bool | None = None) -> str:
    """Recolore uma CÓPIA do relatório para exibição no terminal -- o texto
    gravado em `.sentry/reports/latest.md` pela chamada a `write_reports` vem de
    antes desta função, nunca depois. O veredito e o rótulo de severidade de
    cada achado ganham símbolo sempre (texto, sem gate) e cor quando habilitada;
    o resto do relatório fica como o Markdown já o formata."""
    if enabled is None:
        enabled = supports_color()
    markdown = _VERDICT_LINE.sub(
        lambda m: m.group(1) + paint(VERDICT_SYMBOL.get(m.group(2), "?"), VERDICT_COLOR.get(m.group(2), "gray"), enabled=enabled)
        + " " + m.group(2).capitalize() + m.group(3),
        markdown,
    )
    markdown = _SEVERITY_TAG.sub(
        lambda m: "[" + paint(SEVERITY_SYMBOL.get(m.group(1), "·"), SEVERITY_COLOR.get(m.group(1), "gray"), enabled=enabled)
        + " " + m.group(1) + "]",
        markdown,
    )
    return markdown


# Braille de oito pontos: gira suave num terminal monoespacado sem precisar de
# largura variavel -- qualquer fonte que rendera UTF-8 ja tem esses oito.
_SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


def spinner_frame(tick: int) -> str:
    """Funcao pura: qual caractere mostrar no tick N. Separada do loop de
    thread para ser testavel sem depender de tempo real."""
    return _SPINNER_FRAMES[tick % len(_SPINNER_FRAMES)]


def _frame_line(tick: int, elapsed: float, message: str, *, enabled: bool | None = None) -> str:
    return f"\r{paint(spinner_frame(tick), 'green', enabled=enabled)} {message}… {elapsed:.0f}s"


class Spinner:
    """Feedback de que o Sentry ainda esta trabalhando, nunca no stdout que
    `--json` promete ficar limpo para quem consome por maquina. Com stderr
    interativo, anima; sem tty (CI, pipe, arquivo), escreve uma linha estatica
    e' so -- animar ali so acumularia `\\r` ilegivel num log.

    Nao escreve nada em disco: e' decoracao de espera, nao evidencia. Um erro
    dentro do bloco `with` ainda limpa a linha antes de propagar -- caso
    contrario a mensagem de erro apareceria colada no fim do spinner.
    """

    def __init__(self, message: str = "Analisando", stream: TextIO | None = None, interval: float = 0.1):
        self.message = message
        self.stream = stream if stream is not None else sys.stderr
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._animated = False

    def _is_tty(self) -> bool:
        try:
            return bool(self.stream.isatty())
        except (AttributeError, ValueError):
            return False

    def _run(self) -> None:
        started = time.monotonic()
        for tick in itertools.count():
            if self._stop.is_set():
                return
            self.stream.write(_frame_line(tick, time.monotonic() - started, self.message,
                                          enabled=supports_color(self.stream)))
            self.stream.flush()
            self._stop.wait(self.interval)

    def __enter__(self) -> "Spinner":
        self._animated = self._is_tty()
        if not self._animated:
            self.stream.write(f"{self.message}…\n")
            self.stream.flush()
            return self
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._animated:
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=1)
            # Sobrescreve a linha do ultimo frame com espacos, para o que vem
            # depois (o relatorio) nao ficar colado na cauda da animacao.
            self.stream.write("\r" + " " * (len(self.message) + 12) + "\r")
            self.stream.flush()
        return False


def render_box(lines: list[str], *, title: str | None = None, meta: str | None = None) -> str:
    """Caixa Unicode simples ao redor de `lines`. A largura e' medida sem
    codigo ANSI (`strip_ansi`), senao a caixa ficaria larga demais quando as
    linhas vierem coloridas -- o codigo de escape nao ocupa coluna na tela.

    Com `title` (e opcionalmente `meta`), a borda de cima carrega os dois em
    vez de ficar em branco -- `┌─ TITULO ──── meta ─┐` -- e a largura da
    caixa cresce para caber essa linha inteira quando ela for maior que o
    conteudo."""
    content_width = max((len(strip_ansi(line)) for line in lines), default=0)
    header_prefix = f"─ {title} " if title else ""
    header_suffix = f" {meta} ─" if meta else ""
    header_core = len(header_prefix) + len(header_suffix)
    width = max(content_width, header_core)
    if header_prefix or header_suffix:
        fill = max(width - header_core + 2, 1)
        top = "┌" + header_prefix + "─" * fill + header_suffix + "┐"
    else:
        top = "┌" + "─" * (width + 2) + "┐"
    bottom = "└" + "─" * (width + 2) + "┘"
    body = [f"│ {line}{' ' * (width - len(strip_ansi(line)))} │" for line in lines]
    return "\n".join([top, *body, bottom])


# Fonte figlet "ANSI Shadow" pronta -- não é gerada, é o texto literal (a
# mesma arte que aparece em banners de outras CLIs). Largura fixa, sem
# depender de largura de terminal nem de cor truecolor: funciona em
# qualquer terminal que renderize os caracteres de desenho de caixa (Unicode
# básico, suportado por qualquer fonte monoespaçada moderna).
_WORDMARK_LINES = (
    "███████╗███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗",
    "██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝",
    "███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝ ╚████╔╝ ",
    "╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝  ",
    "███████║███████╗██║ ╚████║   ██║   ██║  ██║   ██║   ",
    "╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   ",
)
# Três faixas, duas linhas cada, de cima pra baixo: verde vivo, verde
# normal, verde apagado -- sem sombra nem gradiente por pixel, a fonte já
# carrega o peso visual sozinha.
_WORDMARK_BANDS = ("bright_green", "green", "dim_green")


def render_wordmark(version: str | None = None, *, enabled: bool | None = None) -> str:
    """SENTRY na fonte figlet "ANSI Shadow", em três faixas de verde (vivo,
    normal, apagado) de cima pra baixo. Com `version`, a versão do pacote
    aparece no pezinho direito -- colada depois da última letra, na mesma
    linha, sem ganhar cabeçalho ou caixa própria."""
    if enabled is None:
        enabled = supports_color()
    band_height = len(_WORDMARK_LINES) // len(_WORDMARK_BANDS)
    colors = [_WORDMARK_BANDS[min(i // band_height, len(_WORDMARK_BANDS) - 1)] for i in range(len(_WORDMARK_LINES))]
    rendered = [paint(line, color, enabled=enabled) for line, color in zip(_WORDMARK_LINES, colors)]
    if version:
        last_body = paint(_WORDMARK_LINES[-1].rstrip(), colors[-1], enabled=enabled)
        rendered[-1] = last_body + "  " + paint(f"v{version}", "green", enabled=enabled)
    return "\n".join(rendered)


# Largura de referencia para o tracinho de preenchimento de render_section.
_LINE_WIDTH = 78


def render_section(title: str, prefix_symbol: str = "", *, enabled: bool | None = None) -> str:
    """Cabeçalho de bloco, tipo 'INICIALIZANDO' -- maiúsculo e verde, com um
    tracinho (`─`) na frente e outro depois que preenche o resto da linha
    larga do terminal, sem passar de `_LINE_WIDTH` nem estourar um terminal
    mais estreito. Os dois tracinhos usam a mesma cor apagada e o mesmo
    espaçamento de um espaço -- só o texto do título é que fica mais vivo."""
    label = title.upper()
    used = (len(prefix_symbol) + 1 if prefix_symbol else 0) + len(label) + 1
    width = min(_LINE_WIDTH, shutil.get_terminal_size(fallback=(_LINE_WIDTH, 24)).columns)
    dash = "─" * max(width - used, 3)
    prefix = f"{paint(prefix_symbol, 'dim_green', enabled=enabled)} " if prefix_symbol else ""
    return f"{prefix}{paint(label, 'bright_green', enabled=enabled)} {paint(dash, 'dim_green', enabled=enabled)}"


def render_checklist_item(text: str, *, detail: str | None = None, detail_color: str = "blue",
                          enabled: bool | None = None) -> str:
    """Uma linha do checklist do `init`: o `✓` verde, o texto e, opcionalmente,
    um detalhe colorido depois (ex.: versão do Python)."""
    line = f"{paint(VERDICT_SYMBOL['aprovado'], 'green', enabled=enabled)} {text}"
    if detail:
        line += " " + paint(detail, detail_color, enabled=enabled)
    return line


def render_dependency_row(name: str, version: str | None, status_label: str, ok: bool, *,
                          enabled: bool | None = None) -> str:
    """Uma linha de dependência: símbolo, nome, versão e o rótulo de status
    (`presente`/`ausente`), sem colchetes -- inspirado nos badges de
    ambiente que editores mostram na barra de status (ex.:
    `✓ .venv 3.12.4`). A linha inteira carrega a cor do status (verde
    presente, vermelho ausente) -- o mesmo par que já colore `sentry check`
    (`✗ erro:`/`✓ sucesso`)."""
    color = "green" if ok else "red"
    symbol = VERDICT_SYMBOL["aprovado"] if ok else VERDICT_SYMBOL["reprovado"]
    label = f"{name} {version}" if version else name
    text = f"{symbol} {label}"
    if status_label:
        text += f" {status_label}"
    return paint(text, color, enabled=enabled)


def render_masthead(payload: dict, *, enabled: bool | None = None) -> str:
    """Caixa curta no topo do relatório impresso no terminal: projeto, commit e
    veredito com símbolo e cor. Recebe o mesmo formato de payload que
    `reporting.markdown_report` -- nunca escrito em disco, só impresso."""
    if enabled is None:
        enabled = supports_color()
    data = payload.get("data") or {}
    status = (data.get("verdict") or {}).get("status", "inconclusivo")
    symbol = VERDICT_SYMBOL.get(status, "?")
    veredito = f"Veredito: {paint(symbol, VERDICT_COLOR.get(status, 'gray'), enabled=enabled)} {status.capitalize()}"
    commit = data.get("commit")
    lines = [
        f"Projeto: {data.get('project', '?')}",
        f"Commit: {commit[:12] if commit else 'indisponível'}",
        veredito,
    ]
    return render_box(lines)


def render_dashboard(payload: dict, *, enabled: bool | None = None) -> str:
    """Rodapé compacto depois do relatório impresso: testes, cobertura global e
    achados por severidade. Mesma regra do masthead -- só para o terminal."""
    data = payload.get("data") or {}
    config = data.get("configuration") or {}
    execution = config.get("test_execution") or {}
    coverage = config.get("coverage") or {}
    global_percent = coverage.get("global_percent")
    cobertura = f"{global_percent:.2f}%".replace(".", ",") if global_percent is not None else "indisponível"
    by_severity: dict[str, int] = {}
    for finding in data.get("findings") or []:
        severity = finding.get("severity", "?")
        by_severity[severity] = by_severity.get(severity, 0) + 1
    achados = ", ".join(
        f"{paint(SEVERITY_SYMBOL.get(severity, '·'), SEVERITY_COLOR.get(severity, 'gray'), enabled=enabled)} {severity}={count}"
        for severity, count in by_severity.items()
    ) or "nenhum"
    lines = [
        f"Testes: {execution.get('passed', 0)} passou, {execution.get('failed', 0)} falhou" if execution
        else "Testes: não executados nesta análise",
        f"Cobertura global: {cobertura}",
        f"Achados: {achados}",
    ]
    return render_box(lines)
