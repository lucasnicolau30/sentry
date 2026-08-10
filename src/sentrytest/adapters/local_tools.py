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

    def change(self, reference: str | None = None) -> GitChange:
        revision = self._run("rev-parse", "HEAD")
        if revision.returncode != 0:
            return GitChange(None, reference, (), error="diretorio nao e um repositorio Git")
        current = revision.stdout.strip()
        base = reference or "HEAD"
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
        statuses = {name: value for name, value in statuses.items() if not is_generated_artifact(name)}
        changed_lines = {}
        current_file = None
        for line in diff.stdout.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:]
            elif line.startswith("@@") and current_file:
                if is_generated_artifact(current_file):
                    continue
                match = re.search(r"\+(\d+)(?:,(\d+))?", line)
                if match:
                    start_line = int(match.group(1))
                    count = int(match.group(2) or "1")
                    changed_lines[current_file] = tuple(range(start_line, start_line + count))
        for name, value in statuses.items():
            if value == "A" and name not in changed_lines and name.endswith(".py"):
                try:
                    line_count = len((self.root / name).read_text(encoding="utf-8").splitlines())
                except (OSError, UnicodeDecodeError):
                    continue
                changed_lines[name] = tuple(range(1, line_count + 1))
        return GitChange(current, reference or "HEAD", tuple(statuses), diff=diff.stdout, statuses=statuses, changed_lines=changed_lines)

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

def _counts_from_regex(output: str, returncode: int) -> tuple[int, int, int, int]:
    passed = _count(r"(\d+) passed", output)
    failed = _count(r"(\d+) failed", output) or (0 if returncode == 0 else 1)
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

class SuiteAdapter:
    """Executa a suite declarada pelo projeto, seja ela pytest ou nao.

    Com `junit_xml` declarado, o projeto ja configurou o proprio reporter
    (jest-junit, gotestsum, surefire, coverlet...) e o Sentry apenas le o
    arquivo; injetar `--junitxml` quebraria o comando dele. Sem declaracao,
    mantem o caminho Python: embrulha em `coverage run` e injeta a flag.
    """

    def __init__(self, root: Path, command: str = "pytest", junit_xml: str | None = None):
        self.root = root
        self.junit_xml = junit_xml
        args = command.split()
        self.is_pytest = bool(args) and args[0] == "pytest"
        self.command = [sys.executable, "-m", "coverage", "run", "-m", *args] if self.is_pytest else args

    def _classify(self, returncode: int, ran: bool) -> str | None:
        if self.is_pytest:
            return PYTEST_INFRA_EXITS.get(returncode)
        # Fora do pytest nao existe tabela confiavel de codigos de saida. O sinal
        # honesto e' a evidencia: sem nenhum teste contabilizado, nao ha prova de
        # que a suite rodou -- isso e' ambiente, nao qualidade do codigo.
        if not ran:
            return f"nenhum teste contabilizado (codigo de saida {returncode})"
        return None

    def run(self, coverage_file: Path, timeout_seconds: int = 300) -> tuple[TestExecution, float | None]:
        command_str = " ".join(self.command)
        started = time.perf_counter()
        with tempfile.TemporaryDirectory() as temp_dir:
            if self.junit_xml:
                report_path = self.root / self.junit_xml
                command = list(self.command)
            else:
                report_path = Path(temp_dir) / "junit.xml"
                command = [*self.command, "--junitxml", str(report_path)]
            try:
                result = subprocess.run(command, cwd=self.root, capture_output=True, timeout=timeout_seconds, **DECODING)
            except (FileNotFoundError, subprocess.TimeoutExpired) as error:
                execution = TestExecution(command_str, infrastructure_error=str(error), status=TestStatus.NOT_RUN, duration_seconds=time.perf_counter() - started)
                return execution, None
            duration = time.perf_counter() - started
            output = result.stdout + result.stderr
            counts = _counts_from_junitxml(report_path)
            if counts is None:
                counts = _counts_from_regex(output, result.returncode)
            passed, failed, skipped, not_run = counts
            if not not_run:
                _, _, _, not_run = _counts_from_regex(output, result.returncode)
        percent = None
        if self.is_pytest:
            subprocess.run([sys.executable, "-m", "coverage", "json", "-o", str(coverage_file)], cwd=self.root, capture_output=True, **DECODING)
            if coverage_file.exists():
                data = json.loads(coverage_file.read_text(encoding="utf-8"))
                percent = data.get("totals", {}).get("percent_covered")
        infrastructure_error = self._classify(result.returncode, passed + failed + skipped > 0)
        if infrastructure_error:
            status = TestStatus.NOT_RUN
        else:
            status = TestStatus.COVERED if result.returncode == 0 else TestStatus.FAILED
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
