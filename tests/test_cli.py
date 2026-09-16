from pathlib import Path

import pytest

from sentrytest import __version__
from sentrytest.cli import main
from sentrytest.adapters.terminal import paint


def test_cli_returns_success_without_arguments() -> None:
    assert main([]) == 0

# cenario: sentry sem argumento equivale a sentry -h
def test_sentry_sem_argumento_equivale_a_sentry_h(capsys) -> None:
    assert main([]) == 0
    saida = capsys.readouterr().out
    assert "█" in saida
    assert "COMANDOS" in saida
    assert "USO" in saida

# cenario: erro da raiz sem subcomando tambem mostra o wordmark
def test_erro_da_raiz_sem_subcomando_tambem_mostra_o_wordmark(capsys) -> None:
    with pytest.raises(SystemExit):
        main(["comando-que-nao-existe"])
    saida = capsys.readouterr().err
    assert "█" in saida

    with pytest.raises(SystemExit):
        main(["--bogus"])
    saida = capsys.readouterr().err
    assert "█" in saida

# cenario: lista de subcomandos no USO da raiz usa colchete reto sem os 3 pontos
def test_lista_de_subcomandos_no_uso_da_raiz_usa_colchete_reto(capsys) -> None:
    with pytest.raises(SystemExit):
        main(["--bogus"])
    saida = capsys.readouterr().err
    assert "[init, new, check, run, review, watch, status, context, report, history, clear]" in saida
    assert "{init,new,check" not in saida
    assert "} ..." not in saida


def test_cli_version(capsys) -> None:
    try:
        main(["--version"])
    except SystemExit as error:
        assert error.code == 0

    assert capsys.readouterr().out.strip() == __version__

def test_codigos_de_saida_cobrem_os_quatro_estados() -> None:
    """SPEC: sucesso, ressalva, reprovacao e infraestrutura sao distinguiveis."""
    from sentrytest.cli import EXIT_BY_VERDICT, EXIT_OK, EXIT_WARNING, EXIT_REJECTED, EXIT_INFRA

    assert EXIT_BY_VERDICT["aprovado"] == EXIT_OK
    assert EXIT_BY_VERDICT["aprovado com ressalvas"] == EXIT_WARNING
    assert EXIT_BY_VERDICT["reprovado"] == EXIT_REJECTED
    assert EXIT_BY_VERDICT["inconclusivo"] == EXIT_INFRA
    assert len(set(EXIT_BY_VERDICT.values())) == 4


def test_todo_veredito_do_dominio_tem_codigo_de_saida() -> None:
    """Um veredito novo sem codigo cairia silenciosamente no default."""
    from sentrytest.cli import EXIT_BY_VERDICT
    from sentrytest.domain.models import VerdictStatus

    assert {status.value for status in VerdictStatus} == set(EXIT_BY_VERDICT)


