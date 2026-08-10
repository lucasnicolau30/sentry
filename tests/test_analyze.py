from pathlib import Path
import pytest
from sentrytest.application.analyze import _severity_policy, analyze, select_spec

CASES_B = """# Segunda spec

## Prompt

Outra funcionalidade de demonstracao.

## Caso: subtracao retorna a diferenca

- **Requisito:** subtrair dois numeros
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** dois inteiros validos
- **Quando:** subtrair e chamado
- **Então:** retorna a diferenca
"""

CASES = """# Demo

## Prompt

Funcionalidade de demonstracao.

## Caso: soma retorna o total

- **Requisito:** somar dois numeros
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** dois inteiros validos
- **Quando:** somar e chamado
- **Então:** retorna a soma
"""

def _spec(root: Path, slug: str = 'demo') -> Path:
    directory = root / '.sentry' / 'specs' / slug
    directory.mkdir(parents=True)
    (directory / 'CASES.md').write_text(CASES, encoding='utf-8')
    return directory

def test_analyze_persists_run(tmp_path:Path):
    _spec(tmp_path)
    run=analyze(tmp_path)
    assert (tmp_path/'.sentry'/'runs'/f'{run.id}.json').exists()

def test_analyze_flags_declared_case_without_test(tmp_path:Path):
    """Caso declarado sem teste associado gera achado e impede aprovacao limpa."""
    _spec(tmp_path)
    run=analyze(tmp_path)
    assert run.verdict.status.value=='aprovado com ressalvas'
    assert 'scenario-without-test' in {finding.rule for finding in run.findings}

def test_analyze_requires_existing_explicit_spec(tmp_path:Path):
    try: analyze(tmp_path,'missing')
    except FileNotFoundError as error: assert 'não encontrada' in str(error)
    else: raise AssertionError('deveria falhar')

def test_analyze_populates_test_cases(tmp_path:Path):
    _spec(tmp_path)
    run=analyze(tmp_path)
    assert len(run.test_cases)==1
    assert run.test_cases[0].requirement=='somar dois numeros'

def test_analyze_runs_tests_once(tmp_path:Path):
    _spec(tmp_path)
    (tmp_path/'tests').mkdir(); (tmp_path/'tests'/'test_ok.py').write_text('def test_ok():\n    assert 1 == 1\n',encoding='utf-8'); (tmp_path/'conftest.py').write_text('',encoding='utf-8')
    run=analyze(tmp_path,run_tests=True)
    runs_dir=tmp_path/'.sentry'/'runs'
    assert not (runs_dir/'pending-coverage.json').exists()
    assert (runs_dir/f'{run.id}-coverage.json').exists()
    assert run.configuration['test_execution']['passed']>=1

# cenario: rejeita slug que escapa da pasta de specs
def test_select_spec_rejects_slug_escaping_specs_dir(tmp_path: Path):
    """`../..` no slug sairia de .sentry/specs e leria arquivo arbitrario."""
    _spec(tmp_path)
    fora = tmp_path / 'segredo'
    fora.mkdir()
    (fora / 'CASES.md').write_text(CASES, encoding='utf-8')
    with pytest.raises(ValueError, match='aponta para fora'):
        select_spec(tmp_path, '../../segredo')

# cenario: rejeita slug com caminho absoluto
def test_select_spec_rejects_absolute_slug(tmp_path: Path):
    """Caminho absoluto descartaria a base inteira no pathlib."""
    _spec(tmp_path)
    fora = tmp_path / 'segredo'
    fora.mkdir()
    (fora / 'CASES.md').write_text(CASES, encoding='utf-8')
    with pytest.raises(ValueError, match='aponta para fora'):
        select_spec(tmp_path, str(fora))

# cenario: aceita slug valido
def test_select_spec_accepts_valid_slug(tmp_path: Path):
    _spec(tmp_path, 'demo')
    assert select_spec(tmp_path, 'demo') == (tmp_path / '.sentry' / 'specs' / 'demo' / 'CASES.md').resolve()

