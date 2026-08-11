"""Inicialização idempotente de um projeto Sentry."""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

from .skills import install_agent_guide, install_skills

def default_config(project_name: str) -> str:
    """Configuracao inicial ja com o nome real do projeto. Um placeholder fixo
    faria todo relatorio de quem nao editasse o arquivo sair com o mesmo nome."""
    return (f'[project]\nname = "{project_name}"\n\n'
            '[specs]\npath = ".sentry/specs"\n\n'
            '[test]\ncommand = "pytest"\n\n'
            '[analysis]\nrun_tests_by_default = false\ntimeout_seconds = 300\n')

# As unicas linhas que o `init` escreve no .gitignore do projeto. Nomeadas aqui
# porque quem monta o diff precisa delas: uma alteracao composta so por estas
# linhas e' do Sentry, e nao mudanca do usuario a revisar.
# specs sao dado local (nao versionado); reports/* fica fora exceto latest.md,
# que fica rastreavel para aparecer no diff da PR sem precisar rodar o Sentry.
# Git nao reinclui arquivo dentro de diretorio excluido, por isso o padrao e
# ".../*" (conteudo) em vez de ".../" (o diretorio inteiro) antes da negacao.
GITIGNORE_ENTRIES = ('.sentry/sentry.db', '.sentry/specs/', '.sentry/reports/*',
                     '!.sentry/reports/latest.md', '.sentry/runs/', '.sentry/test-plans/')
OBSOLETE_GITIGNORE_ENTRIES = frozenset({'.sentry/reports/'})

# Cada versao lista os comandos DDL que faltam para chegar nela, a partir da
# anterior. Todos IF NOT EXISTS: aplicar de novo num banco ja migrado nao falha,
# e um banco criado do zero passa por todas as versoes em sequencia.
CURRENT_SCHEMA_VERSION = 1
MIGRATIONS: dict[int, tuple[str, ...]] = {
    1: ("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",),
}

def migrate(connection: sqlite3.Connection) -> None:
    """Le a versao gravada no banco e aplica, em ordem, as migracoes que faltam
    ate CURRENT_SCHEMA_VERSION. Sem isto, um banco criado por uma versao antiga
    do Sentry ficaria com tabelas faltando quando o schema mudasse."""
    connection.execute('CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)')
    row = connection.execute('SELECT version FROM schema_version').fetchone()
    version = row[0] if row else 0
    for target in range(version + 1, CURRENT_SCHEMA_VERSION + 1):
        for statement in MIGRATIONS[target]:
            connection.execute(statement)
        if row is None:
            connection.execute('INSERT INTO schema_version(version) VALUES (?)', (target,))
            row = (target,)
        else:
            connection.execute('UPDATE schema_version SET version = ?', (target,))

def initialize_project(root: Path) -> list[str]:
    created=[]
    sentry=root/'.sentry'
    for name in ('reports','runs','test-plans','specs'):
        path=sentry/name
        if not path.exists(): path.mkdir(parents=True); created.append(str(path.relative_to(root)))
    sentry.mkdir(exist_ok=True)
    db=sentry/'sentry.db'
    db_existed = db.exists()
    with sqlite3.connect(db) as connection:
        migrate(connection)
    if not db_existed: created.append(str(db.relative_to(root)))
    config=root/'sentry.toml'
    if not config.exists(): config.write_text(default_config(root.resolve().name), encoding='utf-8'); created.append('sentry.toml')
    gitignore=root/'.gitignore'
    existing=gitignore.read_text(encoding='utf-8').splitlines() if gitignore.exists() else []
    filtered=[line for line in existing if line not in OBSOLETE_GITIGNORE_ENTRIES]
    missing=[entry for entry in GITIGNORE_ENTRIES if entry not in filtered]
    if missing or filtered!=existing:
        gitignore.write_text('\n'.join(filtered+missing)+'\n',encoding='utf-8'); created.append('.gitignore')
    created += install_skills(root)
    created += install_agent_guide(root)
    return created

def _module_available(module: str) -> bool:
    result = subprocess.run([sys.executable, '-m', module, '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode == 0

def check_dependencies(root: Path) -> dict[str,bool]:
    return {'pytest': _module_available('pytest'), 'coverage': _module_available('coverage')}

def install_dependencies(names: list[str]) -> list[tuple[str,bool,str]]:
    """Instala no ambiente Python atual. Só é chamada com pedido explícito do usuário,
    porque alterar o ambiente de quem roda a ferramenta nunca pode ser efeito colateral."""
    results = []
    for name in names:
        outcome = subprocess.run([sys.executable, '-m', 'pip', 'install', name],
                                 capture_output=True, text=True, encoding='utf-8', errors='replace')
        error = '' if outcome.returncode == 0 else (outcome.stderr or outcome.stdout).strip().splitlines()[-1:]
        results.append((name, outcome.returncode == 0, error[0] if error else ''))
    return results
