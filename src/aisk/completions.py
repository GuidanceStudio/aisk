from __future__ import annotations

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