# cenario: sem slug e sem nenhuma spec, recusa com erro claro
def test_select_spec_without_slug_and_without_any_spec_raises(tmp_path: Path):
    (tmp_path / '.sentry' / 'specs').mkdir(parents=True)
    with pytest.raises(ValueError, match='nenhuma matriz de casos encontrada'):
        select_spec(tmp_path, None)

# cenario: sem slug e com mais de uma spec, pede para escolher com --spec
def test_select_spec_without_slug_and_multiple_specs_raises(tmp_path: Path):
    _spec(tmp_path, 'demo-a')
    _spec(tmp_path, 'demo-b')
    with pytest.raises(ValueError, match='múltiplas specs encontradas'):
        select_spec(tmp_path, None)

# cenario: severidade invalida no sentry.toml e ignorada, nao quebra a leitura
def test_severity_policy_ignores_invalid_severity_value():
    """Um valor de severidade que nao existe no enum nao pode derrubar a leitura
    do sentry.toml: a regra so fica sem sobrescrita, o resto da politica segue."""
    policy = _severity_policy({'policy': {'severities': {
        'coverage-missing': 'nivel-que-nao-existe',
        'test-failing': 'baixa',
    }}})
    assert 'coverage-missing' not in policy
    assert policy['test-failing'].value == 'baixa'

