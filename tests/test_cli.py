from sentry import __version__
from sentry.cli import main


def test_cli_returns_success_without_arguments() -> None:
    assert main([]) == 0


def test_cli_version(capsys) -> None:
    try:
        main(["--version"])
    except SystemExit as error:
        assert error.code == 0

    assert capsys.readouterr().out.strip() == __version__