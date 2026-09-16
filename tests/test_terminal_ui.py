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

    cli.main(["history"])

    primeira_linha = capsys.readouterr().out.splitlines()[0]
    assert primeira_linha.startswith(COMMAND_ICON["history"])


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
    assert saida.index("█") < saida.index("COMANDOS")

    with pytest.raises(SystemExit):
        cli.main(["check", "-h"])
    saida_subcomando = capsys.readouterr().out
    assert "█" in saida_subcomando
    assert saida_subcomando.index("█") < saida_subcomando.index("USO")


# cenario: sentry --version colore o numero da versao em verde, pontos inclusos
def test_sentry_version_colore_o_numero_em_verde(monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    saida = capsys.readouterr().out.strip()
    assert saida == paint(sentry_version, "green", enabled=True)


# cenario: sentry -h tem cabecalhos com tracinho, igual as secoes do init
def test_sentry_h_tem_cabecalhos_com_tracinho(capsys):
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    assert "positional arguments:" not in saida
    assert "options:" not in saida
    assert "COMANDOS" in saida
    assert "USO" in saida
    assert "─" in saida


# cenario: sentry -h colore o nome de cada comando e cada flag em verde
def test_sentry_h_colore_o_nome_de_cada_comando_e_cada_flag_em_verde(monkeypatch, capsys):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    for name in ("init", "new", "check", "run", "review", "watch",
                 "status", "context", "report", "history", "clear"):
        assert paint(name, "green", enabled=True) in saida
    for flag in ("-h", "--help", "--version"):
        assert paint(flag, "green", enabled=True) in saida


# cenario: sentry -h nao repete a listagem compacta de comandos
def test_sentry_h_nao_repete_a_listagem_compacta_de_comandos(capsys):
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    assert "{init,new,check,run,review,watch,status,context,report,history,clear}" not in saida


# cenario: sentry -h nao repete usage nem descricao antes do wordmark bastar
def test_sentry_h_nao_repete_usage_nem_descricao(capsys):
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    assert "usage:" not in saida
    assert "Deriva a matriz de casos de teste" not in saida
    linhas = saida.splitlines()
    indice_versao = next(i for i, l in enumerate(linhas) if sentry_version in l)
    indice_uso = next(i for i, l in enumerate(linhas) if "USO" in l)
    indice_comandos = next(i for i, l in enumerate(linhas) if "COMANDOS" in l)
    assert linhas[indice_versao + 1].strip() == ""  # uma linha em branco antes do USO...
    assert indice_uso == indice_versao + 2           # ...e so' uma
    assert linhas[indice_comandos - 1].strip() == ""  # uma linha em branco antes do COMANDOS...
    assert linhas[indice_comandos - 2].strip() != ""  # ...e so' uma


# cenario: comandos e USO tem a mesma indentacao
def test_comandos_e_uso_tem_a_mesma_indentacao(capsys):
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    linha_init = next(l for l in saida.splitlines() if l.strip().startswith("init"))
    linha_sentry = next(l for l in saida.splitlines() if l.strip().startswith("sentry ["))
    recuo = lambda linha: len(linha) - len(linha.lstrip(" "))
    assert recuo(linha_init) == recuo(linha_sentry)


# cenario: argumentos e uso de um subcomando tem a mesma indentacao
def test_argumentos_e_uso_de_subcomando_tem_a_mesma_indentacao(capsys):
    recuo = lambda linha: len(linha) - len(linha.lstrip(" "))

    with pytest.raises(SystemExit):
        cli.main(["check", "-h"])
    saida = capsys.readouterr().out
    linha_slug = next(l for l in saida.splitlines() if l.strip() == "slug")
    linha_uso = next(l for l in saida.splitlines() if l.strip() == "sentry check [slug]")
    assert recuo(linha_slug) == recuo(linha_uso)


# cenario: bloco USO e linha de erro tem a mesma margem que as outras secoes
def test_bloco_uso_e_linha_de_erro_tem_a_mesma_margem(capsys):
    recuo = lambda linha: len(linha) - len(linha.lstrip(" "))

    with pytest.raises(SystemExit):
        cli.main(["check", "-h"])
    saida = capsys.readouterr().out
    linha_uso = next(l for l in saida.splitlines() if l.strip() == "sentry check [slug]")
    linha_flag_uso = next(l for l in saida.splitlines() if l.strip().startswith("[-h, --help]"))
    assert recuo(linha_flag_uso) > recuo(linha_uso)

    with pytest.raises(SystemExit):
        cli.main(["new"])
    saida = capsys.readouterr().err
    linha_erro = next(l for l in saida.splitlines() if "erro:" in l)
    linha_uso_new = next(l for l in saida.splitlines() if l.strip() == "sentry new name")
    assert recuo(linha_erro) == recuo(linha_uso_new)


# cenario: -h e --version tem texto de ajuda em portugues
def test_h_e_version_tem_texto_de_ajuda_em_portugues(capsys):
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    assert "mostra esta mensagem de ajuda e sai" in saida
    assert "mostra a versão do programa e sai" in saida
    assert "show this help message and exit" not in saida
    assert "show program's version number and exit" not in saida

    with pytest.raises(SystemExit):
        cli.main(["init", "-h"])
    saida_subcomando = capsys.readouterr().out
    assert "mostra esta mensagem de ajuda e sai" in saida_subcomando
    assert "show this help message and exit" not in saida_subcomando


# cenario: comandos de rotina nao repetem o wordmark
def test_nenhum_outro_comando_repete_o_wordmark(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()  # descarta a saida do init

    cli.main(["history"])

    assert "█" not in capsys.readouterr().out


# cenario: sentry new mostra o wordmark antes do restante da saida
def test_sentry_new_mostra_o_wordmark_antes_do_restante_da_saida(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()

    cli.main(["new", "nome da feature"])

    saida = capsys.readouterr().out
    assert "█" in saida
    assert "Spec criada em" in saida
    assert saida.index("█") < saida.index("Spec criada em")


# cenario: sentry new --json nao mostra o wordmark
def test_sentry_new_json_nao_mostra_o_wordmark(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()

    cli.main(["new", "nome da feature", "--json"])

    assert "█" not in capsys.readouterr().out


# cenario: sentry new sem o name obrigatorio tambem mostra o wordmark
def test_sentry_new_sem_name_tambem_mostra_o_wordmark(capsys):
    with pytest.raises(SystemExit):
        cli.main(["new"])

    saida = capsys.readouterr().err
    assert "█" in saida
    assert "USO" in saida
    assert saida.index("█") < saida.index("USO")


# cenario: bloco USO mostra um token por linha em vez de tudo numa linha so
def test_bloco_uso_mostra_um_token_por_linha(capsys):
    with pytest.raises(SystemExit):
        cli.main(["run", "-h"])

    saida = capsys.readouterr().out
    linhas = saida.splitlines()
    linha_nome = next(l for l in linhas if l.strip().startswith("sentry run"))
    assert linha_nome.strip().startswith("sentry run [-h, --help]")
    indice = linhas.index(linha_nome)
    assert linhas[indice + 1].strip() == "[--spec SPEC]"
    assert linhas[indice + 2].strip() == "[--run-tests]"
    assert linhas[indice + 3].strip().startswith("[--base REF]")


# cenario: posicional vem primeiro no USO, depois -h, depois o resto
def test_posicional_vem_primeiro_no_uso_depois_h_depois_o_resto(capsys):
    with pytest.raises(SystemExit):
        cli.main(["new", "-h"])

    saida = capsys.readouterr().out
    assert saida.index("sentry new name") < saida.index("[-h, --help]") < saida.index("[--prompt PROMPT]") < saida.index("[--json]")


# cenario: sentry new -h tambem mostra o wordmark
def test_sentry_new_h_tambem_mostra_o_wordmark(capsys):
    with pytest.raises(SystemExit):
        cli.main(["new", "-h"])

    saida = capsys.readouterr().out
    assert "█" in saida
    assert "USO" in saida
    assert saida.index("█") < saida.index("USO")


# cenario: erro de qualquer subcomando tambem ganha o wordmark
def test_erro_de_qualquer_subcomando_tambem_ganha_o_wordmark(capsys):
    with pytest.raises(SystemExit):
        cli.main(["check", "--bogus"])

    saida = capsys.readouterr().err
    assert "█" in saida
    assert saida.index("█") < saida.index("USO")


# cenario: sentry init -h tambem mostra o wordmark
def test_sentry_init_h_tambem_mostra_o_wordmark(capsys):
    with pytest.raises(SystemExit):
        cli.main(["init", "-h"])
    saida = capsys.readouterr().out
    assert "█" in saida
    assert "USO" in saida
    assert saida.index("█") < saida.index("USO")


# cenario: token de -h no USO mostra as duas formas da flag
def test_token_de_h_no_uso_mostra_as_duas_formas_da_flag(capsys):
    with pytest.raises(SystemExit):
        cli.main(["init", "-h"])
    assert "[-h, --help]" in capsys.readouterr().out

    with pytest.raises(SystemExit):
        cli.main(["new", "-h"])
    assert "[-h, --help]" in capsys.readouterr().out

    with pytest.raises(SystemExit):
        cli.main(["--bogus"])
    saida = capsys.readouterr().err
    assert "[-h, --help]" in saida
    assert "[-h]" not in saida


# cenario: sentry init -h funde a descricao de cada flag no USO e some com EXTRAS
def test_sentry_init_h_funde_descricao_no_uso_e_some_com_extras(capsys):
    for argv in (["init", "-h"], ["init", "--help"]):
        with pytest.raises(SystemExit):
            cli.main(argv)
        saida = capsys.readouterr().out
        assert "[-h, --help]" in saida
        assert "mostra esta mensagem de ajuda e sai" in saida
        assert "[--install]" in saida
        assert "instala as dependências ausentes" in saida
        assert "EXTRAS" not in saida
        # a descricao esta na MESMA linha do token, nao numa secao separada
        linha_install = next(l for l in saida.splitlines() if "[--install]" in l)
        assert "instala as dependências ausentes" in linha_install


# cenario: sentry new -h funde a descricao no USO mantendo ARGUMENTOS
def test_sentry_new_h_funde_descricao_no_uso_mantendo_argumentos(capsys):
    for argv in (["new", "-h"], ["new", "--help"]):
        with pytest.raises(SystemExit):
            cli.main(argv)
        saida = capsys.readouterr().out
        assert "[-h, --help]" in saida
        assert "mostra esta mensagem de ajuda e sai" in saida
        assert "[--prompt PROMPT]" in saida
        assert "o pedido em texto livre; se omitido, usa o nome" in saida
        assert "EXTRAS" not in saida
        linha_prompt = next(l for l in saida.splitlines() if "[--prompt PROMPT]" in l)
        assert "o pedido em texto livre; se omitido, usa o nome" in linha_prompt
        # ARGUMENTOS continua existindo -- so' EXTRAS some, nao a secao de posicional
        assert "ARGUMENTOS" in saida
        assert "nome da funcionalidade; vira o slug da spec" in saida


# cenario: fusao de USO e EXTRAS vale em todo comando, raiz inclusive
def test_fusao_de_uso_e_extras_vale_em_todo_comando(capsys):
    for argv in (["check", "-h"], ["clear", "-h"], ["run", "-h"], ["review", "-h"],
                 ["watch", "-h"], ["status", "-h"], ["context", "-h"], ["report", "-h"],
                 ["history", "-h"]):
        with pytest.raises(SystemExit):
            cli.main(argv)
        saida = capsys.readouterr().out
        assert "EXTRAS" not in saida
        assert "[-h, --help]" in saida

    with pytest.raises(SystemExit):
        cli.main(["-h"])
    saida = capsys.readouterr().out
    assert "EXTRAS" not in saida
    linha_h = next(l for l in saida.splitlines() if l.strip().startswith("[-h, --help]"))
    assert "mostra esta mensagem de ajuda e sai" in linha_h


# cenario: erro de sentry init e sentry new nao funde USO com EXTRAS
def test_erro_de_init_e_new_nao_funde_uso_com_extras(capsys):
    with pytest.raises(SystemExit):
        cli.main(["init", "--bogus"])
    saida = capsys.readouterr().err
    assert "[-h, --help]" in saida
    assert "[-h, --help]  mostra esta mensagem de ajuda e sai" not in saida
    assert "EXTRAS" not in saida

    with pytest.raises(SystemExit):
        cli.main(["new"])
    saida = capsys.readouterr().err
    assert "[-h, --help]" in saida
    assert "[-h, --help]       mostra esta mensagem de ajuda e sai" not in saida
    assert "EXTRAS" not in saida


# cenario: argumento sobrando num subcomando usa o usage do proprio subcomando
def test_argumento_sobrando_usa_o_usage_do_proprio_subcomando(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()

    with pytest.raises(SystemExit):
        cli.main(["new", "nome da feature", "--json", "name"])

    saida = capsys.readouterr().err
    assert "sentry new name" in saida
    assert "{init,new,check" not in saida
    assert "█" in saida


# cenario: argumento sobrando sem subcomando escolhido usa o usage da raiz
def test_argumento_sobrando_sem_subcomando_usa_o_usage_da_raiz(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--bogus"])

    saida = capsys.readouterr().err
    assert "[init, new, check" in saida


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


# cenario: linha do checklist nao mostra nenhuma badge por categoria
def test_linha_do_checklist_nao_mostra_nenhuma_badge_por_categoria(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.main(["init"])

    saida = capsys.readouterr().out
    for rotulo in ("created", "written", "installed", "ready"):
        assert rotulo not in saida


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
