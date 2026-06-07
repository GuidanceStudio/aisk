from __future__ import annotations

import os
from pathlib import Path

from aisk.config import load_config

SUBCOMMANDS = ("init", "sync", "models", "shortcuts", "completions", "help")
FLAGS = ("-q", "--quiet", "-S", "--no-stream", "--resume", "--version", "--help")
MODEL_POSITION_FLAGS = ("-q", "--quiet", "-S", "--no-stream")

BASH_TEMPLATE = """\
_aisk_completions() {{
    local cur prev
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    if [[ $COMP_CWORD -eq 1 ]] || [[ "$prev" == "-q" ]] || [[ "$prev" == "--quiet" ]] || [[ "$prev" == "-S" ]] || [[ "$prev" == "--no-stream" ]]; then
        local models="{models}"
        local subcommands="{subcommands}"
        COMPREPLY=( $(compgen -W "$models $subcommands" -- "$cur") )
    elif [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "{flags}" -- "$cur") )
    fi
}}
complete -F _aisk_completions aisk
"""

ZSH_TEMPLATE = """\
#compdef aisk

_aisk() {{
    local -a models subcommands flags
    models=({models})
    subcommands=({subcommands})
    flags=({flags})

    if (( CURRENT == 2 )) || [[ "${{words[2]}}" == "-q" ]] || [[ "${{words[2]}}" == "--quiet" ]] || [[ "${{words[2]}}" == "-S" ]] || [[ "${{words[2]}}" == "--no-stream" ]]; then
        _describe 'model or command' models -- subcommands -- flags
    fi
}}

_aisk "$@"
"""

POWERSHELL_TEMPLATE = """\
$script:aiskModels = @({models})
$script:aiskSubcommands = @({subcommands})
$script:aiskFlags = @({flags})
$script:aiskModelPositionFlags = @({model_position_flags})

Register-ArgumentCompleter -Native -CommandName aisk -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)

    $elements = @($commandAst.CommandElements | ForEach-Object {{ $_.Extent.Text }})
    $previous = if ($elements.Count -ge 2) {{ $elements[$elements.Count - 2] }} else {{ "" }}
    $choices = @()

    if ($elements.Count -le 2 -or $script:aiskModelPositionFlags -contains $previous) {{
        $choices += $script:aiskModels + $script:aiskSubcommands + $script:aiskFlags
    }} elseif ($wordToComplete.StartsWith("-")) {{
        $choices += $script:aiskFlags
    }}

    $choices |
        Where-Object {{ $_ -like "$wordToComplete*" }} |
        Sort-Object -Unique |
        ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)
        }}
}}
"""


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _ps_array(items) -> str:
    return ", ".join(_ps_quote(item) for item in items)


def generate_shortcuts(cfg=None) -> str:
    """Generate shell functions from [shortcuts] in conf.toml."""
    if cfg is None:
        cfg = load_config()
    if not cfg.shortcuts:
        return ""
    lines = ["", "# aisk shortcuts"]
    for name, alias in sorted(cfg.shortcuts.items()):
        lines.append(f'{name}() {{ aisk {alias} "$@"; }}')
    return "\n".join(lines) + "\n"


def generate_powershell_shortcuts(cfg=None) -> str:
    """Generate PowerShell shortcut functions from [shortcuts] in conf.toml."""
    if cfg is None:
        cfg = load_config()
    if not cfg.shortcuts:
        return ""
    lines = ["", "# aisk shortcuts"]
    for name, alias in sorted(cfg.shortcuts.items()):
        lines.append(f"function {name} {{ aisk {alias} @args }}")
    return "\n".join(lines) + "\n"


def generate_bash() -> str:
    """Generate bash completion script with current aliases and shortcuts."""
    cfg = load_config()
    models = " ".join(sorted(cfg.aliases.keys()))
    return BASH_TEMPLATE.format(
        models=models,
        subcommands=" ".join(SUBCOMMANDS),
        flags=" ".join(FLAGS),
    ) + generate_shortcuts(cfg)


def generate_zsh() -> str:
    """Generate zsh completion script with current aliases and shortcuts."""
    cfg = load_config()
    models = " ".join(sorted(cfg.aliases.keys()))
    return ZSH_TEMPLATE.format(
        models=models,
        subcommands=" ".join(SUBCOMMANDS),
        flags=" ".join(FLAGS),
    ) + generate_shortcuts(cfg)


def generate_powershell() -> str:
    """Generate PowerShell completion script with current aliases and shortcuts."""
    cfg = load_config()
    return POWERSHELL_TEMPLATE.format(
        models=_ps_array(sorted(cfg.aliases.keys())),
        subcommands=_ps_array(SUBCOMMANDS),
        flags=_ps_array(FLAGS),
        model_position_flags=_ps_array(MODEL_POSITION_FLAGS),
    ) + generate_powershell_shortcuts(cfg)


def _detect_shell() -> str:
    """Detect current shell: 'bash', 'zsh', or 'powershell'."""
    shell = os.environ.get("SHELL", "").lower()
    if "zsh" in shell:
        return "zsh"
    if "bash" in shell:
        return "bash"
    if os.name == "nt" or os.environ.get("PSModulePath"):
        return "powershell"
    return "bash"


def _rc_file(shell: str) -> Path:
    """Return the rc file path for the given shell."""
    if shell == "powershell":
        profile = os.environ.get("AISK_POWERSHELL_PROFILE")
        if profile:
            return Path(profile)
        return Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    if shell == "zsh":
        return Path.home() / ".zshrc"
    return Path.home() / ".bashrc"


_EVAL_LINES = {
    "bash": 'eval "$(aisk completions bash)"',
    "zsh": 'eval "$(aisk completions zsh)"',
    "powershell": "aisk completions powershell | Invoke-Expression",
}


def install_completions() -> str:
    """Append eval line to the user's shell rc file. Returns status message."""
    shell = _detect_shell()
    rc = _rc_file(shell)
    eval_line = _EVAL_LINES[shell]

    if rc.exists() and eval_line in rc.read_text():
        return f"already installed in {rc}"

    rc.parent.mkdir(parents=True, exist_ok=True)
    with open(rc, "a") as f:
        f.write(f"\n# aisk shell completions\n{eval_line}\n")

    if shell == "powershell":
        return f"installed in {rc} — open a new PowerShell window"
    return f"installed in {rc} — run `source {rc}` or open a new terminal"


def generate_refresh() -> str:
    """Generate completion script for the current shell (auto-detected)."""
    shell = _detect_shell()
    if shell == "powershell":
        return generate_powershell()
    if shell == "zsh":
        return generate_zsh()
    return generate_bash()
