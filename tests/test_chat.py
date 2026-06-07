import os
import re
import select
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from aisk.chat import (
    _display_width,
    _input_visual_lines,
    _render_turn,
    _suggest,
    _terminal_columns,
    chat,
)
from aisk.client import ContentChunk, ErrorInfo, UsageInfo
from aisk.config import DEFAULT_ALIASES, Config

try:
    import pty
except ImportError:  # pragma: no cover - non-POSIX
    pty = None


def _events(*evs):
    yield from evs


def _inputs(*values):
    """Return a fake input() that yields values then raises EOFError."""
    it = iter(values)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    return fake_input


def _run_pty_python(code: str, payload: bytes) -> str:
    if pty is None:
        pytest.skip("pty is not available")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [os.path.abspath("src"), env.get("PYTHONPATH", "")]
    )

    master, slave = pty.openpty()
    proc = subprocess.Popen(
        [sys.executable, "-c", code],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
        close_fds=True,
    )
    os.close(slave)
    out = b""

    try:
        deadline = time.time() + 2
        while time.time() < deadline and b"\xe2\x9d\xaf" not in out:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                out += os.read(master, 4096)

        os.write(master, payload)

        deadline = time.time() + 2
        while time.time() < deadline and b"GOT:" not in out:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                out += os.read(master, 4096)

        proc.wait(timeout=2)
    finally:
        if proc.poll() is None:
            proc.terminate()
        os.close(master)

    return out.decode("utf-8", "replace")


def _strip_terminal_codes(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z~]", "", text)


def test_render_turn_collects_content(capsys):
    text, ok, usage = _render_turn(
        _events(
            ContentChunk("Hello "),
            ContentChunk("world"),
            UsageInfo(prompt_tokens=3, completion_tokens=2),
        )
    )
    assert text == "Hello world"
    assert ok is True
    assert usage.prompt_tokens == 3
    assert "Hello world" in capsys.readouterr().out


def test_render_turn_error():
    text, ok, usage = _render_turn(_events(ErrorInfo(message="boom")))
    assert ok is False


def test_chat_resends_growing_history():
    cfg = Config(api_key="k")
    captured = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        captured.append([m.copy() for m in messages])
        yield ContentChunk(f"reply{len(captured)}")

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("hi", "again")):
        assert chat("m", cfg) == 0

    assert captured[0] == [{"role": "user", "content": "hi"}]
    assert captured[1] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "reply1"},
        {"role": "user", "content": "again"},
    ]


def test_chat_failfast_on_first_error():
    """A first turn that errors (e.g. invalid model) exits instead of looping."""
    cfg = Config(api_key="k")

    def err_stream(endpoint, api_key, model, messages, **kw):
        yield ErrorInfo(message="bad model")

    with patch("aisk.chat.stream_chat", err_stream), \
         patch("builtins.input", _inputs("hi", "again")):
        assert chat("m", cfg) == 1


def test_chat_rolls_back_error_after_success():
    """An error AFTER a successful turn rolls back and keeps the chat alive."""
    cfg = Config(api_key="k")
    captured = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        captured.append([m.copy() for m in messages])
        n = len(captured)
        if n == 2:
            yield ErrorInfo(message="blip")
        else:
            yield ContentChunk(f"ok{n}")

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("a", "b", "c")):
        chat("m", cfg)

    # turn1 ok, turn2 errored (rolled back), turn3 sees a / ok1 / c
    assert captured[2] == [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "ok1"},
        {"role": "user", "content": "c"},
    ]


# --- M31: preflight model validation ---


def test_chat_skips_preflight_for_alias():
    cfg = Config(api_key="k")  # "dsf" is a default alias
    with patch("aisk.chat.cache.check_model") as chk, \
         patch("builtins.input", _inputs()):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")
    chk.assert_not_called()


def test_chat_no_model_input_skips_preflight():
    cfg = Config(api_key="k")
    with patch("aisk.chat.cache.check_model") as chk, \
         patch("builtins.input", _inputs()):
        chat("m", cfg)
    chk.assert_not_called()


def test_chat_invalid_model_aborts_with_suggestions(capsys):
    cfg = Config(api_key="k")
    with patch("aisk.chat.cache.check_model",
               return_value=(False, {"deepseek/deepseek-v4-flash"})), \
         patch("builtins.input") as inp:
        rc = chat("dsv4", cfg, model_input="dsv4")
    assert rc == 1
    inp.assert_not_called()  # never reached the prompt
    out = capsys.readouterr().out
    assert "not a valid model" in out
    assert "dsf" in out  # suggested the close alias


def test_chat_unverifiable_model_proceeds():
    cfg = Config(api_key="k")
    with patch("aisk.chat.cache.check_model", return_value=(None, None)), \
         patch("builtins.input", _inputs()):
        assert chat("whatever/model", cfg, model_input="whatever/model") == 0


def test_suggest_close_alias():
    s = _suggest("dsv4", DEFAULT_ALIASES, None)
    assert "dsf" in s and "dsp" in s


def test_prompt_brackets_ansi_under_readline():
    """With readline, the prompt's color codes must be \\x01/\\x02-bracketed."""
    import aisk.chat as c
    if c._HAS_READLINE:
        assert "\x01" in c._PROMPT and "\x02" in c._PROMPT


