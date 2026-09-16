from __future__ import annotations
import argparse
import json
import platform
import re
import sys
from pathlib import Path
from . import __version__
from .init_project import check_dependencies, initialize_project, install_dependencies
from .adapters.case_specs import LAYERS, PRIORITIES, TEMPLATE, TEST_TYPES, CaseSpecAdapter, validate_document
from .adapters.toml_config import load_config
from .domain.catalog import FIELD_CLASSES, merge_catalog, missing_classes, unknown_field_types
from .application.analyze import CASES_PATH, analyze, is_all_spec, merge_documents, select_spec, spec_documents
from .application.cases import scaffold
from .application.context import build_context
from .application.traceability import DEFAULT_TEST_PATHS
from .application.watch import COMPLETO, watch
from .adapters.local_tools import LocalGitAdapter
from .adapters.terminal import (
    COMMAND_ICON, SEVERITY_SYMBOL, VERDICT_COLOR, VERDICT_SYMBOL,
    Spinner, colorize_report, paint, render_checklist_item, render_dashboard,
    render_dependency_row, render_masthead, render_section,
    render_wordmark,
)
from .domain.models import to_json
from .application.reporting import clear_history, load_runs, staleness, write_reports, compare

_COMMAND_NAMES = ("init", "new", "check", "run", "review", "watch", "status", "context", "report", "history", "clear")
_CHOICES_LINE = re.compile(r'^\{[\w,]+\}$')
# Generico -- qualquer `-x`/`--algo`, nao so' `-h`/`--help`/`--version` como antes:
# cada subcomando tem seu proprio conjunto de flags (`--prompt`, `--spec`, `--base`...)
# e todas devem colorir igual, em qualquer usage/ajuda/erro onde aparecerem.
_FLAG_TOKEN = re.compile(r'(?<![\w-])-{1,2}[A-Za-z][\w-]*')

# Mensagens de erro que o argparse realmente produz neste projeto -- nao e' uma
# traducao completa da biblioteca via gettext/locale, so' regex sobre os padroes
# que aparecem de fato. Uma mensagem sem tradutor reconhecido cai no texto
# original em ingles, nunca quebra.
_ARGPARSE_TRANSLATIONS = (
    (re.compile(r'^the following arguments are required: (.+)$'), r'argumento(s) obrigatório(s) ausente(s): \1'),
    (re.compile(r'^unrecognized arguments: (.+)$'), r'argumento(s) não reconhecido(s): \1'),
    (re.compile(r'^one of the arguments (.+) is required$'), r'um dos argumentos \1 é obrigatório'),
    (re.compile(r'^argument (.+): expected one argument$'), r'argumento \1: esperava um valor'),
    (re.compile(r'^argument (.+): expected at least one argument$'), r'argumento \1: esperava ao menos um valor'),
    # Sem o "(choose from ...)" -- a unica acao com `choices` neste projeto e'
    # o subparsers da raiz, cuja lista de opcoes ja' aparece no bloco USO
    # logo acima, no mesmo comando; repetir aqui so' duplicava informacao.
    (re.compile(r"^argument (.+): invalid choice: (.+) \(choose from .+\)$"), r'argumento \1: escolha inválida: \2'),
    (re.compile(r'^argument (.+): invalid (\w+) value: (.+)$'), r'argumento \1: valor inválido (\2): \3'),
)

def _translate_argparse_message(message: str) -> str:
    for pattern, replacement in _ARGPARSE_TRANSLATIONS:
        if pattern.match(message):
            return pattern.sub(replacement, message)
    return message


def _colorize_commands_and_flags(text: str) -> str:
    """Colore em verde cada nome de comando e cada flag (`-x`/`--algo`), em
    qualquer lugar do texto onde aparecerem -- a mesma passada usada tanto no
    bloco de uso quanto no resto da ajuda."""
    for name in _COMMAND_NAMES:
        text = re.sub(rf'(?<![\w-]){name}(?![\w-])', paint(name, "green"), text)
    return _FLAG_TOKEN.sub(lambda m: paint(m.group(), "green"), text)


def _usage_tokens(parser: argparse.ArgumentParser) -> list[tuple[argparse.Action, str]]:
    """Um (action, token) por argumento (`name`, `[-h, --help]`,
    `[--prompt PROMPT]`...), em ordem logica -- nao a ordem que o argparse
    usa sozinho (todos os opcionais primeiro, inclusive `-h`, so' depois os
    posicionais), que escondia o argumento obrigatorio atras de flags menos
    importantes. Aqui: posicionais primeiro (o que a chamada exige de
    verdade), depois `-h` (o menos relevante pra quem ja sabe usar o
    comando, mas ainda o primeiro opcional por convenção), depois o resto
    dos opcionais na ordem declarada. A `action` vai junto pro chamador
    poder anexar a descrição de cada flag quando `with_descriptions=True`
    em `_render_usage_block`. Reusa o formatador do proprio argparse por
    action, em vez de reimplementar a logica de nargs/metavar na mao."""
    formatter = argparse.HelpFormatter(prog=parser.prog)
    optionals = parser._optionals._group_actions
    ajuda = [action for action in optionals if action.dest == "help"]
    outros_opcionais = [action for action in optionals if action.dest != "help"]
    ordenados = parser._positionals._group_actions + ajuda + outros_opcionais
    tokens = []
    for action in ordenados:
        if action.help == argparse.SUPPRESS:
            continue
        if isinstance(action, argparse._SubParsersAction):
            # O formatador padrao do argparse produz `{init,new,...} ...` --
            # colchete curly sem espaco nenhum entre os nomes, mais um "..."
            # solto pro resto dos argumentos que o subcomando escolhido
            # aceita (redundante aqui: cada subcomando ja' tem seu proprio
            # bloco USO detalhado). Troca por colchete reto com espaco depois
            # da virgula, sem o "..." -- so' a lista legivel dos comandos.
            text = "[" + ", ".join(action.choices) + "]"
        elif len(action.option_strings) > 1:
            # O formatador padrao do argparse so' usa a primeira forma no
            # usage (`[-h]`, nunca `[-h, --help]`) -- todas as outras flags
            # deste projeto tem uma forma so', entao isto so' importa pro
            # `-h`/`--help`. Junta as duas, igual a secao EXTRAS ja mostra.
            text = "[" + ", ".join(action.option_strings) + "]"
        else:
            text = formatter._format_actions_usage([action], [])
        if text:
            tokens.append((action, text))
    return tokens


