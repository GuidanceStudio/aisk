from __future__ import annotations

from typing import Generator

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


def _render_turn(events: Generator[Event, None, None]) -> tuple[str, bool]:
    """Stream one assistant turn to stdout.

    Returns (assistant_text, ok). *ok* is False if the stream errored.
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
    if usage:
        parts = [f"In {usage.prompt_tokens}", f"Out {usage.completion_tokens}"]
        if usage.reasoning_tokens:
            parts.append(f"Reasoning {usage.reasoning_tokens}")
        line = " | ".join(parts)
        if usage.cost is not None:
            line += f" | ${usage.cost:.6f}"
        _write(f"{_DIM}{line}{_RESET}\n")

    return "".join(content_parts), ok


def chat(model: str, cfg: Config) -> int:
    """Run an interactive multi-turn chat REPL. Returns an exit code.

    History is kept in memory and resent each turn, so the model sees the whole
    conversation. Exit with Ctrl-C (or EOF).
    """
    _write(f"\n{_BLUE}{_BAR}{_RESET}\n")
    _write(f"  {_CYAN}aisk chat{_RESET} {_DIM}— {model}{_RESET}\n")
    _write(f"  {_DIM}Ctrl-C to exit{_RESET}\n")
    _write(f"{_BLUE}{_BAR}{_RESET}\n")

    messages: list[dict] = []
    try:
        while True:
            try:
                user = input(f"\n{_CYAN}❯{_RESET} ")
            except EOFError:
                _write("\n")
                break
            if not user.strip():
                continue

            messages.append({"role": "user", "content": user})
            _write("\n")
            events = stream_chat(cfg.endpoint, cfg.api_key, model, messages)
            text, ok = _render_turn(events)

            if not ok:
                # Roll back the failed turn so history stays consistent.
                messages.pop()
            elif text:
                messages.append({"role": "assistant", "content": text})
    except KeyboardInterrupt:
        _write("\n")

    return 0