def test_spec_inexistente_retorna_codigo_de_infraestrutura(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    from sentrytest.cli import EXIT_INFRA

    assert main(["run", "--spec", "nao-existe"]) == EXIT_INFRA

# cenario: check com multiplas specs sem --spec imprime erro e retorna 2
def test_check_com_multiplas_specs_sem_escolher_retorna_erro(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    main(["new", "Demo A"])
    main(["new", "Demo B"])
    capsys.readouterr()
    assert main(["check"]) == 2
    assert "erro:" in capsys.readouterr().out

# cenario: erro de multiplas specs do check sai vermelho minusculo e com margem
def test_erro_de_multiplas_specs_do_check_sai_vermelho_minusculo_com_margem(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["init"])
    main(["new", "Demo A"])
    main(["new", "Demo B"])
    capsys.readouterr()

    assert main(["check"]) == 2
    saida = capsys.readouterr().out
    assert "Erro:" not in saida
    linha_erro = next(l for l in saida.splitlines() if "erro:" in l)
    assert linha_erro.startswith("  ")
    assert paint("erro:", "red", enabled=True) in linha_erro

# cenario: erro de multiplas specs do check tambem mostra wordmark e USO
def test_erro_de_multiplas_specs_do_check_tambem_mostra_wordmark_e_uso(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    main(["new", "Demo A"])
    main(["new", "Demo B"])
    capsys.readouterr()

    assert main(["check"]) == 2
    saida = capsys.readouterr().out
    assert "█" in saida
    assert "USO" in saida
    assert saida.index("█") < saida.index("USO") < saida.index("erro:")
    assert "mostra esta mensagem de ajuda e sai" not in saida  # compacto, igual ao erro do argparse

# cenario: check com sucesso ou achados de validacao mostra wordmark e titulo CHECK
def test_check_com_sucesso_ou_achados_mostra_wordmark_e_titulo_check(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    main(["new", "Demo A"])
    capsys.readouterr()

    # com achados (template nao preenchido: titulo/prompt/caso ausentes)
    assert main(["check", "demo-a"]) == 1
    saida = capsys.readouterr().out
    assert "█" in saida
    assert "CHECK" in saida
    assert saida.index("█") < saida.index("CHECK") < saida.index("caso(s)")

    # com sucesso
    spec = tmp_path / ".sentry" / "specs" / "demo-a" / "CASES.md"
    spec.write_text(
        "# Demo\n\n## Prompt\n\nx\n\n## Caso: um caso\n\n"
        "- **Requisito:** x\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Dado:** x\n- **Quando:** x\n- **Então:** x\n",
        encoding="utf-8")
    capsys.readouterr()
    assert main(["check", "demo-a"]) == 0
    saida = capsys.readouterr().out
    assert "█" in saida
    assert "CHECK" in saida

# cenario: sentry check troca o prefixo por simbolo em erro e sucesso
def test_check_troca_o_prefixo_por_simbolo_em_erro_e_sucesso(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["init"])
    main(["new", "Demo B"])
    capsys.readouterr()

    assert main(["check", "demo-b"]) == 1
    saida = capsys.readouterr().out
    assert "☑" not in saida
    assert paint("✗", "red", enabled=True) + " " in saida

    spec = tmp_path / ".sentry" / "specs" / "demo-b" / "CASES.md"
    spec.write_text(
        "# Demo\n\n## Prompt\n\nx\n\n## Caso: um caso\n\n"
        "- **Requisito:** x\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Dado:** x\n- **Quando:** x\n- **Então:** x\n",
        encoding="utf-8")
    capsys.readouterr()
    assert main(["check", "demo-b"]) == 0
    saida = capsys.readouterr().out
    assert "☑" not in saida
    assert paint("✓", "green", enabled=True) + " " in saida

def test_watch_interrompido_por_ctrl_c_termina_sem_traceback(tmp_path, monkeypatch, capsys) -> None:
    """Ctrl+C e' a forma normal de parar um watch, nao uma falha: um traceback
    aqui faria quem esta' desenvolvendo achar que quebrou alguma coisa."""
    monkeypatch.chdir(tmp_path)
    main(["init"])

    def interrompe(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("sentrytest.cli.watch", interrompe)
    capsys.readouterr()
    assert main(["watch"]) == 0
    assert "Parado." in capsys.readouterr().out

# cenario: watch imprime Parado em amarelo ao sair com Ctrl+C
def test_watch_imprime_parado_em_amarelo_ao_sair_com_ctrl_c(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["init"])

    def interrompe(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("sentrytest.cli.watch", interrompe)
    capsys.readouterr()
    assert main(["watch"]) == 0
    saida = capsys.readouterr().out
    assert paint("\nParado.", "yellow", enabled=True) in saida

# cenario: watch colore o modo instantaneo de azul e o completo de magenta
def test_watch_colore_o_modo_instantaneo_de_azul_e_o_completo_de_magenta(tmp_path, monkeypatch, capsys) -> None:
    from sentrytest.application.watch import COMPLETO, INSTANTANEO
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["init"])
    monkeypatch.setattr("sentrytest.cli._run_and_report", lambda *a, **k: 0)

    chamadas = iter([(["arquivo.py"], INSTANTANEO), (["tests/test_x.py"], COMPLETO)])

    def watch_falso(root, on_change, **kwargs):
        for arquivos, modo in chamadas:
            on_change(arquivos, modo)

    monkeypatch.setattr("sentrytest.cli.watch", watch_falso)
    capsys.readouterr()
    assert main(["watch"]) == 0
    saida = capsys.readouterr().out
    assert f"modo {paint(INSTANTANEO, 'blue', enabled=True)}" in saida
    assert f"modo {paint(COMPLETO, 'magenta', enabled=True)}" in saida

# cenario: falha ao reconfigurar stdout/stderr nao impede o comando de rodar
def test_main_sobrevive_a_stream_sem_reconfigure(monkeypatch, capsys) -> None:
    """stream.reconfigure pode nao existir (AttributeError) ou falhar (OSError):
    nenhum dos dois pode impedir o resto do comando de rodar."""
    import io
    monkeypatch.setattr("sys.stdout", io.StringIO())
    monkeypatch.setattr("sys.stderr", io.StringIO())
    assert main([]) == 0

# cenario: rodar como modulo (-m) executa o mesmo CLI
def test_modulo_executavel_roda_o_mesmo_cli() -> None:
    import subprocess, sys
    result = subprocess.run([sys.executable, "-m", "sentrytest.cli", "--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == __version__


def test_fluxo_completo_init_new_check_run(tmp_path, monkeypatch, capsys) -> None:
    """init -> new -> check -> run, os quatro passos do fluxo do usuario."""
    import json as _json
    monkeypatch.chdir(tmp_path)
    from sentrytest.cli import EXIT_INFRA

    assert main(["init"]) == 0
    assert (tmp_path / ".sentry" / "specs").is_dir()
    assert (tmp_path / "sentry.toml").exists()
    capsys.readouterr()

    # `new` funde o antigo `instructions`: cria a spec e ja entrega o template.
    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    assert (tmp_path / ".sentry" / "specs" / "cadastro-de-cliente" / "CASES.md").exists()
    assert "## Caso:" in saida
    assert "sentry check cadastro-de-cliente" in saida

    # CASES.md nasce como template nao preenchido, entao `check` reprova.
    assert main(["check", "cadastro-de-cliente"]) == 1

    # `run` roda mesmo com a matriz incompleta, mas nao aprova.
    assert main(["run", "--spec", "cadastro-de-cliente"]) != 0


def test_new_json_entrega_tudo_que_o_agente_precisa(tmp_path, monkeypatch, capsys) -> None:
    import json as _json
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro", "--prompt", "pedido", "--json"]) == 0
    payload = _json.loads(capsys.readouterr().out)
    assert payload["specDir"].replace("\\", "/").endswith(".sentry/specs/cadastro")
    assert "## Caso:" in payload["template"]
    assert payload["layers"] == ["backend", "integração", "frontend"]
    assert "texto" in payload["field_classes"]

# cenario: sentry new --json continua JSON valido, so a ordem das chaves muda
def test_new_json_continua_valido_com_specdir_primeiro(tmp_path, monkeypatch, capsys) -> None:
    import json as _json
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro", "--prompt", "pedido", "--json"]) == 0
    saida = capsys.readouterr().out
    payload = _json.loads(saida)  # nao lanca -- JSON valido, sem wordmark/titulo
    assert next(iter(payload)) == "specDir"


# cenario: comando check sugerido pelo new sai em verde, sem crases
def test_new_sugere_o_comando_check_em_verde_sem_crases(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    assert paint("sentry check cadastro-de-cliente", "green", enabled=True) in saida
    assert "`sentry check cadastro-de-cliente`" not in saida

# cenario: sentry new usa o checklist com check verde do init, sem caneta nem caminho verde
def test_new_usa_o_checklist_com_check_verde_do_init(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    assert "✎" not in saida
    caminho = str(Path(".sentry") / "specs" / "cadastro-de-cliente")
    assert paint(caminho, "green", enabled=True) not in saida
    linha_spec = next(l for l in saida.splitlines() if "Spec criada em" in l)
    assert linha_spec.strip().startswith(paint("✓", "green", enabled=True))
    linha_prompt = next(l for l in saida.splitlines() if "PROMPT.md" in l)
    assert linha_prompt.strip().startswith(paint("✓", "green", enabled=True))
    linha_cases = next(l for l in saida.splitlines() if "CASES.md" in l)
    assert linha_cases.strip().startswith(paint("✓", "green", enabled=True))

# cenario: sentry new sem arquivo novo mostra a linha maiuscula
def test_new_sem_arquivo_novo_mostra_a_linha_maiuscula(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    main(["new", "Cadastro de cliente"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente"]) == 0
    saida = capsys.readouterr().out
    assert "Nenhum arquivo novo" in saida
    assert "nenhum arquivo novo" not in saida

# cenario: checklist do new usa rotulo descritivo em vez do caminho cru
def test_checklist_do_new_usa_rotulo_descritivo(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente"]) == 0
    saida = capsys.readouterr().out
    assert "Guardando o pedido — PROMPT.md" in saida
    assert "Gerando o template de casos — CASES.md" in saida
    assert "specs\\cadastro-de-cliente\\PROMPT.md" not in saida
    assert "specs/cadastro-de-cliente/PROMPT.md" not in saida

# cenario: sentry new tem um titulo com tracinho antes do template
def test_new_tem_um_titulo_com_tracinho_antes_do_template(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    assert "TEMPLATE" in saida
    assert "─" in saida
    assert saida.index("TEMPLATE") < saida.index("## Caso:")

# cenario: sentry new tem um titulo Vocabulario separado do Template
def test_new_tem_um_titulo_vocabulario_separado_do_template(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    assert "VOCABULÁRIO" in saida
    assert saida.index("TEMPLATE") < saida.index("VOCABULÁRIO")
    assert saida.index("VOCABULÁRIO") < saida.index("Camadas aceitas:")

# cenario: sem espacamento duplo antes do titulo Vocabulario
def test_sem_espacamento_duplo_antes_do_titulo_vocabulario(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    linhas = saida.splitlines()
    indice_vocab = next(i for i, l in enumerate(linhas) if "VOCABULÁRIO" in l)
    assert linhas[indice_vocab - 1].strip() == ""
    assert linhas[indice_vocab - 2].strip() != ""

# cenario: valores aceitos do new saem sem cor, texto plano
def test_valores_aceitos_do_new_saem_sem_cor(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    linha_camadas = next(l for l in saida.splitlines() if l.startswith("Camadas aceitas:"))
    assert "\x1b[" not in linha_camadas
    linha_tipos = next(l for l in saida.splitlines() if l.startswith("Tipos aceitos:"))
    assert "\x1b[" not in linha_tipos

# cenario: sentry new tem um titulo Proximo passo antes da dica do check
def test_new_tem_um_titulo_proximo_passo_antes_da_dica(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    assert main(["new", "Cadastro de cliente", "--prompt", "exige email"]) == 0
    saida = capsys.readouterr().out
    assert "PRÓXIMO PASSO" in saida
    assert saida.index("VOCABULÁRIO") < saida.index("PRÓXIMO PASSO") < saida.index("Depois rode")

def test_new_usa_o_nome_como_prompt_quando_omitido(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init"])
    capsys.readouterr()

    main(["new", "cadastro exige email valido"])
    prompt = (tmp_path / ".sentry" / "specs" / "cadastro-exige-email-valido" / "PROMPT.md")
    assert "cadastro exige email valido" in prompt.read_text(encoding="utf-8")


CASES_COM_LACUNAS = """# Demo

## Prompt

Cadastrar um usuario pelo email.

## Campos

- **email**: email — o endereco do usuario
- **apelido**: sobrenome — tipo fora do catalogo

## Caso: email valido e aceito

- **Requisito:** cadastrar usuario
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** email/valido
- **Dado:** um email bem formado
- **Quando:** o cadastro e feito
- **Então:** o usuario e criado

## Classes não aplicáveis

- **email/espacos**: o formulario faz trim antes de enviar.
"""

def _spec(root, slug, conteudo):
    diretorio = root / ".sentry" / "specs" / slug
    diretorio.mkdir(parents=True)
    (diretorio / "CASES.md").write_text(conteudo, encoding="utf-8")

def test_check_all_junta_as_specs_e_nomeia_cada_uma(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _spec(tmp_path, "primeira", CASES_COM_LACUNAS)
    _spec(tmp_path, "segunda", CASES_COM_LACUNAS.replace("email valido e aceito", "outro caso"))
    main(["check", "all"])
    assert "all (primeira, segunda)" in capsys.readouterr().out

def test_check_all_sem_nenhuma_spec_e_erro(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["check", "all"]) == 2
    assert "nenhuma matriz de casos encontrada" in capsys.readouterr().out

def test_check_lista_classe_ausente_limitacao_e_dispensa(tmp_path, monkeypatch, capsys):
    """As tres saidas sao distintas de proposito: classe ausente e' cobranca, tipo fora
    do catalogo e' limitacao do Sentry, e dispensa e' decisao justificada do time."""
    monkeypatch.chdir(tmp_path)
    _spec(tmp_path, "demo", CASES_COM_LACUNAS)
    assert main(["check", "demo"]) == 0
    saida = capsys.readouterr().out
    assert "classe ausente: email/sem-arroba" in saida
    assert "[limitacao] tipo fora do catalogo" in saida and "sobrenome" in saida
    assert "[classe nao aplicavel] email/espacos" in saida

# cenario: sentry check usa o mesmo catalogo mesclado que o sentry run
def test_check_usa_o_catalogo_mesclado_de_sentry_toml(tmp_path, monkeypatch, capsys):
    """`sentry check` e `sentry run` liam catalogos diferentes: o primeiro so' via
    FIELD_CLASSES, o segundo ja' mesclado com `[catalog.fields]`. Um tipo declarado
    no projeto aparecia como limitacao no check e como cobrado no run -- os dois
    tem que concordar."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sentry.toml").write_text(
        '[catalog.fields]\nmatricula = ["vazio", "valida"]\n', encoding="utf-8")
    _spec(tmp_path, "demo", CASES_COM_LACUNAS.replace("sobrenome — tipo fora do catalogo", "matricula — numero interno"))
    main(["check", "demo"])
    saida = capsys.readouterr().out
    assert "[limitacao]" not in saida
    assert "classe ausente: apelido/vazio" in saida


def test_run_imprime_erro_de_infraestrutura_sem_reprovar_o_codigo(tmp_path, monkeypatch, capsys):
    """Runner ausente e' ambiente quebrado, nao codigo mal testado: sai inconclusivo."""
    monkeypatch.chdir(tmp_path)
    _spec(tmp_path, "demo", CASES_COM_LACUNAS)
    (tmp_path / "sentry.toml").write_text('[test]\ncommand = "runner-que-nao-existe"\n', encoding="utf-8")
    codigo = main(["run", "--spec", "demo", "--run-tests"])
    saida = capsys.readouterr().out
    assert "[infraestrutura] execucao de testes" in saida
    assert codigo == 3
