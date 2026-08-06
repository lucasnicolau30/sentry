from pathlib import Path
from sentry.adapters.toml_config import load_config, _parse_simple_toml, _parse_value

def test_load_config_returns_empty_when_file_missing(tmp_path: Path):
    assert load_config(tmp_path) == {}

def test_load_config_reads_sections(tmp_path: Path):
    (tmp_path / "sentry.toml").write_text(
        '[draun]\nspecs_path = ".draun/specs"\n\n[analysis]\nrun_tests_by_default = false\ntimeout_seconds = 300\n',
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config["draun"]["specs_path"] == ".draun/specs"
    assert config["analysis"]["run_tests_by_default"] is False
    assert config["analysis"]["timeout_seconds"] == 300

def test_parse_simple_toml_handles_sections_and_types():
    text = (
        "# comentario ignorado\n"
        "[project]\n"
        'name = "meu-projeto"\n'
        "\n"
        "[analysis]\n"
        "run_tests_by_default = true\n"
        "timeout_seconds = 300\n"
    )
    result = _parse_simple_toml(text)
    assert result == {
        "project": {"name": "meu-projeto"},
        "analysis": {"run_tests_by_default": True, "timeout_seconds": 300},
    }

def test_parse_value_handles_bool_string_int_float_and_fallback():
    assert _parse_value("true") is True
    assert _parse_value("false") is False
    assert _parse_value('"pytest"') == "pytest"
    assert _parse_value("300") == 300
    assert _parse_value("1.5") == 1.5
    assert _parse_value("unquoted") == "unquoted"
