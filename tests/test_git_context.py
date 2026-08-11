from pathlib import Path
import subprocess
from sentrytest.adapters.local_tools import LocalGitAdapter

def git(root: Path, *args: str):
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)

def test_git_adapter_reads_files_status_and_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ("module.py",)
    assert change.statuses == {"module.py": "M"}
    assert change.changed_lines["module.py"] == (2,)

def test_git_adapter_reports_repo_without_previous_revision(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ()
    assert change.error is None

# cenario: arquivos gerados pelo proprio Sentry ficam fora do diff
def test_git_adapter_filters_sentry_own_generated_files(tmp_path: Path):
    """Sem isto, a primeira analise de todo projeto novo mede os arquivos que o
    `init` acabou de criar. sentry.toml e .gitignore ficam de fora deste filtro
    por nome: o Sentry os cria mas o usuario os edita depois, entao quem decide
    por eles e' `_is_untouched_init_file`, comparando conteudo."""
    from sentrytest.adapters.local_tools import is_generated_artifact
    assert is_generated_artifact("AGENT-SENTRY.md")
    assert is_generated_artifact(".claude/skills/sentry-cases/SKILL.md")
    assert is_generated_artifact(".claude\\skills\\sentry-cases\\SKILL.md")
    assert not is_generated_artifact("sentry.toml")
    assert not is_generated_artifact(".gitignore")
    # Skill de outra ferramenta nao pertence ao Sentry e nao pode ser escondida.
    assert not is_generated_artifact(".claude/skills/minha-skill/SKILL.md")

def test_git_adapter_reports_missing_repository(tmp_path: Path):
    change = LocalGitAdapter(tmp_path).change()
    assert change.error == "diretorio nao e um repositorio Git"

# cenario: arquivo novo ilegivel nao derruba a leitura do diff
def test_git_adapter_skips_unreadable_new_file_when_counting_lines(tmp_path: Path):
    """Um .py novo com bytes invalidos de UTF-8 nao pode quebrar o change():
    so esse arquivo fica sem changed_lines, o resto do diff continua."""
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "ok.py").write_text("um = 1\n", encoding="utf-8")
    (tmp_path / "invalido.py").write_bytes(b"\xff\xfe\x00bytes invalidos")
    change = LocalGitAdapter(tmp_path).change()
    assert change.error is None
    assert "ok.py" in change.changed_lines
    assert "invalido.py" not in change.changed_lines