def _render_usage_block(parser: argparse.ArgumentParser, *, with_descriptions: bool = False) -> str:
    """O bloco de uso vira um título com tracinho ("USO"), igual
    `COMANDOS`/`EXTRAS`/`ARGUMENTOS`. Um token por linha (`[-h, --help]`,
    `[--prompt PROMPT]`, `[--json]`, `name`...), o primeiro colado no nome do
    comando e os demais indentados por baixo -- a linha unica que o argparse
    monta sozinho (`sentry new [-h] [--prompt PROMPT] [--json] name`) fica
    ilegivel assim que o comando tem mais de duas ou tres flags. `sentry` e
    o nome do comando saem em verde, cada flag tambem.

    `with_descriptions=True` (so' `sentry init`, por pedido explicito, nao
    o padrao de todo comando) cola a descrição de cada flag opcional na
    mesma linha, alinhada numa coluna, no lugar de repeti-la de novo em
    `EXTRAS` logo abaixo -- quem chama, nesse caso, tambem pula a seção
    `EXTRAS` via `_decorate_sections(..., include_options=False)`.
    Posicional (`name`, `slug`...) nunca ganha descrição aqui, mesmo com
    `with_descriptions=True` -- essa continua só em `ARGUMENTOS`."""
    prog_plain = parser.prog
    prog = _colorize_commands_and_flags(re.sub(r'(?<![\w-])sentry(?![\w-])', paint('sentry', 'green'), prog_plain))
    tokens = _usage_tokens(parser)
    # Margem esquerda de 2 espaços, igual COMANDOS/ARGUMENTOS/EXTRAS -- toda
    # secao do bloco de ajuda usa o mesmo recuo, o USO nao seria excecao.
    margin = "  "
    indent = margin + " " * (len(prog_plain) + 1)
    if not tokens:
        return f"{render_section('Uso', '─')}\n{margin}{prog}"
    col_width = 0
    if with_descriptions:
        descritos = [text for action, text in tokens
                     if action.option_strings and action.help and action.help != argparse.SUPPRESS]
        col_width = (max(len(text) for text in descritos) + 2) if descritos else 0
    lines = []
    for index, (action, text) in enumerate(tokens):
        prefix = f"{margin}{prog} " if index == 0 else indent
        colored = _colorize_commands_and_flags(text)
        tem_descricao = with_descriptions and action.option_strings and action.help and action.help != argparse.SUPPRESS
        if tem_descricao:
            lines.append(f"{prefix}{colored}{' ' * (col_width - len(text))}{action.help}")
        else:
            lines.append(f"{prefix}{colored}")
    return f"{render_section('Uso', '─')}\n" + "\n".join(lines)


def _decorate_sections(text: str, *, positional_title: str = "Comandos", include_options: bool = True) -> str:
    """Troca os cabeçalhos em inglês, sem estilo ('positional arguments:',
    'options:') pelo mesmo título com tracinho que `sentry init` usa pras
    seções; colore cada nome de comando e cada flag em verde; remove a
    listagem `{init,new,...}` repetida (o bloco de uso já mostra os
    subcomandos numa linha, e o título abaixo mostra de novo com descrição --
    repetir a mesma enumeração compacta duas vezes só polui). A seção de
    posicionais da raiz (onde cada subcomando é listado aninhado sob
    `{init,new,...}`) vem indentada com 4 espaços -- 2 a mais que qualquer
    outra linha (EXTRAS usa 2, e um posicional comum de subcomando, tipo
    `name`/`slug`, também já sai do argparse com só 2). Só a raiz perde 2
    desses 4, pra ficar no mesmo recuo de 2 que o resto -- um subcomando
    comum não tem o que perder, já nasce alinhado. `positional_title` é
    "Comandos" na raiz (os posicionais ali são subcomandos de verdade) e
    "Argumentos" em qualquer subcomando (posicional genérico, ex.: `name`
    do `new`). Espera receber só o texto *depois* do bloco de uso -- quem
    monta o bloco de uso é `_render_usage_block`, chamado à parte.
    `include_options=False` (so' `sentry init`, por pedido explicito) pula a
    seção `EXTRAS` inteira -- a descrição de cada flag já saiu embutida no
    próprio `USO` nesse caso (`_render_usage_block(..., with_descriptions=
    True)`), então repeti-la aqui duplicaria a mesma informação na tela."""
    lines = []
    in_positional = False
    for line in text.splitlines():
        if line.strip() == "positional arguments:":
            lines.append(render_section(positional_title, "─"))
            in_positional = True
            continue
        if line.strip() == "options:":
            if not include_options:
                break
            lines.append(render_section("Extras", "─"))
            in_positional = False
            continue
        if _CHOICES_LINE.match(line.strip()):
            continue
        if in_positional and line.startswith("    "):
            line = line[2:]
        lines.append(_colorize_commands_and_flags(line))
    return "\n".join(lines).rstrip("\n") if not include_options else "\n".join(lines)


