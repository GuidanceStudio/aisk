from __future__ import annotations

import codecs
import difflib
import os
import re
import select
import sys
import unicodedata
from dataclasses import dataclass
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

try:
    from prompt_toolkit import PromptSession as _PromptSession
    from prompt_toolkit.completion import Completer as _Completer
    from prompt_toolkit.completion import Completion as _Completion
    from prompt_toolkit.history import InMemoryHistory as _InMemoryHistory
    from prompt_toolkit.key_binding import KeyBindings as _KeyBindings
except ImportError:  # pragma: no cover - dependency is declared for normal installs
    _PromptSession = None
    _Completer = None
    _Completion = None
    _InMemoryHistory = None
    _KeyBindings = None

from aisk import cache, session
from aisk.aliases import resolve_model
from aisk.client import (
    Event,
    UsageInfo,
    stream_chat,
)
from aisk.config import ALIAS_RENAMES, Config
from aisk.output import (
    _BLUE,
    _CYAN,
    _DIM,
    _RED,
    _RESET,
    render_verbose_stream,
    _write,
)

_BAR = "─" * 60
_CLEAR_SCREEN = "\x1b[2J\x1b[H"
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z~]")
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


def _read_user_input(
    prompt_history: list[str],
    *,
    on_ctrl_s: Any = None,
    on_ctrl_o: Any = None,
    on_ctrl_g: Any = None,
    footer: Any = None,
) -> str:
    """Read one chat prompt, preserving multi-line terminal paste as one value."""
    backend = os.environ.get("AISK_CHAT_BACKEND", "auto").strip().lower()

    if backend == "input":
        return input(_PROMPT)

    if backend != "raw" and _PromptSession is not None and sys.stdin.isatty() and sys.stdout.isatty():
        return _read_prompt_toolkit_input(
            prompt_history,
            on_ctrl_s=on_ctrl_s,
            on_ctrl_o=on_ctrl_o,
            on_ctrl_g=on_ctrl_g,
            footer=footer,
        )

    if termios is None or tty is None or not (sys.stdin.isatty() and sys.stdout.isatty()):
        return input(_PROMPT)

    try:
        return _read_tty_input(prompt_history, on_ctrl_s=on_ctrl_s, on_ctrl_o=on_ctrl_o, on_ctrl_g=on_ctrl_g, footer=footer)
    except termios.error:
        return input(_PROMPT)


def _plain(text: str) -> str:
    return _ANSI_RE.sub("", text)


@dataclass(frozen=True)
class _ModelSelectRequest:
    draft: str


def _read_prompt_toolkit_input(
    prompt_history: list[str],
    *,
    on_ctrl_s: Any = None,
    on_ctrl_o: Any = None,
    on_ctrl_g: Any = None,
    footer: Any = None,
) -> str:
    history = _InMemoryHistory()
    for value in prompt_history:
        history.append_string(value)

    bindings = _KeyBindings()

    @bindings.add("c-s")
    def _(event) -> None:
        if callable(on_ctrl_s):
            on_ctrl_s()
            event.app.invalidate()

    @bindings.add("c-g")
    def _(event) -> None:
        if callable(on_ctrl_g):
            on_ctrl_g()
            event.app.invalidate()

    @bindings.add("c-o")
    def _(event) -> None:
        event.app.exit(result=_ModelSelectRequest(event.current_buffer.text))

    @bindings.add("c-j")
    def _(event) -> None:
        event.current_buffer.insert_text("\n")

    def bottom_toolbar() -> str:
        return _plain(footer()) if callable(footer) else ""

    session = _PromptSession(history=history, key_bindings=bindings)
    draft = ""
    while True:
        result = session.prompt(
            _TTY_PROMPT_TEXT,
            multiline=True,
            default=draft,
            prompt_continuation=lambda width, line_number, is_soft_wrap: _TTY_CONTINUATION,
            bottom_toolbar=bottom_toolbar,
        )
        if isinstance(result, _ModelSelectRequest):
            if callable(on_ctrl_o):
                on_ctrl_o()
            draft = result.draft
            continue
        return result


class _ModelCompleter(_Completer if _Completer is not None else object):
    def __init__(self, aliases: dict[str, str]):
        self.aliases = aliases

    def get_completions(self, document, complete_event):
        query = document.text
        for alias, model_id in _filter_items(query, self.aliases):
            yield _Completion(
                alias,
                start_position=-len(query),
                display=alias,
                display_meta=model_id,
            )


