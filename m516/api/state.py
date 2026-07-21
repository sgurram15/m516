"""In-memory scan state (docs/05_API_DESIGN.md). Deliberately not a database — WP0-WP4 never wired
Postgres, and `docs/02_ARCHITECTURE.md` documents "no queues, no workers, no background jobs" as
intentional for the POC. A module-level dict is the same class of simplification as `m516/cache.py`'s
disk cache: correct for a single-instance demo, lost on restart, not meant to survive productisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from m516.pipeline import PipelineResult

ScanStatus = Literal["pending", "running", "done", "error"]


@dataclass
class ScanState:
    scan_id: str
    domain: str
    pack_id: str
    status: ScanStatus = "pending"
    stage: str | None = None
    error: str | None = None
    result: PipelineResult | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None


_SCANS: dict[str, ScanState] = {}


def create(scan_id: str, domain: str, pack_id: str) -> ScanState:
    state = ScanState(scan_id=scan_id, domain=domain, pack_id=pack_id)
    _SCANS[scan_id] = state
    return state


def get(scan_id: str) -> ScanState | None:
    return _SCANS.get(scan_id)


def update(scan_id: str, **fields) -> None:
    state = _SCANS[scan_id]
    for key, value in fields.items():
        setattr(state, key, value)