def _strip_usage_and_description(text: str) -> str:
    """Descarta o bloco `usage: ...` e o parágrafo de descrição do início do
    texto de ajuda gerado pelo argparse -- o wordmark já identifica o
    programa, repetir usage/descrição antes do título `COMANDOS` só empurra
    a informação útil pra baixo. Cada bloco (usage, descrição) termina numa
    linha em branco dupla, então dois `partition` bastam, não importa
    quantas linhas cada um ocupou."""
    _, _, rest = text.partition("\n\n")
    _, _, rest = rest.partition("\n\n")
    return rest


class _ArgumentParserPT(argparse.ArgumentParser):
    """`-h`/`--help` com texto em português -- o argparse só tem em inglês
    por padrão ("show this help message and exit"). Base de todo subcomando:
    `usage:`/ajuda/erro saem decorados (uso em português, flag em verde,
    títulos com tracinho) igual à raiz; o wordmark é opt-in por subcomando
    via `_wordmark` (raiz, `init` e `new` o ligam; os demais ficam sem)."""

    # Comecou restrito a raiz/`init`/`new` (ligado por instancia, pedido um
    # de cada vez), ate virar "para todo -h e --help por enquanto" -- ligado
    # por padrao na classe inteira, igual `_merge_options_into_usage` abaixo.
    # Controla tanto a ajuda (`-h`/`--help`) quanto o caminho de falha
    # (`error()`), nao so' o de sucesso.
    _wordmark = True

    # Comecou restrito so' ao `sentry init` ("e somente ele fique assim,
    # SOMENTE"), depois `new`, depois `check` -- pedido um de cada vez ate
    # virar "aplica em todos de uma vez". Padrao agora: na ajuda
    # (`-h`/`--help`) de qualquer comando, cada flag opcional mostra a
    # descrição colada na mesma linha do `USO`, e a seção `EXTRAS` nao
    # aparece mais (a descrição dela ja' esta ali). `ARGUMENTOS` nunca e'
    # afetado por esta marca -- continua existindo normalmente pra quem tem
    # posicional.
    _merge_options_into_usage = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("add_help", False)
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="mostra esta mensagem de ajuda e sai")

    def format_usage(self) -> str:
        return _render_usage_block(self) + "\n"

    def format_help(self) -> str:
        # `super().format_help()` ainda gera o bloco de uso do argparse (uma
        # linha so'), mas so' usamos a parte depois dele -- o bloco de uso de
        # verdade, um token por linha, vem de `_render_usage_block(self)`.
        _, _, rest = super().format_help().partition("\n\n")
        merge = self._merge_options_into_usage
        usage_block = _render_usage_block(self, with_descriptions=merge)
        secoes = _decorate_sections(rest, positional_title='Argumentos', include_options=not merge)
        body = f"{usage_block}\n\n{secoes}" if secoes else usage_block
        return f"{render_wordmark(__version__)}\n\n{body}" if self._wordmark else body

    def error(self, message: str) -> None:
        # Sem o prefixo `{prog}: ` do argparse -- o bloco USO logo acima ja'
        # mostra "sentry <comando>" em verde; repetir o mesmo texto sem cor
        # antes de "erro:" so' duplicava informacao.
        if self._wordmark:
            # stderr, nao stdout: `print()` simples ficava sujeito ao buffer
            # de stdout, que so' esvazia na saida do processo -- o wordmark
            # aparecia DEPOIS do usage/erro (que vao pra stderr, sem buffer)
            # em vez de antes. Mesma stream do resto deste metodo garante a
            # ordem visual (wordmark, usage, erro), sem depender de flush.
            print(render_wordmark(__version__), file=sys.stderr)
            print(file=sys.stderr)
        self.print_usage(sys.stderr)
        mensagem = _translate_argparse_message(message)
        self.exit(2, f"  {paint('erro:', 'red')} {mensagem}\n")


