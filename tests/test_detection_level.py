from datetime import datetime, timedelta, timezone

from m516.enrichment.detection_level import cert_detection_level, finding_detection_level
from m516.findings import Finding
from m516.models import Asset, Service

_ASSET = Asset(ip="1.2.3.4")
_SERVICE = Service(port=443, protocol="tcp")


def _finding(severity, match_confidence):
    return Finding(
        asset=_ASSET,
        service=_SERVICE,
        cve_ids=["CVE-TEST-0001"],
        cvss=9.0,
        contextual_score=90,
        severity=severity,
        explanation="",
        match_confidence=match_confidence,
    )


def test_critical_or_high_with_exact_confidence_is_red():
    assert finding_detection_level(_finding("critical", "exact")) == "red"
    assert finding_detection_level(_finding("high", "exact")) == "red"


def test_critical_or_high_with_broad_confidence_is_yellow():
    assert finding_detection_level(_finding("critical", "broad")) == "yellow"
    assert finding_detection_level(_finding("high", "broad")) == "yellow"


def test_medium_is_always_yellow_regardless_of_confidence():
    assert finding_detection_level(_finding("medium", "exact")) == "yellow"
    assert finding_detection_level(_finding("medium", "broad")) == "yellow"


def test_low_is_always_green():
    assert finding_detection_level(_finding("low", "exact")) == "green"
    assert finding_detection_level(_finding("low", "broad")) == "green"


def test_cert_detection_level_red_when_expired():
    asset = Asset(cert_valid_until=datetime.now(timezone.utc) - timedelta(days=1))
    assert cert_detection_level(asset) == "red"


def test_cert_detection_level_yellow_when_expiring_soon():
    asset = Asset(cert_valid_until=datetime.now(timezone.utc) + timedelta(days=10))
    assert cert_detection_level(asset) == "yellow"


def test_cert_detection_level_green_when_valid_and_not_expiring_soon():
    asset = Asset(cert_valid_until=datetime.now(timezone.utc) + timedelta(days=365))
    assert cert_detection_level(asset) == "green"


def test_cert_detection_level_none_when_no_cert_data():
    assert cert_detection_level(Asset(cert_valid_until=None)) is None
