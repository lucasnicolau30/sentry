from __future__ import annotations
import json
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from ..domain.models import TestStatus
from ..ports.inputs import GitChange, TestExecution, CoverageData
from ..skills import generated_artifacts

# `text=True` sozinho decodifica com o locale (cp1252 no Windows pt-BR), o que
# corrompe acentos vindos do diff e da saida do pytest -- e um byte indefinido em
# cp1252 mata a thread leitora do subprocess, deixando stdout None. Toda saida de
# ferramenta externa e UTF-8; `replace` degrada em vez de derrubar a analise.
DECODING = {"text": True, "encoding": "utf-8", "errors": "replace"}

class LocalGitAdapter:
    def __init__(self, root: Path):
        self.root = root

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, check=False, **DECODING)

    def _merge_base(self, reference: str) -> str | None:
        """O ponto em que a branch atual divergiu da referencia. None se a
        referencia nao existe.

        Comparar direto contra `main` responderia "o que difere de main", que
        inclui o que entrou em main depois que a branch saiu -- a branch levaria a
        culpa por mudanca alheia. Revisar uma branch e' revisar o que ela fez, e
        isso comeca na divergencia.

        Sem ancestral comum (historicos separados) a referencia ainda serve: o
        Git a compara inteira, que e' o melhor disponivel ali.
        """
        result = self._run("merge-base", reference, "HEAD")
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return reference if self._run("rev-parse", "--verify", f"{reference}^{{commit}}").returncode == 0 else None

    def change(self, reference: str | None = None) -> GitChange:
        revision = self._run("rev-parse", "HEAD")
        if revision.returncode != 0:
            return GitChange(None, reference, (), error="diretorio nao e um repositorio Git")
        current = revision.stdout.strip()
        base = self._merge_base(reference) if reference else "HEAD"
        if base is None:
            return GitChange(current, reference, (), error=f"referencia Git invalida: {reference}")
        # `--relative` limita o diff ao diretorio atual e emite caminhos relativos a
        # ele. Sem isso o Git responde relativo a raiz do repositorio, e rodar o
        # Sentry num subdiretorio (monorepo) produziria caminhos que nao resolvem.
        status = self._run("diff", "--relative", "--name-status", base)
        diff = self._run("diff", "--relative", "--unified=0", base)
        if status.returncode != 0:
            return GitChange(current, reference, (), diff=diff.stdout, error=status.stderr.strip() or "referencia Git invalida")
        statuses = {}
        for line in status.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                statuses[parts[1]] = parts[0]
        untracked = self._run("ls-files", "--others", "--exclude-standard")
        if untracked.returncode == 0:
            for name in untracked.stdout.splitlines():
                statuses[name] = "A"
        # As linhas acrescentadas por arquivo, para decidir a autoria de alteracao
        # em `sentry.toml` e `.gitignore` -- os dois arquivos que o Sentry escreve
        # mas que o usuario edita depois.
        added_lines: dict[str, list[str]] = {}
        added_file = None
        for line in diff.stdout.splitlines():
            if line.startswith("+++ "):
                added_file = line[6:] if line.startswith("+++ b/") else None
            elif line.startswith("+") and not line.startswith("+++") and added_file:
                added_lines.setdefault(added_file, []).append(line[1:])
        statuses = {name: value for name, value in statuses.items()
                    if not is_generated_artifact(name)
                    and not _is_untouched_init_file(self.root, name, added_lines.get(name, []))}
        # Um arquivo tem uma hunk por trecho alterado, e todas descrevem a mesma
        # mudanca. Guardar por arquivo em vez de acumular deixava so a ultima
        # visivel: mexer na linha 50 e na 370 do mesmo arquivo fazia a analise
        # enxergar apenas a 370, e o caminho de erro da primeira sumia do relatorio.
        accumulated: dict[str, set[int]] = {}
        current_file = None
        for line in diff.stdout.splitlines():
            if line.startswith("+++ "):
                # `+++ /dev/null` e' arquivo removido: nao ha lado novo a atribuir.
                # Sem zerar aqui, as hunks dele entrariam no arquivo anterior --
                # erro que a sobrescrita escondia e que acumular tornaria permanente.
                current_file = line[6:] if line.startswith("+++ b/") else None
            elif line.startswith("@@") and current_file:
                if is_generated_artifact(current_file):
                    continue
                match = re.search(r"\+(\d+)(?:,(\d+))?", line)
                if match:
                    start_line = int(match.group(1))
                    # Contagem omitida significa uma linha; `,0` e' remocao pura e
                    # nao contribui linha nova, mas nao pode apagar as outras hunks.
                    count = int(match.group(2) or "1")
                    accumulated.setdefault(current_file, set()).update(range(start_line, start_line + count))
        # `statuses` ja passou pelos dois filtros; reusa-lo aqui e' o que impede um
        # arquivo excluido de voltar pela porta das linhas alteradas -- e' delas
        # que saem cobertura alterada e caminhos de erro.
        changed_lines = {name: tuple(sorted(lines)) for name, lines in accumulated.items()
                         if lines and name in statuses}
        for name, value in statuses.items():
            if value == "A" and name not in changed_lines and name.endswith(".py"):
                try:
                    line_count = len((self.root / name).read_text(encoding="utf-8").splitlines())
                except (OSError, UnicodeDecodeError):
                    continue
                changed_lines[name] = tuple(range(1, line_count + 1))
        return GitChange(current, reference or "HEAD", tuple(statuses), diff=diff.stdout, statuses=statuses, changed_lines=changed_lines)