class _RootArgumentParser(_ArgumentParserPT):
    """`sentry -h`/`sentry --help` ganha o mesmo wordmark do `sentry init` --
    é a outra porta de entrada de quem nunca usou a ferramenta. Só o parser
    raiz sobrescreve `format_help` pra remover usage/descrição do argparse e
    prefixar o wordmark; `sentry <comando> -h` continua sem wordmark (mas
    com o resto da decoração, herdada de `_ArgumentParserPT`), igual toda
    execução de comando além do `init`/`new`. `_wordmark` fica ligado aqui
    tambem -- um erro na raiz (`sentry comando-que-nao-existe`, `sentry
    --bogus`) ganha o wordmark igual `sentry -h` ja tinha, so' o caminho de
    `error()` que faltava (`format_help` ja' mostrava por reescrever o
    metodo inteiro, sem depender da marca). `_merge_options_into_usage`
    (herdado, ligado por padrao) tambem se aplica aqui -- o bloco `USO` (que
    antes so' aparecia no erro da raiz, nunca na ajuda) passa a aparecer
    tambem em `sentry -h`, com `-h`/`--version` descritos ali dentro, sem
    seção `EXTRAS`; `COMANDOS` continua do jeito que sempre foi."""

    def format_help(self) -> str:
        # `argparse.ArgumentParser.format_help` direto, nao `super()`: o
        # `_ArgumentParserPT.format_help` ja monta o bloco de uso decorado,
        # mas com "Argumentos" como titulo de posicional -- a raiz usa
        # "Comandos" pro seu proprio posicional (o subparsers), entao monta
        # tudo aqui em vez de reaproveitar aquele metodo inteiro.
        rest = _strip_usage_and_description(argparse.ArgumentParser.format_help(self))
        secoes = _decorate_sections(rest, positional_title='Comandos', include_options=not self._merge_options_into_usage)
        usage_block = _render_usage_block(self, with_descriptions=self._merge_options_into_usage)
        corpo = f"{usage_block}\n\n{secoes}" if secoes else usage_block
        return f"{render_wordmark(__version__)}\n\n{corpo}"


def build_parser():
    parser = _RootArgumentParser(
        prog="sentry",
        description="Deriva a matriz de casos de teste de um pedido e verifica se a implementação corresponde.",
    )
    parser.add_argument("--version", action="version", version=paint(__version__, "green"), help="mostra a versão do programa e sai")
    # `parser_class` explícito: sem isso, `add_subparsers` propaga a classe do
    # pai (_RootArgumentParser) pra cada subcomando, e `sentry init -h`
    # ganharia o wordmark também -- só o `-h` raiz deve ter. `_ArgumentParserPT`
    # (sem o wordmark, só o `-h` traduzido) é a classe base dos subcomandos.
    sub = parser.add_subparsers(dest="command", parser_class=_ArgumentParserPT)
    # `argparse.ArgumentParser.parse_args` sempre reporta "unrecognized
    # arguments" pelo parser RAIZ, nunca pelo subcomando que de fato rejeitou
    # o argumento sobrando -- e' o proprio `parse_args` da stdlib que funciona
    # assim (os args nao reconhecidos so' aparecem depois que o subparser ja'
    # terminou de rodar e devolveu o controle pra raiz). Guardamos o mapa
    # nome->parser aqui pra `main()` poder rotear esse erro especifico pro
    # subcomando certo, com o usage e o wordmark dele, em vez do usage gigante
    # da raiz (a lista inteira de subcomandos, ilegivel como mensagem de erro).
    parser._subcommands = sub

    init = sub.add_parser("init", help="prepara o projeto atual")
    init.add_argument("--install", action="store_true", help="instala as dependências ausentes")

    new = sub.add_parser("new", help="guarda o pedido e cria o CASES.md a preencher")
    new.add_argument("name", help="nome da funcionalidade; vira o slug da spec")
    new.add_argument("--prompt", default="", help="o pedido em texto livre; se omitido, usa o nome")
    new.add_argument("--json", action="store_true", dest="as_json", help="emite as instruções em JSON, para o agente")

    check = sub.add_parser("check", help="a matriz de casos está completa?")
    check.add_argument("slug", nargs="?")

    run = sub.add_parser("run", help="a implementação corresponde à matriz?")
    run.add_argument("--spec")
    run.add_argument("--run-tests", action="store_true", default=None)
    run.add_argument("--base", metavar="REF", help=(
        "compara com esta referência Git a partir do ponto em que a branch divergiu "
        "(ex.: --base origin/main). Sem ela, compara a árvore de trabalho com HEAD, "
        "o que numa branch já commitada produz diff vazio"))

    review = sub.add_parser("review", help="check + run + relatório num comando só")
    review.add_argument("--spec")
    review.add_argument("--base", metavar="REF", help="compara com esta referência Git (ver `run --base`)")
    review.add_argument("--no-tests", action="store_true", help="não executa a suíte; só a conferência estrutural e o diff")

    watch_cmd = sub.add_parser("watch", help="reavalia ao salvar; escala para a suíte quando o salvo é um teste")
    watch_cmd.add_argument("--spec")
    watch_cmd.add_argument("--interval", type=float, default=0.4, metavar="SEGUNDOS",
                           help="de quanto em quanto tempo olhar o disco (padrão: 0,4 s)")

    status = sub.add_parser("status", help="mapa da aplicação inteira: onde nenhum teste alcança, não só o diff")
    status.add_argument("--json", action="store_true", dest="as_json", help="emite o payload em JSON, em vez do relatório em Markdown")

    context = sub.add_parser("context", help="as lacunas da última análise, para o agente de IA")
    context.add_argument("--json", action="store_true", dest="as_json", default=True,
                         help="emite o payload em JSON (padrão; a saída existe para ser consumida por máquina)")

    sub.add_parser("report", help="exibe o último relatório")
    sub.add_parser("history", help="lista execuções anteriores")

    clear = sub.add_parser("clear", help="poda execuções e relatórios antigos")
    clear.add_argument("--keep-last", type=int, default=0, metavar="N", help="preserva as N execuções mais recentes")
    clear.add_argument("--yes", action="store_true", help="confirma a remoção; sem isto, apenas mostra o que sairia")
    return parser

