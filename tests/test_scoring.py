from datetime import datetime, timedelta, timezone

from m516.enrichment.nvd import CVEMatch
from m516.enrichment.scoring import score_finding
from m516.models import Asset, Service


def _match(cvss=5.0, severity="MEDIUM", published=None, cve_id="CVE-TEST-0001"):
    return CVEMatch(id=cve_id, cvss_score=cvss, cvss_severity=severity, published=published, description=None)


def test_sensitive_port_scores_higher_than_web_port():
    asset = Asset(is_behind_waf=False)
    sensitive = Service(port=22, protocol="tcp")
    web = Service(port=443, protocol="tcp")
    match = _match(cvss=5.0)

    score_sensitive, _, _ = score_finding(sensitive, asset, [match])
    score_web, _, _ = score_finding(web, asset, [match])

    assert score_sensitive == 65  # 50 base * 1.3
    assert score_web == 50  # 50 base * 1.0
    assert score_sensitive > score_web


def test_waf_reduces_score():
    service = Service(port=443, protocol="tcp")
    match = _match(cvss=8.0)

    score_open, severity_open, _ = score_finding(service, Asset(is_behind_waf=False), [match])
    score_waf, severity_waf, _ = score_finding(service, Asset(is_behind_waf=True), [match])

    assert score_open == 80
    assert score_waf == 56  # 80 * 0.7
    assert severity_open == "high"
    assert severity_waf == "medium"


def test_staleness_bonus_for_cve_older_than_two_years():
    service = Service(port=443, protocol="tcp")
    asset = Asset(is_behind_waf=False)
    old = _match(cvss=5.0, published=datetime.now(timezone.utc) - timedelta(days=800))
    recent = _match(cvss=5.0, published=datetime.now(timezone.utc) - timedelta(days=30))

    score_old, _, explanation_old = score_finding(service, asset, [old])
    score_recent, _, explanation_recent = score_finding(service, asset, [recent])

    assert score_old == 60  # 50 base + 10 staleness bonus
    assert score_recent == 50
    assert "Publicly known for over" in explanation_old
    assert "Publicly known for over" not in explanation_recent


def test_severity_buckets():
    service = Service(port=443, protocol="tcp")
    asset = Asset(is_behind_waf=False)

    _, critical, _ = score_finding(service, asset, [_match(cvss=9.0)])
    _, high, _ = score_finding(service, asset, [_match(cvss=7.0)])
    _, medium, _ = score_finding(service, asset, [_match(cvss=4.0)])
    _, low, _ = score_finding(service, asset, [_match(cvss=3.9)])

    assert (critical, high, medium, low) == ("critical", "high", "medium", "low")


def test_picks_most_severe_match_as_primary_and_notes_total_count():
    service = Service(port=443, protocol="tcp")
    asset = Asset(is_behind_waf=False)
    matches = [_match(cvss=3.0, cve_id="CVE-LOW"), _match(cvss=9.0, cve_id="CVE-HIGH")]

    score, severity, explanation = score_finding(service, asset, matches)

    assert "CVE-HIGH" in explanation
    assert "CVE-LOW" not in explanation
    assert "2 known CVEs" in explanation


def test_missing_cvss_score_treated_as_zero_but_still_explained():
    service = Service(port=443, protocol="tcp")
    asset = Asset(is_behind_waf=False)
    match = _match(cvss=None, severity=None)

    score, severity, explanation = score_finding(service, asset, [match])

    assert score == 0
    assert severity == "low"
    assert "no CVSS score available" in explanation