def test_git_adapter_filters_generated_artifacts(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf-8")
    (tmp_path / ".coverage").write_text("data", encoding="utf-8")
    (tmp_path / "artifact.pyo").write_text("data", encoding="utf-8")
    (tmp_path / ".sentry").mkdir()
    (tmp_path / ".sentry" / "report.md").write_text("data", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert change.files == ("module.py",)
    assert ".coverage" not in change.files
    assert "artifact.pyo" not in change.files
    assert ".sentry/report.md" not in change.files

def test_git_adapter_filters_generated_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    (tmp_path / ".sentry").mkdir()
    (tmp_path / ".sentry" / "report.md").write_text("a\nb\n", encoding="utf-8")
    git(tmp_path, "add", "module.py", ".sentry/report.md")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "module.py").write_text("one\ntwo\n", encoding="utf-8")
    (tmp_path / ".sentry" / "report.md").write_text("a\nb\nc\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert "module.py" in change.files
    assert "module.py" in change.changed_lines
    assert ".sentry/report.md" not in change.files
    assert ".sentry/report.md" not in change.changed_lines

def test_git_adapter_includes_untracked_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "new_mod.py").write_text("a\nb\nc\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert "new_mod.py" in change.files
    assert change.changed_lines["new_mod.py"] == (1, 2, 3)

def test_git_adapter_ignores_untracked_docs_in_changed_lines(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "module.py").write_text("one\n", encoding="utf-8")
    git(tmp_path, "add", "module.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "notes.md").write_text("doc\n", encoding="utf-8")
    change = LocalGitAdapter(tmp_path).change()
    assert "notes.md" in change.files
    assert "notes.md" not in change.changed_lines



def test_subdiretorio_reporta_caminhos_relativos_a_ele(tmp_path: Path):
    """Rodar o Sentry num subdiretorio (monorepo) deve produzir caminhos que resolvem."""
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "raiz.py").write_text("x = 1\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "dentro.py").write_text("y = 1\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "raiz.py").write_text("x = 2\n", encoding="utf-8")
    (sub / "dentro.py").write_text("y = 2\n", encoding="utf-8")

    change = LocalGitAdapter(sub).change()
    assert change.files == ("dentro.py",)
    assert all((sub / name).exists() for name in change.files)

def _adapter_com_diff(tmp_path: Path, diff: str, statuses: str = "M\tapp.py\n") -> LocalGitAdapter:
    """Um LocalGitAdapter cujo Git responde o diff pedido. A leitura das hunks e'
    pura analise de texto: encenar o repositorio inteiro so para produzir uma
    forma de cabecalho tornaria o teste lento e menos exato sobre o que verifica."""
    import subprocess as sp

    adapter = LocalGitAdapter(tmp_path)
    respostas = {
        ("rev-parse", "HEAD"): "abc123\n",
        ("diff", "--relative", "--name-status", "HEAD"): statuses,
        ("diff", "--relative", "--unified=0", "HEAD"): diff,
        ("ls-files", "--others", "--exclude-standard"): "",
    }
    adapter._run = lambda *args: sp.CompletedProcess(args, 0, respostas.get(args, ""), "")
    return adapter

# cenario: duas hunks no mesmo arquivo acumulam em vez de sobrescrever
# cenario: hunk que so remove linhas nao apaga as demais do arquivo
# cenario: hunk sem contagem explicita vale uma linha
def test_hunks_do_mesmo_arquivo_acumulam(tmp_path: Path):
    """Guardar por arquivo em vez de acumular deixava so a ultima hunk visivel:
    alterar a linha 50 e a 370 fazia a analise enxergar apenas a 370, e o caminho
    de erro da primeira sumia do relatorio. Junto vao as duas formas de cabecalho
    que o acumulo precisa aguentar: contagem omitida (vale 1) e `,0` (remocao
    pura, que nao contribui linha e nao pode apagar as outras)."""
    diff = (
        "+++ b/app.py\n"
        "@@ -50 +50,2 @@\n"
        "+    raise ValidationError('telefone')\n"
        "@@ -120,3 +120,0 @@\n"
        "@@ -370 +370 @@\n"
        "+    raise ValidationError('cep')\n"
    )
    change = _adapter_com_diff(tmp_path, diff).change()
    assert change.changed_lines["app.py"] == (50, 51, 370)

# cenario: muitas hunks no mesmo arquivo e nenhuma e perdida
def test_muitas_hunks_no_mesmo_arquivo_nenhuma_e_perdida(tmp_path: Path):
    """O defeito nao tinha limite: com N hunks, N-1 ficavam invisiveis."""
    inicios = range(10, 610, 10)
    diff = "+++ b/app.py\n" + "".join(f"@@ -{i} +{i} @@\n+x\n" for i in inicios)
    change = _adapter_com_diff(tmp_path, diff).change()
    assert change.changed_lines["app.py"] == tuple(inicios)

# cenario: hunk de arquivo removido nao e atribuida ao arquivo anterior
def test_hunk_de_arquivo_removido_nao_entra_no_arquivo_anterior(tmp_path: Path):
    """Arquivo removido tem `+++ /dev/null`: nao ha lado novo a atribuir. Sem
    zerar o arquivo corrente, as hunks dele entravam no arquivo anterior -- erro
    que a sobrescrita escondia e que acumular tornaria permanente."""
    diff = (
        "+++ b/app.py\n"
        "@@ -10 +10 @@\n"
        "+x\n"
        "--- a/velho.py\n"
        "+++ /dev/null\n"
        "@@ -1,40 +0,0 @@\n"
        "@@ -900 +900 @@\n"
    )
    change = _adapter_com_diff(tmp_path, diff, statuses="M\tapp.py\nD\tvelho.py\n").change()
    assert change.changed_lines["app.py"] == (10,)
    assert "velho.py" not in change.changed_lines

# cenario: linhas alteradas alimentam a analise de cobertura de todas as hunks
def test_duas_hunks_distantes_em_repositorio_real(tmp_path: Path):
    """O sintoma relatado, ponta a ponta: dois `raise` em pontos distantes do
    mesmo arquivo, com o Git de verdade produzindo o diff."""
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    original = [f"linha_{i} = {i}" for i in range(1, 401)]
    (tmp_path / "serializers.py").write_text("\n".join(original) + "\n", encoding="utf-8")
    git(tmp_path, "add", "serializers.py")
    git(tmp_path, "commit", "-m", "initial")

    alterado = list(original)
    alterado[49] = "    raise ValidationError('telefone')"
    alterado[369] = "    raise ValidationError('cep')"
    (tmp_path / "serializers.py").write_text("\n".join(alterado) + "\n", encoding="utf-8")

    change = LocalGitAdapter(tmp_path).change()
    assert change.changed_lines["serializers.py"] == (50, 370)

# cenario: base declarada revela o que a branch mudou
# cenario: sem base declarada o comportamento atual permanece
# cenario: base compara a partir do ponto em que a branch divergiu
def test_base_declarada_compara_a_partir_da_divergencia(tmp_path: Path):
    """O sintoma relatado: numa PR ja commitada, `git diff HEAD` sai vazio e nao
    ha o que revisar. Com base declarada o diff volta -- e comeca na divergencia,
    nao em `main`: o commit que entrou em main depois que a branch saiu nao e'
    mudanca da branch, e cobrar teste por ele seria acusar autoria alheia."""
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "base.py").write_text("x = 1\n", encoding="utf-8")
    git(tmp_path, "add", "base.py")
    git(tmp_path, "commit", "-m", "initial")
    git(tmp_path, "branch", "-M", "main")

    git(tmp_path, "checkout", "-b", "feature")
    (tmp_path / "da_branch.py").write_text("y = 2\n", encoding="utf-8")
    git(tmp_path, "add", "da_branch.py")
    git(tmp_path, "commit", "-m", "trabalho da branch")

    # Um commit que entrou em main depois da divergencia.
    git(tmp_path, "checkout", "main")
    (tmp_path / "de_outra_pessoa.py").write_text("z = 3\n", encoding="utf-8")
    git(tmp_path, "add", "de_outra_pessoa.py")
    git(tmp_path, "commit", "-m", "outro trabalho")
    git(tmp_path, "checkout", "feature")

    adapter = LocalGitAdapter(tmp_path)
    # Sem base: arvore limpa, nada a revisar -- exatamente o buraco relatado.
    assert adapter.change().files == ()

    da_branch = adapter.change("main")
    assert da_branch.files == ("da_branch.py",)
    assert "de_outra_pessoa.py" not in da_branch.files
    assert da_branch.changed_lines["da_branch.py"] == (1,)
    assert da_branch.error is None

# cenario: base inexistente vira erro de infraestrutura
def test_base_inexistente_vira_erro_e_nao_diff_vazio(tmp_path: Path):
    """Em CI, um nome de base errado nao pode virar diff vazio e aprovacao: nada
    a medir e' indistinguivel de nada mudou. E a distincao so existe se a
    referencia invalida for reportada em vez de silenciosamente ignorada."""
    from sentrytest.application.analyze import analyze

    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "initial")

    change = LocalGitAdapter(tmp_path).change("origin/nao-existe~~")
    assert change.files == ()
    assert "origin/nao-existe~~" in (change.error or "")

    spec = tmp_path / ".sentry" / "specs" / "s"
    spec.mkdir(parents=True)
    (spec / "CASES.md").write_text(
        "# S\n\n## Campos\n\n- **a**: texto — regra\n\n"
        "## Caso: faz algo\n\n- **Requisito:** r\n- **Camada:** backend\n- **Tipo:** unitário\n"
        "- **Prioridade:** alta\n- **Classe:** a/valido\n- **Dado:** d\n- **Quando:** q\n"
        "- **Então:** e\n- **Entrada:** `a = 1`\n", encoding="utf-8")

    resultado = analyze(tmp_path, "s", False, "origin/nao-existe~~")
    assert resultado.verdict.status.value != "aprovado"
    erro = next(error for error in resultado.infrastructure_errors if "origin/nao-existe~~" in error.message)
    assert erro.stage == "leitura do diff"
    # Repetir nao resolve: o nome da referencia nao vai passar a existir.
    assert erro.retryable is False

