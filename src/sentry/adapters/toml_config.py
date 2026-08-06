from __future__ import annotations
from pathlib import Path

def load_config(root: Path) -> dict:
    path = root / "sentry.toml"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import tomllib
        return tomllib.loads(text)
    except ModuleNotFoundError:
        return _parse_simple_toml(text)

def _parse_simple_toml(text: str) -> dict:
    result: dict = {}
    section = result
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = result.setdefault(line[1:-1].strip(), {})
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            section[key.strip()] = _parse_value(value.strip())
    return result

def _parse_value(value: str):
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value
