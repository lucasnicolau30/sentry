from __future__ import annotations
import tomllib
from pathlib import Path

def load_config(root: Path) -> dict:
    path = root / "sentry.toml"
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))
