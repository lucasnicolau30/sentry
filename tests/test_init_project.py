import sqlite3
from pathlib import Path
from sentrytest.init_project import CURRENT_SCHEMA_VERSION, _installed_version, initialize_project, migrate

def test_versao_de_pacote_inexistente_no_importlib_metadata_e_none() -> None:
    """Caminho defensivo, sem cenário declarado: um módulo cujo nome não
    resolve em `importlib.metadata` (nome de pacote diferente do módulo, por
    exemplo) não pode derrubar `check_dependencies` -- devolve None, não
    inventa versão nem propaga a exceção."""
    assert _installed_version('um-pacote-que-nao-existe-de-verdade') is None

def test_initialize_project_is_idempotent(tmp_path: Path) -> None:
    first=initialize_project(tmp_path)
    second=initialize_project(tmp_path)
    assert 'sentry.toml' in first
    assert second == []
    assert (tmp_path/'.sentry'/'sentry.db').exists()
    assert (tmp_path/'.gitignore').read_text(encoding='utf-8').count('.sentry/sentry.db') == 1

# cenario: gitignore novo nasce sem a linha de specs
def test_gitignore_novo_nao_exclui_specs_e_mantem_latest_md_rastreavel(tmp_path: Path) -> None:
    """Spec e' intencao declarada, nao evidencia gerada: nao versionada, ela so
    existe na maquina de quem a escreveu e um checkout limpo nao tem o que medir."""
    initialize_project(tmp_path)
    content=(tmp_path/'.gitignore').read_text(encoding='utf-8')
    assert '.sentry/specs/' not in content
    assert '.sentry/reports/*' in content
    assert '!.sentry/reports/latest.md' in content
    assert '.sentry/reports/\n' not in content  # padrao antigo bloquearia latest.md

# cenario: specs saem do gitignore na proxima inicializacao
def test_gitignore_existente_perde_a_exclusao_de_specs(tmp_path: Path) -> None:
    (tmp_path/'.gitignore').write_text('.sentry/sentry.db\n.sentry/specs/\n.sentry/runs/\n', encoding='utf-8')
    initialize_project(tmp_path)
    content=(tmp_path/'.gitignore').read_text(encoding='utf-8')
    assert '.sentry/specs/' not in content

# cenario: as outras entradas do init sobrevivem a remocao
def test_remocao_de_specs_preserva_as_demais_entradas(tmp_path: Path) -> None:
    """Remover uma entrada obsoleta nao pode levar as outras junto: o usuario perderia
    a exclusao do banco e das execucoes sem ter pedido nada."""
    initialize_project(tmp_path)
    (tmp_path/'.gitignore').write_text(
        (tmp_path/'.gitignore').read_text(encoding='utf-8')+'.sentry/specs/\n', encoding='utf-8')
    initialize_project(tmp_path)
    content=(tmp_path/'.gitignore').read_text(encoding='utf-8')
    assert '.sentry/specs/' not in content
    for entrada in ('.sentry/sentry.db', '.sentry/runs/', '.sentry/test-plans/',
                    '.sentry/reports/*', '!.sentry/reports/latest.md'):
        assert entrada in content
    assert initialize_project(tmp_path)==[]  # idempotente apos a migracao

# cenario: linha parecida escrita pelo usuario nao e removida
def test_linha_do_usuario_parecida_com_a_obsoleta_permanece(tmp_path: Path) -> None:
    """A comparacao e' por linha inteira: apagar qualquer linha que *contenha*
    `.sentry/specs/` mudaria a configuracao do usuario sem ele ter pedido."""
    (tmp_path/'.gitignore').write_text('.sentry/specs/rascunhos/\n', encoding='utf-8')
    initialize_project(tmp_path)
    assert '.sentry/specs/rascunhos/' in (tmp_path/'.gitignore').read_text(encoding='utf-8')

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