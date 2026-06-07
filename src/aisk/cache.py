from __future__ import annotations

import json
import time
from pathlib import Path

from aisk import config
from aisk.client import list_models
from aisk.permissions import chmod_private

CACHE_TTL = 24 * 3600  # seconds


def _cache_path() -> Path:
    return config.CONFIG_DIR / "models-cache.json"


def _load() -> dict:
    p = _cache_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (ValueError, OSError):
        return {}


def _read(endpoint: str, now: float) -> tuple[set[str] | None, bool]:
    """Return (cached model set, is_fresh) for an endpoint, or (None, False)."""
    entry = _load().get(endpoint)
    if not entry:
        return None, False
    models = set(entry.get("models", []))
    fresh = (now - entry.get("ts", 0)) < CACHE_TTL
    return models, fresh


def _write(endpoint: str, models: set[str], now: float) -> None:
    data = _load()
    data[endpoint] = {"ts": now, "models": sorted(models)}
    p = _cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data))
    chmod_private(p, 0o600)


def check_model(
    endpoint: str, api_key: str, model: str, *, now: float | None = None
) -> tuple[bool | None, set[str] | None]:
    """Best-effort check that *model* is available at *endpoint*.

    Returns (verdict, available) where verdict is:
      - True  → model is available,
      - False → model is confirmed not available (live),
      - None  → could not determine (no /models, network error).

    A fresh positive cache hit is trusted; anything else (miss, stale, or a
    negative against the cache) triggers a live refetch — the cache is never
    authoritative on "not found", since a newly added model wouldn't be in it.
    """
    now = time.time() if now is None else now
    cached, fresh = _read(endpoint, now)
    if cached is not None and fresh and model in cached:
        return True, cached

    live = list_models(endpoint, api_key)
    if live is None:
        return None, cached

    _write(endpoint, live, now)
    return (model in live), live
