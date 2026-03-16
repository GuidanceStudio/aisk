import io
from unittest.mock import patch

from aisk import __version__
from aisk.cli import main


def test_version(capsys):
    try:
        main(["--version"])
    except SystemExit:
        pass
    assert __version__ in capsys.readouterr().out


def test_no_args_returns_2(capsys):
    assert main([]) == 2


def test_init_subcommand(capsys):
    assert main(["init"]) == 0
    assert "init" in capsys.readouterr().out


def test_models_subcommand(capsys):
    assert main(["models"]) == 0
    assert "models" in capsys.readouterr().out


def test_model_and_message(capsys):
    assert main(["ge3flash", "hello"]) == 0
    out = capsys.readouterr().out
    assert "ge3flash" in out
    assert "hello" in out


def test_quiet_flag(capsys):
    assert main(["-q", "ge3flash", "hello"]) == 0
    assert "quiet=True" in capsys.readouterr().out


def test_model_no_message_tty(capsys):
    with patch("aisk.cli.sys.stdin") as mock_stdin:
        mock_stdin.isatty.return_value = True
        assert main(["ge3flash"]) == 2


def test_model_stdin_message(capsys):
    with patch("aisk.cli.sys.stdin", io.StringIO("from stdin")):
        assert main(["ge3flash"]) == 0
    assert "from stdin" in capsys.readouterr().out


def test_model_empty_stdin():
    with patch("aisk.cli.sys.stdin", io.StringIO("")):
        assert main(["ge3flash"]) == 2


def test_passthrough_model(capsys):
    assert main(["perplexity/sonar", "test"]) == 0
    assert "perplexity/sonar" in capsys.readouterr().out
