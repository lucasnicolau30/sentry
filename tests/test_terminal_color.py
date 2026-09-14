"""Cor ANSI no terminal: sempre sobre a cópia impressa, nunca sobre o que é
gravado em disco ou devolvido em `--json`. `NO_COLOR` desliga sempre;
`FORCE_COLOR` liga sempre, mesmo sem terminal interativo.
"""
from __future__ import annotations

from pathlib import Path

from sentrytest import cli
from sentrytest.adapters.terminal import colorize_report, paint, strip_ansi, supports_color


class _Stream:
    def __init__(self, is_tty: bool):
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


# cenario: cor desabilitada fora de terminal interativo
def test_cor_desabilitada_fora_de_terminal_interativo(monkeypatch):
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.delenv('FORCE_COLOR', raising=False)
    assert supports_color(_Stream(False)) is False


# cenario: NO_COLOR desabilita mesmo em terminal interativo
def test_no_color_desabilita_mesmo_em_terminal_interativo(monkeypatch):
    monkeypatch.setenv('NO_COLOR', '1')
    monkeypatch.delenv('FORCE_COLOR', raising=False)
    assert supports_color(_Stream(True)) is False


# cenario: FORCE_COLOR habilita mesmo sem terminal interativo
def test_force_color_habilita_mesmo_sem_terminal_interativo(monkeypatch):
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.setenv('FORCE_COLOR', '1')
    assert supports_color(_Stream(False)) is True


def test_stream_sem_isatty_utilizavel_nao_habilita_cor(monkeypatch):
    """Caminho defensivo, sem cenário declarado: um stream que não sabe responder
    `isatty()` (ou levanta ao tentar) não pode travar a decisão de cor -- a
    resposta segura é sempre 'sem cor', nunca uma exceção subindo até o usuário."""
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.delenv('FORCE_COLOR', raising=False)

    class Quebrado:
        def isatty(self):
            raise ValueError("closed stream")

    assert supports_color(Quebrado()) is False


def _relatorio(veredito: str, achados: str = "") -> str:
    return f"# Sentry Report\n\n- Veredito: **{veredito}** — texto\n\n## Achados\n\n{achados}"


# cenario: veredito aprovado sai verde
def test_veredito_aprovado_sai_verde():
    saida = colorize_report(_relatorio("aprovado"), enabled=True)
    assert paint("aprovado", "green", enabled=True) in saida


# cenario: veredito aprovado com ressalvas sai amarelo
def test_veredito_aprovado_com_ressalvas_sai_amarelo():
    saida = colorize_report(_relatorio("aprovado com ressalvas"), enabled=True)
    assert paint("aprovado com ressalvas", "yellow", enabled=True) in saida


# cenario: veredito reprovado sai vermelho
def test_veredito_reprovado_sai_vermelho():
    saida = colorize_report(_relatorio("reprovado"), enabled=True)
    assert paint("reprovado", "red", enabled=True) in saida


# cenario: veredito inconclusivo sai cinza
def test_veredito_inconclusivo_sai_cinza():
    saida = colorize_report(_relatorio("inconclusivo"), enabled=True)
    assert paint("inconclusivo", "gray", enabled=True) in saida


# cenario: achado critico ou alto sai vermelho
def test_achado_critico_ou_alto_sai_vermelho():
    saida = colorize_report(_relatorio("reprovado", "- [crítica] `x` — y\n- [alta] `z` — w"), enabled=True)
    assert paint("crítica", "red", enabled=True) in saida
    assert paint("alta", "red", enabled=True) in saida


# cenario: achado de media severidade sai amarelo
def test_achado_de_media_severidade_sai_amarelo():
    saida = colorize_report(_relatorio("aprovado com ressalvas", "- [média] `x` — y"), enabled=True)
    assert paint("média", "yellow", enabled=True) in saida


