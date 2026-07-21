"""Red/yellow/green detection-level classification — a presentation-friendly overlay on top of the
existing severity/confidence data, deterministic and explainable (ADR-007, BR-3), never an LLM.

Rule criteria for `finding_detection_level`:
  - red    — severity is critical/high AND the CVE match is version-confirmed ("exact"). Real danger.
  - yellow — severity is critical/high but the match is "broad" (unconfirmed version — real signal,
             needs verification before acting on it) OR severity is "medium" regardless of confidence.
  - green  — severity is "low".

A CVE-eligible service that was checked and matched **zero** CVEs isn't a `Finding` at all (see
`m516/findings.py`) — callers should treat that case as green "clean" themselves; a service with no
CPE/version data was never evaluated at all, and should be shown as neutral, not green. Green must mean
"checked and fine", never "we didn't check" — collapsing "unknown" into "green" would misrepresent
absence of data as safety.

Rule criteria for `cert_detection_level`:
  - red    — certificate expired.
  - yellow — certificate valid but expires within 30 days.
  - green  — certificate valid with more than 30 days remaining.
  - None   — no certificate data was captured for this asset (neutral, not green).
"""

from __future__ import annotations

from datetime import datetime, timezone

from m516.findings import Finding
from m516.models import Asset

_CERT_EXPIRY_WARNING_DAYS = 30


def finding_detection_level(finding: Finding) -> str:
    if finding.severity in ("critical", "high"):
        return "red" if finding.match_confidence == "exact" else "yellow"
    if finding.severity == "medium":
        return "yellow"
    return "green"


def cert_detection_level(asset: Asset) -> str | None:
    if asset.cert_valid_until is None:
        return None

    valid_until = asset.cert_valid_until
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)

    days_remaining = (valid_until - datetime.now(timezone.utc)).days
    if days_remaining < 0:
        return "red"
    if days_remaining < _CERT_EXPIRY_WARNING_DAYS:
        return "yellow"
    return "green"