# cenario: a base efetivamente usada aparece no relatorio
def test_base_usada_aparece_no_relatorio():
    """Contra o que se comparou muda o que "alterado" significa; sem declarar
    isso, analise de branch e analise da arvore de trabalho ficam iguais no papel."""
    from sentrytest.application.reporting import markdown_report

    def relatorio(reference):
        return markdown_report({"data": {
            "id": "r", "verdict": {"status": "aprovado", "summary": "s"}, "findings": [],
            "configuration": {"git_change": {"reference": reference, "files": ["app.py"]}},
        }})

    assert "Comparado com: `main`" in relatorio("main")
    assert "árvore de trabalho contra `HEAD`" in relatorio("HEAD")

def _projeto_inicializado(tmp_path: Path) -> None:
    """Um repositorio Git com um commit e o `sentry init` rodado por cima -- o
    estado exato em que o defeito aparecia: a primeira analise de qualquer um."""
    from sentrytest.init_project import initialize_project

    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "initial")
    initialize_project(tmp_path)

# cenario: sentry.toml intocado desde o init fica fora do diff
# cenario: gitignore so com as entradas do Sentry fica fora do diff
def test_arquivos_escritos_pelo_init_ficam_fora_do_diff(tmp_path: Path):
    """O defeito relatado: "Arquivos alterados: 3" contava sentry.toml e
    .gitignore, que o proprio Sentry acabara de escrever. Medir o que a
    ferramenta criou como se fosse mudanca do usuario e' ruido em toda primeira
    analise -- e nas linhas alteradas vira cobertura e caminho de erro falsos."""
    _projeto_inicializado(tmp_path)
    change = LocalGitAdapter(tmp_path).change()
    assert "sentry.toml" not in change.files
    assert ".gitignore" not in change.files
    assert "sentry.toml" not in change.changed_lines
    assert ".gitignore" not in change.changed_lines

