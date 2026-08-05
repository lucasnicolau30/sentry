from pathlib import Path
from sentry.init_project import initialize_project

def test_initialize_project_is_idempotent(tmp_path: Path) -> None:
    first=initialize_project(tmp_path)
    second=initialize_project(tmp_path)
    assert 'sentry.toml' in first
    assert second == []
    assert (tmp_path/'.sentry'/'sentry.db').exists()
    assert (tmp_path/'.gitignore').read_text().count('.sentry/sentry.db') == 1