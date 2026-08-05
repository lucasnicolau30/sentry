"""Inicialização idempotente de um projeto Sentry."""
from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

CONFIG = '''[project]\nname = "meu-projeto"\n\n[draun]\nspecs_path = ".draun/specs"\n\n[pytest]\ncommand = "pytest"\n\n[analysis]\nrun_tests_by_default = false\ntimeout_seconds = 300\n'''
SCHEMA = "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);"

def initialize_project(root: Path) -> list[str]:
    created=[]
    sentry=root/'.sentry'
    for name in ('reports','runs','test-plans'):
        path=sentry/name
        if not path.exists(): path.mkdir(parents=True); created.append(str(path.relative_to(root)))
    sentry.mkdir(exist_ok=True)
    db=sentry/'sentry.db'
    with sqlite3.connect(db) as connection:
        connection.execute(SCHEMA)
        connection.execute('INSERT INTO schema_version(version) SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM schema_version)')
    if not db.exists(): created.append(str(db.relative_to(root)))
    config=root/'sentry.toml'
    if not config.exists(): config.write_text(CONFIG, encoding='utf-8'); created.append('sentry.toml')
    gitignore=root/'.gitignore'
    entries=['.sentry/sentry.db','.sentry/reports/','.sentry/runs/','.sentry/test-plans/']
    existing=gitignore.read_text(encoding='utf-8').splitlines() if gitignore.exists() else []
    missing=[entry for entry in entries if entry not in existing]
    if missing: gitignore.write_text('\n'.join(existing+missing)+'\n',encoding='utf-8'); created.append('.gitignore')
    return created

def _module_available(module: str) -> bool:
    result = subprocess.run([sys.executable, '-m', module, '--version'], capture_output=True, text=True)
    return result.returncode == 0

def check_dependencies(root: Path) -> dict[str,bool]:
    return {'draun': shutil.which('draun') is not None, 'pytest': _module_available('pytest'), 'coverage': _module_available('coverage')}
