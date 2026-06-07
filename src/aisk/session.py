from __future__ import annotations

import json
import os
import time
from pathlib import Path

from aisk import config
from aisk.permissions import chmod_private

SESSION_TTL = 7 * 24 * 3600  # seconds


def _sessions_dir() -> Path:
    return config.CONFIG_DIR / "sessions"


def _key() -> str:
    """Per-terminal key — the parent shell PID, stable within one terminal."""
    return str(os.getppid())


def _session_file(key: str) -> Path:
    return _sessions_dir() / f"{key}.json"


def _read(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except (ValueError, OSError):
        return None
    if isinstance(data, dict) and "model" in data and "messages" in data:
        return data
    return None


def save_session(
    model: str, messages: list[dict], *, key: str | None = None, now: float | None = None
) -> None:
    """Persist the conversation for the current terminal, then prune old ones."""
    now = time.time() if now is None else now
    d = _sessions_dir()
    d.mkdir(parents=True, exist_ok=True)
    # Conversations are stored in plain text — keep the directory owner-only.
    chmod_private(d, 0o700)
    path = _session_file(key or _key())
    path.write_text(json.dumps({"model": model, "messages": messages, "updated_at": now}))
    chmod_private(path, 0o600)
    _prune(now)


def load_session(*, key: str | None = None, now: float | None = None) -> dict | None:
    """The current terminal's conversation, else the most recent one (fallback)."""
    own = _session_file(key or _key())
    if own.exists():
        s = _read(own)
        if s:
            return s

    best: dict | None = None
    d = _sessions_dir()
    if d.exists():
        for f in d.glob("*.json"):
            s = _read(f)
            if s and (best is None or s.get("updated_at", 0) > best.get("updated_at", 0)):
                best = s
    return best


def _prune(now: float) -> None:
    d = _sessions_dir()
    if not d.exists():
        return
    for f in d.glob("*.json"):
        s = _read(f)
        if s is None or (now - s.get("updated_at", 0)) > SESSION_TTL:
            try:
                f.unlink()
            except OSError:
                pass
