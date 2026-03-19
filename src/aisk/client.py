from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Generator

import httpx


@dataclass
class ContentChunk:
    text: str


@dataclass
class ReasoningChunk:
    text: str


@dataclass
class UsageInfo:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float | None = None


@dataclass
class ErrorInfo:
    message: str
    code: str | None = None


Event = ContentChunk | ReasoningChunk | UsageInfo | ErrorInfo


def stream_chat(
    endpoint: str,
    api_key: str,
    model: str,
    message: str,
    *,
    read_timeout: float = 120.0,
    connect_timeout: float = 10.0,
) -> Generator[Event, None, None]:
    """Stream a chat completion from an OpenAI-compatible endpoint.

    Yields typed events as they arrive from the SSE stream.

    The *read_timeout* is an **idle timeout**: it fires only when no data
    arrives for the given number of seconds between chunks, so long-running
    streamed responses will never time out as long as the model keeps sending.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    timeout = httpx.Timeout(
        connect=connect_timeout,
        read=read_timeout,
        write=10.0,
        pool=10.0,
    )

    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream(
                "POST", endpoint, headers=headers, json=payload
            ) as response:
                if response.status_code != 200:
                    body = response.read().decode()
                    try:
                        err = json.loads(body)
                        msg = err.get("error", {}).get("message", body)
                    except (json.JSONDecodeError, AttributeError):
                        msg = body
                    yield ErrorInfo(message=msg, code=str(response.status_code))
                    return

                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    # Check for error in chunk
                    if "error" in chunk:
                        err_obj = chunk["error"]
                        msg = err_obj.get("message", str(err_obj)) if isinstance(err_obj, dict) else str(err_obj)
                        yield ErrorInfo(message=msg)
                        return

                    # Usage info (final chunk)
                    usage = chunk.get("usage")
                    if usage:
                        reasoning = 0
                        details = usage.get("completion_tokens_details") or {}
                        reasoning = details.get("reasoning_tokens", 0)
                        cost = usage.get("cost", usage.get("total_cost"))
                        yield UsageInfo(
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            reasoning_tokens=reasoning,
                            cost=cost,
                        )

                    # Content / reasoning deltas
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})

                    # Reasoning content (varies by provider)
                    for key in ("reasoning_content", "reasoning"):
                        rc = delta.get(key)
                        if rc:
                            yield ReasoningChunk(text=rc)

                    content = delta.get("content")
                    if content:
                        yield ContentChunk(text=content)

    except httpx.ConnectError as e:
        yield ErrorInfo(message=f"Connection error: {e}")
    except httpx.ConnectTimeout:
        yield ErrorInfo(message="Connection timed out")
    except httpx.ReadTimeout:
        yield ErrorInfo(
            message=f"Response timed out (no data for {read_timeout:.0f}s)"
        )
    except httpx.TimeoutException:
        yield ErrorInfo(message="Request timed out")
