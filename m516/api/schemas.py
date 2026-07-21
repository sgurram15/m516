"""Pydantic response models (docs/05_API_DESIGN.md). Every model here is a thin, explicit projection
of an existing engine dataclass — never a re-aggregation. Dashboard/assets/findings/compliance all
read from the one `ReportData` a scan already built (`m516/report/template.py`); nothing here
recomputes counts or groupings.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from m516.api.state import ScanState
from m516.compliance.mapper import ComplianceMapping
from m516.compliance.pack_loader import CompliancePack
from m516.findings import Finding
from m516.models import Asset, Service
from m516.report.template import AssetSummary, ComplianceGap, ReportData


class ScanCreateRequest(BaseModel):
    domain: str
    pack_id: str | None = None


class ScanStatusOut(BaseModel):
    scan_id: str
    domain: str
    pack_id: str
    status: str
    stage: str | None
    error: str | None
    started_at: datetime
    finished_at: datetime | None

    @classmethod
    def from_state(cls, state: ScanState) -> "ScanStatusOut":
        return cls(
            scan_id=state.scan_id,
            domain=state.domain,
            pack_id=state.pack_id,
            status=state.status,
            stage=state.stage,
            error=state.error,
            started_at=state.started_at,
            finished_at=state.finished_at,
        )


class ScanSummaryOut(BaseModel):
    domain: str
    generated_at: datetime
    report_title: str
    primary_regulator: str | None
    pack_display_name: str | None
    executive_summary: str
    severity_counts: dict[str, int]
    asset_count: int
    service_count: int
    finding_count: int

    @classmethod
    def from_report_data(cls, report: ReportData) -> "ScanSummaryOut":
        return cls(
            domain=report.domain,
            generated_at=report.generated_at,
            report_title=report.report_title,
            primary_regulator=report.primary_regulator,
            pack_display_name=report.pack_display_name,
            executive_summary=report.executive_summary,
            severity_counts=report.severity_counts,
            asset_count=report.asset_count,
            service_count=report.service_count,
            finding_count=report.finding_count,
        )


class AssetSummaryOut(BaseModel):
    ip: str | None
    hostname: str | None
    domain: str | None
    country: str | None
    is_behind_waf: bool
    service_count: int
    cert_detection_level: str | None
    sources: list[str]

    @classmethod
    def from_asset_summary(cls, asset: AssetSummary) -> "AssetSummaryOut":
        return cls(**asset.__dict__)


class ServiceOut(BaseModel):
    port: int
    protocol: str
    name: str | None
    product: str | None
    version: str | None
    cpe: str | None

    @classmethod
    def from_service(cls, service: Service) -> "ServiceOut":
        return cls(
            port=service.port,
            protocol=service.protocol,
            name=service.name,
            product=service.product,
            version=service.version,
            cpe=service.cpe,
        )


class AssetRefOut(BaseModel):
    ip: str | None
    hostname: str | None
    domain: str | None
    country: str | None
    is_behind_waf: bool

    @classmethod
    def from_asset(cls, asset: Asset) -> "AssetRefOut":
        return cls(
            ip=asset.ip,
            hostname=asset.hostname,
            domain=asset.domain,
            country=asset.country,
            is_behind_waf=asset.is_behind_waf,
        )


class ComplianceMappingOut(BaseModel):
    framework: str
    clause: str
    status: str
    remediation: str | None

    @classmethod
    def from_mapping(cls, mapping: ComplianceMapping) -> "ComplianceMappingOut":
        return cls(
            framework=mapping.framework,
            clause=mapping.clause,
            status=mapping.status,
            remediation=mapping.remediation,
        )


class FindingOut(BaseModel):
    asset: AssetRefOut
    service: ServiceOut
    cve_ids: list[str]
    cvss: float
    contextual_score: float
    severity: str
    explanation: str
    match_confidence: str
    exploitability_score: float | None
    impact_score: float | None
    compliance: list[ComplianceMappingOut]

    @classmethod
    def from_finding(cls, finding: Finding) -> "FindingOut":
        return cls(
            asset=AssetRefOut.from_asset(finding.asset),
            service=ServiceOut.from_service(finding.service),
            cve_ids=finding.cve_ids,
            cvss=finding.cvss,
            contextual_score=finding.contextual_score,
            severity=finding.severity,
            explanation=finding.explanation,
            match_confidence=finding.match_confidence,
            exploitability_score=finding.exploitability_score,
            impact_score=finding.impact_score,
            compliance=[ComplianceMappingOut.from_mapping(m) for m in finding.compliance],
        )


class ComplianceGapOut(BaseModel):
    framework: str
    clause: str
    clause_title: str
    status: str
    remediation: str | None
    finding_refs: list[str]

    @classmethod
    def from_gap(cls, gap: ComplianceGap) -> "ComplianceGapOut":
        return cls(**gap.__dict__)


class PackOut(BaseModel):
    id: str
    display_name: str
    sector: str
    home_country: str

    @classmethod
    def from_pack(cls, pack: CompliancePack) -> "PackOut":
        return cls(
            id=pack.id,
            display_name=pack.display_name,
            sector=pack.sector,
            home_country=pack.home_country,
        )
