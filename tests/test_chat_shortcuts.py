"""Tests for keyboard shortcuts (Ctrl+S, Ctrl+O, Ctrl+G) replacing slash commands."""

import os
import re
import select
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from aisk.chat import chat
from aisk.client import ContentChunk, UsageInfo
from aisk.config import Config


try:
    import pty
except ImportError:  # pragma: no cover - non-POSIX
    pty = None


def _events(*evs):
    yield from evs


def _inputs(*values):
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


def _run_pty_until_marker(code: str, payload: bytes, marker: bytes) -> str:
    """Like _run_pty_python but waits for a custom marker instead of ❯."""
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
        while time.time() < deadline and marker not in out:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                out += os.read(master, 4096)

        os.write(master, payload)

        deadline = time.time() + 2
        while time.time() < deadline and b"SELECTED:" not in out and b"CANCELLED" not in out:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                out += os.read(master, 4096)

        proc.wait(timeout=2)
    finally:
        if proc.poll() is None:
            proc.terminate()
        os.close(master)

    return out.decode("utf-8", "replace")


# ── Tests: slash commands no longer exist ──────────────────────────

def test_slash_model_goes_to_model():
    """/model <alias> is sent to the model as a regular message."""
    cfg = Config(api_key="k")
    messages_sent = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        messages_sent.append([m.copy() for m in messages])
        yield ContentChunk("ok")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("/model dsf")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    assert len(messages_sent) == 1
    assert messages_sent[0][0]["content"] == "/model dsf"


def test_slash_search_goes_to_model():
    """/search is sent to the model as a regular message."""
    cfg = Config(api_key="k")
    messages_sent = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        messages_sent.append([m.copy() for m in messages])
        yield ContentChunk("ok")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("/search")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    assert len(messages_sent) == 1
    assert messages_sent[0][0]["content"] == "/search"


def test_slash_help_goes_to_model():
    """/help is sent to the model as a regular message."""
    cfg = Config(api_key="k")
    messages_sent = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        messages_sent.append([m.copy() for m in messages])
        yield ContentChunk("ok")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("/help")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    assert len(messages_sent) == 1
    assert messages_sent[0][0]["content"] == "/help"


def test_message_starting_with_slash_not_special():
    """Any message starting with / is sent to the model, not interpreted."""
    cfg = Config(api_key="k")
    messages_sent = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        messages_sent.append([m.copy() for m in messages])
        yield ContentChunk("ok")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("/whatever nonsense")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    assert len(messages_sent) == 1
    assert messages_sent[0][0]["content"] == "/whatever nonsense"


# ── Tests: Ctrl+S search toggle (pty) ──────────────────────────────

def test_ctrl_s_toggles_search_in_tty():
    """Ctrl+S toggles search mode and prints notification, then continues input."""
    code = (
        "from aisk.chat import _read_user_input, _SEARCH_MODES\n"
        "search_state = {'mode': 'auto'}\n"
        "def toggle():\n"
        "    idx = _SEARCH_MODES.index(search_state['mode'])\n"
        "    search_state['mode'] = _SEARCH_MODES[(idx + 1) % len(_SEARCH_MODES)]\n"
        "    print(f'Search: {search_state[\"mode\"]}', flush=True)\n"
        "s = _read_user_input([], on_ctrl_s=toggle)\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x13test\r")
    assert "Search: native" in out
    assert "GOT:'test'" in out


def test_ctrl_s_toggles_through_all_modes():
    """Ctrl+S pressed multiple times cycles through all search modes."""
    code = (
        "from aisk.chat import _read_user_input, _SEARCH_MODES\n"
        "search_state = {'mode': 'auto'}\n"
        "def toggle():\n"
        "    idx = _SEARCH_MODES.index(search_state['mode'])\n"
        "    search_state['mode'] = _SEARCH_MODES[(idx + 1) % len(_SEARCH_MODES)]\n"
        "    print(f'Search: {search_state[\"mode\"]}', flush=True)\n"
        "s = _read_user_input([], on_ctrl_s=toggle)\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x13\x13\x13hello\r")
    assert "Search: native" in out
    assert "Search: off" in out
    assert "Search: auto" in out
    assert "GOT:'hello'" in out


