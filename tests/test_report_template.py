from pathlib import Path

from m516.compliance.mapper import UNMAPPED, ComplianceMapping
from m516.compliance.pack_loader import load_pack
from m516.findings import Finding
from m516.models import Asset, DiscoveryResult, Service
from m516.report.template import build_report_data

STUB_PACK = Path(__file__).parent / "fixtures" / "packs" / "test-stub"


def _finding(severity="critical", compliance=None):
    return Finding(
        asset=Asset(ip="1.2.3.4", country="NG"),
        service=Service(port=2083, protocol="tcp", product="cpanel"),
        cve_ids=["CVE-TEST-0001"],
        cvss=9.0,
        contextual_score=100,
        severity=severity,
        explanation="An exposed hosting control panel was found directly reachable from the internet.",
        match_confidence="broad",
        compliance=compliance or [],
    )


def test_build_report_data_computes_severity_counts_and_summary():
    asset = Asset(ip="1.2.3.4", country="NG", services=[Service(port=2083, protocol="tcp")])
    result = DiscoveryResult(domain="example.com", assets=[asset])
    findings = [_finding(severity="critical")]

    report = build_report_data("example.com", result, findings)

    assert report.domain == "example.com"
    assert report.asset_count == 1
    assert report.service_count == 1
    assert report.finding_count == 1
    assert report.severity_counts["critical"] == 1
    assert "example.com" in report.executive_summary
    assert report.disclaimer  # non-empty, always present (NFR-SEC)


def test_build_report_data_with_no_findings_is_honest_not_falsely_clean():
    result = DiscoveryResult(domain="example.com", assets=[])

    report = build_report_data("example.com", result, [])

    assert report.finding_count == 0
    assert "No CVE-eligible findings" in report.executive_summary


def test_build_report_data_uses_pack_report_labels():
    pack = load_pack(STUB_PACK)
    result = DiscoveryResult(domain="example.com", assets=[])

    report = build_report_data("example.com", result, [], pack=pack)

    assert report.pack_display_name == pack.display_name
    assert report.report_title == pack.report_labels.get("report_title")
    assert report.primary_regulator == pack.report_labels.get("primary_regulator")


def test_build_report_data_groups_compliance_mappings_into_gaps_with_clause_titles():
    pack = load_pack(STUB_PACK)
    clause_ref = pack.frameworks[0].clauses[0].ref
    clause_title = pack.frameworks[0].clauses[0].title
    framework_id = pack.frameworks[0].id
    finding = _finding(
        compliance=[
            ComplianceMapping(framework=framework_id, clause=clause_ref, status="non-compliant", remediation="Fix it")
        ]
    )
    result = DiscoveryResult(domain="example.com", assets=[])

    report = build_report_data("example.com", result, [finding], pack=pack)

    assert len(report.compliance_gaps) == 1
    gap = report.compliance_gaps[0]
    assert gap.clause == clause_ref
    assert gap.clause_title == clause_title
    assert gap.status == "non-compliant"
    assert gap.remediation == "Fix it"
    assert len(gap.finding_refs) == 1


def test_build_report_data_unmapped_compliance_is_not_fabricated_as_compliant():
    finding = _finding(compliance=[ComplianceMapping(framework="ACME-STD", clause="ACME-STD 1.1", status=UNMAPPED, remediation=None)])
    result = DiscoveryResult(domain="example.com", assets=[])

    report = build_report_data("example.com", result, [finding])

    assert report.compliance_gaps[0].status == UNMAPPED
    assert "no LLM classifier is currently configured" in report.executive_summary


def test_remediation_roadmap_prefers_llm_remediation_but_falls_back_to_explanation():
    mapped = _finding(
        severity="high",
        compliance=[ComplianceMapping(framework="ACME-STD", clause="ACME-STD 1.1", status="non-compliant", remediation="Do X")],
    )
    unmapped = _finding(severity="low", compliance=[])
    result = DiscoveryResult(domain="example.com", assets=[])

    report = build_report_data("example.com", result, [mapped, unmapped])

    assert "Do X" in report.remediation_roadmap[0]
    assert unmapped.explanation in report.remediation_roadmap[1]
