import sqlite3
from pathlib import Path
from sentrytest.init_project import CURRENT_SCHEMA_VERSION, initialize_project, migrate

def test_initialize_project_is_idempotent(tmp_path: Path) -> None:
    first=initialize_project(tmp_path)
    second=initialize_project(tmp_path)
    assert 'sentry.toml' in first
    assert second == []
    assert (tmp_path/'.sentry'/'sentry.db').exists()
    assert (tmp_path/'.gitignore').read_text(encoding='utf-8').count('.sentry/sentry.db') == 1

# cenario: specs ficam fora do git e latest.md fica rastreavel
def test_gitignore_ignores_specs_but_keeps_latest_md_trackable(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    content=(tmp_path/'.gitignore').read_text(encoding='utf-8')
    assert '.sentry/specs/' in content
    assert '.sentry/reports/*' in content
    assert '!.sentry/reports/latest.md' in content
    assert '.sentry/reports/\n' not in content  # padrao antigo bloquearia latest.md

# cenario: gitignore antigo e migrado sem duplicar entradas
def test_gitignore_migrates_obsolete_reports_pattern(tmp_path: Path) -> None:
    """O padrao antigo (`.sentry/reports/`) exclui o diretorio inteiro: uma
    negacao para latest.md depois dele nao teria efeito. Precisa ser removido,
    nao só complementado."""
    (tmp_path/'.gitignore').write_text('.sentry/sentry.db\n.sentry/reports/\n.sentry/runs/\n', encoding='utf-8')
    initialize_project(tmp_path)
    content=(tmp_path/'.gitignore').read_text(encoding='utf-8')
    assert '.sentry/reports/\n' not in content
    assert '.sentry/reports/*' in content
    assert '!.sentry/reports/latest.md' in content
    assert initialize_project(tmp_path)==[]  # idempotente apos a migracao

# cenario: init instala o guia de agente na raiz do projeto
def test_initialize_project_installs_agent_guide_at_root(tmp_path: Path) -> None:
    """Diferente da skill (.claude/skills, so Claude Code), este arquivo fica na
    raiz para qualquer agente de IA que consiga rodar comandos de shell ler."""
    created=initialize_project(tmp_path)
    guide=tmp_path/'AGENT-SENTRY.md'
    assert 'AGENT-SENTRY.md' in created
    assert guide.exists()
    assert 'sentry new' in guide.read_text(encoding='utf-8')
    assert initialize_project(tmp_path)==[]

# cenario: init cria o banco ja na versao atual, com a tabela runs pronta
def test_initialize_project_leaves_db_on_current_schema_version(tmp_path: Path) -> None:
    """Sem isso, runs so era criada na primeira analise: sentry history antes de
    qualquer run tocaria numa tabela inexistente."""
    initialize_project(tmp_path)
    with sqlite3.connect(tmp_path/'.sentry'/'sentry.db') as connection:
        version=connection.execute('SELECT version FROM schema_version').fetchone()[0]
        assert version==CURRENT_SCHEMA_VERSION
        connection.execute("SELECT 1 FROM runs WHERE 0")  # nao levanta OperationalError

# cenario: banco de versao antiga e migrado sem perder dados existentes
def test_migrate_upgrades_a_pre_existing_database_without_losing_data(tmp_path: Path) -> None:
    """Simula um sentry.db criado por uma versao anterior, com schema_version
    mas sem a tabela runs: migrate precisa completar o schema sem apagar nada."""
    db=tmp_path/'sentry.db'
    with sqlite3.connect(db) as connection:
        connection.execute('CREATE TABLE schema_version (version INTEGER NOT NULL)')
        connection.execute('INSERT INTO schema_version(version) VALUES (0)')
        connection.execute('CREATE TABLE specs_marker (name TEXT)')
        connection.execute("INSERT INTO specs_marker VALUES ('preserved')")
    with sqlite3.connect(db) as connection:
        migrate(connection)
        assert connection.execute('SELECT version FROM schema_version').fetchone()[0]==CURRENT_SCHEMA_VERSION
        assert connection.execute('SELECT name FROM specs_marker').fetchone()[0]=='preserved'
        connection.execute("SELECT 1 FROM runs WHERE 0")