def _is_untouched_init_file(root: Path, name: str, added: list[str]) -> bool:
    """O arquivo alterado e' obra do `init` e so dele?

    `sentry.toml` e `.gitignore` sao criados pelo Sentry mas editados depois pelo
    usuario, entao nem "sempre excluir" nem "nunca excluir" servem: o primeiro
    esconderia configuracao que o usuario mudou, o segundo -- o comportamento
    relatado -- fazia a primeira analise de todo projeto contar como mudanca do
    usuario os arquivos que o `init` acabara de escrever. Quem decide e' o
    conteudo, nao o nome.
    """
    from ..init_project import GITIGNORE_ENTRIES, OBSOLETE_GITIGNORE_ENTRIES, default_config

    try:
        if name == "sentry.toml":
            # Identico ao que o `init` escreveria: ninguem tocou nele desde entao.
            return (root / name).read_text(encoding="utf-8") == default_config(root.resolve().name)
        if name == ".gitignore":
            # Aqui a comparacao e' por linha, nao pelo arquivo: o `init` acrescenta
            # entradas a um arquivo que ja era do usuario. Excluir do diff so
            # quando nenhuma linha alterada e' dele.
            known = set(GITIGNORE_ENTRIES) | OBSOLETE_GITIGNORE_ENTRIES
            # Arquivo novo e ainda nao rastreado nao tem hunk no diff; ai o
            # conteudo inteiro e' a alteracao.
            lines = added or (root / name).read_text(encoding="utf-8").splitlines()
            return bool(lines) and all(line.strip() in known for line in lines if line.strip())
    except (OSError, UnicodeDecodeError):
        # Nao conseguir ler nao autoriza esconder: sem prova de que o conteudo e'
        # o do `init`, a alteracao segue sendo do usuario e fica no diff.
        return False
    return False


def is_generated_artifact(name: str) -> bool:
    # Artefato gerado nao e' mudanca do usuario: entra aqui tanto o que as
    # ferramentas produzem (cache, bytecode) quanto o que o proprio Sentry
    # escreve no `init` -- este ultimo vem de skills.generated_artifacts().
    normalized = name.replace("\\", "/")
    if any(normalized == item or normalized.startswith(item) for item in generated_artifacts()):
        return True
    return normalized.startswith(".sentry/") or "/__pycache__/" in normalized or normalized.endswith(".pyc") or normalized == ".coverage" or ".egg-info/" in normalized or normalized == ".pytest_cache" or normalized.startswith(".pytest_cache/") or normalized.endswith(".pyo")
def _count(pattern: str, text: str) -> int:
    match = re.search(pattern, text)
    return int(match.group(1)) if match else 0

def _counts_from_regex(output: str) -> tuple[int, int, int, int]:
    """Contagem lida da saida, sem inventar nada. Um `failed` fabricado a partir do
    codigo de saida transformaria "nao consegui rodar" em "seu codigo reprovou" --
    era isso que fazia `No module named 'pytest'` virar achado critico."""
    passed = _count(r"(\d+) passed", output)
    failed = _count(r"(\d+) failed", output)
    skipped = _count(r"(\d+) skipped", output)
    collected = _count(r"(\d+) collected", output)
    deselected = _count(r"(\d+) deselected", output)
    not_run = deselected if deselected else max(0, collected - (passed + failed + skipped)) if collected else 0
    return passed, failed, skipped, not_run