def test_analyze_reporta_caminho_de_erro_sem_cobertura(tmp_path: Path):
    """Fim a fim: raise em linha alterada, sem execucao, vira achado na Run."""
    import subprocess
    _spec(tmp_path)
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        subprocess.run(['git', *args], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.py').write_text('x = 1\n', encoding='utf-8')
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, capture_output=True)
    subprocess.run(['git', 'commit', '-qm', 'base'], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.py').write_text('def f(v):\n    raise ValueError("x")\n', encoding='utf-8')

    run = analyze(tmp_path)
    error_paths = run.configuration['error_paths']
    # Sem --run-tests nao ha cobertura: limitacao registrada, nenhum achado inventado.
    assert error_paths['uncovered'] == ()
    assert any('sem dados de cobertura' in item for item in error_paths['limitations'])
    assert 'error-path-without-test' not in {finding.rule for finding in run.findings}

# cenario: arquivo em diretório excluído não entra no diff analisado
def test_analyze_exclude_removes_out_of_scope_files_from_git_change(tmp_path: Path):
    """frontend/ (ou outro diretorio fora do escopo) nao deve contar como codigo
    alterado: sem isso ele distorce impacto e cobertura do codigo alterado."""
    import subprocess
    _spec(tmp_path)
    (tmp_path / 'sentry.toml').write_text('[analysis]\nexclude = ["frontend/"]\n', encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        subprocess.run(['git', *args], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.py').write_text('x = 1\n', encoding='utf-8')
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, capture_output=True)
    subprocess.run(['git', 'commit', '-qm', 'base'], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.py').write_text('x = 2\n', encoding='utf-8')
    (tmp_path / 'frontend').mkdir()
    (tmp_path / 'frontend' / 'App.tsx').write_text('export default function App() {}\n', encoding='utf-8')

    run = analyze(tmp_path)
    files = run.configuration['git_change']['files']
    assert 'app.py' in files
    assert not any(name.startswith('frontend/') for name in files)

# cenario: sem exclude declarado, nada é filtrado
def test_analyze_without_exclude_keeps_every_changed_file(tmp_path: Path):
    """O padrao nao pode filtrar nada sem configuracao explicita: sem
    [analysis] exclude, ate um arquivo de outra stack continua no diff."""
    import subprocess
    _spec(tmp_path)
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        subprocess.run(['git', *args], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.py').write_text('x = 1\n', encoding='utf-8')
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, capture_output=True)
    subprocess.run(['git', 'commit', '-qm', 'base'], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.py').write_text('x = 2\n', encoding='utf-8')
    (tmp_path / 'frontend').mkdir()
    (tmp_path / 'frontend' / 'App.tsx').write_text('export default function App() {}\n', encoding='utf-8')

    run = analyze(tmp_path)
    files = run.configuration['git_change']['files']
    assert 'app.py' in files
    assert 'frontend/App.tsx' in files  # sem exclude, nada e' removido

# cenario: spec all junta casos de todas as pastas
def test_analyze_spec_all_merges_every_spec(tmp_path: Path):
    """--spec all precisa somar os casos das duas pastas num veredito so, em vez
    de exigir escolher uma spec quando ha mais de uma."""
    _spec(tmp_path, 'demo-a')
    directory_b = tmp_path / '.sentry' / 'specs' / 'demo-b'
    directory_b.mkdir(parents=True)
    (directory_b / 'CASES.md').write_text(CASES_B, encoding='utf-8')

    run = analyze(tmp_path, 'all')
    assert len(run.test_cases) == 2
    assert run.configuration['spec'] == 'all (demo-a, demo-b)'

# cenario: spec all sem nenhuma pasta ainda recusa com erro claro
def test_analyze_spec_all_requires_at_least_one_spec(tmp_path: Path):
    with pytest.raises(ValueError, match='nenhuma matriz de casos encontrada'):
        analyze(tmp_path, 'all')

# cenario: projeto de outra stack mede cobertura pelo relatório que ele mesmo gera
def test_analyze_reads_coverage_from_declared_lcov_path(tmp_path: Path):
    """Um projeto Node/Go/Java gera lcov com a propria ferramenta; declarando
    [coverage] path, o Sentry mede cobertura alterada sem depender de coverage.py."""
    import subprocess
    _spec(tmp_path)
    (tmp_path / 'sentry.toml').write_text('[coverage]\npath = "coverage/lcov.info"\n', encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        subprocess.run(['git', *args], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.js').write_text('const a = 1;\n', encoding='utf-8')
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, capture_output=True)
    subprocess.run(['git', 'commit', '-qm', 'base'], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.js').write_text('const a = 1;\nconst b = 2;\nconst c = 3;\n', encoding='utf-8')
    coverage = tmp_path / 'coverage' / 'lcov.info'
    coverage.parent.mkdir()
    coverage.write_text('SF:app.js\nDA:1,1\nDA:2,1\nDA:3,0\nend_of_record\n', encoding='utf-8')

    run = analyze(tmp_path, run_tests=True)
    reported = run.configuration['coverage']
    assert reported['error'] is None
    # linhas 2 e 3 mudaram; a 2 executou e a 3 nao -> 50% do codigo alterado
    assert reported['changed_percent'] == 50.0

# cenario: projeto de outra stack roda a propria suite e tem veredito real
def test_analyze_runs_declared_suite_and_reaches_a_real_verdict(tmp_path: Path):
    """Fim a fim fora de Python: o projeto declara comando, junit e lcov; o
    Sentry executa, conta os testes e mede cobertura sem tocar em pytest."""
    import subprocess, sys
    _spec(tmp_path)
    runner = tmp_path / 'runner.py'
    runner.write_text('pass\n', encoding='utf-8')
    (tmp_path / 'sentry.toml').write_text(
        f'[test]\ncommand = "{sys.executable.replace(chr(92), "/")} {runner.as_posix()}"\n'
        'junit_xml = "reports/junit.xml"\n\n'
        '[coverage]\npath = "coverage/lcov.info"\n', encoding='utf-8')
    (tmp_path / 'reports').mkdir()
    (tmp_path / 'reports' / 'junit.xml').write_text(
        '<testsuite name="jest" tests="2" failures="0" errors="0" skipped="0"/>', encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        subprocess.run(['git', *args], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.js').write_text('const a = 1;\n', encoding='utf-8')
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, capture_output=True)
    subprocess.run(['git', 'commit', '-qm', 'base'], cwd=tmp_path, capture_output=True)
    (tmp_path / 'app.js').write_text('const a = 1;\nconst b = 2;\nconst c = 3;\n', encoding='utf-8')
    coverage = tmp_path / 'coverage' / 'lcov.info'
    coverage.parent.mkdir()
    coverage.write_text('SF:app.js\nDA:1,1\nDA:2,1\nDA:3,0\nend_of_record\n', encoding='utf-8')

    run = analyze(tmp_path, run_tests=True)
    assert run.configuration['test_execution']['passed'] == 2
    assert run.configuration['test_execution']['infrastructure_error'] is None
    assert run.configuration['coverage']['changed_percent'] == 50.0
    assert run.verdict.status.value != 'inconclusivo'

# cenario: classe nao aplicavel some dos achados e aparece como limitacao registrada
def test_analyze_not_applicable_class_is_not_a_finding_but_is_recorded(tmp_path: Path):
    """Sem justificativa aceita, o Sentry cobraria 4 classes de 'exclude' que nao
    fazem sentido para um parametro de configuracao. A justificativa remove o
    achado sem escondê-lo: ele fica registrado nas limitações do relatório."""
    directory = tmp_path / '.sentry' / 'specs' / 'demo'
    directory.mkdir(parents=True)
    (directory / 'CASES.md').write_text(
        "# Demo\n\n## Prompt\n\nDemo.\n\n"
        "## Campos\n\n- **exclude**: texto — lista de prefixos de diretorio\n\n"
        "## Caso: exclude filtra prefixo\n\n"
        "- **Requisito:** filtrar arquivos\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Dado:** exclude declarado\n- **Quando:** analyze roda\n"
        "- **Então:** o arquivo some do diff\n\n"
        "## Classes não aplicáveis\n\n"
        "- **exclude/tamanho-maximo-excedido**: é parâmetro de configuração, não entrada de usuário\n"
        "- **exclude/caracteres-especiais**: idem\n",
        encoding='utf-8',
    )
    run = analyze(tmp_path)
    findings_classes = {f.message for f in run.findings if f.rule == 'missing-equivalence-class'}
    assert not any('tamanho-maximo-excedido' in message for message in findings_classes)
    assert not any('caracteres-especiais' in message for message in findings_classes)
    assert any('vazio' in message for message in findings_classes)  # nao justificada, continua cobrada
    assert any('tamanho-maximo-excedido' in item for item in run.configuration['justified_classes'])

# cenario: nome do projeto vem do toml, com o diretorio como fallback
def test_analyze_usa_o_nome_declarado_no_toml(tmp_path: Path):
    """A chave [project] name existia no template do init mas nunca era lida:
    o relatorio sempre mostrava o nome do diretorio."""
    _spec(tmp_path)
    (tmp_path / 'sentry.toml').write_text('[project]\nname = "cobranca-api"\n', encoding='utf-8')
    assert analyze(tmp_path).project == 'cobranca-api'

def test_analyze_cai_no_nome_do_diretorio_sem_declaracao(tmp_path: Path):
    """Config sem a secao [project]: o nome do diretorio e' o fallback."""
    _spec(tmp_path)
    (tmp_path / 'sentry.toml').write_text('[specs]\npath = ".sentry/specs"\n', encoding='utf-8')
    assert analyze(tmp_path).project == tmp_path.name

def test_init_grava_o_nome_real_do_projeto_na_config(tmp_path: Path):
    """Um placeholder fixo no template faria todo projeto que nao editasse o
    sentry.toml reportar o mesmo nome."""
    from sentrytest.init_project import initialize_project
    initialize_project(tmp_path)
    assert f'name = "{tmp_path.name}"' in (tmp_path / 'sentry.toml').read_text(encoding='utf-8')
