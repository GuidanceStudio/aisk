import json
from unittest.mock import MagicMock, patch

import httpx

from aisk.client import (
    ContentChunk,
    ErrorInfo,
    ReasoningChunk,
    UsageInfo,
    stream_chat,
)

ENDPOINT = "https://api.example.com/v1/chat/completions"
API_KEY = "test-key"
MODEL = "test/model"
MESSAGE = "hello"


def _make_sse(*chunks: dict) -> list[str]:
    """Build SSE lines from chunk dicts."""
    lines = []
    for c in chunks:
        lines.append(f"data: {json.dumps(c)}")
    lines.append("data: [DONE]")
    return lines


def _mock_stream_response(lines: list[str], status_code: int = 200):
    """Create a mock httpx streaming response."""
    response = MagicMock()
    response.status_code = status_code
    response.iter_lines.return_value = iter(lines)
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)
    return response


def test_content_streaming():
    lines = _make_sse(
        {"choices": [{"delta": {"content": "Hello"}}]},
        {"choices": [{"delta": {"content": " world"}}]},
        {"usage": {"prompt_tokens": 5, "completion_tokens": 2}},
    )
    resp = _mock_stream_response(lines)
    client = MagicMock()
    client.stream.return_value = resp
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    with patch("aisk.client.httpx.Client", return_value=client):
        events = list(stream_chat(ENDPOINT, API_KEY, MODEL, MESSAGE))

    assert events[0] == ContentChunk(text="Hello")
    assert events[1] == ContentChunk(text=" world")
    assert isinstance(events[2], UsageInfo)
    assert events[2].prompt_tokens == 5
    assert events[2].completion_tokens == 2


def test_reasoning_chunks():
    lines = _make_sse(
        {"choices": [{"delta": {"reasoning_content": "thinking..."}}]},
        {"choices": [{"delta": {"content": "answer"}}]},
    )
    resp = _mock_stream_response(lines)
    client = MagicMock()
    client.stream.return_value = resp
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    with patch("aisk.client.httpx.Client", return_value=client):
        events = list(stream_chat(ENDPOINT, API_KEY, MODEL, MESSAGE))

    assert events[0] == ReasoningChunk(text="thinking...")
    assert events[1] == ContentChunk(text="answer")


def test_error_in_chunk():
    lines = _make_sse(
        {"error": {"message": "rate limited", "code": 429}},
    )
    resp = _mock_stream_response(lines)
    client = MagicMock()
    client.stream.return_value = resp
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    with patch("aisk.client.httpx.Client", return_value=client):
        events = list(stream_chat(ENDPOINT, API_KEY, MODEL, MESSAGE))

    assert len(events) == 1
    assert isinstance(events[0], ErrorInfo)
    assert "rate limited" in events[0].message


def test_http_error_status():
    resp = MagicMock()
    resp.status_code = 401
    resp.read.return_value = b'{"error": {"message": "invalid key"}}'
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)

    client = MagicMock()
    client.stream.return_value = resp
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    with patch("aisk.client.httpx.Client", return_value=client):
        events = list(stream_chat(ENDPOINT, API_KEY, MODEL, MESSAGE))

    assert len(events) == 1
    assert isinstance(events[0], ErrorInfo)
    assert "invalid key" in events[0].message


def test_connection_error():
    client = MagicMock()
    client.stream.side_effect = httpx.ConnectError("refused")
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    with patch("aisk.client.httpx.Client", return_value=client):
        events = list(stream_chat(ENDPOINT, API_KEY, MODEL, MESSAGE))

    assert len(events) == 1
    assert isinstance(events[0], ErrorInfo)
    assert "Connection error" in events[0].message


def test_usage_with_reasoning_tokens():
    lines = _make_sse(
        {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 50,
                "completion_tokens_details": {"reasoning_tokens": 30},
            },
            "cost": 0.0123,
        },
    )
    resp = _mock_stream_response(lines)
    client = MagicMock()
    client.stream.return_value = resp
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    with patch("aisk.client.httpx.Client", return_value=client):
        events = list(stream_chat(ENDPOINT, API_KEY, MODEL, MESSAGE))

    usage = [e for e in events if isinstance(e, UsageInfo)][0]
    assert usage.reasoning_tokens == 30
    assert usage.cost == 0.0123


def test_malformed_json_skipped():
    lines = [
        "data: not-json",
        'data: {"choices": [{"delta": {"content": "ok"}}]}',
        "data: [DONE]",
    ]
    resp = _mock_stream_response(lines)
    client = MagicMock()
    client.stream.return_value = resp
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    with patch("aisk.client.httpx.Client", return_value=client):
        events = list(stream_chat(ENDPOINT, API_KEY, MODEL, MESSAGE))

    assert len(events) == 1
    assert events[0] == ContentChunk(text="ok")
