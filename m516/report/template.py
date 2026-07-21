"""Module 4 content model (docs/03_DOMAIN_MODEL.md, docs/22_BUILD_PLAN.md WP4): assembles a
`ReportData` from real pipeline output — never from an LLM narrative, since none is wired yet
(docs/15_PROGRESS.md — same honest-partial stance as `m516/compliance/mapper.py`). All prose here is
templated from computed facts (BR-5: no fabrication); nothing is invented about a target that the
pipeline didn't itself find.

`pack` is optional and, when given, only ever read through `CompliancePack`'s generic fields
(`display_name`, `report_labels`, `frameworks[].clauses[]`) — never a hard-coded framework/country name
(golden rule).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from m516.compliance.mapper import UNMAPPED, ComplianceMapping
from m516.compliance.pack_loader import CompliancePack
from m516.enrichment.detection_level import cert_detection_level
from m516.findings import Finding
from m516.models import DiscoveryResult

_DISCLAIMER = (
    "This report was produced by an automated, strictly passive attack-surface and compliance-"
    "intelligence tool. No active scan traffic was ever sent to the target's infrastructure; all "
    "findings derive from third-party passive data sources and deterministic, rules-based scoring. "
    "Findings may be incomplete or contain false positives and must be validated by a qualified "
    "security analyst before being relied upon. Compliance clause references are retrieved "
    "automatically and do not constitute legal advice; they must be validated by a qualified "
    "compliance professional before any client relies on this report."
)

_DEFAULT_REPORT_TITLE = "External Attack Surface & Compliance Exposure Report"


@dataclass
class AssetSummary:
    ip: str | None
    hostname: str | None
    domain: str | None
    country: str | None
    is_behind_waf: bool
    service_count: int
    cert_detection_level: str | None
    sources: list[str]


@dataclass
class ComplianceGap:
    framework: str
    clause: str
    clause_title: str
    status: str
    remediation: str | None
    finding_refs: list[str] = field(default_factory=list)


@dataclass
class ReportData:
    domain: str
    generated_at: datetime
    report_title: str
    primary_regulator: str | None
    pack_display_name: str | None
    disclaimer: str
    executive_summary: str
    severity_counts: dict[str, int]
    asset_count: int
    service_count: int
    finding_count: int
    assets: list[AssetSummary]
    findings: list[Finding]
    compliance_gaps: list[ComplianceGap]
    remediation_roadmap: list[str]


def build_report_data(
    domain: str,
    discovery_result: DiscoveryResult,
    findings: list[Finding],
    pack: CompliancePack | None = None,
) -> ReportData:
    assets = [_asset_summary(a) for a in discovery_result.assets]
    service_count = sum(a.service_count for a in assets)
    severity_counts = _severity_counts(findings)
    compliance_gaps = _compliance_gaps(findings, pack)

    report_labels = pack.report_labels if pack else {}

    return ReportData(
        domain=domain,
        generated_at=datetime.now(timezone.utc),
        report_title=report_labels.get("report_title", _DEFAULT_REPORT_TITLE),
        primary_regulator=report_labels.get("primary_regulator"),
        pack_display_name=pack.display_name if pack else None,
        disclaimer=_DISCLAIMER,
        executive_summary=_executive_summary(domain, assets, service_count, findings, severity_counts, compliance_gaps),
        severity_counts=severity_counts,
        asset_count=len(assets),
        service_count=service_count,
        finding_count=len(findings),
        assets=assets,
        findings=findings,
        compliance_gaps=compliance_gaps,
        remediation_roadmap=_remediation_roadmap(findings),
    )


def _asset_summary(asset) -> AssetSummary:
    return AssetSummary(
        ip=asset.ip,
        hostname=asset.hostname,
        domain=asset.domain,
        country=asset.country,
        is_behind_waf=asset.is_behind_waf,
        service_count=len(asset.services),
        cert_detection_level=cert_detection_level(asset),
        sources=sorted(asset.sources),
    )


def _severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def _finding_ref(finding: Finding) -> str:
    label = finding.service.product or finding.service.name or "unidentified service"
    return f"{label} on port {finding.service.port}/{finding.service.protocol} ({finding.severity})"


def _clause_title(pack: CompliancePack | None, framework_id: str, ref: str) -> str:
    if pack is None:
        return ref
    for framework in pack.frameworks:
        if framework.id != framework_id:
            continue
        for clause in framework.clauses:
            if clause.ref == ref:
                return clause.title
    return ref


def _compliance_gaps(findings: list[Finding], pack: CompliancePack | None) -> list[ComplianceGap]:
    gaps: dict[tuple[str, str], ComplianceGap] = {}
    for finding in findings:
        mapping: ComplianceMapping
        for mapping in finding.compliance:
            key = (mapping.framework, mapping.clause)
            gap = gaps.get(key)
            if gap is None:
                gap = ComplianceGap(
                    framework=mapping.framework,
                    clause=mapping.clause,
                    clause_title=_clause_title(pack, mapping.framework, mapping.clause),
                    status=mapping.status,
                    remediation=mapping.remediation,
                )
                gaps[key] = gap
            gap.finding_refs.append(_finding_ref(finding))
            if gap.status == UNMAPPED and mapping.status != UNMAPPED:
                gap.status = mapping.status
                gap.remediation = mapping.remediation
    return list(gaps.values())


def _remediation_roadmap(findings: list[Finding]) -> list[str]:
    roadmap = []
    for finding in findings:
        remediation = next(
            (m.remediation for m in finding.compliance if m.remediation),
            None,
        )
        if remediation:
            roadmap.append(f"[{finding.severity.upper()}] {_finding_ref(finding)}: {remediation}")
        else:
            roadmap.append(f"[{finding.severity.upper()}] {_finding_ref(finding)}: {finding.explanation}")
    return roadmap


def _executive_summary(
    domain: str,
    assets: list[AssetSummary],
    service_count: int,
    findings: list[Finding],
    severity_counts: dict[str, int],
    compliance_gaps: list[ComplianceGap],
) -> str:
    parts = [
        f"Passive analysis of {domain} identified {len(assets)} internet-facing asset(s) exposing "
        f"{service_count} discovered service(s)."
    ]

    if findings:
        parts.append(
            f"{len(findings)} finding(s) were matched to known CVEs and risk-scored: "
            f"{severity_counts.get('critical', 0)} critical, {severity_counts.get('high', 0)} high, "
            f"{severity_counts.get('medium', 0)} medium, {severity_counts.get('low', 0)} low."
        )
        top = findings[0]
        parts.append(f"The highest-ranked finding is on {_finding_ref(top)}: {top.explanation}")
    else:
        parts.append("No CVE-eligible findings were produced from the discovered services.")

    if compliance_gaps:
        unresolved = [g for g in compliance_gaps if g.status == UNMAPPED]
        if len(unresolved) == len(compliance_gaps):
            parts.append(
                f"{len(compliance_gaps)} candidate regulatory clause(s) were retrieved against these "
                "findings, but no LLM classifier is currently configured — clause references below are "
                "shown for analyst review, not as a compliant/non-compliant determination."
            )
        else:
            parts.append(
                f"{len(compliance_gaps)} candidate regulatory clause(s) were evaluated, of which "
                f"{len(compliance_gaps) - len(unresolved)} received a compliance classification "
                "requiring analyst review before client reliance."
            )

    return " ".join(parts)
