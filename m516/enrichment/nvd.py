"""NVD/CVE adapter (ADR-006). https://services.nvd.nist.gov/rest/json/cves/2.0

FR-2.1: look up known vulnerabilities by CPE (preferred), falling back to a keyword search on
`version_string` when there's no CPE. Live-verified against real NVD responses: `cpeName` (exact match)
only hits when the CPE string exactly matches NVD's dictionary entry, including a specific version.
Providers often report a wildcarded CPE (no version) — for those, `virtualMatchString` (NVD's broader,
version-range-aware match) is used instead. Confirmed live: a wildcarded nginx CPE got 0 results via
`cpeName` but 41 via `virtualMatchString`; a versioned CPE got exact `cpeName` hits.

Rate limits (confirmed live): 5 requests/30s unauthenticated, 50/30s with `NVD_API_KEY` (`apiKey`
header) — ADR-002 spirit: works without a key, just slower.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from m516.cache import cache_get, cache_set
from m516.logging import get_logger
from m516.models import Service

_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_RESULTS_PER_PAGE = 20

_MIN_INTERVAL_WITH_KEY = 30 / 50
_MIN_INTERVAL_NO_KEY = 30 / 5
_last_request_at = 0.0

logger = get_logger(__name__)


@dataclass
class CVEMatch:
    id: str
    cvss_score: float | None
    cvss_severity: str | None
    published: datetime | None
    description: str | None


def lookup_cves(service: Service, api_key: str | None = None, cache_ttl_seconds: int = 86400) -> list[CVEMatch]:
    params, cache_key = _build_query(service)
    if params is None:
        return []

    data = cache_get("nvd", cache_key, cache_ttl_seconds)
    if data is None:
        _throttle(has_key=bool(api_key))
        headers = {"apiKey": api_key} if api_key else {}
        response = requests.get(_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        cache_set("nvd", cache_key, data)

    return from_records(data)


def _build_query(service: Service) -> tuple[dict | None, str | None]:
    """CPE preferred (FR-2.1); versioned CPE -> exact match, wildcarded CPE -> broad match, no CPE but
    a version string -> keyword search. No cpe/version_string -> nothing to query (BR-2)."""
    if service.cpe:
        parts = service.cpe.split(":")
        version = parts[5] if len(parts) > 5 else "*"
        if version not in ("*", "-", ""):
            return {"cpeName": service.cpe, "resultsPerPage": _RESULTS_PER_PAGE}, f"cpeName:{service.cpe}"
        return (
            {"virtualMatchString": service.cpe, "resultsPerPage": _RESULTS_PER_PAGE},
            f"virtualMatchString:{service.cpe}",
        )

    if service.version_string:
        return (
            {"keywordSearch": service.version_string, "resultsPerPage": _RESULTS_PER_PAGE},
            f"keywordSearch:{service.version_string}",
        )

    return None, None


def _throttle(has_key: bool) -> None:
    global _last_request_at
    min_interval = _MIN_INTERVAL_WITH_KEY if has_key else _MIN_INTERVAL_NO_KEY
    elapsed = time.monotonic() - _last_request_at
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_request_at = time.monotonic()


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _extract_cvss(cve: dict) -> tuple[float | None, str | None]:
    metrics = cve.get("metrics", {}) or {}

    for key in ("cvssMetricV31", "cvssMetricV30"):
        entries = metrics.get(key) or []
        if entries:
            data = entries[0].get("cvssData", {}) or {}
            return data.get("baseScore"), data.get("baseSeverity")

    entries = metrics.get("cvssMetricV2") or []
    if entries:
        data = entries[0].get("cvssData", {}) or {}
        return data.get("baseScore"), entries[0].get("baseSeverity")

    return None, None


def _extract_description(cve: dict) -> str | None:
    for entry in cve.get("descriptions", []) or []:
        if entry.get("lang") == "en":
            return entry.get("value")
    return None


def from_records(data: dict) -> list[CVEMatch]:
    """Offline parse path (docs/07_BACKEND_ARCHITECTURE.md §8)."""
    if not data:
        return []

    matches = []
    for item in data.get("vulnerabilities", []) or []:
        cve = item.get("cve", {}) or {}
        cve_id = cve.get("id")
        if not cve_id:
            continue

        cvss_score, cvss_severity = _extract_cvss(cve)
        matches.append(
            CVEMatch(
                id=cve_id,
                cvss_score=cvss_score,
                cvss_severity=cvss_severity,
                published=_parse_datetime(cve.get("published")),
                description=_extract_description(cve),
            )
        )

    return matches
