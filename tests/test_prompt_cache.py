from unittest.mock import MagicMock, patch

from aisk.client import _apply_prompt_cache, _supports_explicit_cache, stream_chat

OR = "https://openrouter.ai/api/v1/chat/completions"
OTHER = "https://api.example.com/v1/chat/completions"
EPHEMERAL = {"type": "ephemeral"}


def test_supports_explicit_cache():
    assert _supports_explicit_cache("anthropic/claude-opus-4.8")
    assert _supports_explicit_cache("google/gemini-3.5-flash")
    assert not _supports_explicit_cache("openai/gpt-5.5")
    assert not _supports_explicit_cache("deepseek/deepseek-v4-flash")


def test_apply_cache_marks_last_message_anthropic_openrouter():
    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "yo"},
        {"role": "user", "content": "more"},
    ]
    out = _apply_prompt_cache(msgs, "anthropic/claude-opus-4.8", OR)
    assert out[-1]["content"] == [
        {"type": "text", "text": "more", "cache_control": EPHEMERAL}
    ]
    assert out[0] == {"role": "user", "content": "hi"}  # earlier ones untouched
    assert msgs[-1] == {"role": "user", "content": "more"}  # input not mutated


def test_apply_cache_noop_for_openai():
    msgs = [{"role": "user", "content": "hi"}]
    assert _apply_prompt_cache(msgs, "openai/gpt-5.5", OR) == msgs


def test_apply_cache_noop_for_nonopenrouter():
    msgs = [{"role": "user", "content": "hi"}]
    assert _apply_prompt_cache(msgs, "anthropic/claude-opus-4.8", OTHER) == msgs


def _capture_json(model, messages, endpoint, prompt_cache):
    resp = MagicMock()
    resp.status_code = 200
    resp.iter_lines.return_value = iter(["data: [DONE]"])
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    client = MagicMock()
    client.stream.return_value = resp
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    with patch("aisk.client.httpx.Client", return_value=client):
        list(stream_chat(endpoint, "k", model, messages, prompt_cache=prompt_cache))
    return client.stream.call_args.kwargs["json"]


def test_stream_chat_applies_cache():
    payload = _capture_json(
        "anthropic/claude-opus-4.8", [{"role": "user", "content": "hi"}], OR, True
    )
    assert payload["messages"][-1]["content"][0]["cache_control"] == EPHEMERAL


def test_stream_chat_no_cache_when_disabled():
    payload = _capture_json(
        "anthropic/claude-opus-4.8", [{"role": "user", "content": "hi"}], OR, False
    )
    assert payload["messages"] == [{"role": "user", "content": "hi"}]
