from __future__ import annotations
import argparse
from pathlib import Path
from . import __version__
from .init_project import check_dependencies, initialize_project
from .application.analyze import analyze
from .application.reporting import load_runs, write_reports, compare

def build_parser():
    parser=argparse.ArgumentParser(prog='sentry',description='Avalia a qualidade dos testes associados a uma mudança.')
    parser.add_argument('--version',action='version',version=__version__)
    sub=parser.add_subparsers(dest='command')
    sub.add_parser('init',help='inicializa o projeto atual')
    command=sub.add_parser('analyze',help='analisa a mudança atual'); command.add_argument('--spec'); command.add_argument('--run-tests',action='store_true')
    sub.add_parser('report',help='exibe o último relatório')
    sub.add_parser('history',help='lista execuções anteriores')
    return parser

def main(argv=None):
    args=build_parser().parse_args(argv); root=Path.cwd()
    if args.command=='init':
        created=initialize_project(root); deps=check_dependencies(root); print('Projeto Sentry inicializado.'); print('Criados: '+(', '.join(created) if created else 'nenhum arquivo novo')); print('Dependências: '+', '.join(f'{n}={"presente" if ok else "ausente"}' for n,ok in deps.items()))
    elif args.command=='report':
        runs=load_runs(root)
        if not runs: print('Nenhuma execução encontrada.'); return 0
        print(write_reports(root,runs[-1]))
    elif args.command=='history':
        for item in load_runs(root): print(item['data'].get('id'), item['data'].get('timestamp'))
    elif args.command=='analyze':
        try:
            run=analyze(root,args.spec,args.run_tests); payload=__import__('json').loads(__import__('sentry.domain.models',fromlist=['to_json']).to_json(run)); write_reports(root,payload); print(f'Análise {run.id}: {run.verdict.status.value}'); return 0
        except (ValueError,FileNotFoundError) as error: print(f'Erro de configuração: {error}'); return 2
    return 0