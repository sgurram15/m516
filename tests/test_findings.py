import m516.findings as findings_module
from m516.enrichment.nvd import CVEMatch
from m516.findings import build_findings
from m516.models import Asset, DiscoveryResult, Service

_CPE = "cpe:2.3:a:x:x:1.0:*:*:*:*:*:*:*"


def _match(cvss, cve_id="CVE-X", match_confidence="broad"):
    return CVEMatch(
        id=cve_id,
        cvss_score=cvss,
        cvss_severity="HIGH",
        published=None,
        description=None,
        match_confidence=match_confidence,
    )


def test_build_findings_skips_non_cve_eligible_services(monkeypatch):
    def fail(*_a, **_k):
        raise AssertionError("lookup_cves should not be called for a non-eligible service")

    monkeypatch.setattr(findings_module, "lookup_cves", fail)
    asset = Asset(ip="1.2.3.4", services=[Service(port=80, protocol="tcp")])
    result = DiscoveryResult(domain="example.com", assets=[asset])

    findings, errors = build_findings(result)

    assert findings == []
    assert errors == []


def test_build_findings_creates_finding_for_eligible_service_with_matches(monkeypatch):
    monkeypatch.setattr(findings_module, "lookup_cves", lambda service, api_key, ttl: [_match(9.0)])
    asset = Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp", cpe=_CPE)])
    result = DiscoveryResult(domain="example.com", assets=[asset])

    findings, errors = build_findings(result)

    assert len(findings) == 1
    assert findings[0].cve_ids == ["CVE-X"]
    assert findings[0].cvss == 9.0
    assert findings[0].match_confidence == "broad"
    assert errors == []


def test_build_findings_propagates_exact_match_confidence(monkeypatch):
    monkeypatch.setattr(
        findings_module, "lookup_cves", lambda service, api_key, ttl: [_match(9.0, match_confidence="exact")]
    )
    asset = Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp", cpe=_CPE)])
    result = DiscoveryResult(domain="example.com", assets=[asset])

    findings, _ = build_findings(result)

    assert findings[0].match_confidence == "exact"


def test_build_findings_ranks_by_contextual_score_descending(monkeypatch):
    def fake_lookup(service, api_key, ttl):
        cvss = 9.0 if service.port == 22 else 2.0
        return [_match(cvss, cve_id=f"CVE-{service.port}")]

    monkeypatch.setattr(findings_module, "lookup_cves", fake_lookup)
    asset = Asset(
        ip="1.2.3.4",
        services=[
            Service(port=443, protocol="tcp", cpe=_CPE),
            Service(port=22, protocol="tcp", cpe=_CPE),
        ],
    )
    result = DiscoveryResult(domain="example.com", assets=[asset])

    findings, _ = build_findings(result)

    assert [f.cve_ids[0] for f in findings] == ["CVE-22", "CVE-443"]
    assert findings[0].contextual_score >= findings[1].contextual_score


def test_build_findings_records_error_and_continues_when_lookup_fails(monkeypatch):
    def fake_lookup(service, api_key, ttl):
        if service.port == 22:
            raise RuntimeError("boom")
        return [_match(9.0)]

    monkeypatch.setattr(findings_module, "lookup_cves", fake_lookup)
    asset = Asset(
        ip="1.2.3.4",
        services=[
            Service(port=22, protocol="tcp", cpe=_CPE),
            Service(port=443, protocol="tcp", cpe=_CPE),
        ],
    )
    result = DiscoveryResult(domain="example.com", assets=[asset])

    findings, errors = build_findings(result)

    assert len(findings) == 1
    assert len(errors) == 1
    assert "22" in errors[0]


def test_build_findings_no_matches_produces_no_finding(monkeypatch):
    monkeypatch.setattr(findings_module, "lookup_cves", lambda *a, **k: [])
    asset = Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp", cpe=_CPE)])
    result = DiscoveryResult(domain="example.com", assets=[asset])

    findings, errors = build_findings(result)

    assert findings == []
    assert errors == []
