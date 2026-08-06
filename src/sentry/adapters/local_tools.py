from __future__ import annotations
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from ..domain.models import TestStatus
from ..ports.inputs import GitChange, TestExecution, CoverageData

class LocalGitAdapter:
    def __init__(self, root: Path):
        self.root = root

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=False)

    def change(self, reference: str | None = None) -> GitChange:
        revision = self._run("rev-parse", "HEAD")
        if revision.returncode != 0:
            return GitChange(None, reference, (), error="diretorio nao e um repositorio Git")
        current = revision.stdout.strip()
        base = reference or "HEAD"
        status = self._run("diff", "--name-status", base)
        diff = self._run("diff", "--unified=0", base)
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
                    line_count = len((self.root / name).read_text(encoding="utf8").splitlines())
                except (OSError, UnicodeDecodeError):
                    continue
                changed_lines[name] = tuple(range(1, line_count + 1))
        return GitChange(current, reference or "HEAD", tuple(statuses), diff=diff.stdout, statuses=statuses, changed_lines=changed_lines)

def is_generated_artifact(name: str) -> bool:
    return name.startswith(".sentry/") or "/__pycache__/" in name or name.endswith(".pyc") or name == ".coverage" or ".egg-info/" in name or name == ".pytest_cache" or name.startswith(".pytest_cache/") or name.endswith(".pyo")
def _count(pattern: str, text: str) -> int:
    match = re.search(pattern, text)
    return int(match.group(1)) if match else 0

class PytestAdapter:
    def __init__(self, root: Path, command: str = "pytest"):
        self.root = root
        args = command.split()
        self.command = [sys.executable, "-m", "coverage", "run", "-m"] + args if args and args[0] == "pytest" else args

    def run(self, coverage_file: Path, timeout_seconds: int = 300) -> tuple[TestExecution, float | None]:
        command_str = " ".join(self.command)
        started = time.perf_counter()
        try:
            result = subprocess.run(self.command, cwd=self.root, text=True, capture_output=True, timeout=timeout_seconds)
        except (FileNotFoundError, subprocess.TimeoutExpired) as error:
            execution = TestExecution(command_str, infrastructure_error=str(error), status=TestStatus.NOT_RUN, duration_seconds=time.perf_counter() - started)
            return execution, None
        duration = time.perf_counter() - started
        output = result.stdout + result.stderr
        passed = _count(r"(\d+) passed", output)
        failed = _count(r"(\d+) failed", output) or (0 if result.returncode == 0 else 1)
        skipped = _count(r"(\d+) skipped", output)
        collected = _count(r"(\d+) collected", output)
        deselected = _count(r"(\d+) deselected", output)
        not_run = deselected if deselected else max(0, collected - (passed + failed + skipped)) if collected else 0
        subprocess.run([sys.executable, "-m", "coverage", "json", "-o", str(coverage_file)], cwd=self.root, text=True, capture_output=True)
        percent = None
        if coverage_file.exists():
            data = json.loads(coverage_file.read_text(encoding="utf8"))
            percent = data.get("totals", {}).get("percent_covered")
        status = TestStatus.COVERED if result.returncode == 0 else TestStatus.FAILED
        execution = TestExecution(command_str, passed=passed, failed=failed, skipped=skipped, not_run=not_run, output=output[-4000:], infrastructure_error=None, status=status, duration_seconds=round(duration, 2))
        return execution, percent

class CoverageAdapter:
    def read(self, path: Path) -> CoverageData:
        if not path.exists():
            return CoverageData(None, {}, error="arquivo de cobertura ausente")
        try:
            import json
            data = json.loads(path.read_text(encoding="utf8"))
            files = {}
            executed = {}
            for filename, payload in data.get("files", {}).items():
                normalized = filename.replace("\\", "/")
                summary = payload.get("summary", {})
                files[normalized] = summary.get("percent_covered")
                executed[normalized] = tuple(payload.get("executed_lines", []))
            total = data.get("totals", {}).get("percent_covered")
            return CoverageData(total, files, executed_lines=executed)
        except (OSError, ValueError, TypeError, KeyError) as error:
            return CoverageData(None, {}, error=f"formato de cobertura invalido: {error}")
