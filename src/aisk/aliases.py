from __future__ import annotations


def resolve_model(name: str, aliases: dict[str, str]) -> str:
    """Resolve a model alias to its full name.

    If *name* is found in *aliases*, returns the mapped value.
    Otherwise returns *name* unchanged (pass-through for direct model names
    like ``perplexity/sonar``).
    """
    return aliases.get(name, name)
