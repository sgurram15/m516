from pathlib import Path

from pypdf import PdfReader

from m516.compliance.mapper import ComplianceMapping
from m516.findings import Finding
from m516.models import Asset, DiscoveryResult, Service
from m516.report.render import render_pdf
from m516.report.template import build_report_data


def _finding():
    return Finding(
        asset=Asset(ip="1.2.3.4", country="NG"),
        service=Service(port=2083, protocol="tcp", product="cpanel"),
        cve_ids=["CVE-TEST-0001"],
        cvss=9.0,
        contextual_score=100,
        severity="critical",
        explanation="An exposed hosting control panel was found directly reachable from the internet.",
        match_confidence="broad",
        compliance=[ComplianceMapping(framework="ACME-STD", clause="ACME-STD 1.1", status="non-compliant", remediation="Restrict access")],
    )


def test_render_pdf_produces_a_readable_pdf_file(tmp_path):
    asset = Asset(ip="1.2.3.4", country="NG", services=[Service(port=2083, protocol="tcp")])
    result = DiscoveryResult(domain="example.com", assets=[asset])
    report = build_report_data("example.com", result, [_finding()])

    output_path = render_pdf(report, tmp_path / "report.pdf")

    assert output_path.exists()
    reader = PdfReader(str(output_path))
    assert len(reader.pages) >= 2
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "example.com" in text
    assert "CVE-TEST-0001" in text
    assert "ACME-STD" in text


def test_render_pdf_with_no_findings_does_not_crash(tmp_path):
    result = DiscoveryResult(domain="example.com", assets=[])
    report = build_report_data("example.com", result, [])

    output_path = render_pdf(report, tmp_path / "empty.pdf")

    assert output_path.exists()