def _counts_from_junitxml(report_path: Path) -> tuple[int, int, int, int] | None:
    if not report_path.exists():
        return None
    try:
        root = ET.parse(report_path).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        if suite is None:
            return None
        total = int(suite.get("tests", 0))
        failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
        skipped = int(suite.get("skipped", 0))
        passed = max(0, total - failed - skipped)
        return passed, failed, skipped, 0
    except (ET.ParseError, ValueError, OSError):
        return None

# O pytest usa o codigo de saida para distinguir "a suite reprovou" de "nao foi
# possivel rodar a suite". Só 0 e 1 sao veredito de qualidade; o resto e ambiente
# ou configuracao, e tratar como reprovacao mentiria sobre o estado do codigo.
PYTEST_INFRA_EXITS = {
    2: "execucao interrompida",
    3: "erro interno do pytest",
    4: "erro de uso na linha de comando do pytest",
    5: "nenhum teste coletado",
}

def _resolved_executable(root: Path, executable: str) -> str:
    """O caminho declarado no comando, pronto para o sistema operacional executar.

    Duas coisas separam "reconhecer" de "executar", e o codigo so fazia a primeira:

    - No Windows o CreateProcess nao resolve `venv/Scripts/python.exe`. Barra
      normal so funciona em caminho absoluto; relativo exige `\\` ou um `./`
      explicito. Das quatro grafias do mesmo arquivo, era a unica que falhava.
    - Caminho relativo e' resolvido contra o diretorio do processo que chama, nao
      contra o `cwd=` passado ao subprocess. Rodar a CLI de fora da raiz do
      projeto procurava o venv no lugar errado -- ou, pior, achava outro.

    Resolver contra a raiz do projeto conserta os dois: vira caminho absoluto com
    os separadores da plataforma. Nome puro (sem separador) segue intocado, que e'
    o que mantem a resolucao pelo PATH.
    """
    normalized = executable.replace("\\", "/")
    if "/" not in normalized:
        return executable
    candidate = Path(normalized)
    return str(candidate if candidate.is_absolute() else (root / candidate))


def _interpreter_beside(root: Path, executable: str) -> str | None:
    """O interpretador irmao de um console script instalado. Num venv, `bin/pytest`
    e `bin/python` (ou `Scripts\\pytest.exe` e `Scripts\\python.exe`) moram lado a
    lado, e e' o irmao que o console script usa. None quando nao ha nenhum ali."""
    directory = Path(_resolved_executable(root, executable)).parent
    for name in ("python.exe", "python", "python3"):
        candidate = directory / name
        if candidate.exists():
            return str(candidate)
    return None


def _pytest_invocation(root: Path, args: list[str]) -> tuple[str | None, list[str]] | None:
    """Reconhece as formas de invocar o pytest e devolve `(interpretador, argumentos
    do pytest)`. None quando o comando nao e' pytest; interpretador None quando e'
    pytest mas o ambiente nao e' deduzivel -- ai o comando declarado roda literalmente.

    `pytest -x`, `python -m pytest -x` e `.venv/bin/pytest -x` sao o mesmo runner
    escrito de tres jeitos. Casar so com o literal `pytest` fazia as outras duas
    cairem no caminho generico: perdiam o `coverage run` (logo, sem cobertura) e
    mesmo assim recebiam `--junitxml`.

    Mas normalizar nao pode virar substituir: um caminho escrito no comando e' a
    declaracao do usuario sobre em qual ambiente rodar. Trocar `.venv/Scripts/
    python.exe` pelo interpretador do proprio Sentry rodava a suite no Python
    global -- com outras dependencias instaladas, e em silencio.
    """
    if not args:
        return None
    # `\` so e' separador para o PurePath do Windows; num runner Linux analisando
    # um comando escrito com caminho Windows, `Path(...).name` devolveria a string
    # inteira. Normalizar antes torna o reconhecimento igual nas duas plataformas.
    first = args[0].replace("\\", "/")
    head = Path(first).name.lower().removesuffix(".exe")
    # Sem separador e' um nome a resolver no PATH, nao um ambiente declarado: ai o
    # interpretador do Sentry e' a melhor resposta disponivel, e e' o que ja fazia.
    declared = "/" in first
    if head == "pytest":
        # O console script nao aceita `-m coverage`; quem roda e' o interpretador
        # ao lado dele. Sem esse irmao nao ha o que deduzir, e substituir seria de
        # novo trocar o ambiente do usuario pelo nosso.
        return (_interpreter_beside(root, args[0]) if declared else sys.executable), args[1:]
    if (head.startswith("python") or head == "py") and args[1:3] == ["-m", "pytest"]:
        return (_resolved_executable(root, args[0]) if declared else sys.executable), args[3:]
    return None


