"""`sentry review`: seis passos viram um.

A friccao e' o que decide se a avaliacao vira habito ou cerimonia. Enquanto obter um
veredito custava `new`, preencher, `check`, `run`, `report` e ler o codigo de saida, ela
so acontecia quando alguem lembrava.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from sentrytest.cli import EXIT_OK, EXIT_REJECTED, EXIT_WARNING, main

APP = "def somar(a, b):\n    return a + b\n"
TESTE = "from app import somar\n\n\ndef test_soma_retorna_o_total():\n    assert somar(1, 2) == 3\n"

CASES = """# Demo

## Prompt

Somar dois numeros.

## Caso: soma retorna o total

- **Requisito:** somar dois numeros
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** dois inteiros validos
- **Quando:** somar e chamado
- **Então:** retorna a soma
"""

def _git(root: Path, *args: str):
    return subprocess.run(['git', *args], cwd=root, capture_output=True)

def _projeto(root: Path, cases: str | None = CASES) -> None:
    (root / 'tests').mkdir()
    (root / 'app.py').write_text(APP, encoding='utf-8')
    (root / 'tests' / 'test_app.py').write_text(TESTE, encoding='utf-8')
    if cases is not None:
        spec = root / '.sentry' / 'specs' / 'demo'
        spec.mkdir(parents=True)
        (spec / 'CASES.md').write_text(cases, encoding='utf-8')
    for args in (('init',), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
        _git(root, *args)
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'base')
    (root / 'app.py').write_text(APP + "\n\ndef dobrar(a):\n    return a * 2\n", encoding='utf-8')

# cenario: review encadeia check run e report num comando
def test_review_encadeia_check_run_e_report(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _projeto(tmp_path)
    main(['review'])
    saida = capsys.readouterr().out
    assert 'Estrutura valida e catalogo de classes coberto.' in saida   # o check
    assert '# Sentry Report' in saida                                    # o report
    assert '## Dimensões de cobertura' in saida
    # O check vem antes do relatorio: spec quebrada precisa aparecer antes do veredito.
    assert saida.index('Estrutura valida') < saida.index('# Sentry Report')

# cenario: review devolve o codigo de saida do veredito
def test_review_devolve_o_codigo_de_saida_do_veredito(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _projeto(tmp_path)
    assert main(['review']) in (EXIT_OK, EXIT_WARNING)
    assert '- Veredito:' in capsys.readouterr().out

# cenario: review roda em repositorio sem sentry e sem toml
def test_review_roda_em_repositorio_sem_sentry_e_sem_toml(tmp_path: Path, monkeypatch, capsys):
    """O criterio de aceite da fase: nenhum preparo, e ainda assim relatorio util."""
    monkeypatch.chdir(tmp_path)
    _projeto(tmp_path, cases=None)
    assert not (tmp_path / 'sentry.toml').exists()
    codigo = main(['review'])
    saida = capsys.readouterr().out
    assert 'Nenhuma spec declarada' in saida
    assert '# Sentry Report' in saida
    assert 'Cobertura alterada' in saida
    assert codigo in (EXIT_OK, EXIT_WARNING)

# cenario: review com CASES.md invalido sai reprovado
def test_review_com_cases_invalido_sai_reprovado(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _projeto(tmp_path, cases="## Caso: sem titulo nem prompt\n")
    assert main(['review']) == EXIT_REJECTED
    saida = capsys.readouterr().out
    assert 'erro:' in saida
    assert 'case-spec-invalid' in saida

def test_review_sem_testes_nao_executa_a_suite(tmp_path: Path, monkeypatch, capsys):
    """`--no-tests` existe para o diff e a conferencia estrutural, sem pagar a suite."""
    monkeypatch.chdir(tmp_path)
    _projeto(tmp_path)
    main(['review', '--no-tests'])
    assert '### Execução de testes' not in capsys.readouterr().out