def _prompt_toolkit_model_selector(aliases: dict[str, str]) -> str | None:
    session = _PromptSession()
    try:
        value = session.prompt(
            "Model: ",
            completer=_ModelCompleter(aliases),
            complete_while_typing=True,
            bottom_toolbar="Type to filter; Enter selects; Ctrl-C cancels",
        ).strip()
    except (KeyboardInterrupt, EOFError):
        return None

    if not value:
        return None
    if value in aliases:
        return aliases[value]

    matches = _filter_items(value, aliases)
    if matches:
        return matches[0][1]
    return value


def _select_model_prompt(aliases: dict[str, str]) -> str | None:
    backend = os.environ.get("AISK_CHAT_BACKEND", "auto").strip().lower()
    if backend == "raw" and termios is not None and tty is not None:
        return _model_selector(aliases)
    if _PromptSession is not None:
        return _prompt_toolkit_model_selector(aliases)
    if termios is not None and tty is not None and sys.stdin.isatty() and sys.stdout.isatty():
        return _model_selector(aliases)
    value = input("Model: ").strip()
    return value or None


def _read_tty_input(
    prompt_history: list[str],
    *,
    on_ctrl_s: Any = None,
    on_ctrl_o: Any = None,
    on_ctrl_g: Any = None,
    footer: Any = None,
) -> str:
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

        if callable(footer):
            ft = footer()
            if ft:
                sys.stdout.write(f"\r\n  {_DIM}───{_RESET}")
                sys.stdout.write(f"\r\n  {ft}")

        columns = _terminal_columns()
        cursor_row, cursor_column = _input_cursor_position(value, cursor, columns)
        end_row, _ = _input_cursor_position(value, len(value), columns)
        if end_row > cursor_row:
            sys.stdout.write("\x1b[1A" * (end_row - cursor_row))
        if callable(footer) and footer():
            sys.stdout.write("\x1b[1A\x1b[1A")
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
        sys.stdout.write("\r\n\x1b[J")
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
        if callable(footer):
            ft = footer()
            if ft:
                sys.stdout.write(f"\r\n  {_DIM}───{_RESET}")
                sys.stdout.write(f"\r\n  {ft}")
                sys.stdout.write(f"\x1b[2A\r\x1b[{_TTY_PROMPT_WIDTH}C")
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
            if byte == b"\x13" and callable(on_ctrl_s):
                on_ctrl_s()
                redraw()
                continue
            if byte == b"\x0f" and callable(on_ctrl_o):
                saved_value = text()
                new_model = on_ctrl_o()
                buf[:] = list(saved_value)
                cursor = len(saved_value)
                redraw()
                continue
            if byte == b"\x07" and callable(on_ctrl_g):
                on_ctrl_g()
                redraw()
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


def _filter_items(query: str, aliases: dict[str, str]) -> list[tuple[str, str]]:
    """Filter aliases by case-insensitive match on alias or model name."""
    q = query.lower()
    return [
        (a, m) for a, m in sorted(aliases.items())
        if q in a.lower() or q in m.lower()
    ]