class SuiteAdapter:
    """Executa a suite declarada pelo projeto, seja ela pytest ou nao.

    Com `junit_xml` declarado, o projeto ja configurou o proprio reporter
    (jest-junit, gotestsum, surefire, coverlet...) e o Sentry apenas le o
    arquivo. Sem declaracao, `--junitxml` so e' injetado quando o comando
    reconhecidamente e' pytest -- e' flag dele, e passa-la a um `unittest` ou a
    um `go test` quebraria o comando do usuario por erro de linha de comando.
    """

    def __init__(self, root: Path, command: str = "pytest", junit_xml: str | None = None):
        self.root = root
        self.junit_xml = junit_xml
        args = command.split()
        invocation = _pytest_invocation(root, args)
        self.is_pytest = invocation is not None
        interpreter = invocation[0] if invocation else None
        # Cobertura so existe quando o Sentry embrulha a execucao em `coverage run`.
        # Reconhecer como pytest e medir cobertura sao coisas distintas: o comando
        # declarado que roda literalmente continua sendo pytest -- vale a tabela de
        # codigos de saida e a flag `--junitxml` -- mas nao passa pelo coverage.
        self.measures_coverage = interpreter is not None
        self.interpreter = interpreter or sys.executable
        # O defeito e' da execucao, nao do reconhecimento do pytest: qualquer runner
        # declarado por caminho relativo sofre o mesmo, entao o caminho generico
        # tambem passa pela resolucao.
        self.command = ([interpreter, "-m", "coverage", "run", "-m", "pytest", *invocation[1]] if interpreter
                        else [_resolved_executable(root, args[0]), *args[1:]] if args else [])

    def _classify(self, returncode: int, ran: bool) -> str | None:
        if self.is_pytest:
            known = PYTEST_INFRA_EXITS.get(returncode)
            if known:
                return known
            if ran:
                return None
            # Codigo 0 ou 1 sem nenhum teste contabilizado nao e' o pytest falando:
            # o pytest so sai 0/1 depois de coletar e rodar (nada coletado e' 5).
            # Quem devolve 1 aqui e' o interpretador ou o `coverage run` -- runner
            # ausente, ImportError na coleta, venv errado. Ambiente, nao qualidade.
            return f"a suite nao contabilizou nenhum teste (codigo de saida {returncode}); verifique se o runner esta instalado no ambiente"
        # Fora do pytest nao existe tabela confiavel de codigos de saida. O sinal
        # honesto e' a evidencia: sem nenhum teste contabilizado, nao ha prova de
        # que a suite rodou -- isso e' ambiente, nao qualidade do codigo.
        if not ran:
            detail = f"nenhum teste contabilizado (codigo de saida {returncode})"
            if not self.junit_xml:
                # Sem junit_xml e fora do pytest nao ha de onde tirar contagem: o
                # fallback por regex so entende o resumo do pytest. Dizer "ambiente"
                # e parar esconderia a acao que resolve.
                detail += "; declare [test] junit_xml em sentry.toml para o Sentry ler o relatorio da sua suite"
            return detail
        return None

    def run(self, coverage_file: Path, timeout_seconds: int = 300) -> tuple[TestExecution, float | None]:
        command_str = " ".join(self.command)
        started = time.perf_counter()
        # Comando vazio nao chega ao subprocess: cada plataforma reage de um jeito
        # (POSIX estoura IndexError ao ler args[0]; Windows deixa o CreateProcess
        # recusar com OSError), e nenhuma das duas mensagens diz o que fazer.
        if not self.command:
            execution = TestExecution(command_str, infrastructure_error="comando de teste vazio; declare [test] command em sentry.toml", status=TestStatus.NOT_RUN, duration_seconds=0.0)
            return execution, None
        with tempfile.TemporaryDirectory() as temp_dir:
            if self.junit_xml:
                report_path = self.root / self.junit_xml
                command = list(self.command)
            else:
                report_path = Path(temp_dir) / "junit.xml"
                # Fora do pytest o arquivo nunca sera escrito; `_counts_from_junitxml`
                # devolve None e a contagem cai no fallback por regex.
                command = [*self.command, "--junitxml", str(report_path)] if self.is_pytest else list(self.command)
            try:
                result = subprocess.run(command, cwd=self.root, capture_output=True, timeout=timeout_seconds, **DECODING)
            # OSError, e nao so FileNotFoundError: executavel sem permissao, caminho
            # invalido e recusa do SO chegam aqui como irmaos. Configuracao ruim e'
            # infraestrutura, nao motivo para derrubar a analise com excecao.
            # OSError nao diz qual arquivo faltou (no Windows, "[WinError 2] o sistema
            # nao pode encontrar o arquivo especificado" e so isso). Nomear o
            # executavel e' o que separa "meu venv nao existe" de um erro qualquer.
            except (OSError, subprocess.TimeoutExpired) as error:
                execution = TestExecution(command_str, infrastructure_error=f"{error} ao executar {command[0]}", status=TestStatus.NOT_RUN, duration_seconds=time.perf_counter() - started)
                return execution, None
            duration = time.perf_counter() - started
            output = result.stdout + result.stderr
            counts = _counts_from_junitxml(report_path)
            if counts is None:
                counts = _counts_from_regex(output)
            passed, failed, skipped, not_run = counts
            if not not_run:
                _, _, _, not_run = _counts_from_regex(output)
        percent = None
        if self.measures_coverage:
            # O mesmo interpretador que gravou o `.coverage`: o formato do arquivo de
            # dados e' versionado, e ler com outro coverage pode simplesmente falhar.
            subprocess.run([self.interpreter, "-m", "coverage", "json", "-o", str(coverage_file)], cwd=self.root, capture_output=True, **DECODING)
            if coverage_file.exists():
                data = json.loads(coverage_file.read_text(encoding="utf-8"))
                percent = data.get("totals", {}).get("percent_covered")
        infrastructure_error = self._classify(result.returncode, passed + failed + skipped > 0)
        if infrastructure_error:
            # Sem execucao provada nao ha contagem a reportar: zerar evita que um
            # relatorio inconclusivo exiba numero nenhum como se fosse veredito.
            status, passed, failed, skipped = TestStatus.NOT_RUN, 0, 0, 0
        elif result.returncode == 0:
            status = TestStatus.COVERED
        else:
            status = TestStatus.FAILED
            # Aqui ha prova de execucao e a suite reprovou; se o resumo nao trouxe
            # `N failed` (erro em teardown, por exemplo), uma reprovacao e' o piso.
            failed = failed or 1
        execution = TestExecution(command_str, passed=passed, failed=failed, skipped=skipped, not_run=not_run, output=output[-4000:], infrastructure_error=infrastructure_error, status=status, duration_seconds=round(duration, 2))
        return execution, percent