def instructions_payload():
    """Template e vocabulário aceito, para o agente que vai preencher o CASES.md.
    JSON valido continua obrigatorio (quem consome isto faz `json.loads`, sem
    wordmark nem titulo nenhum que quebraria o parse) -- so' a ORDEM das chaves
    muda pra ficar mais legivel lendo de cima pra baixo: primeiro o que e'
    especifico desta chamada (onde escrever), depois o vocabulario de
    referencia (o que pode ser usado ali), do menor bloco pro maior."""
    return {
        "artifact": "cases",
        "relOutputPath": ".sentry/specs/<slug>/CASES.md",
        "template": TEMPLATE,
        "layers": list(LAYERS),
        "test_types": list(TEST_TYPES),
        "priorities": list(PRIORITIES),
        "field_classes": {name: list(classes) for name, classes in FIELD_CLASSES.items()},
    }

# Quatro estados distintos, conforme SPEC: quem consome a saida precisa separar
# "codigo mal testado" de "meu ambiente quebrou". Configuracao invalida entra em
# INFRA porque tambem impede a analise, em vez de reprovar o codigo.
EXIT_OK, EXIT_WARNING, EXIT_REJECTED, EXIT_INFRA = 0, 1, 2, 3
EXIT_BY_VERDICT = {
    "aprovado": EXIT_OK,
    "aprovado com ressalvas": EXIT_WARNING,
    "reprovado": EXIT_REJECTED,
    "inconclusivo": EXIT_INFRA,
}

def _print_app_error(message: str, *, parser: argparse.ArgumentParser | None = None) -> None:
    """Erro de aplicação (fora do argparse -- `_check` valida a matriz depois
    que o argparse já aceitou os argumentos) no mesmo padrão visual que o
    `error()` do argparse já usa: wordmark (se o comando tiver `_wordmark`),
    bloco `USO` e a linha `erro:` em vermelho com a mesma margem de 2
    espaços. Sem `parser` (chamador que não tem um subcomando associado),
    imprime só a linha de erro."""
    if parser is not None:
        if parser._wordmark:
            print(render_wordmark(__version__))
            print()
        # Compacto (sem descricao), igual `format_usage()`/`error()` do argparse
        # ja fazem -- descricao de flag so' aparece na ajuda (`-h`/`--help`),
        # nunca no caminho de erro, em nenhum comando.
        print(_render_usage_block(parser))
    message = re.sub(r"`(sentry [^`]+)`", lambda m: paint(m.group(1), "green"), message)
    print(f"  {paint('erro:', 'red')} {message}")


def _check(root: Path, slug: str | None, tolerate_missing: bool = False, *,
          parser: argparse.ArgumentParser | None = None) -> int:
    """A validação estrutural da matriz. `tolerate_missing` é para o `review`, que
    precisa seguir para a medição quando não há spec nenhuma — ali a ausência de
    intenção declarada não é erro, e sim o modo sem spec. `parser` e' o subcomando
    que chamou (`check` ou `review`), so' pra estilizar o erro igual o do argparse."""
    config = load_config(root)
    cases_path = config.get('specs', {}).get('path', CASES_PATH)
    catalog = merge_catalog(config.get('catalog', {}).get('fields'))
    try:
        if is_all_spec(slug):
            entries = spec_documents(root, cases_path)
            if not entries:
                _print_app_error(f"nenhuma matriz de casos encontrada em {cases_path}", parser=parser)
                return 2
            document = merge_documents([(name, CaseSpecAdapter(path).document()) for name, path in entries])
            label = 'all (' + ', '.join(name for name, _ in entries) + ')'
        else:
            spec = select_spec(root, slug, cases_path)
            document = CaseSpecAdapter(spec).document()
            label = str(spec.relative_to(root))
    except (ValueError, FileNotFoundError) as error:
        if tolerate_missing and slug is None and not spec_documents(root, cases_path):
            print("Nenhuma spec declarada: medindo só o que não depende dela.")
            return 0
        _print_app_error(str(error), parser=parser)
        return 2
    errors = validate_document(document)
    missing = missing_classes(document.fields, document.cases, catalog, not_applicable=document.not_applicable)
    unknown = unknown_field_types(document.fields, catalog)
    if parser is not None and parser._wordmark:
        print(render_wordmark(__version__))
        print()
        print(render_section("Check", "─"))
    resumo_simbolo = VERDICT_SYMBOL['reprovado'] if errors else VERDICT_SYMBOL['aprovado']
    resumo_cor = 'red' if errors else 'green'
    print(f"{paint(resumo_simbolo, resumo_cor)} {label}: {len(document.cases)} caso(s), {len(document.fields)} campo(s)")
    for error in errors:
        print(f"  {paint(SEVERITY_SYMBOL['crítica'], 'red')} erro: {error}")
    for item in missing:
        print(f"  {paint(SEVERITY_SYMBOL['média'], 'yellow')} classe ausente: {item['field']}/{item['class']} (tipo {item['type']})")
    for item in unknown:
        print(f"  [limitacao] tipo fora do catalogo, sem cobranca de classes: {item}")
    for item in document.not_applicable:
        print(f"  [classe nao aplicavel] {item.field}/{item.class_name} — {item.reason}")
    if not errors and not missing:
        print(f"{paint(VERDICT_SYMBOL['aprovado'], 'green')} Estrutura valida e catalogo de classes coberto.")
    return 1 if errors else 0

def _print_pretty(payload: dict, markdown: str) -> None:
    """A visão bonita do relatório para o terminal: caixa de topo, corpo
    colorido, rodapé de dashboard. Nada disto passou por `write_reports` --
    quem chama já gravou `markdown` em disco antes de pedir esta versão."""
    print(render_masthead(payload))
    print()
    print(colorize_report(markdown).rstrip("\n"))
    print()
    print(render_dashboard(payload))

