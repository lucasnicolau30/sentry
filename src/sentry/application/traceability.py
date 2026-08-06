from __future__ import annotations
import re
from pathlib import Path
from ..ports.inputs import SpecScenario

_MARKER = re.compile(r"(?:scenario|cenario)\s*[:=]\s*([^\n#]+)", re.IGNORECASE)

def _associated_tests(tests: dict[str, list[str]], scenario_name: str) -> list[str]:
    associated = []
    for key, paths_for_key in tests.items():
        name = scenario_name.casefold()
        if key == name or key in name or name in key:
            associated.extend(paths_for_key)
    return sorted(set(associated))

def build_traceability(specs: tuple[SpecScenario, ...], root: Path, behaviors: tuple[str, ...] = ()) -> dict:
    tests = {}
    paths = sorted((root / "tests").rglob("*.py")) if (root / "tests").exists() else ()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in _MARKER.finditer(text):
            name = match.group(1).strip().strip("'""")
            tests.setdefault(name.casefold(), []).append(str(path.relative_to(root)))
    scenarios = []
    missing = []
    for scenario in specs:
        associated = _associated_tests(tests, scenario.name)
        scenarios.append({"name": scenario.name, "tests": associated, "covered": bool(associated)})
        if not associated:
            missing.append(scenario.name)
    requirements_without_scenarios = []
    for behavior in behaviors:
        if not any(_associated_tests(tests, behavior) or scenario.name.casefold() == behavior.casefold() or behavior.casefold() in scenario.name.casefold() for scenario in specs):
            requirements_without_scenarios.append(behavior)
    return {"scenarios": scenarios, "scenarios_without_tests": missing, "requirements_without_scenarios": requirements_without_scenarios}
