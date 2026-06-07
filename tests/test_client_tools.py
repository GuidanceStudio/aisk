import json
from unittest.mock import MagicMock, patch

from aisk.client import stream_chat, ContentChunk, UsageInfo


def _make_sse(*chunks) -> list[str]:
    lines = []
    for c in chunks:
        lines.append("data: " + json.dumps(c))
    lines.append("data: [DONE]")
    return lines


def test_stream_chat_without_tools():
    """Without tools param, payload does not contain 'tools' key."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = _make_sse(
        {"choices": [{"delta": {"content": "hello"}}]},
        {"usage": {"prompt_tokens": 1, "completion_tokens": 1}},
    )
    mock_client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = mock_response

    with patch("aisk.client.httpx.Client", mock_client):
        events = list(stream_chat("https://example.com/api", "key", "test-model", "hi"))
        assert any(isinstance(e, ContentChunk) for e in events)

    call_args = mock_client.return_value.__enter__.return_value.stream.call_args
    payload = call_args.kwargs["json"]
    assert "tools" not in payload


def test_stream_chat_with_tools():
    """With tools param, the payload includes the tools array."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = _make_sse(
        {"choices": [{"delta": {"content": "hello"}}]},
        {"usage": {"prompt_tokens": 1, "completion_tokens": 1}},
    )
    mock_client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = mock_response

    tools = [{"type": "openrouter:web_search"}]

    with patch("aisk.client.httpx.Client", mock_client):
        events = list(stream_chat("https://example.com/api", "key", "test-model", "hi", tools=tools))
        assert any(isinstance(e, ContentChunk) for e in events)

    call_args = mock_client.return_value.__enter__.return_value.stream.call_args
    payload = call_args.kwargs["json"]
    assert "tools" in payload
    assert payload["tools"] == tools


def test_stream_chat_with_tools_native_engine():
    """Tools with native engine parameters are passed through as-is."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = _make_sse(
        {"choices": [{"delta": {"content": "ok"}}]},
        {"usage": {"prompt_tokens": 1, "completion_tokens": 1}},
    )
    mock_client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = mock_response

    tools = [{"type": "openrouter:web_search", "parameters": {"engine": "native"}}]

    with patch("aisk.client.httpx.Client", mock_client):
        events = list(stream_chat("https://openrouter.ai/api/v1/chat/completions", "key", "test-model", "hi", tools=tools))
        assert any(isinstance(e, ContentChunk) for e in events)

    call_args = mock_client.return_value.__enter__.return_value.stream.call_args
    payload = call_args.kwargs["json"]
    assert payload["tools"] == tools


def test_stream_chat_tools_none_means_no_tools():
    """tools=None behaves the same as the parameter not being passed."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = _make_sse(
        {"choices": [{"delta": {"content": "x"}}]},
        {"usage": {"prompt_tokens": 1, "completion_tokens": 1}},
    )
    mock_client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = mock_response

    with patch("aisk.client.httpx.Client", mock_client):
        events = list(stream_chat("https://example.com/api", "key", "test-model", "hi", tools=None))
        assert any(isinstance(e, ContentChunk) for e in events)

    call_args = mock_client.return_value.__enter__.return_value.stream.call_args
    payload = call_args.kwargs["json"]
    assert "tools" not in payload
