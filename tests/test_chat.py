from unittest.mock import patch

from aisk.chat import _render_turn, chat
from aisk.client import ContentChunk, ErrorInfo, UsageInfo
from aisk.config import Config


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


def test_render_turn_collects_content(capsys):
    text, ok = _render_turn(
        _events(
            ContentChunk("Hello "),
            ContentChunk("world"),
            UsageInfo(prompt_tokens=3, completion_tokens=2),
        )
    )
    assert text == "Hello world"
    assert ok is True
    assert "Hello world" in capsys.readouterr().out


def test_render_turn_error():
    text, ok = _render_turn(_events(ErrorInfo(message="boom")))
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


def test_chat_rolls_back_failed_turn():
    cfg = Config(api_key="k")
    captured = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        captured.append([m.copy() for m in messages])
        if len(captured) == 1:
            yield ErrorInfo(message="boom")
        else:
            yield ContentChunk("ok")

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("bad", "good")):
        chat("m", cfg)

    # The failed 'bad' turn was rolled back, so the second call only sees 'good'.
    assert captured[1] == [{"role": "user", "content": "good"}]


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


def test_chat_keyboardinterrupt_exits_clean():
    cfg = Config(api_key="k")

    def boom(prompt=""):
        raise KeyboardInterrupt

    with patch("builtins.input", boom):
        assert chat("m", cfg) == 0
