"""Deterministic, explainable contextual risk scoring (ADR-007, BR-3) — never an LLM. FR-2.3 names
three factors: exposure, port sensitivity, staleness. `01_REQUIREMENTS.md` doesn't define these
precisely; the interpretation below is documented here and in `docs/15_PROGRESS.md`.

Formula: `contextual_score = min(100, round(base_cvss_x10 * port_multiplier * exposure_multiplier +
staleness_bonus))`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from m516.enrichment.nvd import CVEMatch
from m516.models import Asset, Service

# Universal infra knowledge (not pack-specific) — administrative/database ports carry more real-world
# risk than standard web ports when exposed to the internet.
_SENSITIVE_PORTS = {21, 22, 23, 445, 1433, 3306, 3389, 5432, 6379, 27017}
_WEB_PORTS = {80, 443}

_PORT_MULTIPLIER_SENSITIVE = 1.3
_PORT_MULTIPLIER_WEB = 1.0
_PORT_MULTIPLIER_OTHER = 1.15

_EXPOSURE_MULTIPLIER_WAF = 0.7
_EXPOSURE_MULTIPLIER_DIRECT = 1.0

_STALENESS_THRESHOLD_DAYS = 730  # >2 years
_STALENESS_BONUS = 10

_SEVERITY_THRESHOLDS = (
    (90, "critical"),
    (70, "high"),
    (40, "medium"),
)


def score_finding(service: Service, asset: Asset, matches: list[CVEMatch]) -> tuple[float, str, str]:
    """Returns (contextual_score, severity, explanation) for the most severe of `matches`."""
    primary = max(matches, key=lambda m: m.cvss_score or 0)

    base = (primary.cvss_score or 0) * 10

    port_multiplier, port_note = _port_factor(service.port)
    exposure_multiplier, exposure_note = _exposure_factor(asset)
    staleness_bonus, staleness_note = _staleness_factor(primary.published)

    contextual_score = min(100, round(base * port_multiplier * exposure_multiplier + staleness_bonus))
    severity = _severity_for(contextual_score)

    explanation = _explain(service, matches, primary, port_note, exposure_note, staleness_note)

    return contextual_score, severity, explanation


def _port_factor(port: int) -> tuple[float, str]:
    if port in _SENSITIVE_PORTS:
        return _PORT_MULTIPLIER_SENSITIVE, "administrative/database port"
    if port in _WEB_PORTS:
        return _PORT_MULTIPLIER_WEB, "standard web port"
    return _PORT_MULTIPLIER_OTHER, "non-standard port"


def _exposure_factor(asset: Asset) -> tuple[float, str]:
    if asset.is_behind_waf:
        return _EXPOSURE_MULTIPLIER_WAF, "mitigated by a detected WAF/CDN"
    return _EXPOSURE_MULTIPLIER_DIRECT, "directly exposed, no WAF detected"


def _staleness_factor(published: datetime | None) -> tuple[int, str | None]:
    if published is None:
        return 0, None

    age_days = (datetime.now(timezone.utc) - published).days
    if age_days > _STALENESS_THRESHOLD_DAYS:
        years = age_days // 365
        return (
            _STALENESS_BONUS,
            f"publicly known for over {years} years - increased for prolonged unpatched exposure",
        )
    return 0, None


def _severity_for(score: float) -> str:
    for threshold, label in _SEVERITY_THRESHOLDS:
        if score >= threshold:
            return label
    return "low"


def _explain(
    service: Service,
    matches: list[CVEMatch],
    primary: CVEMatch,
    port_note: str,
    exposure_note: str,
    staleness_note: str | None,
) -> str:
    cvss_part = (
        f"CVSS {primary.cvss_score}/{primary.cvss_severity.lower()}"
        if primary.cvss_score is not None
        else "no CVSS score available"
    )
    parts = [f"{primary.id} ({cvss_part}) on port {service.port}/{service.protocol} ({port_note})."]
    parts.append(f"{exposure_note.capitalize()}.")
    if staleness_note:
        parts.append(f"{staleness_note.capitalize()}.")
    if len(matches) > 1:
        parts.append(f"{len(matches)} known CVEs matched this service; showing the most severe.")
    return " ".join(parts)