def _init_checklist(created: list[str], deps: dict) -> list[dict]:
    """Agrupa a lista crua de `initialize_project` (um caminho por linha) nas
    categorias que o usuário reconhece -- ninguém pensa em ".sentry/specs"
    como item separado de ".sentry/runs", pensa em ".sentry/ inteiro".

    Toda categoria aparece sempre, mesmo em uma re-execução onde nada foi
    criado -- o próprio `✓` verde já basta, sem rótulo adicional nenhum.
    Sumir a linha inteira quando idempotente escondia informação real do
    usuário.

    Cada item carrega, além do texto, um detalhe opcional (complemento
    colorido) -- quem imprime é `render_checklist_item`, isto só decide o
    quê. O item de ambiente concentra python, arquitetura e todas as
    dependências detectadas numa única linha, sem uma tabela separada pra
    isso."""
    normalized = [name.replace("\\", "/") for name in created]
    sentry_extra = sorted(name.rsplit("/", 1)[-1] for name in normalized if name.startswith(".sentry/"))
    config = [name for name in ("sentry.toml", ".gitignore") if name in normalized]
    skill = next((name for name in normalized if name.startswith(".claude/skills/")), None)
    dep_parts = [f"sentry-test {__version__}"]
    dep_parts += [f"{name} {info['version']}" if info["installed"] else f"{name} ausente" for name, info in deps.items()]
    detail = " • ".join([f"python {platform.python_version()}", *dep_parts, platform.machine()])
    detail_color = "red" if any(not info["installed"] for info in deps.values()) else "green"
    return [
        {
            "text": "Verificando ambiente do projeto",
            "detail": detail,
            "detail_color": detail_color,
        },
        {
            "text": f"Criando .sentry/ ({', '.join(sentry_extra)})" if sentry_extra else "Diretório .sentry/",
        },
        {
            "text": "Gerando " + " e ".join(config) if config else "Config sentry.toml e .gitignore",
        },
        {
            "text": f"Instalando skill Claude — {skill}" if skill else "Skill Claude",
        },
        {
            "text": "Gravando AGENT-SENTRY.md",
        },
    ]

def _run_and_report(root: Path, slug: str | None, run_tests: bool | None,
                    base: str | None, print_report: bool = False, whole_project: bool = False,
                    as_json: bool = False, *, parser: argparse.ArgumentParser | None = None) -> int:
    """Analisa, grava os relatórios e traduz o veredito em código de saída."""
    try:
        # Um `with` só, em volta de toda a analise: cobre tanto o tempo do
        # subprocesso da suite (a fatia que domina o tempo total) quanto o
        # resto de `analyze()`, sem duplicar o wrapping em cada comando que
        # passa por aqui (`run`, `review`, `status`, e o modo completo do
        # `watch`, que chama esta mesma funcao).
        with Spinner("Analisando"):
            run = analyze(root, slug, run_tests, base, whole_project=whole_project)
    except (ValueError, FileNotFoundError) as error:
        _print_app_error(str(error), parser=parser)
        return EXIT_INFRA
    payload = json.loads(to_json(run))
    markdown = write_reports(root, payload)
    if as_json:
        # Mesmo padrao de `new`/`context`: a saida existe para ser consumida por
        # maquina, entao nada alem do JSON vai para stdout.
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        # A cor e o simbolo colorem/marcam so' a copia impressa aqui:
        # `markdown` ja foi gravado em disco, intocado, na linha de cima.
        status = run.verdict.status.value
        if print_report:
            _print_pretty(payload, markdown)
        else:
            symbol = VERDICT_SYMBOL.get(status, "?")
            print(f"Análise {run.id}: {paint(symbol, VERDICT_COLOR.get(status, 'gray'))} {status.capitalize()}")
        for error in run.infrastructure_errors:
            print(f"{paint('[infraestrutura]', 'yellow')} {error.stage}: {error.message}" + (" (pode ser repetido)" if error.retryable else ""))
    return EXIT_BY_VERDICT.get(run.verdict.status.value, EXIT_INFRA)

def _signed(value):
    if value is None: return "indisponível"
    return f"+{value}" if value > 0 else str(value)

def _signed_colored(value, *, higher_is_better: bool = True) -> str:
    """Igual a `_signed`, mas verde quando o numero favorece o projeto e
    vermelho no sentido contrario -- zero e indisponivel ficam sem cor, nem
    bons nem ruins."""
    text = _signed(value)
    if not value: return text
    favorable = (value > 0) == higher_is_better
    return paint(text, "green" if favorable else "red")