def test_cor_desabilitada_ainda_assim_nao_tem_codigo_ansi():
    """Controle: sem cor habilitada, os símbolos ainda aparecem (são texto, não
    código de escape), mas nenhum ANSI entra na saída."""
    original = _relatorio("reprovado", "- [crítica] `x` — y")
    saida = colorize_report(original, enabled=False)
    assert "✗" in saida  # simbolo do veredito reprovado
    assert strip_ansi(saida) == saida


# cenario: relatorio salvo em disco nunca contem codigo ANSI
def test_relatorio_salvo_em_disco_nunca_contem_codigo_ansi(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv('FORCE_COLOR', '1')
    monkeypatch.delenv('NO_COLOR', raising=False)

    cli._run_and_report(tmp_path, None, False, None, print_report=True)

    impresso = capsys.readouterr().out
    assert '\x1b[' in impresso  # a copia no terminal saiu colorida
    salvo = (tmp_path / '.sentry' / 'reports' / 'latest.md').read_text(encoding='utf-8')
    assert '\x1b[' not in salvo
    assert strip_ansi(salvo) == salvo


# cenario: sentry check colore erro de vermelho e sucesso de verde
def test_sentry_check_colore_erro_de_vermelho_e_sucesso_de_verde(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv('FORCE_COLOR', '1')
    monkeypatch.delenv('NO_COLOR', raising=False)
    spec = tmp_path / '.sentry' / 'specs' / 'demo'
    spec.mkdir(parents=True)
    (spec / 'CASES.md').write_text("# Demo\n\n## Prompt\n\nx\n", encoding='utf-8')  # sem nenhum caso: erro estrutural

    cli._check(tmp_path, 'demo')
    saida_com_erro = capsys.readouterr().out
    assert paint('✗ erro:', 'red', enabled=True) in saida_com_erro

    (spec / 'CASES.md').write_text(
        "# Demo\n\n## Prompt\n\nx\n\n## Caso: um caso\n\n"
        "- **Requisito:** x\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Dado:** x\n- **Quando:** x\n- **Então:** x\n",
        encoding='utf-8')
    cli._check(tmp_path, 'demo')
    saida_ok = capsys.readouterr().out
    assert paint('Estrutura valida e catalogo de classes coberto.', 'green', enabled=True) in saida_ok


# cenario: dependencia ausente vira vermelho e presente vira verde no detalhe do ambiente
def test_sentry_init_colore_dependencia_ausente_de_vermelho_e_presente_de_verde(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv('FORCE_COLOR', '1')
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, 'check_dependencies', lambda root: {
        'pytest': {'installed': True, 'version': '8.1.1'},
        'coverage': {'installed': False, 'version': None},
    })

    cli.main(['init'])

    saida = capsys.readouterr().out
    linha = next(l for l in saida.splitlines() if 'Verificando ambiente do projeto' in l)
    assert 'pytest 8.1.1' in linha and 'coverage ausente' in linha
    assert paint('X', 'red', enabled=True).split('X')[0] in linha  # a linha inteira sai vermelha

    monkeypatch.setattr(cli, 'check_dependencies', lambda root: {
        'pytest': {'installed': True, 'version': '8.1.1'},
        'coverage': {'installed': True, 'version': '7.4.4'},
    })
    capsys.readouterr()

    cli.main(['init'])

    saida = capsys.readouterr().out
    linha = next(l for l in saida.splitlines() if 'Verificando ambiente do projeto' in l)
    assert 'pytest 8.1.1' in linha and 'coverage 7.4.4' in linha
    assert paint('X', 'green', enabled=True).split('X')[0] in linha  # a linha inteira sai verde


# cenario: checklist do init em reexecucao nao mostra nenhuma badge
def test_checklist_do_init_em_reexecucao_nao_mostra_nenhuma_badge(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv('FORCE_COLOR', '1')
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.chdir(tmp_path)
    cli.main(['init'])
    capsys.readouterr()  # descarta a primeira execucao

    cli.main(['init'])

    saida = capsys.readouterr().out
    assert 'presente' not in saida
