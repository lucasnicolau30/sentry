from sentrytest import __version__
from sentrytest.cli import main


def test_cli_returns_success_without_arguments() -> None:
    assert main([]) == 0


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
    assert "Erro:" in capsys.readouterr().out

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
