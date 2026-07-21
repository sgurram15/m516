"""Disk cache for provider responses, keyed by (provider, identifier) (docs/07_BACKEND_ARCHITECTURE.md
§6). POC convenience to conserve free-tier quota across repeated dev runs — not a productised cache
store.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

_CACHE_DIR = Path(".cache")


def _path_for(provider: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return _CACHE_DIR / provider / f"{digest}.json"


def cache_get(provider: str, key: str, ttl_seconds: int) -> dict | None:
    path = _path_for(provider, key)
    if not path.exists():
        return None

    if time.time() - path.stat().st_mtime > ttl_seconds:
        return None

    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def cache_set(provider: str, key: str, data: dict) -> None:
    path = _path_for(provider, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
