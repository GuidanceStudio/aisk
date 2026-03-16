from aisk.cli import main
from aisk.completions import generate_bash, generate_zsh
from aisk.config import DEFAULT_ALIASES


def test_bash_contains_aliases():
    script = generate_bash()
    assert "complete -F _aisk_completions aisk" in script
    for alias in ("ge3flash", "cls46", "s", "sps", "gpt5"):
        assert alias in script


def test_bash_contains_subcommands():
    script = generate_bash()
    assert "init" in script
    assert "models" in script
    assert "completions" in script


def test_zsh_contains_aliases():
    script = generate_zsh()
    assert "#compdef aisk" in script
    for alias in ("ge3flash", "cls46", "s", "sps", "gpt5"):
        assert alias in script


def test_zsh_contains_subcommands():
    script = generate_zsh()
    assert "init" in script
    assert "models" in script
    assert "completions" in script


def test_cli_completions_bash(capsys):
    assert main(["completions", "bash"]) == 0
    out = capsys.readouterr().out
    assert "complete -F" in out


def test_cli_completions_zsh(capsys):
    assert main(["completions", "zsh"]) == 0
    out = capsys.readouterr().out
    assert "#compdef aisk" in out


def test_cli_completions_no_shell(capsys):
    assert main(["completions"]) == 2


def test_cli_completions_invalid_shell(capsys):
    assert main(["completions", "fish"]) == 2
