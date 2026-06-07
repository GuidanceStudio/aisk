from aisk.cli import main
from aisk.completions import (
    generate_bash,
    generate_powershell,
    generate_refresh,
    generate_shortcuts,
    generate_zsh,
    install_completions,
)
from aisk.config import Config, DEFAULT_ALIASES, DEFAULT_SHORTCUTS


def test_bash_contains_aliases():
    script = generate_bash()
    assert "complete -F _aisk_completions aisk" in script
    for alias in ("gel", "cls", "s", "sps", "gpt"):
        assert alias in script


def test_bash_contains_subcommands():
    script = generate_bash()
    assert "init" in script
    assert "models" in script
    assert "completions" in script
    assert "sync" in script
    # help must be in the subcommands list, not just --help flag
    assert "sync models shortcuts completions help" in script


def test_bash_completes_after_no_stream_flags():
    """Model completion triggers after -S/--no-stream, and the flags are offered."""
    script = generate_bash()
    assert '"$prev" == "-S"' in script
    assert '"$prev" == "--no-stream"' in script
    assert "-S --no-stream" in script


def test_zsh_completes_after_no_stream_flags():
    script = generate_zsh()
    assert '"${words[2]}" == "-S"' in script
    assert '"${words[2]}" == "--no-stream"' in script
    assert "-S --no-stream" in script


def test_zsh_contains_aliases():
    script = generate_zsh()
    assert "#compdef aisk" in script
    for alias in ("gel", "cls", "s", "sps", "gpt"):
        assert alias in script


def test_zsh_contains_subcommands():
    script = generate_zsh()
    assert "init" in script
    assert "models" in script
    assert "completions" in script
    assert "sync" in script
    # help must be in the subcommands array, not just --help flag
    assert "init sync models shortcuts completions help" in script


def test_powershell_contains_aliases_subcommands_flags_and_shortcuts():
    script = generate_powershell()
    assert "Register-ArgumentCompleter -Native -CommandName aisk" in script
    for alias in ("gel", "cls", "s", "sps", "gpt"):
        assert f"'{alias}'" in script
    assert "'init'" in script
    assert "'sync'" in script
    assert "'--resume'" in script
    assert "'-S'" in script
    assert "function ds { aisk dsf @args }" in script
    assert "function news { aisk sps @args }" in script


def test_cli_completions_bash(capsys):
    assert main(["completions", "bash"]) == 0
    out = capsys.readouterr().out
    assert "complete -F" in out


def test_cli_completions_zsh(capsys):
    assert main(["completions", "zsh"]) == 0
    out = capsys.readouterr().out
    assert "#compdef aisk" in out


def test_cli_completions_powershell(capsys):
    assert main(["completions", "powershell"]) == 0
    out = capsys.readouterr().out
    assert "Register-ArgumentCompleter" in out


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


def test_install_completions_powershell_fresh(tmp_path, monkeypatch):
    monkeypatch.delenv("SHELL", raising=False)
    monkeypatch.setenv("PSModulePath", "C:\\Modules")
    monkeypatch.setattr("aisk.completions.Path.home", lambda: tmp_path)

    result = install_completions()

    profile = tmp_path / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    assert "installed" in result
    assert profile.exists()
    assert "aisk completions powershell | Invoke-Expression" in profile.read_text()


def test_install_completions_powershell_no_duplicate(tmp_path, monkeypatch):
    monkeypatch.delenv("SHELL", raising=False)
    monkeypatch.setenv("PSModulePath", "C:\\Modules")
    monkeypatch.setattr("aisk.completions.Path.home", lambda: tmp_path)
    profile = tmp_path / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    profile.parent.mkdir(parents=True)
    profile.write_text("aisk completions powershell | Invoke-Expression\n")

    result = install_completions()

    assert "already installed" in result
    assert profile.read_text().count("aisk completions powershell") == 1


def test_refresh_generates_script(monkeypatch):
    """Refresh outputs a valid completion script for current shell."""
    monkeypatch.setenv("SHELL", "/bin/bash")
    script = generate_refresh()
    assert "complete -F _aisk_completions aisk" in script
    assert "gel" in script


def test_refresh_generates_powershell(monkeypatch):
    monkeypatch.delenv("SHELL", raising=False)
    monkeypatch.setenv("PSModulePath", "C:\\Modules")
    script = generate_refresh()
    assert "Register-ArgumentCompleter" in script


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
    assert 'ds() { aisk dsf "$@"; }' in output
    assert 'news() { aisk sps "$@"; }' in output


def test_generate_shortcuts_empty():
    """No shortcuts → empty string."""
    cfg = Config(shortcuts={})
    assert generate_shortcuts(cfg) == ""


def test_generate_shortcuts_custom():
    """Custom shortcuts produce correct shell functions."""
    cfg = Config(shortcuts={"gpt": "gpt", "cl": "cls"})
    output = generate_shortcuts(cfg)
    assert 'gpt() { aisk gpt "$@"; }' in output
    assert 'cl() { aisk cls "$@"; }' in output


def test_bash_includes_shortcuts():
    """Bash completion script includes shortcuts at the end."""
    script = generate_bash()
    assert "complete -F _aisk_completions aisk" in script
    assert 'ds() { aisk dsf "$@"; }' in script


def test_zsh_includes_shortcuts():
    """Zsh completion script includes shortcuts at the end."""
    script = generate_zsh()
    assert "#compdef aisk" in script
    assert 'ds() { aisk dsf "$@"; }' in script


def test_cli_shortcuts(capsys):
    """aisk shortcuts prints the generated functions."""
    assert main(["shortcuts"]) == 0
    out = capsys.readouterr().out
    assert 'ds() { aisk dsf "$@"; }' in out
    assert 'news() { aisk sps "$@"; }' in out


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
        '[shortcuts]\nmyds = "dsf"\nmysps = "sps"\n'
    )
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    output = generate_shortcuts()
    assert 'myds() { aisk dsf "$@"; }' in output
    assert 'mysps() { aisk sps "$@"; }' in output
    # Defaults are merged
    assert 'ds() { aisk dsf "$@"; }' in output


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
    assert 'ds() { aisk dsf "$@"; }' in out
