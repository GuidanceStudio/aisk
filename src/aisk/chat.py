from __future__ import annotations

import codecs
import difflib
import os
import select
import sys
import unicodedata
from typing import Any, Generator

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - POSIX-only interactive enhancement
    termios = None
    tty = None

try:
    # Loading readline gives input() line editing + ↑/↓ prompt history for free.
    import readline

    _HAS_READLINE = True
except ImportError:  # not in the stdlib on some platforms (e.g. Windows)
    readline = None
    _HAS_READLINE = False

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
_BRACKETED_PASTE_ON = "\x1b[?2004h"
_BRACKETED_PASTE_OFF = "\x1b[?2004l"
_BRACKETED_PASTE_START = b"\x1b[200~"
_BRACKETED_PASTE_END = b"\x1b[201~"
_KEY_LEFT = (b"\x1b[D", b"\x1bOD", b"\x1b[1D", b"\x1b[1;1D")
_KEY_RIGHT = (b"\x1b[C", b"\x1bOC", b"\x1b[1C", b"\x1b[1;1C")
_KEY_UP = (b"\x1b[A", b"\x1bOA", b"\x1b[1A", b"\x1b[1;1A")
_KEY_DOWN = (b"\x1b[B", b"\x1bOB", b"\x1b[1B", b"\x1b[1;1B")
_KEY_DELETE = (b"\x1b[3~",)
_KEY_HOME = (b"\x1b[H", b"\x1bOH", b"\x1b[1~", b"\x1b[7~")
_KEY_END = (b"\x1b[F", b"\x1bOF", b"\x1b[4~", b"\x1b[8~")
_KEY_INSERT_NEWLINE = (
    # Kitty / progressive keyboard protocol.
    b"\x1b[13;2u",   # Shift+Enter
    b"\x1b[13;5u",   # Ctrl+Enter
    b"\x1b[13;6u",   # Ctrl+Shift+Enter
    # xterm modifyOtherKeys variants.
    b"\x1b[27;2;13~",
    b"\x1b[27;5;13~",
    b"\x1b[27;6;13~",
    # Common Meta/Alt+Enter fallback.
    b"\x1b\r",
    b"\x1b\n",
)
_TTY_PROMPT_TEXT = "❯ "
_TTY_PROMPT = f"{_CYAN}{_TTY_PROMPT_TEXT}{_RESET}"


def _char_width(char: str) -> int:
    if unicodedata.combining(char):
        return 0
    if unicodedata.east_asian_width(char) in {"F", "W"}:
        return 2
    return 1


def _display_width(value: str, *, start_column: int = 0) -> int:
    column = start_column
    for char in value:
        if char == "\t":
            column += 8 - (column % 8)
        elif char >= " ":
            column += _char_width(char)
    return column - start_column


_TTY_PROMPT_WIDTH = _display_width(_TTY_PROMPT_TEXT)
_TTY_CONTINUATION = " " * _TTY_PROMPT_WIDTH


def _terminal_columns() -> int:
    try:
        columns = os.get_terminal_size(sys.stdout.fileno()).columns
    except OSError:
        return 80
    return columns if columns > 0 else 80


