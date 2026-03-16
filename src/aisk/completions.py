from __future__ import annotations

import os
from pathlib import Path

from aisk.config import load_config

BASH_TEMPLATE = """\
_aisk_completions() {{
    local cur prev
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    if [[ $COMP_CWORD -eq 1 ]]; then
        local models="{models}"
        local subcommands="init models completions"
        COMPREPLY=( $(compgen -W "$models $subcommands" -- "$cur") )
    elif [[ $COMP_CWORD -eq 1 ]] || [[ "$prev" == "-q" ]] || [[ "$prev" == "--quiet" ]]; then
        local models="{models}"
        local subcommands="init models completions"
        COMPREPLY=( $(compgen -W "$models $subcommands" -- "$cur") )
    elif [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "-q --quiet --version --help" -- "$cur") )
    fi
}}
complete -F _aisk_completions aisk
"""

ZSH_TEMPLATE = """\
#compdef aisk

_aisk() {{
    local -a models subcommands flags
    models=({models})
    subcommands=(init models completions)
    flags=(-q --quiet --version --help)

    if (( CURRENT == 2 )); then
        _describe 'model or command' models -- subcommands -- flags
    elif (( CURRENT == 2 )) || [[ "${{words[2]}}" == "-q" ]] || [[ "${{words[2]}}" == "--quiet" ]]; then
        _describe 'model or command' models -- subcommands
    fi
}}

_aisk "$@"
"""


def generate_bash() -> str:
    """Generate bash completion script with current aliases."""
    cfg = load_config()
    models = " ".join(sorted(cfg.aliases.keys()))
    return BASH_TEMPLATE.format(models=models)


def generate_zsh() -> str:
    """Generate zsh completion script with current aliases."""
    cfg = load_config()
    models = " ".join(sorted(cfg.aliases.keys()))
    return ZSH_TEMPLATE.format(models=models)


def _detect_shell() -> str:
    """Detect current shell: 'bash' or 'zsh'."""
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    return "bash"


def _rc_file(shell: str) -> Path:
    """Return the rc file path for the given shell."""
    if shell == "zsh":
        return Path.home() / ".zshrc"
    return Path.home() / ".bashrc"


_EVAL_LINES = {
    "bash": 'eval "$(aisk completions bash)"',
    "zsh": 'eval "$(aisk completions zsh)"',
}


def install_completions() -> str:
    """Append eval line to the user's shell rc file. Returns status message."""
    shell = _detect_shell()
    rc = _rc_file(shell)
    eval_line = _EVAL_LINES[shell]

    if rc.exists() and eval_line in rc.read_text():
        return f"already installed in {rc}"

    with open(rc, "a") as f:
        f.write(f"\n# aisk shell completions\n{eval_line}\n")

    return f"installed in {rc} — run `source {rc}` or open a new terminal"


def generate_refresh() -> str:
    """Generate completion script for the current shell (auto-detected)."""
    shell = _detect_shell()
    if shell == "zsh":
        return generate_zsh()
    return generate_bash()
