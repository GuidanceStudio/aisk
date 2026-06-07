"""Tests for in-chat commands: /model, /search, /help."""

from unittest.mock import patch

from aisk.chat import chat
from aisk.client import ContentChunk, UsageInfo
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


def _fake_stream_one_reply(*chunks):
    """Return a fake stream_chat that yields one ContentChunk + UsageInfo."""
    def stream(endpoint, api_key, model, messages, **kw):
        content = " ".join(chunks)
        yield ContentChunk(content)
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)
    return stream


def test_slash_help_does_not_call_model():
    """Typing /help prints command list and does NOT call the model."""
    cfg = Config(api_key="k")
    calls = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        calls.append(("stream", model, messages))
        yield ContentChunk("response")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("/help")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    # /help should not trigger a model call
    stream_calls = [c for c in calls if c[0] == "stream"]
    assert len(stream_calls) == 0


def test_slash_model_switches_model():
    """Typing /model <alias> switches to that model and continues the chat."""
    cfg = Config(api_key="k")
    models_seen = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        models_seen.append(model)
        yield ContentChunk("ok")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("aisk.chat.cache.check_model", return_value=(None, None)), \
         patch("builtins.input", _inputs("/model gel", "hello")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    # First call (after /model) should use the new model gel
    assert len(models_seen) >= 1
    assert models_seen[0] == "google/gemini-3.1-flash-lite-preview"


def test_slash_model_skips_validation_for_alias():
    """When switching to a known alias, no cache check is done."""
    cfg = Config(api_key="k")

    with patch("aisk.chat.cache.check_model") as chk, \
         patch("aisk.chat.stream_chat", _fake_stream_one_reply("ok")), \
         patch("builtins.input", _inputs("/model dsf", "hello")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    # /model dsf is a known alias → skip cache check
    chk.assert_not_called()


def test_slash_search_toggle_cycles():
    """/search cycles through search modes: auto → native → off → auto."""
    cfg = Config(api_key="k")
    tools_sent = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        tools_sent.append(kw.get("tools"))
        yield ContentChunk("ok")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs(
             "/search",   # auto → native
             "q1",
             "/search",   # native → off
             "q2",
             "/search",   # off → auto
             "q3",
         )):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    # After first /search: native mode
    assert tools_sent[0] == [{"type": "openrouter:web_search", "parameters": {"engine": "native"}}]
    # After second /search: off mode (no tools)
    assert tools_sent[1] is None
    # After third /search: auto mode
    assert tools_sent[2] == [{"type": "openrouter:web_search"}]


def test_slash_unknown_command(capsys):
    """An unknown /xxx command prints an error but does NOT call the model."""
    cfg = Config(api_key="k")
    calls = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        calls.append(("stream", model))
        yield ContentChunk("response")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("/unknown_cmd")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    out = capsys.readouterr().out
    assert "Unknown command" in out
    stream_calls = [c for c in calls if c[0] == "stream"]
    assert len(stream_calls) == 0


def test_normal_message_not_interpreted_as_command():
    """A message starting with a letter, not /, goes to the model normally."""
    cfg = Config(api_key="k")
    messages_sent = []

    def fake_stream(endpoint, api_key, model, messages, **kw):
        messages_sent.append([m.copy() for m in messages])
        yield ContentChunk("response")
        yield UsageInfo(prompt_tokens=1, completion_tokens=1)

    with patch("aisk.chat.stream_chat", fake_stream), \
         patch("builtins.input", _inputs("how are you?")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    assert len(messages_sent) == 1
    assert messages_sent[0][0]["content"] == "how are you?"


def test_slash_help_content(capsys):
    """/help prints a list of available commands."""
    cfg = Config(api_key="k")

    with patch("aisk.chat.stream_chat", _fake_stream_one_reply("ok")), \
         patch("builtins.input", _inputs("/help")):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsf")

    out = capsys.readouterr().out
    assert "/model" in out
    assert "/search" in out
    assert "/help" in out