def _wrapped_rows(line: str, columns: int, start_column: int = 0) -> int:
    first_width = max(1, columns - start_column)
    width = _display_width(line, start_column=start_column)
    if width <= first_width:
        return 1
    return 1 + ((width - first_width - 1) // columns) + 1


def _input_visual_lines(value: str, columns: int | None = None) -> int:
    columns = columns or _terminal_columns()
    rows = 0
    for line in value.split("\n"):
        rows += _wrapped_rows(line, columns, _TTY_PROMPT_WIDTH)
    return max(1, rows)


def _render_input_value(value: str) -> str:
    return value.replace("\n", "\r\n" + _TTY_CONTINUATION)


def _iter_cursor_positions(value: str, columns: int):
    row = 0
    column = _TTY_PROMPT_WIDTH
    yield 0, row, column

    for index, char in enumerate(value, start=1):
        if char == "\n":
            row += 1
            column = _TTY_PROMPT_WIDTH
        elif char >= " ":
            width = 8 - (column % 8) if char == "\t" else _char_width(char)
            if column + width > columns:
                row += 1
                column = 0
            column += width
        yield index, row, column


def _input_cursor_position(
    value: str, cursor: int, columns: int | None = None,
) -> tuple[int, int]:
    columns = columns or _terminal_columns()
    cursor = max(0, min(cursor, len(value)))
    for index, row, column in _iter_cursor_positions(value, columns):
        if index == cursor:
            return row, column
    return 0, _TTY_PROMPT_WIDTH


def _cursor_for_visual_position(
    value: str,
    target_row: int,
    target_column: int,
    columns: int | None = None,
) -> int:
    columns = columns or _terminal_columns()
    best: int | None = None
    for index, row, column in _iter_cursor_positions(value, columns):
        if row < target_row:
            continue
        if row > target_row:
            break
        best = index
        if column >= target_column:
            return index
    return len(value) if best is None else best


def _configure_readline(readline_module: Any) -> bool:
    """Enable readline behaviors needed by the interactive chat."""
    try:
        readline_module.parse_and_bind("set enable-bracketed-paste on")
    except Exception:
        return False
    return True


_HAS_BRACKETED_PASTE = _configure_readline(readline) if readline is not None else False

# readline strips the ESC byte from unbracketed color codes in an input() prompt,
# so wrap them in \x01 (start-ignore) / \x02 (end-ignore). Without readline those
# markers would print as garbage, so fall back to the plain colored prompt.
if _HAS_READLINE:
    _PROMPT = f"\n\x01{_CYAN}\x02❯\x01{_RESET}\x02 "
else:
    _PROMPT = f"\n{_CYAN}❯{_RESET} "


def _read_user_input(prompt_history: list[str]) -> str:
    """Read one chat prompt, preserving multi-line terminal paste as one value."""
    if termios is None or tty is None or not (sys.stdin.isatty() and sys.stdout.isatty()):
        return input(_PROMPT)

    try:
        return _read_tty_input(prompt_history)
    except termios.error:
        return input(_PROMPT)


def _read_tty_input(prompt_history: list[str]) -> str:
    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)

    buf: list[str] = []
    cursor = 0
    pending = b""
    in_paste = False
    history_index = len(prompt_history)
    draft = ""
    rendered_cursor_row = 0
    paste_decoder = codecs.getincrementaldecoder("utf-8")("replace")

    def text() -> str:
        return "".join(buf)

    def redraw() -> None:
        nonlocal rendered_cursor_row
        if rendered_cursor_row > 0:
            sys.stdout.write("\r" + "\x1b[1A\r" * rendered_cursor_row)
        else:
            sys.stdout.write("\r")
        sys.stdout.write("\x1b[J")
        value = text()
        sys.stdout.write(_TTY_PROMPT + _render_input_value(value))

        columns = _terminal_columns()
        cursor_row, cursor_column = _input_cursor_position(value, cursor, columns)
        end_row, _ = _input_cursor_position(value, len(value), columns)
        if end_row > cursor_row:
            sys.stdout.write("\x1b[1A" * (end_row - cursor_row))
        sys.stdout.write("\r")
        if cursor_column:
            sys.stdout.write(f"\x1b[{cursor_column}C")
        rendered_cursor_row = cursor_row
        sys.stdout.flush()

    def replace_buffer(value: str) -> None:
        nonlocal cursor
        buf.clear()
        buf.extend(value)
        cursor = len(buf)
        redraw()

    def append_text(value: str) -> None:
        nonlocal cursor
        if not value:
            return
        chars = list(value.replace("\r\n", "\n").replace("\r", "\n"))
        buf[cursor:cursor] = chars
        cursor += len(chars)
        redraw()

    def insert_newline() -> None:
        append_text("\n")

    def move_left() -> None:
        nonlocal cursor
        if cursor > 0:
            cursor -= 1
            redraw()

    def move_right() -> None:
        nonlocal cursor
        if cursor < len(buf):
            cursor += 1
            redraw()

    def delete_before_cursor() -> None:
        nonlocal cursor
        if cursor > 0:
            del buf[cursor - 1]
            cursor -= 1
            redraw()

    def delete_at_cursor() -> None:
        if cursor < len(buf):
            del buf[cursor]
            redraw()

    def move_home() -> None:
        nonlocal cursor
        if cursor != 0:
            cursor = 0
            redraw()

    def move_end() -> None:
        nonlocal cursor
        if cursor != len(buf):
            cursor = len(buf)
            redraw()

    def history_up() -> None:
        nonlocal draft, history_index
        if not prompt_history or history_index == 0:
            return
        if history_index == len(prompt_history):
            draft = text()
        history_index -= 1
        replace_buffer(prompt_history[history_index])

    def history_down() -> None:
        nonlocal history_index
        if history_index >= len(prompt_history):
            return
        history_index += 1
        if history_index == len(prompt_history):
            replace_buffer(draft)
        else:
            replace_buffer(prompt_history[history_index])

    def move_vertical(delta: int) -> None:
        nonlocal cursor
        value = text()
        columns = _terminal_columns()
        row, column = _input_cursor_position(value, cursor, columns)
        target_row = row + delta
        if target_row < 0:
            history_up()
            return
        if target_row >= _input_visual_lines(value, columns):
            history_down()
            return
        cursor = _cursor_for_visual_position(value, target_row, column, columns)
        redraw()

    def finish_input() -> str:
        value = text()
        columns = _terminal_columns()
        cursor_row, _ = _input_cursor_position(value, cursor, columns)
        end_row, _ = _input_cursor_position(value, len(value), columns)
        if end_row > cursor_row:
            sys.stdout.write("\x1b[1B" * (end_row - cursor_row))
        sys.stdout.write("\r\n")
        sys.stdout.flush()
        return value

    def read_more(timeout: float | None = None) -> bool:
        nonlocal pending
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return False
        pending += os.read(fd, 4096)
        return True

    def consume_sequence(sequences: tuple[bytes, ...]) -> bytes | None:
        nonlocal pending
        while True:
            for sequence in sequences:
                if pending.startswith(sequence):
                    pending = pending[len(sequence):]
                    return sequence
            if pending and any(sequence.startswith(pending) for sequence in sequences):
                if read_more(0.01):
                    continue
            return None

    def consume_text_bytes() -> None:
        nonlocal pending
        data = b""
        while True:
            while pending and 0x20 <= pending[0] != 0x7F:
                data += pending[:1]
                pending = pending[1:]
            try:
                append_text(data.decode("utf-8"))
                return
            except UnicodeDecodeError as exc:
                if exc.reason == "unexpected end of data" and read_more(0.01):
                    continue
                append_text(data.decode("utf-8", "replace"))
                return

    def consume_unknown_escape() -> None:
        nonlocal pending
        if pending.startswith(b"\x1b") and len(pending) < 8:
            read_more(0.01)
        if pending.startswith(b"\x1b["):
            for i, byte in enumerate(pending[2:], start=2):
                if 0x40 <= byte <= 0x7E:
                    pending = pending[i + 1:]
                    return
        pending = pending[1:]

    try:
        tty.setraw(fd)
        sys.stdout.write(_BRACKETED_PASTE_ON + "\r\n" + _TTY_PROMPT)
        sys.stdout.flush()

        while True:
            if not pending:
                read_more(None)

            if in_paste:
                end = pending.find(_BRACKETED_PASTE_END)
                if end == -1:
                    append_text(paste_decoder.decode(pending, final=False))
                    pending = b""
                    continue
                append_text(paste_decoder.decode(pending[:end], final=True))
                paste_decoder.reset()
                pending = pending[end + len(_BRACKETED_PASTE_END):]
                in_paste = False
                continue

            if _BRACKETED_PASTE_START.startswith(pending) and pending != _BRACKETED_PASTE_START:
                read_more(0.01)
                if _BRACKETED_PASTE_START.startswith(pending):
                    continue

            if consume_sequence(_KEY_INSERT_NEWLINE):
                insert_newline()
                continue

            if pending.startswith(_BRACKETED_PASTE_START):
                pending = pending[len(_BRACKETED_PASTE_START):]
                paste_decoder.reset()
                in_paste = True
                continue

            if consume_sequence(_KEY_LEFT):
                move_left()
                continue

            if consume_sequence(_KEY_RIGHT):
                move_right()
                continue

            if consume_sequence(_KEY_UP):
                move_vertical(-1)
                continue

            if consume_sequence(_KEY_DOWN):
                move_vertical(1)
                continue

            if consume_sequence(_KEY_DELETE):
                delete_at_cursor()
                continue

            if consume_sequence(_KEY_HOME):
                move_home()
                continue

            if consume_sequence(_KEY_END):
                move_end()
                continue

            byte = pending[:1]
            pending = pending[1:]

            if byte == b"\x03":
                raise KeyboardInterrupt
            if byte == b"\x04":
                if not buf:
                    raise EOFError
                delete_at_cursor()
                continue
            if byte in (b"\x7f", b"\b"):
                delete_before_cursor()
                continue
            if byte == b"\x01":
                move_home()
                continue
            if byte == b"\x05":
                move_end()
                continue
            if byte == b"\n":
                insert_newline()
                continue
            if byte == b"\r":
                if pending or read_more(0.02):
                    insert_newline()
                    continue
                return finish_input()
            if byte == b"\x1b":
                pending = byte + pending
                consume_unknown_escape()
                continue
            if byte >= b" ":
                pending = byte + pending
                consume_text_bytes()
    finally:
        try:
            sys.stdout.write(_BRACKETED_PASTE_OFF)
            sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)


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
    _write(f"  {_DIM}Enter: send · Ctrl-J: newline · Ctrl-C: stop reply/exit · Ctrl-D: exit{_RESET}\n")
    _write(f"{_BLUE}{_BAR}{_RESET}\n")

    messages: list[dict] = list(history) if history else []
    prompt_history: list[str] = []
    totals = {"cost": 0.0, "in": 0, "out": 0, "any_cost": False}
    had_success = False

    while True:
        try:
            user = _read_user_input(prompt_history)
        except (EOFError, KeyboardInterrupt):
            # Ctrl-D or Ctrl-C at the prompt → leave the chat.
            _write("\n")
            break

        if not user.strip():
            continue

        prompt_history.append(user)
        messages.append({"role": "user", "content": user})
        _write("\n")
        try:
            text, ok, usage = _render_turn(
                stream_chat(
                    cfg.endpoint, cfg.api_key, model, messages,
                    prompt_cache=cfg.prompt_cache,
                )
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