# cenario: sentry.toml editado pelo usuario volta ao diff
def test_sentry_toml_editado_pelo_usuario_volta_ao_diff(tmp_path: Path):
    """Excluir sempre pelo nome seria o erro oposto: mudar a suite declarada ou os
    limiares de politica e' mudanca do usuario, e precisa ser revisada."""
    _projeto_inicializado(tmp_path)
    caminho = tmp_path / "sentry.toml"
    caminho.write_text(caminho.read_text(encoding="utf-8") + '\n[tests]\npaths = ["users"]\n', encoding="utf-8")

    change = LocalGitAdapter(tmp_path).change()
    assert "sentry.toml" in change.files
    assert ".gitignore" not in change.files

# cenario: gitignore com linha do usuario na mesma mudanca entra no diff
def test_gitignore_com_linha_do_usuario_entra_no_diff(tmp_path: Path):
    """No .gitignore a comparacao tem que ser por linha: o `init` acrescenta
    entradas a um arquivo que ja e' do usuario. Esconder o arquivo inteiro
    esconderia junto o que ele escreveu."""
    _projeto_inicializado(tmp_path)
    caminho = tmp_path / ".gitignore"
    caminho.write_text(caminho.read_text(encoding="utf-8") + "*.env\n", encoding="utf-8")

    change = LocalGitAdapter(tmp_path).change()
    assert ".gitignore" in change.files

# cenario: arquivo de nome parecido nao e excluido
# cenario: exclusao nao depende de leitura possivel do arquivo
def test_nome_parecido_e_arquivo_ilegivel_nao_sao_excluidos(tmp_path: Path):
    """A exclusao vale para os dois arquivos que o `init` escreve na raiz, e so
    mediante prova de conteudo. Um caminho parecido nao herda a excecao, e nao
    conseguir ler o arquivo nao autoriza esconde-lo -- sem prova, a alteracao
    continua sendo do usuario."""
    from sentrytest.adapters.local_tools import _is_untouched_init_file
    from sentrytest.init_project import GITIGNORE_ENTRIES, initialize_project

    initialize_project(tmp_path)
    assert _is_untouched_init_file(tmp_path, "sentry.toml", [])

    for parecido in ("sentry.toml.bak", "pacote/sentry.toml", "docs/.gitignore"):
        assert not _is_untouched_init_file(tmp_path, parecido, list(GITIGNORE_ENTRIES))

    ilegivel = tmp_path / "vazio"
    ilegivel.mkdir()
    assert not _is_untouched_init_file(ilegivel, "sentry.toml", [])
    assert not _is_untouched_init_file(ilegivel, ".gitignore", [])