def _model_selector(aliases: dict[str, str]) -> str | None:
    """Interactive fuzzy model selector overlay.

    Returns the selected model ID (from aliases) or a pass-through string,
    or None if cancelled.

    Arrow keys move the selection (with wrap-around) using incremental
    cursor updates — no full repaint on navigation.  Typing a filter
    triggers a full redraw of the item list.
    """
    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)
    tty.setraw(fd)
    cursor_row = 0

    try:
        items = sorted(aliases.items())
        filter_text = ""
        selected_idx = 0
        filtered = items[:]
        rendered_items = 0
        max_alias_len = max((len(a) for a, _ in items), default=8)

        def _bar() -> str:
            return "─" * max(10, _terminal_columns() - 12)

        def _filter_line_num() -> int:
            return 1 + rendered_items + 1  # header + items + bar → filter line

        def _move_to_row(row: int) -> None:
            nonlocal cursor_row
            delta = row - cursor_row
            if delta > 0:
                sys.stdout.write(f"\x1b[{delta}B")
            elif delta < 0:
                sys.stdout.write(f"\x1b[{-delta}A")
            sys.stdout.write("\r")
            cursor_row = row

        def _move_to_filter() -> None:
            _move_to_row(_filter_line_num())
            column = _display_width(f"Filter: {filter_text}")
            if column:
                sys.stdout.write(f"\x1b[{column}C")

        def draw_overlay() -> None:
            nonlocal rendered_items, cursor_row
            bar = _bar()
            lines: list[str] = []
            _move_to_row(0)
            lines.append(f"{_DIM}Model {bar}{_RESET}")

            for i, (alias, model_id) in enumerate(filtered):
                prefix = f"{_CYAN}>" if i == selected_idx else " "
                alias_padded = f"{alias:<{max_alias_len}}"
                lines.append(f"  {prefix} {alias_padded}  {_DIM}{model_id}{_RESET}")

            if not filtered and filter_text:
                lines.append(f"  {_DIM}(no matches — Enter to use as pass-through){_RESET}")

            rendered_items = len(filtered) if filtered else (1 if filter_text else 0)

            lines.append(f"{_DIM}{bar}{_RESET}")
            lines.append(f"Filter: {filter_text}")
            lines.append(f"{_DIM}↑↓ navigate  ·  Enter select  ·  Esc cancel  ·  Type to filter{_RESET}")

            sys.stdout.write("\x1b[J" + "\r\n".join(lines))
            cursor_row = len(lines) - 1
            _move_to_filter()
            sys.stdout.flush()

        def _move_marker(old_idx: int, new_idx: int) -> None:
            if old_idx == new_idx or not filtered:
                return

            alias_old, model_old = filtered[old_idx]
            alias_new, model_new = filtered[new_idx]
            alias_padded_old = f"{alias_old:<{max_alias_len}}"
            alias_padded_new = f"{alias_new:<{max_alias_len}}"

            _move_to_row(1 + old_idx)
            sys.stdout.write(f"\r    {alias_padded_old}  {_DIM}{model_old}{_RESET}\x1b[K")

            _move_to_row(1 + new_idx)
            sys.stdout.write(f"\r  {_CYAN}> {alias_padded_new}  {_DIM}{model_new}{_RESET}\x1b[K")

            _move_to_filter()
            sys.stdout.flush()

        def apply_filter() -> None:
            nonlocal filtered, selected_idx
            filtered = _filter_items(filter_text, aliases) if filter_text else items[:]
            if filtered:
                selected_idx = selected_idx % len(filtered)
            else:
                selected_idx = 0

        draw_overlay()

        pending = b""
        while True:
            if not pending:
                pending = os.read(fd, 4096)

            byte = pending[:1]
            pending = pending[1:]

            if byte == b"\x03":
                sys.stdout.write("\r\n")
                cursor_row += 1
                return None
            if byte == b"\x1b":
                if len(pending) < 2:
                    try:
                        ready, _, _ = select.select([fd], [], [], 0.05)
                        if ready:
                            pending += os.read(fd, 16)
                    except OSError:
                        pass
                if pending.startswith(b"[A") or pending.startswith(b"OA"):
                    pending = pending[pending.index(b"A") + 1:]
                    if filtered:
                        old = selected_idx
                        selected_idx = (selected_idx - 1) % len(filtered)
                        _move_marker(old, selected_idx)
                    continue
                if pending.startswith(b"[B") or pending.startswith(b"OB"):
                    pending = pending[pending.index(b"B") + 1:]
                    if filtered:
                        old = selected_idx
                        selected_idx = (selected_idx + 1) % len(filtered)
                        _move_marker(old, selected_idx)
                    continue
                sys.stdout.write("\r\n")
                cursor_row += 1
                return None
            if byte == b"\r":
                sys.stdout.write("\r\n")
                cursor_row += 1
                if filtered:
                    _, selected_model = filtered[selected_idx]
                    return selected_model
                if filter_text.strip():
                    return filter_text.strip()
                return None
            if byte in (b"\x7f", b"\b"):
                if filter_text:
                    filter_text = filter_text[:-1]
                    apply_filter()
                    draw_overlay()
                continue
            if byte >= b" ":
                try:
                    filter_text += byte.decode("utf-8")
                except UnicodeDecodeError:
                    filter_text += byte.decode("utf-8", "replace")
                apply_filter()
                draw_overlay()
    finally:
        if cursor_row > 0:
            sys.stdout.write(f"\x1b[{cursor_row}A")
        sys.stdout.write("\r\x1b[J")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)


def _suggest(typed: str, aliases: dict[str, str], available: set[str] | None) -> list[str]:
    """Close-match suggestions for a mistyped model: aliases first, then IDs."""
    matches = difflib.get_close_matches(typed, list(aliases), n=3, cutoff=0.6)
    if not matches:
        retired = difflib.get_close_matches(typed, list(ALIAS_RENAMES), n=3, cutoff=0.5)
        matches = [
            ALIAS_RENAMES[old]
            for old in retired
            if ALIAS_RENAMES[old] in aliases
        ]
    if not matches and available:
        matches = difflib.get_close_matches(typed, sorted(available), n=3, cutoff=0.5)
    return list(dict.fromkeys(matches))


