"""The orchestrator (docs/02_ARCHITECTURE.md §3, docs/07_BACKEND_ARCHITECTURE.md §2): domain -> a
finished scan. Wires Modules 1-4 in sequence — discovery -> enrichment -> compliance -> report. Each
module already isolates its own failures (NFR-REL); this module adds no new error handling beyond
letting a pack-load failure (a genuine "can't proceed" error, unlike a single provider timing out)
propagate to the caller.

Engine stays generic (golden rule): `pack_dir` is a parameter, never a hard-coded pack id. Any
"nigeria-banking" default lives in deployment config (`m516/config.py`'s `default_pack_id`), not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from m516.compliance.ingest import ingest_pack
from m516.compliance.mapper import map_finding
from m516.compliance.pack_loader import CompliancePack, load_pack
from m516.discovery import run_discovery
from m516.findings import Finding, build_findings
from m516.logging import get_logger
from m516.models import DiscoveryResult
from m516.report.render import render_pdf
from m516.report.template import ReportData, build_report_data

logger = get_logger(__name__)

STAGE_DISCOVERY = "discovery"
STAGE_ENRICHMENT = "enrichment"
STAGE_COMPLIANCE = "compliance"
STAGE_REPORT = "report"
STAGE_DONE = "done"


@dataclass
class PipelineResult:
    discovery_result: DiscoveryResult
    findings: list[Finding]
    report_data: ReportData
    pdf_path: Path
    discovery_errors: list[str]
    enrichment_errors: list[str]
    pack: CompliancePack


def run_scan(
    domain: str,
    pack_dir: Path,
    output_dir: Path,
    scan_id: str,
    on_stage: Callable[[str], None] | None = None,
    chroma_path: str | None = None,
) -> PipelineResult:
    """Run one full scan. `scan_id` names the output PDF (`output_dir / f"{scan_id}.pdf"`) — the
    caller (typically `m516/api/`) owns id generation, this function stays storage-agnostic.

    `chroma_path` defaults to `ingest_pack`'s own default (`.chroma`) when omitted — exposed here only
    so tests can isolate into a tmp dir, same reasoning as `ingest_pack`/`mapper` already taking one."""

    def announce(stage: str) -> None:
        logger.info("scan %s: entering stage %s", scan_id, stage)
        if on_stage is not None:
            on_stage(stage)

    announce(STAGE_DISCOVERY)
    discovery_result = run_discovery(domain)

    announce(STAGE_ENRICHMENT)
    findings, enrichment_errors = build_findings(discovery_result)

    announce(STAGE_COMPLIANCE)
    pack = load_pack(pack_dir)
    collection = ingest_pack(pack) if chroma_path is None else ingest_pack(pack, chroma_path=chroma_path)
    for finding in findings:
        finding.compliance = map_finding(finding, pack, collection, llm_client=None)

    announce(STAGE_REPORT)
    report_data = build_report_data(domain, discovery_result, findings, pack=pack)
    output_dir = Path(output_dir)
    pdf_path = render_pdf(report_data, output_dir / f"{scan_id}.pdf")

    announce(STAGE_DONE)
    return PipelineResult(
        discovery_result=discovery_result,
        findings=findings,
        report_data=report_data,
        pdf_path=pdf_path,
        discovery_errors=list(discovery_result.errors),
        enrichment_errors=enrichment_errors,
        pack=pack,
    )
