from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .init_project import check_dependencies, initialize_project, install_dependencies
from .adapters.case_specs import LAYERS, PRIORITIES, TEMPLATE, TEST_TYPES, CaseSpecAdapter, validate_document
from .adapters.toml_config import load_config
from .domain.catalog import FIELD_CLASSES, missing_classes, unknown_field_types
from .application.analyze import CASES_PATH, analyze, is_all_spec, merge_documents, select_spec, spec_documents
from .application.cases import scaffold
from .application.reporting import clear_history, load_runs, write_reports, compare

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
        print("Projeto Sentry inicializado.")
        print("Criados: " + (", ".join(created) if created else "nenhum arquivo novo"))
        missing = [name for name, ok in deps.items() if not ok]
        print("Dependências: " + ", ".join(f"{name}={'presente' if ok else 'ausente'}" for name, ok in deps.items()))
        if missing and args.install:
            for name, ok, error in install_dependencies(missing):
                print(f"  {name}: {'instalado' if ok else 'falhou'}" + (f" — {error}" if error else ""))
            deps = check_dependencies(root)
            if any(not ok for ok in deps.values()):
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
        print(f"Spec criada em {directory.relative_to(root)}")
        print("Criados: " + (", ".join(created) if created else "nenhum arquivo novo"))
        print("\nPreencha o CASES.md seguindo este template:\n")
        print(TEMPLATE)
        print(f"Camadas aceitas: {', '.join(LAYERS)}")
        print(f"Tipos aceitos: {', '.join(TEST_TYPES)}")
        print(f"Prioridades: {', '.join(PRIORITIES)}")
        print(f"Tipos de campo com classes cobradas: {', '.join(sorted(FIELD_CLASSES))}")
        print(f"\nDepois rode `sentry check {directory.name}` até fechar limpo.")
    elif args.command == "check":
        cases_path = load_config(root).get('specs', {}).get('path', CASES_PATH)
        try:
            if is_all_spec(args.slug):
                entries = spec_documents(root, cases_path)
                if not entries:
                    print(f"Erro: nenhuma matriz de casos encontrada em {cases_path}")
                    return 2
                document = merge_documents([(name, CaseSpecAdapter(path).document()) for name, path in entries])
                label = 'all (' + ', '.join(name for name, _ in entries) + ')'
            else:
                spec = select_spec(root, args.slug, cases_path)
                document = CaseSpecAdapter(spec).document()
                label = str(spec.relative_to(root))
        except (ValueError, FileNotFoundError) as error:
            print(f"Erro: {error}")
            return 2
        errors = validate_document(document)
        missing = missing_classes(document.fields, document.cases, not_applicable=document.not_applicable)
        unknown = unknown_field_types(document.fields)
        print(f"{label}: {len(document.cases)} caso(s), {len(document.fields)} campo(s)")
        for error in errors:
            print(f"  [erro] {error}")
        for item in missing:
            print(f"  [classe ausente] {item['field']}/{item['class']} (tipo {item['type']})")
        for item in unknown:
            print(f"  [limitacao] tipo fora do catalogo, sem cobranca de classes: {item}")
        for item in document.not_applicable:
            print(f"  [classe nao aplicavel] {item.field}/{item.class_name} — {item.reason}")
        if not errors and not missing:
            print("Estrutura valida e catalogo de classes coberto.")
        return 1 if errors else 0
    elif args.command == "clear":
        result = clear_history(root, keep_last=args.keep_last, apply=args.yes)
        if not result["removed_runs"]:
            print("Nada a remover.")
            return 0
        print(f"Execuções a remover: {len(result['removed_runs'])}" + (f" (preservando as {len(result['kept_runs'])} mais recentes)" if result["kept_runs"] else ""))
        for path in result["files"]:
            print(f"  {path}")
        if result["applied"]:
            print(f"\nRemovidos {len(result['files'])} arquivo(s). As specs em .sentry/specs/ não foram tocadas.")
        else:
            # Apagar historico e' irreversivel: o padrao mostra o escopo primeiro.
            print("\nNada foi removido. Repita com `--yes` para confirmar.")
    elif args.command == "report":
        runs = load_runs(root)
        if not runs:
            print("Nenhuma execução encontrada.")
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
    elif args.command == "run":
        try:
            run = analyze(root, args.spec, args.run_tests, args.base)
            payload = json.loads(__import__("sentrytest.domain.models", fromlist=["to_json"]).to_json(run))
            write_reports(root, payload)
            print(f"Análise {run.id}: {run.verdict.status.value}")
            for error in run.infrastructure_errors:
                print(f"  [infraestrutura] {error.stage}: {error.message}" + (" (pode ser repetido)" if error.retryable else ""))
            return EXIT_BY_VERDICT.get(run.verdict.status.value, EXIT_INFRA)
        except (ValueError, FileNotFoundError) as error:
            print(f"Erro de configuração: {error}")
            return EXIT_INFRA
    return 0

if __name__ == "__main__":  # pragma: no cover
    # Executa so como `python -m sentrytest.cli`, num processo separado que o
    # coverage.py nao instrumenta. E' coberto por test_modulo_executavel_roda_o_mesmo_cli,
    # via subprocess -- o pragma marca a cegueira da medicao, nao ausencia de teste.
    raise SystemExit(main())
