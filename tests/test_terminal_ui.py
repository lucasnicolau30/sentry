"""Identidade visual da CLI além da cor: símbolo junto do veredito/severidade
(texto, sem gate de cor), spinner em stderr enquanto a análise roda, e uma
caixa de topo/rodapé no terminal que nunca chega ao arquivo salvo em disco.
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from sentrytest import __version__ as sentry_version
from sentrytest import cli
from sentrytest.adapters.terminal import (
    COMMAND_ICON, SEVERITY_SYMBOL, VERDICT_SYMBOL,
    Spinner, colorize_report, paint, render_checklist_item, render_dashboard, render_masthead,
    render_section, render_wordmark, spinner_frame, strip_ansi,
)
from sentrytest.application.analyze import analyze


def _relatorio(veredito: str, achados: str = "") -> str:
    return f"# Sentry Report\n\n- Veredito: **{veredito}** — texto\n\n## Achados\n\n{achados}"


# cenario: veredito aprovado tem o simbolo de check
def test_veredito_aprovado_tem_o_simbolo_de_check():
    assert VERDICT_SYMBOL["aprovado"] in colorize_report(_relatorio("aprovado"), enabled=False)


# cenario: veredito reprovado tem o simbolo de x
def test_veredito_reprovado_tem_o_simbolo_de_x():
    assert VERDICT_SYMBOL["reprovado"] in colorize_report(_relatorio("reprovado"), enabled=False)


# cenario: veredito inconclusivo tem o simbolo de circulo vazio
def test_veredito_inconclusivo_tem_o_simbolo_de_circulo_vazio():
    assert VERDICT_SYMBOL["inconclusivo"] in colorize_report(_relatorio("inconclusivo"), enabled=False)


# cenario: achado critico ou alto tem o simbolo de x
def test_achado_critico_ou_alto_tem_o_simbolo_de_x():
    saida = colorize_report(_relatorio("reprovado", "- [crítica] `x` — y\n- [alta] `z` — w"), enabled=False)
    assert saida.count(SEVERITY_SYMBOL["crítica"]) >= 2


# cenario: resumo compacto do veredito tambem traz o simbolo
def test_resumo_compacto_do_veredito_tambem_traz_o_simbolo(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)

    cli._run_and_report(tmp_path, None, False, None, print_report=False)
    saida = capsys.readouterr().out

    run = analyze(tmp_path, run_tests=False)
    assert VERDICT_SYMBOL[run.verdict.status.value] in saida


# cenario: sentry check troca o prefixo por simbolo em erro e sucesso
def test_sentry_check_troca_o_prefixo_por_simbolo_em_erro_e_sucesso(tmp_path: Path, monkeypatch, capsys):
    spec = tmp_path / ".sentry" / "specs" / "demo"
    spec.mkdir(parents=True)
    (spec / "CASES.md").write_text("# Demo\n\n## Prompt\n\nx\n", encoding="utf-8")

    cli._check(tmp_path, "demo")
    saida_com_erro = capsys.readouterr().out
    assert "[erro]" not in saida_com_erro
    assert SEVERITY_SYMBOL["crítica"] in saida_com_erro

    (spec / "CASES.md").write_text(
        "# Demo\n\n## Prompt\n\nx\n\n## Caso: um caso\n\n"
        "- **Requisito:** x\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Dado:** x\n- **Quando:** x\n- **Então:** x\n",
        encoding="utf-8")
    cli._check(tmp_path, "demo")
    saida_ok = capsys.readouterr().out
    assert VERDICT_SYMBOL["aprovado"] in saida_ok


class _Stream(io.StringIO):
    def __init__(self, tty: bool):
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_spinner_stream_sem_isatty_utilizavel_nao_anima():
    """Caminho defensivo, sem cenário declarado: um stream que levanta ao
    responder `isatty()` não pode travar o spinner -- a resposta segura é
    sempre 'sem tty', igual ao stream redirecionado."""
    class Quebrado(io.StringIO):
        def isatty(self):
            raise ValueError("closed stream")

    stream = Quebrado()
    with Spinner("Testando", stream=stream, interval=0.01):
        pass
    assert stream.getvalue() == "Testando…\n"


def test_spinner_frame_vem_sempre_do_mesmo_conjunto_fechado():
    """Função pura, sem thread nem tempo real: a espinha do spinner."""
    vistos = {spinner_frame(tick) for tick in range(20)}
    assert vistos <= set("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    assert len(vistos) == 10  # gira pelo conjunto inteiro em 10 ticks


# cenario: spinner anima em stderr quando e tty
def test_spinner_anima_em_stderr_quando_e_tty():
    stream = _Stream(tty=True)
    with Spinner("Testando", stream=stream, interval=0.01):
        time.sleep(0.05)
    saida = stream.getvalue()
    assert "\r" in saida
    assert spinner_frame(0) in saida


# cenario: spinner nao anima fora de terminal interativo
def test_spinner_nao_anima_fora_de_terminal_interativo():
    stream = _Stream(tty=False)
    with Spinner("Testando", stream=stream, interval=0.01):
        pass
    saida = stream.getvalue()
    assert saida == "Testando…\n"
    assert "\r" not in saida
    assert spinner_frame(0) not in saida


# cenario: masthead e dashboard nunca aparecem no relatorio salvo em disco
def test_masthead_e_dashboard_nunca_aparecem_no_relatorio_salvo_em_disco(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)

    cli._run_and_report(tmp_path, None, False, None, print_report=True)

    impresso = capsys.readouterr().out
    assert "┌" in impresso and "└" in impresso  # masthead/dashboard na tela

    salvo = (tmp_path / ".sentry" / "reports" / "latest.md").read_text(encoding="utf-8")
    assert "┌" not in salvo and "└" not in salvo and "│" not in salvo
    assert strip_ansi(salvo) == salvo


# cenario: dashboard traz testes cobertura e achados por severidade
def test_dashboard_traz_testes_cobertura_e_achados_por_severidade():
    payload = {"data": {
        "verdict": {"status": "aprovado com ressalvas"},
        "findings": [{"severity": "alta"}, {"severity": "alta"}, {"severity": "média"}],
        "configuration": {
            "test_execution": {"passed": 40, "failed": 2},
            "coverage": {"global_percent": 87.5},
        },
    }}
    saida = render_dashboard(payload)
    assert "40" in saida and "2" in saida  # testes
    assert "87,50%" in saida  # cobertura, virgula pt-BR
    assert "alta=2" in saida and "média=1" in saida  # achados por severidade


# cenario: icone do comando prefixa a primeira linha impressa
def test_icone_do_comando_prefixa_a_primeira_linha_impressa(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["clear"])

    primeira_linha = capsys.readouterr().out.splitlines()[0]
    assert primeira_linha.startswith(COMMAND_ICON["clear"])


# cenario: sentry init mostra o wordmark antes do texto de conclusao
def test_sentry_init_mostra_o_wordmark_antes_do_texto_de_conclusao(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    assert "█" in saida
    assert "Projeto Sentry inicializado." in saida
    assert saida.index("█") < saida.index("Projeto Sentry inicializado.")


# cenario: conclusao do init ganha um simbolo antes do texto
def test_conclusao_do_init_ganha_um_simbolo_antes_do_texto(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    linha = next(l for l in saida.splitlines() if "Projeto Sentry inicializado." in l)
    assert linha.strip().startswith(VERDICT_SYMBOL["aprovado"])


# cenario: conclusao do init nao pula linha antes nem depois do bloco
def test_conclusao_do_init_nao_pula_linha_antes_nem_depois_do_bloco(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    linhas = capsys.readouterr().out.splitlines()
    indice = next(i for i, l in enumerate(linhas) if "Projeto Sentry inicializado." in l)
    assert linhas[indice - 1].strip() != ""
    assert indice == len(linhas) - 1


# cenario: python entra como detalhe do item de ambiente, dentro do checklist
def test_python_entra_como_detalhe_do_item_de_ambiente(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    assert "python 3." in saida
    assert saida.index("INICIALIZANDO") < saida.index("python 3.") < saida.index("sentry-test")


# cenario: sentry -h mostra o wordmark antes do texto de ajuda
def test_sentry_h_mostra_o_wordmark_antes_do_texto_de_ajuda(capsys):
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    assert "█" in saida
    assert saida.index("█") < saida.index("usage:")

    with pytest.raises(SystemExit):
        cli.main(["init", "-h"])
    saida_subcomando = capsys.readouterr().out
    assert "█" not in saida_subcomando


# cenario: nenhum outro comando repete o wordmark
def test_nenhum_outro_comando_repete_o_wordmark(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()  # descarta a saida do init

    cli.main(["check"])

    assert "█" not in capsys.readouterr().out


# cenario: sentry init mostra o checklist dos passos com check verde
def test_sentry_init_mostra_o_checklist_dos_passos_com_check_verde(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    for item in ("Verificando ambiente do projeto", "Criando .sentry/",
                 "Gerando sentry.toml e .gitignore", "Instalando skill Claude",
                 "Gravando AGENT-SENTRY.md"):
        assert item in saida
        linha = next(l for l in saida.splitlines() if item in l)
        assert linha.startswith(VERDICT_SYMBOL["aprovado"])


# cenario: checklist do init mostra todas as categorias mesmo em reexecucao
def test_checklist_do_init_mostra_todas_as_categorias_mesmo_em_reexecucao(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()  # descarta a primeira execucao

    cli.main(["init"])

    saida = capsys.readouterr().out
    for item in ("Diretório .sentry/", "Config sentry.toml e .gitignore", "AGENT-SENTRY.md"):
        assert item in saida
    assert "presente" not in saida


# cenario: init tem um unico cabecalho verde com tracinho antes e depois
def test_init_tem_um_unico_cabecalho_verde_com_tracinho(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    assert saida.count("INICIALIZANDO") == 1
    assert "DEPENDÊNCIAS" not in saida
    assert "─" in saida
    assert saida.index("INICIALIZANDO") < saida.index("pytest") < saida.index("Criando .sentry/")


# cenario: tracinho do cabecalho de secao respeita a largura do terminal
def test_tracinho_do_cabecalho_respeita_largura_do_terminal(monkeypatch):
    monkeypatch.setattr(shutil, 'get_terminal_size', lambda fallback=(0, 0): os.terminal_size((40, 24)))

    linha = strip_ansi(render_section("Inicializando", "─", enabled=True))

    assert len(linha) <= 40


# cenario: sentry init nao termina com nenhuma caixa de proximo passo
def test_sentry_init_nao_termina_com_nenhuma_caixa_de_proximo_passo(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    assert "PRÓXIMO PASSO" not in saida
    assert "sentry new" not in saida


def _git(root: Path, *args: str):
    return subprocess.run(["git", *args], cwd=root, capture_output=True)


# cenario: versao aparece no pezinho direito do wordmark e em chip nas dependencias
def test_versao_aparece_no_pezinho_do_wordmark_e_em_chip_nas_dependencias(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    assert f"v{sentry_version}" in saida  # pezinho direito do wordmark
    assert f"sentry-test {sentry_version}" in saida  # chip junto das dependencias
    assert "ENGINE ACTIVE" not in saida  # cabecalho separado foi removido


# cenario: linha do checklist mostra a badge alinhada a direita por categoria
def test_linha_do_checklist_mostra_a_badge_alinhada_a_direita_por_categoria():
    linha = render_checklist_item("Criando .sentry/ (reports)", badge="created", badge_color="blue", enabled=False)

    assert linha.rstrip().endswith("created")
    assert "Criando .sentry/ (reports)" in linha


# cenario: detalhe do ambiente mostra a versao real de cada dependencia
def test_detalhe_do_ambiente_mostra_a_versao_real_de_cada_dependencia(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "check_dependencies", lambda root: {
        "pytest": {"installed": True, "version": "8.1.1"},
        "coverage": {"installed": True, "version": "7.4.4"},
    })

    cli.main(["init"])

    saida = capsys.readouterr().out
    assert "8.1.1" in saida
    assert "7.4.4" in saida


# cenario: linha de git aparece com branch e status quando ha repositorio
def test_linha_de_git_aparece_com_branch_e_status_quando_ha_repositorio(tmp_path: Path, monkeypatch, capsys):
    """`init` recem-rodado sempre mostra `sujo` -- ele proprio acabou de
    escrever `.sentry/specs`, `sentry.toml`, `AGENT-SENTRY.md`, que ninguem
    commitou ainda. A arvore so fica `limpo` depois que esses artefatos
    entram no commit; uma segunda chamada (idempotente, sem nada novo)
    prova isso."""
    monkeypatch.chdir(tmp_path)
    for args in (("init",), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
        _git(tmp_path, *args)
    (tmp_path / "arquivo.txt").write_text("x", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")

    cli.main(["init"])
    saida = capsys.readouterr().out
    assert "git repo" in saida
    assert "sujo" in saida

    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "sentry scaffolding")
    cli.main(["init"])
    saida = capsys.readouterr().out
    assert "limpo" in saida


# cenario: linha de git some fora de repositorio Git
def test_linha_de_git_some_fora_de_repositorio_git(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    assert "git repo" not in saida


# cenario: wordmark grande aparece no topo do init
def test_wordmark_grande_aparece_no_topo_do_init(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    linhas = saida.splitlines()
    wordmark_linhas = linhas[:6]
    assert "█" in "\n".join(wordmark_linhas)  # a fonte figlet usa bloco cheio na maior parte
    assert not any("┌" in linha or "└" in linha for linha in wordmark_linhas)  # sem moldura
    assert saida.index(linhas[5]) < saida.index("INICIALIZANDO")


# cenario: wordmark usa tres faixas de verde
def test_wordmark_usa_tres_faixas_de_verde():
    wordmark = render_wordmark(enabled=True)

    linhas = wordmark.splitlines()
    assert len(linhas) == 6
    codigo_do_topo = linhas[0].split("m", 1)[0]
    codigo_do_meio = linhas[2].split("m", 1)[0]
    codigo_de_baixo = linhas[5].split("m", 1)[0]
    assert len({codigo_do_topo, codigo_do_meio, codigo_de_baixo}) == 3
    assert codigo_do_topo == "\x1b[92"  # verde vivo
    assert codigo_de_baixo == "\x1b[2;32"  # verde apagado


# cenario: wordmark sem cor fica so' com o texto puro
def test_wordmark_sem_cor_fica_so_com_o_texto_puro():
    wordmark = render_wordmark(enabled=False)

    assert strip_ansi(wordmark) == wordmark
    assert "SENTRY" not in wordmark  # e' a fonte figlet, nao o texto literal
    assert "█" in wordmark