def test_configure_readline_enables_bracketed_paste():
    import aisk.chat as c

    calls = []

    class FakeReadline:
        __doc__ = "GNU readline"

        @staticmethod
        def parse_and_bind(command):
            calls.append(command)

    assert c._configure_readline(FakeReadline) is True
    assert calls == ["set enable-bracketed-paste on"]


def test_configure_readline_ignores_unsupported_binding():
    import aisk.chat as c

    class FakeReadline:
        @staticmethod
        def parse_and_bind(command):
            raise ValueError("unsupported")

    assert c._configure_readline(FakeReadline) is False


def test_tty_input_bracketed_paste_keeps_multiline_prompt():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x1b[200~prima riga\nseconda riga\x1b[201~\r")
    assert "GOT:'prima riga\\nseconda riga'" in out


def test_tty_input_arrow_up_recalls_prompt_history():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input(['vecchio prompt'])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x1b[A\r")
    assert "GOT:'vecchio prompt'" in out


def test_tty_input_preserves_utf8_text():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, "caffè 界\r".encode())
    assert "GOT:'caffè 界'" in out


def test_tty_input_left_right_insert_in_middle():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"ac\x1b[Db\r")
    assert "GOT:'abc'" in out


def test_tty_input_up_down_moves_within_multiline_prompt():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x1b[200~abcd\nefgh\x1b[201~\x1b[A\x1b[DX\r")
    assert "GOT:'abcXd\\nefgh'" in out


def test_tty_input_csi_1_up_variant_moves_within_multiline_prompt():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x1b[200~abcd\nefgh\x1b[201~\x1b[1A!\r")
    assert "GOT:'abcd!\\nefgh'" in out


def test_tty_input_down_moves_within_multiline_prompt():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x1b[200~abcd\nefgh\x1b[201~\x1b[A\x1b[BX\r")
    assert "GOT:'abcd\\nefghX'" in out


def test_tty_input_ctrl_enter_inserts_newline():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"prima\x1b[13;5useconda\r")
    assert "GOT:'prima\\nseconda'" in out


def test_tty_input_ctrl_j_inserts_newline():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"prima\nseconda\r")
    assert "GOT:'prima\\nseconda'" in out


def test_tty_input_continuation_line_has_no_extra_prompt():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _strip_terminal_codes(_run_pty_python(code, b"prima\nseconda\r"))
    assert "❯ prima\r\n  seconda" in out
    assert "❯ prima\r\n❯ seconda" not in out


def test_chat_banner_mentions_ctrl_j(capsys):
    cfg = Config(api_key="k")
    with patch("builtins.input", _inputs()):
        chat("m", cfg)

    out = capsys.readouterr().out
    assert "Enter: send" in out
    assert "Ctrl-J: newline" in out
    assert "Ctrl-C: stop the reply" not in out


def test_tty_input_delete_removes_character_at_cursor():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"abcd\x1b[D\x1b[D\x1b[3~\r")
    assert "GOT:'abd'" in out


def test_tty_input_ctrl_d_removes_character_at_cursor():
    code = (
        "from aisk.chat import _read_user_input\n"
        "s = _read_user_input([])\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"abcd\x1b[D\x1b[D\x04\r")
    assert "GOT:'abd'" in out


def test_input_visual_lines_counts_terminal_wraps():
    assert _input_visual_lines("12345678", columns=10) == 1
    assert _input_visual_lines("123456789", columns=10) == 2
    assert _input_visual_lines("123456789\nabc", columns=10) == 3


def test_display_width_ignores_combining_marks_and_counts_wide_chars():
    assert _display_width("e\u0301") == 1
    assert _display_width("界") == 2


def test_terminal_columns_falls_back_when_tty_reports_zero(monkeypatch):
    import aisk.chat as c

    monkeypatch.setattr(
        c.os,
        "get_terminal_size",
        lambda fd: os.terminal_size((0, 0)),
    )
    assert _terminal_columns() == 80


def test_chat_blank_input_skipped():
    cfg = Config(api_key="k")
    calls = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        calls.append(messages)
        yield ContentChunk("x")

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("  ", "real")):
        chat("m", cfg)

    # Blank line did not trigger a request.
    assert len(calls) == 1


def test_chat_keyboardinterrupt_at_prompt_exits_clean():
    cfg = Config(api_key="k")

    def boom(prompt=""):
        raise KeyboardInterrupt

    with patch("builtins.input", boom):
        assert chat("m", cfg) == 0


def test_chat_interrupt_during_reply_continues():
    """Ctrl-C during a reply drops that exchange but keeps the chat alive."""
    cfg = Config(api_key="k")
    captured = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        captured.append([m.copy() for m in messages])
        if len(captured) == 1:
            yield ContentChunk("partial...")
            raise KeyboardInterrupt  # stall interrupted mid-reply
        else:
            yield ContentChunk("done")

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("first", "second")):
        assert chat("m", cfg) == 0

    # Second turn must NOT carry the interrupted 'first' exchange.
    assert captured[1] == [{"role": "user", "content": "second"}]


def test_chat_cumulative_cost(capsys):
    cfg = Config(api_key="k")

    def fake_stream(endpoint, api_key, model, messages, **kw):
        yield ContentChunk("x")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1, cost=0.00001)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("a", "b")):
        chat("m", cfg)

    out = capsys.readouterr().out
    assert "$0.000010" in out          # per-turn cost
    assert "Σ $0.000020" in out        # cumulative across two turns