def main(argv=None):
    # A saida carrega acentos e e consumida por agentes de IA; o console do Windows
    # usa codepage local por padrao e corromperia o JSON de `instructions`. stderr
    # entra junto porque tracebacks e erros do argparse tambem carregam acento.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    parser = build_parser()
    args, extras = parser.parse_known_args(argv)
    if extras:
        # Roteia pro subparser que de fato recebeu o argumento sobrando (se
        # algum subcomando foi escolhido) -- ele e' quem sabe seu proprio
        # usage e se tem `_wordmark`; sem `args.command` (erro antes
        # de qualquer subcomando, ex.: `sentry --bogus`), fica na raiz mesmo.
        target = parser._subcommands.choices.get(args.command, parser) if getattr(args, "command", None) else parser
        target.error("unrecognized arguments: " + " ".join(extras))
    if args.command is None:
        # `sentry` sozinho, sem nenhum subcomando: mostra a ajuda em vez de
        # nao imprimir nada, igual `git`/`docker` fazem -- nao e' erro, so'
        # ausencia de intencao declarada, entao o codigo de saida continua 0.
        parser.print_help()
        return 0
    root = Path.cwd()
    if args.command == "init":
        created = initialize_project(root)
        deps = check_dependencies(root)
        print(render_wordmark(__version__))
        print()
        print(render_section("Inicializando", "─"))
        for item in _init_checklist(created, deps):
            print(render_checklist_item(item["text"], detail=item.get("detail"),
                                        detail_color=item.get("detail_color", "blue")))
        branch, clean = LocalGitAdapter(root).status_summary()
        if branch is not None:
            print(render_dependency_row("git repo", f"branch {branch}", "limpo" if clean else "sujo", bool(clean)))
        print(f"{paint(VERDICT_SYMBOL['aprovado'], 'green')} Projeto Sentry inicializado.")
        missing = [name for name, info in deps.items() if not info["installed"]]
        if missing and args.install:
            for name, ok, error in install_dependencies(missing):
                print(f"  {name}: {'instalado' if ok else 'falhou'}" + (f" — {error}" if error else ""))
            deps = check_dependencies(root)
            if any(not info["installed"] for info in deps.values()):
                return EXIT_INFRA
        elif missing:
            # A instalacao muda o ambiente do usuario: so acontece com pedido explicito.
            print(f"Rode {paint('sentry init --install', 'green')} para instalar: {', '.join(missing)}")
            return EXIT_INFRA
    elif args.command == "new":
        prompt = args.prompt or args.name
        directory, created = scaffold(root, args.name, prompt)
        if args.as_json:
            print(json.dumps({"specDir": str(directory.relative_to(root)), **instructions_payload()}, ensure_ascii=False, indent=2))
            return 0
        print(render_wordmark(__version__))
        print()
        print(render_checklist_item(f"Spec criada em {directory.relative_to(root)}"))
        # Rotulo descritivo por arquivo -- igual ao checklist do init ("Instalando
        # skill Claude — <path>"), em vez do caminho cru repetindo o que a linha
        # de cima ja mostrou (o proprio diretorio da spec).
        labels = {
            "PROMPT.md": "Guardando o pedido — PROMPT.md",
            "CASES.md": "Gerando o template de casos — CASES.md",
        }
        for name in (created or ["Nenhum arquivo novo"]):
            basename = Path(name).name
            print(render_checklist_item(labels.get(basename, name)))
        print()
        print(render_section("Template", "─"))
        print(TEMPLATE)
        print(render_section("Vocabulário", "─"))
        print(f"Camadas aceitas: {', '.join(LAYERS)}")
        print(f"Tipos aceitos: {', '.join(TEST_TYPES)}")
        print(f"Prioridades: {', '.join(PRIORITIES)}")
        print(f"Tipos de campo com classes cobradas: {', '.join(sorted(FIELD_CLASSES))}")
        print()
        print(render_section("Próximo passo", "─"))
        print(f"Depois rode {paint(f'sentry check {directory.name}', 'green')} até fechar limpo.")
    elif args.command == "check":
        return _check(root, args.slug, parser=parser._subcommands.choices["check"])
    elif args.command == "clear":
        result = clear_history(root, keep_last=args.keep_last, apply=args.yes)
        if not result["removed_runs"]:
            print(f"{paint(VERDICT_SYMBOL['aprovado'], 'green')} Nada a remover.")
            return 0
        contagem = f"Execuções a remover: {len(result['removed_runs'])}" + (f" (preservando as {len(result['kept_runs'])} mais recentes)" if result["kept_runs"] else "")
        print(f"{paint(COMMAND_ICON['clear'], 'yellow')} {contagem}")
        for path in result["files"]:
            print(f"  {path}")
        if result["applied"]:
            print(f"\n{paint(VERDICT_SYMBOL['aprovado'], 'green')} Removidos {len(result['files'])} arquivo(s). As specs em .sentry/specs/ não foram tocadas.")
        else:
            # Apagar historico e' irreversivel: o padrao mostra o escopo primeiro.
            print(paint("\nNada foi removido. Repita com `--yes` para confirmar.", "yellow"))
    elif args.command == "watch":
        # O mesmo `[tests] paths` que a rastreabilidade usa: se o watch discordasse
        # dela sobre o que e' teste, escalaria para a suite na hora errada.
        test_paths = tuple(load_config(root).get('tests', {}).get('paths') or DEFAULT_TEST_PATHS)
        print(f"{paint(VERDICT_SYMBOL['aprovado'], 'green')} Observando {root}.\nCtrl+C para parar.")

        def reavaliar(arquivos, modo):
            modo_colorido = paint(modo, "magenta" if modo == COMPLETO else "blue")
            print(f"\n{', '.join(arquivos[:4])}{'…' if len(arquivos) > 4 else ''} → modo {modo_colorido}")
            _run_and_report(root, args.spec, modo == COMPLETO, None,
                            parser=parser._subcommands.choices["watch"])

        try:
            watch(root, reavaliar, interval=args.interval, test_paths=test_paths)
        except KeyboardInterrupt:
            # Ctrl+C e' a forma normal de terminar um watch, nao uma falha: um
            # traceback aqui faria o usuario achar que quebrou alguma coisa.
            print(paint("\nParado.", "yellow"))
        return 0
    elif args.command == "context":
        runs = load_runs(root)
        if not runs:
            # Sem execucao nao ha lacuna medida a devolver, e um payload vazio seria
            # lido como "nada falta". O agente precisa distinguir os dois.
            print(f"{paint(VERDICT_SYMBOL['reprovado'], 'red')} Nenhuma execução encontrada; rode {paint('sentry review', 'green')} antes.")
            return EXIT_INFRA
        print(json.dumps(build_context(runs[-1]), ensure_ascii=False, indent=2))
    elif args.command == "report":
        runs = load_runs(root)
        if not runs:
            print(f"{paint(VERDICT_SYMBOL['reprovado'], 'red')} Nenhuma execução encontrada.")
            return 0
        # A acusacao vem antes do relatorio: quem le a primeira linha precisa saber
        # que o que vem abaixo nao descreve o codigo atual.
        stale = staleness(runs[-1], LocalGitAdapter(root).head())
        if stale:
            stale = stale.replace("sentry run", paint("sentry run", "green"))
            print(f"{paint(VERDICT_SYMBOL['aprovado com ressalvas'], 'yellow')} {stale}\n")
        payload = runs[-1]
        markdown = write_reports(root, payload)
        _print_pretty(payload, markdown)
    elif args.command == "history":
        runs = load_runs(root)
        print(f"{paint(COMMAND_ICON['history'], 'green')} Execuções:")
        for item in runs:
            print(item["data"].get("id"), item["data"].get("timestamp"))
        if len(runs) < 2:
            print("Análise inicial: sem execução anterior para comparar.")
        else:
            previous, current = runs[-2], runs[-1]
            result = compare(previous, current)
            if not result["comparable"]:
                print("Execuções incomparáveis: " + "; ".join(result["incomparable_reasons"]))
            else:
                coverage = result["coverage"]
                tests = result["tests"]
                print(f"Cobertura global: {_signed_colored(coverage['global_percent_delta'])}")
                print(f"Cobertura alterada: {_signed_colored(coverage['changed_percent_delta'])}")
                print(f"Testes: passed {_signed_colored(tests['passed_delta'])}, "
                      f"failed {_signed_colored(tests['failed_delta'], higher_is_better=False)}, "
                      f"skipped {_signed(tests['skipped_delta'])}, "
                      f"not_run {_signed_colored(tests['not_run_delta'], higher_is_better=False)}")
            achados_novos = ', '.join(result['new']) or 'nenhum'
            achados_resolvidos = ', '.join(result['resolved']) or 'nenhum'
            achados_persistentes = ', '.join(result['persistent']) or 'nenhum'
            print(f"Achados novos: {paint(achados_novos, 'red') if result['new'] else achados_novos}")
            print(f"Achados resolvidos: {paint(achados_resolvidos, 'green') if result['resolved'] else achados_resolvidos}")
            print(f"Achados persistentes: {paint(achados_persistentes, 'yellow') if result['persistent'] else achados_persistentes}")
            de_status, para_status = result['verdict']['from'], result['verdict']['to']
            de_simbolo = paint(VERDICT_SYMBOL.get(de_status, '?'), VERDICT_COLOR.get(de_status, 'gray'))
            para_simbolo = paint(VERDICT_SYMBOL.get(para_status, '?'), VERDICT_COLOR.get(para_status, 'gray'))
            print(f"Veredito: {de_simbolo} {de_status.capitalize()} -> {para_simbolo} {para_status.capitalize()}")
    elif args.command == "run":
        return _run_and_report(root, args.spec, args.run_tests, args.base,
                               parser=parser._subcommands.choices["run"])
    elif args.command == "status":
        # Sempre `--spec all`, sempre a suite completa, nunca o cache: e' a medicao
        # autoritativa do projeto inteiro, nao o loop rapido que `run`/`watch` sao.
        # Wordmark tambem no sucesso (nao so' em `-h`/erro) -- e' rodado uma vez so',
        # igual `init`/`new`/`check`, nao repetido feito `run`/`watch`. Nunca com
        # `--json`, que promete stdout so' com o payload.
        status_parser = parser._subcommands.choices["status"]
        if not args.as_json and status_parser._wordmark:
            print(render_wordmark(__version__))
            print()
        return _run_and_report(root, None, True, None, print_report=True, whole_project=True, as_json=args.as_json,
                               parser=status_parser)
    elif args.command == "review":
        # Seis passos viram um. A fricção é o que decide se a avaliação vira hábito
        # ou cerimônia, e o passo que se repete precisa caber numa linha.
        _check(root, args.spec, tolerate_missing=True, parser=parser._subcommands.choices["review"])
        print()
        # Testes por padrão: sem execução não há cobertura nem contagem, e o que
        # sobra é uma conferência estrutural, não um veredito.
        return _run_and_report(root, args.spec, not args.no_tests, args.base, print_report=True,
                               parser=parser._subcommands.choices["review"])
    return 0

if __name__ == "__main__":  # pragma: no cover
    # Executa so como `python -m sentrytest.cli`, num processo separado que o
    # coverage.py nao instrumenta. E' coberto por test_modulo_executavel_roda_o_mesmo_cli,
    # via subprocess -- o pragma marca a cegueira da medicao, nao ausencia de teste.
    raise SystemExit(main())
