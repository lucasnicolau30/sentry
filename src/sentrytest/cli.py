from __future__ import annotations
import argparse
import json
import platform
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

def build_parser():
    parser = argparse.ArgumentParser(
        prog="sentry",
        description="Deriva a matriz de casos de teste de um pedido e verifica se a implementação corresponde.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

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
    """Template e vocabulário aceito, para o agente que vai preencher o CASES.md."""
    return {
        "artifact": "cases",
        "template": TEMPLATE,
        "layers": list(LAYERS),
        "test_types": list(TEST_TYPES),
        "priorities": list(PRIORITIES),
        "field_classes": {name: list(classes) for name, classes in FIELD_CLASSES.items()},
        "relOutputPath": ".sentry/specs/<slug>/CASES.md",
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

def _check(root: Path, slug: str | None, tolerate_missing: bool = False) -> int:
    """A validação estrutural da matriz. `tolerate_missing` é para o `review`, que
    precisa seguir para a medição quando não há spec nenhuma — ali a ausência de
    intenção declarada não é erro, e sim o modo sem spec."""
    config = load_config(root)
    cases_path = config.get('specs', {}).get('path', CASES_PATH)
    catalog = merge_catalog(config.get('catalog', {}).get('fields'))
    try:
        if is_all_spec(slug):
            entries = spec_documents(root, cases_path)
            if not entries:
                print(f"Erro: nenhuma matriz de casos encontrada em {cases_path}")
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
        print(f"Erro: {error}")
        return 2
    errors = validate_document(document)
    missing = missing_classes(document.fields, document.cases, catalog, not_applicable=document.not_applicable)
    unknown = unknown_field_types(document.fields, catalog)
    print(f"{COMMAND_ICON['check']} {label}: {len(document.cases)} caso(s), {len(document.fields)} campo(s)")
    for error in errors:
        print(f"  {paint(SEVERITY_SYMBOL['crítica'] + ' erro:', 'red')} {error}")
    for item in missing:
        print(f"  {paint(SEVERITY_SYMBOL['média'] + ' classe ausente:', 'yellow')} {item['field']}/{item['class']} (tipo {item['type']})")
    for item in unknown:
        print(f"  [limitacao] tipo fora do catalogo, sem cobranca de classes: {item}")
    for item in document.not_applicable:
        print(f"  [classe nao aplicavel] {item.field}/{item.class_name} — {item.reason}")
    if not errors and not missing:
        print(f"{VERDICT_SYMBOL['aprovado']} " + paint("Estrutura valida e catalogo de classes coberto.", "green"))
    return 1 if errors else 0

def _print_pretty(payload: dict, markdown: str) -> None:
    """A visão bonita do relatório para o terminal: caixa de topo, corpo
    colorido, rodapé de dashboard. Nada disto passou por `write_reports` --
    quem chama já gravou `markdown` em disco antes de pedir esta versão."""
    print(render_masthead(payload))
    print()
    print(colorize_report(markdown))
    print()
    print(render_dashboard(payload))

def _init_checklist(created: list[str], deps: dict) -> list[dict]:
    """Agrupa a lista crua de `initialize_project` (um caminho por linha) nas
    categorias que o usuário reconhece -- ninguém pensa em ".sentry/specs"
    como item separado de ".sentry/runs", pensa em ".sentry/ inteiro".

    Toda categoria aparece sempre, mesmo em uma re-execução onde nada foi
    criado -- a badge (created/written/installed/ready) só aparece quando a
    categoria é nova nesta execução; numa re-execução idempotente a linha
    continua lá, sem badge nenhuma -- o próprio `✓` já basta. Sumir a linha
    inteira quando idempotente escondia informação real do usuário.

    Cada item carrega, além do texto, um detalhe opcional (complemento
    colorido) e uma badge opcional -- quem imprime é `render_checklist_item`,
    isto só decide o quê. O item de ambiente concentra python, arquitetura e
    todas as dependências detectadas numa única linha, sem uma tabela
    separada pra isso."""
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
            "badge": "created" if sentry_extra else None, "badge_color": "blue",
        },
        {
            "text": "Gerando " + " e ".join(config) if config else "Config sentry.toml e .gitignore",
            "badge": "written" if config else None, "badge_color": "blue",
        },
        {
            "text": f"Instalando skill Claude — {skill}" if skill else "Skill Claude",
            "badge": "installed" if skill else None, "badge_color": "magenta",
        },
        {
            "text": "Gravando AGENT-SENTRY.md",
            "badge": "ready" if "AGENT-SENTRY.md" in normalized else None,
            "badge_color": "yellow",
        },
    ]

