"""Disk cache for external-call responses, keyed by (namespace, identifier)
(docs/07_BACKEND_ARCHITECTURE.md §6). Shared infra used by both discovery providers and enrichment —
lives at the top level, not under `providers/`, so no module has to reach into a sibling module's
package to use it (docs/07_BACKEND_ARCHITECTURE.md §2). POC convenience to conserve free-tier quota
across repeated dev runs — not a productised cache store.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

_CACHE_DIR = Path(".cache")


def _path_for(namespace: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return _CACHE_DIR / namespace / f"{digest}.json"


def cache_get(namespace: str, key: str, ttl_seconds: int) -> dict | None:
    path = _path_for(namespace, key)
    if not path.exists():
        return None

    if time.time() - path.stat().st_mtime > ttl_seconds:
        return None

    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def cache_set(namespace: str, key: str, data: dict) -> None:
    path = _path_for(namespace, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
