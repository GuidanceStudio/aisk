from __future__ import annotations

import sys
from typing import Generator

from aisk.client import ContentChunk, ErrorInfo, Event, ReasoningChunk, UsageInfo

# ANSI codes
_BLUE = "\033[38;5;33m"
_CYAN = "\033[36m"
_ORANGE = "\033[38;5;214m"
_RED = "\033[38;5;196m"
_DIM = "\033[2m"
_ITALIC = "\033[3m"
_RESET = "\033[0m"
_DIM_ITALIC = f"{_DIM}{_ITALIC}"

_SEP = "─" * 90


def _write(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def render_verbose(
    model: str, message: str, events: Generator[Event, None, None]
) -> int:
    """Render streaming events with full decoration. Returns exit code."""
    # Header
    _write(f"\n{_BLUE}{_SEP}{_RESET}\n")
    _write(f" {_CYAN}Model:{_RESET} {model} {_DIM}| User: {message}{_RESET}\n")
    _write(f"{_BLUE}{_SEP}{_RESET}\n")

    in_reasoning = False
    in_content = False
    exit_code = 0
    usage: UsageInfo | None = None

    for event in events:
        if isinstance(event, ReasoningChunk):
            if not in_reasoning:
                _write(f"\n{_ORANGE}► THINKING{_RESET}\n")
                in_reasoning = True
            _write(f"{_DIM_ITALIC}{event.text}{_RESET}")

        elif isinstance(event, ContentChunk):
            if in_reasoning and not in_content:
                _write(f"{_RESET}\n\n{_BLUE}{'┈' * 90}{_RESET}\n")
            if not in_content:
                _write(f"\n{_ORANGE}► ANSWER{_RESET}\n")
                in_content = True
            _write(event.text)

        elif isinstance(event, UsageInfo):
            usage = event

        elif isinstance(event, ErrorInfo):
            _write(f"\n{_RED}Error: {event.message}{_RESET}\n")
            exit_code = 1

    # Footer
    _write("\n\n")
    _write(f"{_BLUE}{_SEP}{_RESET}\n")
    if usage:
        parts = [f"In {usage.prompt_tokens}", f"Out {usage.completion_tokens}"]
        if usage.reasoning_tokens:
            parts.append(f"Reasoning: {usage.reasoning_tokens}")
        tokens_str = " | ".join(parts)
        line = f"Tokens: {tokens_str}"
        if usage.cost is not None:
            line += f" | Cost: ${usage.cost:.6f}"
        _write(f"{line}\n")
        _write(f"{_BLUE}{_SEP}{_RESET}\n")

    return exit_code


def render_quiet(events: Generator[Event, None, None]) -> int:
    """Render only content text, no decoration. Returns exit code."""
    for event in events:
        if isinstance(event, ContentChunk):
            _write(event.text)
        elif isinstance(event, ErrorInfo):
            sys.stderr.write(f"Error: {event.message}\n")
            return 1
    _write("\n")
    return 0