def _run_and_report(root: Path, slug: str | None, run_tests: bool | None,
                    base: str | None, print_report: bool = False, whole_project: bool = False,
                    as_json: bool = False) -> int:
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
        print(f"Erro de configuração: {error}")
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
            print(f"Análise {run.id}: {symbol} {paint(status, VERDICT_COLOR.get(status, 'gray'))}")
        for error in run.infrastructure_errors:
            print(f"  {paint('[infraestrutura]', 'yellow')} {error.stage}: {error.message}" + (" (pode ser repetido)" if error.retryable else ""))
    return EXIT_BY_VERDICT.get(run.verdict.status.value, EXIT_INFRA)

def _signed(value):
    if value is None: return "indisponível"
    return f"+{value}" if value > 0 else str(value)

def main(argv=None):
    # A saida carrega acentos e e consumida por agentes de IA; o console do Windows
    # usa codepage local por padrao e corromperia o JSON de `instructions`. stderr
    # entra junto porque tracebacks e erros do argparse tambem carregam acento.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    args = build_parser().parse_args(argv)
    root = Path.cwd()
    if args.command == "init":
        created = initialize_project(root)
        deps = check_dependencies(root)
        print(render_wordmark(__version__))
        print()
        print(render_section("Inicializando", "─"))
        for item in _init_checklist(created, deps):
            print(render_checklist_item(item["text"], detail=item.get("detail"),
                                        detail_color=item.get("detail_color", "blue"),
                                        badge=item.get("badge"), badge_color=item.get("badge_color", "blue")))
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
            print(f"Rode `sentry init --install` para instalar: {', '.join(missing)}")
            return EXIT_INFRA
    elif args.command == "new":
        prompt = args.prompt or args.name
        directory, created = scaffold(root, args.name, prompt)
        if args.as_json:
            print(json.dumps({**instructions_payload(), "specDir": str(directory.relative_to(root))}, ensure_ascii=False, indent=2))
            return 0
        print(f"{COMMAND_ICON['new']} Spec criada em {directory.relative_to(root)}")
        print("Criados: " + (", ".join(created) if created else "nenhum arquivo novo"))
        print("\nPreencha o CASES.md seguindo este template:\n")
        print(TEMPLATE)
        print(f"Camadas aceitas: {', '.join(LAYERS)}")
        print(f"Tipos aceitos: {', '.join(TEST_TYPES)}")
        print(f"Prioridades: {', '.join(PRIORITIES)}")
        print(f"Tipos de campo com classes cobradas: {', '.join(sorted(FIELD_CLASSES))}")
        print(f"\nDepois rode `sentry check {directory.name}` até fechar limpo.")
    elif args.command == "check":
        return _check(root, args.slug)
    elif args.command == "clear":
        result = clear_history(root, keep_last=args.keep_last, apply=args.yes)
        if not result["removed_runs"]:
            print(f"{COMMAND_ICON['clear']} Nada a remover.")
            return 0
        print(f"{COMMAND_ICON['clear']} Execuções a remover: {len(result['removed_runs'])}" + (f" (preservando as {len(result['kept_runs'])} mais recentes)" if result["kept_runs"] else ""))
        for path in result["files"]:
            print(f"  {path}")
        if result["applied"]:
            print(f"\nRemovidos {len(result['files'])} arquivo(s). As specs em .sentry/specs/ não foram tocadas.")
        else:
            # Apagar historico e' irreversivel: o padrao mostra o escopo primeiro.
            print("\nNada foi removido. Repita com `--yes` para confirmar.")
    elif args.command == "watch":
        # O mesmo `[tests] paths` que a rastreabilidade usa: se o watch discordasse
        # dela sobre o que e' teste, escalaria para a suite na hora errada.
        test_paths = tuple(load_config(root).get('tests', {}).get('paths') or DEFAULT_TEST_PATHS)
        print(f"{COMMAND_ICON['watch']} Observando {root}. Ctrl+C para parar.")

        def reavaliar(arquivos, modo):
            print(f"\n{', '.join(arquivos[:4])}{'…' if len(arquivos) > 4 else ''} → modo {modo}")
            _run_and_report(root, args.spec, modo == COMPLETO, None)

        try:
            watch(root, reavaliar, interval=args.interval, test_paths=test_paths)
        except KeyboardInterrupt:
            # Ctrl+C e' a forma normal de terminar um watch, nao uma falha: um
            # traceback aqui faria o usuario achar que quebrou alguma coisa.
            print("\nParado.")
        return 0
    elif args.command == "context":
        runs = load_runs(root)
        if not runs:
            # Sem execucao nao ha lacuna medida a devolver, e um payload vazio seria
            # lido como "nada falta". O agente precisa distinguir os dois.
            print(f"{COMMAND_ICON['context']} Nenhuma execução encontrada; rode `sentry review` antes.")
            return EXIT_INFRA
        print(json.dumps(build_context(runs[-1]), ensure_ascii=False, indent=2))
    elif args.command == "report":
        runs = load_runs(root)
        if not runs:
            print(f"{COMMAND_ICON['report']} Nenhuma execução encontrada.")
            return 0
        # A acusacao vem antes do relatorio: quem le a primeira linha precisa saber
        # que o que vem abaixo nao descreve o codigo atual.
        stale = staleness(runs[-1], LocalGitAdapter(root).head())
        if stale:
            print(stale + "\n")
        payload = runs[-1]
        markdown = write_reports(root, payload)
        _print_pretty(payload, markdown)
    elif args.command == "history":
        runs = load_runs(root)
        print(f"{COMMAND_ICON['history']} Execuções:")
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
                print(f"Cobertura global: {_signed(coverage['global_percent_delta'])}")
                print(f"Cobertura alterada: {_signed(coverage['changed_percent_delta'])}")
                print(f"Testes: passed {_signed(tests['passed_delta'])}, failed {_signed(tests['failed_delta'])}, skipped {_signed(tests['skipped_delta'])}, not_run {_signed(tests['not_run_delta'])}")
            print(f"Achados novos: {', '.join(result['new']) or 'nenhum'}")
            print(f"Achados resolvidos: {', '.join(result['resolved']) or 'nenhum'}")
            print(f"Achados persistentes: {', '.join(result['persistent']) or 'nenhum'}")
            print(f"Veredito: {result['verdict']['from']} -> {result['verdict']['to']}")
    elif args.command == "run":
        return _run_and_report(root, args.spec, args.run_tests, args.base)
    elif args.command == "status":
        # Sempre `--spec all`, sempre a suite completa, nunca o cache: e' a medicao
        # autoritativa do projeto inteiro, nao o loop rapido que `run`/`watch` sao.
        return _run_and_report(root, None, True, None, print_report=True, whole_project=True, as_json=args.as_json)
    elif args.command == "review":
        # Seis passos viram um. A fricção é o que decide se a avaliação vira hábito
        # ou cerimônia, e o passo que se repete precisa caber numa linha.
        _check(root, args.spec, tolerate_missing=True)
        print()
        # Testes por padrão: sem execução não há cobertura nem contagem, e o que
        # sobra é uma conferência estrutural, não um veredito.
        return _run_and_report(root, args.spec, not args.no_tests, args.base, print_report=True)
    return 0

if __name__ == "__main__":  # pragma: no cover
    # Executa so como `python -m sentrytest.cli`, num processo separado que o
    # coverage.py nao instrumenta. E' coberto por test_modulo_executavel_roda_o_mesmo_cli,
    # via subprocess -- o pragma marca a cegueira da medicao, nao ausencia de teste.
    raise SystemExit(main())
