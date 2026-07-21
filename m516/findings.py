"""Module 2 orchestrator + domain object (docs/03_DOMAIN_MODEL.md Finding, docs/22_BUILD_PLAN.md WP2):
services -> CVEs (NVD) -> deterministic contextual score -> ranked Finding[].

`Finding.compliance` is populated by Module 3 (WP3) — empty here, engine stays generic (golden rule).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from m516.config import load_config
from m516.enrichment.nvd import lookup_cves
from m516.enrichment.scoring import score_finding
from m516.logging import get_logger
from m516.models import Asset, DiscoveryResult, Service

logger = get_logger(__name__)


@dataclass
class Finding:
    asset: Asset
    service: Service
    cve_ids: list[str]
    cvss: float
    contextual_score: float
    severity: str
    explanation: str
    match_confidence: str
    exploitability_score: float | None = None
    impact_score: float | None = None
    compliance: list = field(default_factory=list)
    tenant_id: str | None = None


def build_findings(discovery_result: DiscoveryResult) -> tuple[list[Finding], list[str]]:
    """Ranked by contextual_score descending (FR-2.5). One service's NVD lookup failing doesn't abort
    the rest (NFR-REL's spirit applies pipeline-wide, not just Module 1)."""
    config = load_config()
    findings: list[Finding] = []
    errors: list[str] = []

    for asset in discovery_result.assets:
        for service in asset.services:
            if not service.is_cve_eligible:
                continue

            try:
                matches = lookup_cves(service, config.nvd_api_key, config.cache_ttl_seconds)
            except Exception as exc:  # noqa: BLE001 — one lookup must never abort the rest
                logger.warning("NVD lookup failed for %s:%s: %s", asset.ip, service.port, exc)
                errors.append(f"nvd: {asset.ip}:{service.port}: {exc}")
                continue

            if not matches:
                continue

            contextual_score, severity, explanation = score_finding(service, asset, matches)
            # Recomputed rather than threaded through score_finding()'s return — same primary-match
            # selection scoring.py already does internally; avoids widening its return contract for
            # display-only fields (matches the existing `cvss=max(...)` pattern below).
            primary = max(matches, key=lambda m: m.cvss_score or 0)
            findings.append(
                Finding(
                    asset=asset,
                    service=service,
                    cve_ids=[m.id for m in matches],
                    cvss=max((m.cvss_score or 0) for m in matches),
                    contextual_score=contextual_score,
                    severity=severity,
                    explanation=explanation,
                    match_confidence=primary.match_confidence,
                    exploitability_score=primary.exploitability_score,
                    impact_score=primary.impact_score,
                )
            )

    findings.sort(key=lambda f: f.contextual_score, reverse=True)
    return findings, errors
