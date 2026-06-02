from __future__ import annotations

import difflib
from typing import Generator

from aisk import cache, session
from aisk.client import (
    ContentChunk,
    ErrorInfo,
    Event,
    ReasoningChunk,
    UsageInfo,
    stream_chat,
)
from aisk.config import Config
from aisk.output import (
    _BLUE,
    _CYAN,
    _DIM,
    _DIM_ITALIC,
    _RED,
    _RESET,
    _write,
)

_BAR = "─" * 60


def _suggest(typed: str, aliases: dict[str, str], available: set[str] | None) -> list[str]:
    """Close-match suggestions for a mistyped model: aliases first, then IDs."""
    matches = difflib.get_close_matches(typed, list(aliases), n=3, cutoff=0.6)
    if not matches and available:
        matches = difflib.get_close_matches(typed, sorted(available), n=3, cutoff=0.5)
    return matches


def _render_turn(
    events: Generator[Event, None, None],
) -> tuple[str, bool, UsageInfo | None]:
    """Stream one assistant turn to stdout.

    Returns (assistant_text, ok, usage). *ok* is False if the stream errored.
    """
    content_parts: list[str] = []
    in_reasoning = False
    in_content = False
    usage: UsageInfo | None = None
    ok = True

    for event in events:
        if isinstance(event, ReasoningChunk):
            if not in_reasoning:
                _write(f"{_DIM}thinking…{_RESET}\n")
                in_reasoning = True
            _write(f"{_DIM_ITALIC}{event.text}{_RESET}")
        elif isinstance(event, ContentChunk):
            if in_reasoning and not in_content:
                _write("\n\n")
            in_content = True
            content_parts.append(event.text)
            _write(event.text)
        elif isinstance(event, UsageInfo):
            usage = event
        elif isinstance(event, ErrorInfo):
            _write(f"\n{_RED}Error: {event.message}{_RESET}\n")
            ok = False

    _write("\n")
    return "".join(content_parts), ok, usage


def _validate_model(model: str, cfg: Config, model_input: str | None) -> int | None:
    """Preflight: confirm the model is valid before the prompt.

    Skipped for curated aliases and when the original input is unknown. Returns
    an exit code (1) if the model is confirmed invalid, else None (proceed).
    """
    if model_input is None or model_input in cfg.aliases:
        return None

    verdict, available = cache.check_model(cfg.endpoint, cfg.api_key, model)
    if verdict is not False:
        return None

    _write(f"\n{_RED}Error: '{model_input}' is not a valid model for this endpoint.{_RESET}\n")
    suggestions = _suggest(model_input, cfg.aliases, available)
    if suggestions:
        _write(f"{_DIM}Did you mean: {', '.join(suggestions)}?  (or run `aisk models`){_RESET}\n")
    else:
        _write(f"{_DIM}Run `aisk models`, or pass a full model ID.{_RESET}\n")
    return 1


def chat(
    model: str,
    cfg: Config,
    *,
    model_input: str | None = None,
    history: list[dict] | None = None,
) -> int:
    """Run an interactive multi-turn chat REPL. Returns an exit code.

    History is kept in memory and resent each turn, so the model sees the whole
    conversation. Ctrl-C stops the current reply (or exits at the prompt);
    Ctrl-D exits.
    """
    rc = _validate_model(model, cfg, model_input)
    if rc is not None:
        return rc

    _write(f"\n{_BLUE}{_BAR}{_RESET}\n")
    _write(f"  {_CYAN}aisk chat{_RESET} {_DIM}— {model}{_RESET}\n")
    _write(f"  {_DIM}Ctrl-C: stop the reply (or exit at the prompt) · Ctrl-D: exit{_RESET}\n")
    _write(f"{_BLUE}{_BAR}{_RESET}\n")

    messages: list[dict] = list(history) if history else []
    totals = {"cost": 0.0, "in": 0, "out": 0, "any_cost": False}
    had_success = False

    while True:
        try:
            user = input(f"\n{_CYAN}❯{_RESET} ")
        except (EOFError, KeyboardInterrupt):
            # Ctrl-D or Ctrl-C at the prompt → leave the chat.
            _write("\n")
            break

        if not user.strip():
            continue

        messages.append({"role": "user", "content": user})
        _write("\n")
        try:
            text, ok, usage = _render_turn(
                stream_chat(cfg.endpoint, cfg.api_key, model, messages)
            )
        except KeyboardInterrupt:
            # Ctrl-C during a reply → drop this exchange, keep chatting.
            messages.pop()
            _write(f"\n{_DIM}(interrupted){_RESET}\n")
            continue

        if not ok:
            # Roll back the failed turn so history stays consistent.
            messages.pop()
            # If nothing has worked yet, the setup is broken — fail fast.
            if not had_success:
                return 1
            continue

        had_success = True
        if text:
            messages.append({"role": "assistant", "content": text})
            session.save_session(model, messages)

        if usage:
            _write(f"{_DIM}{_format_usage(usage, totals)}{_RESET}\n")

    return 0


def _format_usage(usage: UsageInfo, totals: dict) -> str:
    """Build the per-turn footer with running conversation totals."""
    totals["in"] += usage.prompt_tokens
    totals["out"] += usage.completion_tokens

    parts = [f"In {usage.prompt_tokens}", f"Out {usage.completion_tokens}"]
    if usage.reasoning_tokens:
        parts.append(f"Reasoning {usage.reasoning_tokens}")
    line = " | ".join(parts)

    if usage.cost is not None:
        totals["cost"] += usage.cost
        totals["any_cost"] = True
        line += f" | ${usage.cost:.6f}"

    # Running total for the whole conversation.
    if totals["any_cost"]:
        line += f"  ·  Σ ${totals['cost']:.6f}"
    else:
        line += f"  ·  Σ In {totals['in']} | Out {totals['out']}"
    return line
