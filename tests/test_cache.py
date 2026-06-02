from unittest.mock import MagicMock, patch

import httpx

from aisk import cache
from aisk.client import _models_url, list_models

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def _resp(status=200, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload if payload is not None else {}
    return r


# --- _models_url / list_models ---


def test_models_url_derives_from_chat_completions():
    assert _models_url(ENDPOINT) == "https://openrouter.ai/api/v1/models"


def test_models_url_none_for_nonstandard():
    assert _models_url("https://x.example/weird") is None


def test_list_models_parses_ids():
    payload = {"data": [{"id": "a/b"}, {"id": "c/d"}, {"nope": 1}]}
    with patch("aisk.client.httpx.get", return_value=_resp(200, payload)):
        assert list_models(ENDPOINT, "k") == {"a/b", "c/d"}


def test_list_models_non200_returns_none():
    with patch("aisk.client.httpx.get", return_value=_resp(500, {})):
        assert list_models(ENDPOINT, "k") is None


def test_list_models_network_error_returns_none():
    with patch("aisk.client.httpx.get", side_effect=httpx.ConnectError("x")):
        assert list_models(ENDPOINT, "k") is None


def test_list_models_unknown_url_no_call():
    with patch("aisk.client.httpx.get") as g:
        assert list_models("https://x/weird", "k") is None
        g.assert_not_called()


# --- check_model (cache logic) ---


def test_check_model_fresh_hit_no_fetch():
    now = 1000.0
    cache._write(ENDPOINT, {"a/b", "c/d"}, now)
    with patch("aisk.cache.list_models") as fetch:
        verdict, _ = cache.check_model(ENDPOINT, "k", "a/b", now=now + 10)
    assert verdict is True
    fetch.assert_not_called()


def test_check_model_negative_refetches_live():
    now = 1000.0
    cache._write(ENDPOINT, {"a/b"}, now)  # fresh but missing the model
    with patch("aisk.cache.list_models", return_value={"a/b", "z/z"}) as fetch:
        verdict, _ = cache.check_model(ENDPOINT, "k", "z/z", now=now + 10)
    assert verdict is True  # found in the live refetch
    fetch.assert_called_once()


def test_check_model_invalid_after_refetch():
    now = 1000.0
    cache._write(ENDPOINT, {"a/b"}, now)
    with patch("aisk.cache.list_models", return_value={"a/b"}):
        verdict, available = cache.check_model(ENDPOINT, "k", "dsv4", now=now + 10)
    assert verdict is False
    assert available == {"a/b"}


def test_check_model_stale_refetches_even_on_positive():
    now = 1000.0
    cache._write(ENDPOINT, {"a/b"}, now)
    with patch("aisk.cache.list_models", return_value={"a/b"}) as fetch:
        cache.check_model(ENDPOINT, "k", "a/b", now=now + cache.CACHE_TTL + 1)
    fetch.assert_called_once()


def test_check_model_fetch_fails_returns_none():
    with patch("aisk.cache.list_models", return_value=None):
        verdict, _ = cache.check_model(ENDPOINT, "k", "x", now=1000.0)
    assert verdict is None


def test_check_model_writes_cache():
    now = 2000.0
    with patch("aisk.cache.list_models", return_value={"a/b"}):
        cache.check_model(ENDPOINT, "k", "a/b", now=now)
    cached, fresh = cache._read(ENDPOINT, now)
    assert cached == {"a/b"} and fresh
