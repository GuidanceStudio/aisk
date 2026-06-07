from __future__ import annotations

import os
from pathlib import Path


def chmod_private(path: str | Path, mode: int) -> None:
    """Apply private POSIX permissions when the platform supports them."""
    try:
        os.chmod(path, mode)
    except (OSError, NotImplementedError):
        pass
