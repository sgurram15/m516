from pathlib import Path

import m516.findings as findings_module
import m516.pipeline as pipeline_module
from m516.enrichment.nvd import CVEMatch
from m516.models import Asset, DiscoveryResult, Service
from m516.pipeline import (
    STAGE_COMPLIANCE,
    STAGE_DISCOVERY,
    STAGE_DONE,
    STAGE_ENRICHMENT,
    STAGE_REPORT,
    run_scan,
)

STUB_PACK = Path(__file__).parent / "fixtures" / "packs" / "test-stub"
_CPE = "cpe:2.3:a:x:x:1.0:*:*:*:*:*:*:*"


def _fake_discovery(domain):
    asset = Asset(
        ip="1.2.3.4",
        hostname=domain,
        country="ZZ",
        services=[Service(port=2083, protocol="tcp", product="cpanel", cpe=_CPE)],
    )
    return DiscoveryResult(domain=domain, assets=[asset])


def _fake_lookup(service, api_key, ttl):
    return [
        CVEMatch(
            id="CVE-TEST-0001",
            cvss_score=9.0,
            cvss_severity="CRITICAL",
            published=None,
            description=None,
            match_confidence="broad",
            exploitability_score=None,
            impact_score=None,
        )
    ]


def test_run_scan_runs_all_stages_in_order_against_the_stub_pack(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline_module, "run_discovery", _fake_discovery)
    monkeypatch.setattr(findings_module, "lookup_cves", _fake_lookup)

    stages: list[str] = []
    result = run_scan(
        "example.com", STUB_PACK, tmp_path, "scan-1", on_stage=stages.append, chroma_path=str(tmp_path / "chroma")
    )

    assert stages == [STAGE_DISCOVERY, STAGE_ENRICHMENT, STAGE_COMPLIANCE, STAGE_REPORT, STAGE_DONE]
    assert result.pdf_path.exists()
    assert result.pack.id == "test-stub"
    assert len(result.findings) == 1
    assert result.discovery_errors == []
    assert result.enrichment_errors == []


def test_run_scan_populates_honest_unmapped_compliance_status(monkeypatch, tmp_path):
    """No llm_client is wired (WP3 is deliberately gated on that decision) — the pipeline must not
    fabricate a compliant/non-compliant verdict."""
    monkeypatch.setattr(pipeline_module, "run_discovery", _fake_discovery)
    monkeypatch.setattr(findings_module, "lookup_cves", _fake_lookup)

    result = run_scan("example.com", STUB_PACK, tmp_path, "scan-2", chroma_path=str(tmp_path / "chroma"))

    assert result.findings[0].compliance
    assert all(m.status == "unmapped" for m in result.findings[0].compliance)
    assert result.report_data.finding_count == 1
    assert result.report_data.compliance_gaps


def test_run_scan_names_the_pdf_after_scan_id(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline_module, "run_discovery", _fake_discovery)
    monkeypatch.setattr(findings_module, "lookup_cves", _fake_lookup)

    result = run_scan("example.com", STUB_PACK, tmp_path, "my-scan-id", chroma_path=str(tmp_path / "chroma"))

    assert result.pdf_path == tmp_path / "my-scan-id.pdf"


def test_run_scan_works_with_no_on_stage_callback(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline_module, "run_discovery", _fake_discovery)
    monkeypatch.setattr(findings_module, "lookup_cves", _fake_lookup)

    result = run_scan(
        "example.com", STUB_PACK, tmp_path, "scan-3", on_stage=None, chroma_path=str(tmp_path / "chroma")
    )

    assert result.pdf_path.exists()