def _render_turn(
    events: Generator[Event, None, None],
) -> tuple[str, bool, UsageInfo | None]:
    """Stream one assistant turn to stdout.

    Returns (assistant_text, ok, usage). *ok* is False if the stream errored.
    """
    text, exit_code, usage = render_verbose_stream(events, show_usage=False)
    return text, exit_code == 0, usage


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


_SEARCH_MODES = ["auto", "native", "off"]
_SHORTCUT_HELP = """\
  Ctrl+S          toggle web search: off → auto → native → off
  Ctrl+O          select model (fuzzy menu with arrow keys)
  Ctrl+G          show this help
  Enter           send message
  Ctrl+J          insert newline
  Ctrl+C          stop reply / exit (at empty prompt)""".splitlines()


def _compute_tools(search_mode: str) -> list[dict] | None:
    if search_mode == "off":
        return None
    if search_mode == "native":
        return [{"type": "openrouter:web_search", "parameters": {"engine": "native"}}]
    return [{"type": "openrouter:web_search"}]  # auto


def chat(
    model: str,
    cfg: Config,
    *,
    model_input: str | None = None,
    history: list[dict] | None = None,
) -> int:
    """Run an interactive multi-turn chat REPL. Returns an exit code.

    Keyboard shortcuts (raw-TTY mode):
      Ctrl+S  toggle web search: off → auto → native → off
      Ctrl+O  select model (fuzzy menu with arrow keys)
      Ctrl+G  show help
      Enter   send message
      Ctrl+J  insert newline
      Ctrl+C  stop reply / exit (at empty prompt)
    """
    rc = _validate_model(model, cfg, model_input)
    if rc is not None:
        return rc

    search_mode = "off"

    sys.stdout.write(_CLEAR_SCREEN)
    _write(f"{_BLUE}{_BAR}{_RESET}\n")
    _write(f"  {_CYAN}aisk chat{_RESET} {_DIM}— {model}  ·  Search: {search_mode}{_RESET}\n")
    _write(f"{_BLUE}{_BAR}{_RESET}\n")

    messages: list[dict] = list(history) if history else []
    prompt_history: list[str] = []
    totals = {"cost": 0.0, "in": 0, "out": 0, "any_cost": False}
    had_success = False

    def _make_footer() -> str:
        return f"{_DIM}{model}  |  Search: {search_mode}  |  Ctrl+S: search · Ctrl+O: model · Ctrl+G: help · Enter: send · Ctrl-J: newline · Ctrl+C: stop/exit{_RESET}"

    def _toggle_search() -> None:
        nonlocal search_mode
        idx = _SEARCH_MODES.index(search_mode)
        search_mode = _SEARCH_MODES[(idx + 1) % len(_SEARCH_MODES)]

    def _select_model() -> str | None:
        nonlocal model
        selected = _select_model_prompt(cfg.aliases)
        if selected is None:
            return None
        new_model = _handle_model_switch(selected, cfg)
        if new_model is not None:
            model = new_model
        return new_model

    def _show_help() -> None:
        _write("\r\n")
        for line in _SHORTCUT_HELP:
            _write(f"  {_DIM}{line}{_RESET}\r\n")
        _write("\r\n")

    while True:
        try:
            user = _read_user_input(
                prompt_history,
                on_ctrl_s=_toggle_search,
                on_ctrl_o=_select_model,
                on_ctrl_g=_show_help,
                footer=_make_footer,
            )
        except (EOFError, KeyboardInterrupt):
            _write(_CLEAR_SCREEN)
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
                    tools=_compute_tools(search_mode),
                )
            )
        except KeyboardInterrupt:
            messages.pop()
            _write(f"\n{_DIM}(interrupted){_RESET}\n")
            continue

        if not ok:
            messages.pop()
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


def _handle_model_switch(model_input: str, cfg: Config) -> str | None:
    """Validate and switch model. Returns the new model ID or None if invalid."""
    new_model = resolve_model(model_input, cfg.aliases)

    if model_input in cfg.aliases:
        pass  # skip cache check for known aliases
    else:
        verdict, available = cache.check_model(cfg.endpoint, cfg.api_key, new_model)
        if verdict is False:
            _write(f"\r\n  {_RED}Error: '{model_input}' is not a valid model.{_RESET}\r\n")
            suggestions = _suggest(model_input, cfg.aliases, available)
            if suggestions:
                _write(f"  {_DIM}Did you mean: {', '.join(suggestions)}?{_RESET}\r\n")
            _write("\r\n")
            return None
        elif verdict is None:
            pass  # unverifiable, proceed optimistically

    _write(f"\r\n  {_DIM}Switched to {new_model}{_RESET}\r\n")
    return new_model


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