# Cada stack tem seu proprio medidor de cobertura, mas quase todos exportam um
# destes tres formatos. Depender do formato de intercambio -- e nao da ferramenta
# -- e' o que permite verificar cobertura fora de Python sem um adapter por stack.
COVERAGE_FORMATS = ("coverage.py", "lcov", "cobertura")


def detect_coverage_format(text: str) -> str | None:
    """Formato do relatorio pelo proprio conteudo. None quando nao reconhecido."""
    stripped = text.lstrip()
    if not stripped:
        return None
    if stripped[0] == "{":
        return "coverage.py"
    if stripped[0] == "<":
        return "cobertura"
    if stripped.startswith(("TN:", "SF:")):
        return "lcov"
    return None


def _relative(filename: str, root: Path | None) -> str:
    """Caminho comparavel com o do Git. LCOV e Cobertura costumam gravar caminho
    absoluto; o diff e' sempre relativo a raiz, entao sem isto nada casa."""
    normalized = filename.replace("\\", "/")
    candidate = Path(normalized)
    if root is not None and candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            return normalized
    return normalized


def _from_line_hits(instrumented: dict[str, set[int]], hit: dict[str, set[int]],
                    global_percent: float | None = None) -> CoverageData:
    """Monta o CoverageData a partir de linha->executou, comum a lcov e cobertura."""
    files: dict[str, float | None] = {}
    executed: dict[str, tuple[int, ...]] = {}
    for filename, lines in instrumented.items():
        covered = hit.get(filename, set())
        executed[filename] = tuple(sorted(covered))
        files[filename] = (len(covered) / len(lines) * 100) if lines else None
    if global_percent is None:
        total = sum(len(lines) for lines in instrumented.values())
        covered_total = sum(len(hit.get(name, set())) for name in instrumented)
        global_percent = (covered_total / total * 100) if total else None
    return CoverageData(global_percent, files, executed_lines=executed)


