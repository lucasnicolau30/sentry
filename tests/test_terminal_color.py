"""Cor ANSI no terminal: sempre sobre a cópia impressa, nunca sobre o que é
gravado em disco ou devolvido em `--json`. `NO_COLOR` desliga sempre;
`FORCE_COLOR` liga sempre, mesmo sem terminal interativo.
"""
from __future__ import annotations

from pathlib import Path

import pytest

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
    assert paint("✓", "green", enabled=True) + " Aprovado" in saida


# cenario: veredito aprovado com ressalvas sai amarelo
def test_veredito_aprovado_com_ressalvas_sai_amarelo():
    saida = colorize_report(_relatorio("aprovado com ressalvas"), enabled=True)
    assert paint("⚠", "yellow", enabled=True) + " Aprovado com ressalvas" in saida


# cenario: veredito reprovado sai vermelho
def test_veredito_reprovado_sai_vermelho():
    saida = colorize_report(_relatorio("reprovado"), enabled=True)
    assert paint("✗", "red", enabled=True) + " Reprovado" in saida


# cenario: veredito inconclusivo sai cinza
def test_veredito_inconclusivo_sai_cinza():
    saida = colorize_report(_relatorio("inconclusivo"), enabled=True)
    assert paint("○", "gray", enabled=True) + " Inconclusivo" in saida


# cenario: achado critico ou alto sai vermelho
def test_achado_critico_ou_alto_sai_vermelho():
    saida = colorize_report(_relatorio("reprovado", "- [crítica] `x` — y\n- [alta] `z` — w"), enabled=True)
    assert paint("✗", "red", enabled=True) + " crítica" in saida
    assert paint("✗", "red", enabled=True) + " alta" in saida


# cenario: achado de media severidade sai amarelo
def test_achado_de_media_severidade_sai_amarelo():
    saida = colorize_report(_relatorio("aprovado com ressalvas", "- [média] `x` — y"), enabled=True)
    assert paint("⚠", "yellow", enabled=True) + " média" in saida


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
    assert paint('✗', 'red', enabled=True) + ' erro:' in saida_com_erro

    (spec / 'CASES.md').write_text(
        "# Demo\n\n## Prompt\n\nx\n\n## Caso: um caso\n\n"
        "- **Requisito:** x\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Dado:** x\n- **Quando:** x\n- **Então:** x\n",
        encoding='utf-8')
    cli._check(tmp_path, 'demo')
    saida_ok = capsys.readouterr().out
    assert paint('✓', 'green', enabled=True) + ' Estrutura valida e catalogo de classes coberto.' in saida_ok


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


# cenario: uso de subcomando ganha titulo com tracinho e colore comando e flag
def test_usage_de_subcomando_usa_uso_em_portugues_e_colore_qualquer_flag(monkeypatch, capsys):
    monkeypatch.setenv('FORCE_COLOR', '1')
    monkeypatch.delenv('NO_COLOR', raising=False)

    with pytest.raises(SystemExit):
        cli.main(['new', '-h'])

    saida = capsys.readouterr().out
    assert 'USO' in saida
    assert 'usage:' not in saida
    assert paint('sentry', 'green', enabled=True) in saida
    assert paint('new', 'green', enabled=True) in saida
    for flag in ('-h', '--prompt', '--json'):
        assert paint(flag, 'green', enabled=True) in saida


# cenario: erro do argparse nao repete sentry comando antes de erro
def test_erro_do_argparse_nao_repete_sentry_comando_antes_de_erro(capsys):
    with pytest.raises(SystemExit):
        cli.main(['new'])

    saida = capsys.readouterr().err
    assert 'sentry new:' not in saida
    linha_de_erro = next(l for l in saida.splitlines() if 'erro:' in l)
    assert linha_de_erro.strip().startswith('erro:')


# cenario: subcomando sem name nem valor colorido ainda assim tem flag colorida
def test_subcomando_sem_positional_ainda_assim_tem_flag_colorida(monkeypatch, capsys):
    monkeypatch.setenv('FORCE_COLOR', '1')
    monkeypatch.delenv('NO_COLOR', raising=False)

    with pytest.raises(SystemExit):
        cli.main(['check', '-h'])

    saida = capsys.readouterr().out
    assert paint('-h', 'green', enabled=True) in saida


# cenario: argumento obrigatorio ausente vira mensagem em portugues
def test_argumento_obrigatorio_ausente_vira_mensagem_em_portugues(capsys):
    with pytest.raises(SystemExit) as info:
        cli.main(['new'])

    assert info.value.code == 2
    saida = capsys.readouterr().err
    assert 'argumento(s) obrigatório(s) ausente(s): name' in saida
    assert 'the following arguments are required' not in saida


# cenario: escolha invalida de subcomando vira mensagem em portugues
def test_escolha_invalida_de_subcomando_vira_mensagem_em_portugues(capsys):
    with pytest.raises(SystemExit):
        cli.main(['comando-que-nao-existe'])

    saida = capsys.readouterr().err
    assert 'escolha inválida' in saida
    assert 'invalid choice' not in saida


# cenario: escolha invalida nao repete a lista de opcoes que o USO ja mostra
def test_escolha_invalida_nao_repete_a_lista_de_opcoes(capsys):
    with pytest.raises(SystemExit):
        cli.main(['comando-que-nao-existe'])

    saida = capsys.readouterr().err
    linha_erro = next(l for l in saida.splitlines() if 'erro:' in l)
    assert "escolha inválida: 'comando-que-nao-existe'" in linha_erro
    assert 'opções' not in linha_erro


# cenario: mensagem de erro sem tradutor reconhecida cai no texto original
def test_mensagem_de_erro_sem_tradutor_reconhecida_cai_no_texto_original():
    from sentrytest.cli import _translate_argparse_message

    original = "some completely unmapped argparse message"
    assert _translate_argparse_message(original) == original


# cenario: palavra erro sai em vermelho na linha de erro
def test_palavra_erro_sai_em_vermelho_na_linha_de_erro(monkeypatch, capsys):
    monkeypatch.setenv('FORCE_COLOR', '1')
    monkeypatch.delenv('NO_COLOR', raising=False)

    with pytest.raises(SystemExit):
        cli.main(['new'])

    saida = capsys.readouterr().err
    assert paint('erro:', 'red', enabled=True) in saida


# cenario: subcomando sem subcomandos proprios usa titulo Argumentos
def test_subcomando_usa_titulo_argumentos_raiz_usa_titulo_comandos(capsys):
    with pytest.raises(SystemExit):
        cli.main(['new', '-h'])
    saida_subcomando = capsys.readouterr().out

    with pytest.raises(SystemExit):
        cli.main(['-h'])
    saida_raiz = capsys.readouterr().out

    assert 'ARGUMENTOS' in saida_subcomando
    assert 'COMANDOS' in saida_raiz
    assert 'ARGUMENTOS' not in saida_raiz
