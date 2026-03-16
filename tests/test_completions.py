from aisk.cli import main
from aisk.completions import generate_bash, generate_refresh, generate_zsh, install_completions
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


def test_install_completions_fresh(tmp_path, monkeypatch):
    """Appends eval line to rc file on fresh install."""
    bashrc = tmp_path / ".bashrc"
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setattr("aisk.completions.Path.home", lambda: tmp_path)
    result = install_completions()
    assert "installed" in result
    content = bashrc.read_text()
    assert 'eval "$(aisk completions bash)"' in content


def test_install_completions_no_duplicate(tmp_path, monkeypatch):
    """Does not duplicate eval line if already present."""
    bashrc = tmp_path / ".bashrc"
    bashrc.write_text('eval "$(aisk completions bash)"\n')
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setattr("aisk.completions.Path.home", lambda: tmp_path)
    result = install_completions()
    assert "already installed" in result
    assert bashrc.read_text().count("aisk completions bash") == 1


def test_install_completions_zsh(tmp_path, monkeypatch):
    """Installs zsh completions to .zshrc."""
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr("aisk.completions.Path.home", lambda: tmp_path)
    install_completions()
    zshrc = tmp_path / ".zshrc"
    assert zshrc.exists()
    assert 'eval "$(aisk completions zsh)"' in zshrc.read_text()


def test_refresh_generates_script(monkeypatch):
    """Refresh outputs a valid completion script for current shell."""
    monkeypatch.setenv("SHELL", "/bin/bash")
    script = generate_refresh()
    assert "complete -F _aisk_completions aisk" in script
    assert "ge3flash" in script


def test_cli_completions_install(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setattr("aisk.completions.Path.home", lambda: tmp_path)
    assert main(["completions", "install"]) == 0
    assert "installed" in capsys.readouterr().out


def test_cli_completions_refresh(capsys, monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/bash")
    assert main(["completions", "refresh"]) == 0
    out = capsys.readouterr().out
    assert "complete -F" in out