def _parse_coverage_py(text: str, root: Path | None) -> CoverageData:
    data = json.loads(text)
    files = {}
    executed = {}
    excluded = {}
    for filename, payload in data.get("files", {}).items():
        normalized = _relative(filename, root)
        files[normalized] = payload.get("summary", {}).get("percent_covered")
        executed[normalized] = tuple(payload.get("executed_lines", []))
        # Só o coverage.py tem o conceito de exclusão declarada; lcov e cobertura
        # descrevem apenas linha instrumentada e execuções.
        excluded[normalized] = tuple(payload.get("excluded_lines", []))
    return CoverageData(data.get("totals", {}).get("percent_covered"), files, executed_lines=executed, excluded_lines=excluded)


def _parse_lcov(text: str, root: Path | None) -> CoverageData:
    """LCOV: `SF:<arquivo>` abre um registro, `DA:<linha>,<execucoes>` descreve
    cada linha instrumentada, `end_of_record` fecha. Conjuntos, nao listas: relatorios
    mesclados repetem o mesmo DA e a contagem sairia inflada."""
    instrumented: dict[str, set[int]] = {}
    hit: dict[str, set[int]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("SF:"):
            current = _relative(line[3:].strip(), root)
            instrumented.setdefault(current, set())
        elif line == "end_of_record":
            current = None
        elif line.startswith("DA:") and current is not None:
            parts = line[3:].split(",")
            if len(parts) < 2:
                continue
            number, count = int(parts[0]), int(float(parts[1]))
            instrumented[current].add(number)
            if count > 0:
                hit.setdefault(current, set()).add(number)
    if not instrumented:
        raise ValueError("nenhum registro SF:/DA: encontrado no relatorio lcov")
    return _from_line_hits(instrumented, hit)


def _parse_cobertura(text: str, root: Path | None) -> CoverageData:
    """Cobertura XML: `<class filename=...>` agrupa `<line number= hits=>`. Varias
    classes podem compartilhar o mesmo arquivo, entao os registros sao acumulados."""
    document = ET.fromstring(text)
    instrumented: dict[str, set[int]] = {}
    hit: dict[str, set[int]] = {}
    for element in document.iter("class"):
        filename = element.get("filename")
        if not filename:
            continue
        normalized = _relative(filename, root)
        instrumented.setdefault(normalized, set())
        for line in element.iter("line"):
            number = int(line.get("number", 0))
            if not number:
                continue
            instrumented[normalized].add(number)
            if int(float(line.get("hits", 0))) > 0:
                hit.setdefault(normalized, set()).add(number)
    if not instrumented:
        raise ValueError("nenhum <class filename=...> encontrado no relatorio cobertura")
    rate = document.get("line-rate")
    return _from_line_hits(instrumented, hit, float(rate) * 100 if rate is not None else None)


_COVERAGE_PARSERS = {
    "coverage.py": _parse_coverage_py,
    "lcov": _parse_lcov,
    "cobertura": _parse_cobertura,
}


class CoverageAdapter:
    def read(self, path: Path, declared_format: str | None = None, root: Path | None = None) -> CoverageData:
        if not path.exists():
            return CoverageData(None, {}, error="arquivo de cobertura ausente")
        try:
            text = path.read_text(encoding="utf-8")
            fmt = declared_format or detect_coverage_format(text)
            if fmt not in _COVERAGE_PARSERS:
                known = ", ".join(COVERAGE_FORMATS)
                return CoverageData(None, {}, error=(
                    f"formato de cobertura nao reconhecido em {path.name}"
                    f"; declare [coverage] format em sentry.toml (aceitos: {known})"
                ))
            return _COVERAGE_PARSERS[fmt](text, root)
        except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as error:
            return CoverageData(None, {}, error=f"formato de cobertura invalido: {error}")
