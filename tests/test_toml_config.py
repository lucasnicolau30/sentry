from pathlib import Path
from sentrytest.adapters.toml_config import load_config

def test_load_config_returns_empty_when_file_missing(tmp_path: Path):
    assert load_config(tmp_path) == {}

def test_load_config_reads_sections(tmp_path: Path):
    (tmp_path / "sentry.toml").write_text(
        '[specs]\npath = ".sentry/specs"\n\n[analysis]\nrun_tests_by_default = false\ntimeout_seconds = 300\n',
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config["specs"]["path"] == ".sentry/specs"
    assert config["analysis"]["run_tests_by_default"] is False
    assert config["analysis"]["timeout_seconds"] == 300

def test_load_config_reads_nested_tables(tmp_path: Path):
    """tomllib entende estruturas que o parser artesanal anterior nao suportava."""
    (tmp_path / "sentry.toml").write_text(
        '[catalog.fields]\nmatricula = ["vazio", "formato-invalido", "valida"]\n\n'
        '[policy.severities]\ncoverage-missing = "alta"\n',
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config["catalog"]["fields"]["matricula"] == ["vazio", "formato-invalido", "valida"]
    assert config["policy"]["severities"]["coverage-missing"] == "alta"

def test_limiares_chegam_do_toml_ate_o_contexto(tmp_path: Path):
    """[policy.thresholds] no sentry.toml vira Thresholds na avaliacao."""
    from sentrytest.application.analyze import _thresholds
    (tmp_path / "sentry.toml").write_text(
        '[policy.thresholds]\nchanged_coverage = 80\nglobal_coverage = 60.5\n',
        encoding="utf-8",
    )
    limiares = _thresholds(load_config(tmp_path))
    assert limiares.changed_coverage == 80.0
    assert limiares.global_coverage == 60.5

def test_limiar_invalido_e_ignorado_em_vez_de_quebrar(tmp_path: Path):
    from sentrytest.application.analyze import _thresholds
    (tmp_path / "sentry.toml").write_text(
        '[policy.thresholds]\nchanged_coverage = "oitenta"\n', encoding="utf-8")
    assert _thresholds(load_config(tmp_path)).changed_coverage is None