# ── Tests: Ctrl+G help (pty) ───────────────────────────────────────

def test_ctrl_g_shows_help_in_tty():
    """Ctrl+G prints help text and continues reading input."""
    code = (
        "from aisk.chat import _read_user_input\n"
        "def show_help():\n"
        "    print('Ctrl+S: search  Ctrl+O: model  Ctrl+G: help', flush=True)\n"
        "s = _read_user_input([], on_ctrl_g=show_help)\n"
        "print('GOT:' + repr(s), flush=True)\n"
    )
    out = _run_pty_python(code, b"\x07msg\r")
    assert "Ctrl+S: search" in out
    assert "Ctrl+O: model" in out
    assert "Ctrl+G: help" in out
    assert "GOT:'msg'" in out


# ── Tests: Ctrl+O model selector (pty) ─────────────────────────────

_MODEL_SELECTOR_MARKER = b"Model"

def test_model_selector_navigate_and_select():
    """Arrow down + Enter selects the second alias in the list."""
    code = (
        "from aisk.chat import _model_selector\n"
        "from aisk.config import DEFAULT_ALIASES\n"
        "model = _model_selector(DEFAULT_ALIASES)\n"
        "if model:\n"
        "    print(f'SELECTED:{model}', flush=True)\n"
        "else:\n"
        "    print('CANCELLED', flush=True)\n"
    )
    out = _run_pty_until_marker(code, b"\x1b[B\r", _MODEL_SELECTOR_MARKER)
    assert "SELECTED:" in out


def test_model_selector_escape_cancels():
    """Esc cancels the model selector without selecting."""
    code = (
        "from aisk.chat import _model_selector\n"
        "from aisk.config import DEFAULT_ALIASES\n"
        "model = _model_selector(DEFAULT_ALIASES)\n"
        "if model:\n"
        "    print(f'SELECTED:{model}', flush=True)\n"
        "else:\n"
        "    print('CANCELLED', flush=True)\n"
    )
    out = _run_pty_until_marker(code, b"\x1b", _MODEL_SELECTOR_MARKER)
    assert "CANCELLED" in out


def test_model_selector_filter_and_select():
    """Typing a filter narrows the list, then Enter selects the match."""
    code = (
        "from aisk.chat import _model_selector\n"
        "from aisk.config import DEFAULT_ALIASES\n"
        "model = _model_selector(DEFAULT_ALIASES)\n"
        "if model:\n"
        "    print(f'SELECTED:{model}', flush=True)\n"
        "else:\n"
        "    print('CANCELLED', flush=True)\n"
    )
    out = _run_pty_until_marker(code, b"cls\r", _MODEL_SELECTOR_MARKER)
    assert "SELECTED:" in out


# ── Tests: model selector helper logic ─────────────────────────────

def test_model_selector_filter_matching():
    """_filter_items case-insensitive matches on alias and model name."""
    from aisk.chat import _filter_items
    aliases = {"dsf": "deepseek/deepseek-v4-flash", "cls": "anthropic/claude-sonnet-4.6"}
    assert len(_filter_items("ds", aliases)) == 1
    assert len(_filter_items("CL", aliases)) == 1
    assert len(_filter_items("anthropic", aliases)) == 1
    assert len(_filter_items("zzz", aliases)) == 0


# ── Tests: banner shows shortcuts ──────────────────────────────────

def test_chat_banner_shows_shortcut_keys(capsys):
    """The chat banner does not mention slash commands (shortcuts are in footer)."""
    cfg = Config(api_key="k")
    with patch("builtins.input", _inputs()):
        chat("m", cfg)

    out = capsys.readouterr().out
    assert "aisk chat" in out
    assert "/model" not in out
    assert "/search" not in out
    assert "/help" not in out
