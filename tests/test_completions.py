from aisk.cli import main
from aisk.completions import generate_bash, generate_refresh, generate_shortcuts, generate_zsh, install_completions
from aisk.config import Config, DEFAULT_ALIASES, DEFAULT_SHORTCUTS


def test_bash_contains_aliases():
    script = generate_bash()
    assert "complete -F _aisk_completions aisk" in script
    for alias in ("ge31lite", "cls46", "s", "sps", "gpt5"):
        assert alias in script


def test_bash_contains_subcommands():
    script = generate_bash()
    assert "init" in script
    assert "models" in script
    assert "completions" in script


def test_zsh_contains_aliases():
    script = generate_zsh()
    assert "#compdef aisk" in script
    for alias in ("ge31lite", "cls46", "s", "sps", "gpt5"):
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
    assert "ge31lite" in script


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


# --- Shortcuts ---


def test_generate_shortcuts_default():
    """Default shortcuts produce correct shell functions."""
    output = generate_shortcuts()
    assert 'ds() { aisk dsv32 "$@"; }' in output
    assert 'sps() { aisk sps "$@"; }' in output


def test_generate_shortcuts_empty():
    """No shortcuts → empty string."""
    cfg = Config(shortcuts={})
    assert generate_shortcuts(cfg) == ""


def test_generate_shortcuts_custom():
    """Custom shortcuts produce correct shell functions."""
    cfg = Config(shortcuts={"gpt": "gpt54", "cl": "cls46"})
    output = generate_shortcuts(cfg)
    assert 'gpt() { aisk gpt54 "$@"; }' in output
    assert 'cl() { aisk cls46 "$@"; }' in output


def test_bash_includes_shortcuts():
    """Bash completion script includes shortcuts at the end."""
    script = generate_bash()
    assert "complete -F _aisk_completions aisk" in script
    assert 'ds() { aisk dsv32 "$@"; }' in script


def test_zsh_includes_shortcuts():
    """Zsh completion script includes shortcuts at the end."""
    script = generate_zsh()
    assert "#compdef aisk" in script
    assert 'ds() { aisk dsv32 "$@"; }' in script


def test_cli_shortcuts(capsys):
    """aisk shortcuts prints the generated functions."""
    assert main(["shortcuts"]) == 0
    out = capsys.readouterr().out
    assert 'ds() { aisk dsv32 "$@"; }' in out
    assert 'sps() { aisk sps "$@"; }' in out


def test_shortcuts_subcommand_in_completions():
    """The 'shortcuts' subcommand is included in completion scripts."""
    script = generate_bash()
    assert "shortcuts" in script


# --- Integration: shortcuts loaded from conf.toml ---


def test_shortcuts_from_custom_conf(tmp_path, monkeypatch):
    """Full flow: custom conf.toml with shortcuts → generate_shortcuts → correct output."""
    conf = tmp_path / "conf.toml"
    conf.write_text(
        '[api]\nendpoint = "https://openrouter.ai/api/v1/chat/completions"\n\n'
        '[shortcuts]\nmyds = "dsv32"\nmysps = "sps"\n'
    )
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    output = generate_shortcuts()
    assert 'myds() { aisk dsv32 "$@"; }' in output
    assert 'mysps() { aisk sps "$@"; }' in output
    # Defaults are merged
    assert 'ds() { aisk dsv32 "$@"; }' in output


def test_shortcuts_in_eval_flow(tmp_path, monkeypatch):
    """Full eval flow: bash completions include both completions and shortcuts."""
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    script = generate_bash()
    # Completions part
    assert "complete -F _aisk_completions aisk" in script
    # Shortcuts part comes after
    completions_end = script.index("complete -F _aisk_completions aisk")
    shortcuts_start = script.index("# aisk shortcuts")
    assert shortcuts_start > completions_end


def test_cli_shortcuts_no_config(capsys, tmp_path, monkeypatch):
    """aisk shortcuts with empty shortcuts section shows message."""
    conf = tmp_path / "conf.toml"
    conf.write_text('[api]\nendpoint = "https://openrouter.ai/api/v1/chat/completions"\n\n[shortcuts]\n')
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    # With empty [shortcuts] in toml, defaults are not overridden — they still exist
    # So this test validates the default shortcuts still show up
    assert main(["shortcuts"]) == 0
    out = capsys.readouterr().out
    assert 'ds() { aisk dsv32 "$@"; }' in out
