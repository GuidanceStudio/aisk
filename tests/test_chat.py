from unittest.mock import patch

from aisk.chat import _render_turn, _suggest, chat
from aisk.client import ContentChunk, ErrorInfo, UsageInfo
from aisk.config import DEFAULT_ALIASES, Config


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
    cfg = Config(api_key="k")  # "dsv4f" is a default alias
    with patch("aisk.chat.cache.check_model") as chk, \
         patch("builtins.input", _inputs()):
        chat("deepseek/deepseek-v4-flash", cfg, model_input="dsv4f")
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
    assert "dsv4f" in out  # suggested the close alias


def test_chat_unverifiable_model_proceeds():
    cfg = Config(api_key="k")
    with patch("aisk.chat.cache.check_model", return_value=(None, None)), \
         patch("builtins.input", _inputs()):
        assert chat("whatever/model", cfg, model_input="whatever/model") == 0


def test_suggest_close_alias():
    s = _suggest("dsv4", DEFAULT_ALIASES, None)
    assert "dsv4f" in s and "dsv4p" in s


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
