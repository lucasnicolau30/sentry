from __future__ import annotations
import argparse
import json
from pathlib import Path
from . import __version__
from .init_project import check_dependencies, initialize_project
from .application.analyze import analyze
from .application.reporting import load_runs, write_reports, compare

def build_parser():
    parser = argparse.ArgumentParser(prog="sentry", description="Avalia a qualidade dos testes associados a uma mudan\u00e7a.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="inicializa o projeto atual")
    command = sub.add_parser("analyze", help="analisa a mudan\u00e7a atual")
    command.add_argument("--spec")
    command.add_argument("--run-tests", action="store_true", default=None)
    sub.add_parser("report", help="exibe o \u00faltimo relat\u00f3rio")
    sub.add_parser("history", help="lista execu\u00e7\u00f5es anteriores")
    return parser

def _signed(value):
    if value is None: return "indisponível"
    return f"+{value}" if value > 0 else str(value)

def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path.cwd()
    if args.command == "init":
        created = initialize_project(root)
        deps = check_dependencies(root)
        print("Projeto Sentry inicializado.")
        print("Criados: " + (", ".join(created) if created else "nenhum arquivo novo"))
        print("Depend\u00eancias: " + ", ".join(f"{name}={'presente' if ok else 'ausente'}" for name, ok in deps.items()))
    elif args.command == "report":
        runs = load_runs(root)
        if not runs:
            print("Nenhuma execu\u00e7\u00e3o encontrada.")
            return 0
        print(write_reports(root, runs[-1]))
    elif args.command == "history":
        runs = load_runs(root)
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
    elif args.command == "analyze":
        try:
            run = analyze(root, args.spec, args.run_tests)
            payload = json.loads(__import__("sentry.domain.models", fromlist=["to_json"]).to_json(run))
            write_reports(root, payload)
            print(f"An\u00e1lise {run.id}: {run.verdict.status.value}")
            return 0
        except (ValueError, FileNotFoundError) as error:
            print(f"Erro de configura\u00e7\u00e3o: {error}")
            return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
