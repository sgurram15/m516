from datetime import datetime, timedelta, timezone

from m516.models import Asset, DiscoveryResult, Service


def test_service_version_string_requires_both_product_and_version():
    assert Service(port=25, protocol="tcp", product="MailEnable", version="10.57").version_string == (
        "MailEnable 10.57"
    )
    assert Service(port=25, protocol="tcp", product="MailEnable").version_string is None


def test_service_is_cve_eligible_via_version_string_or_cpe():
    assert Service(port=25, protocol="tcp", product="X", version="1").is_cve_eligible
    assert Service(port=25, protocol="tcp", cpe="cpe:/a:x:x").is_cve_eligible
    assert not Service(port=25, protocol="tcp").is_cve_eligible


def test_asset_is_locally_hosted_compares_against_given_home_country():
    asset = Asset(country="NG", is_behind_waf=False)
    assert asset.is_locally_hosted("NG")
    assert not asset.is_locally_hosted("US")


def test_asset_is_locally_hosted_false_when_behind_waf():
    asset = Asset(country="NG", is_behind_waf=True)
    assert not asset.is_locally_hosted("NG")


def test_cert_is_expired():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    future = datetime.now(timezone.utc) + timedelta(days=365)
    assert Asset(cert_valid_until=past).cert_is_expired is True
    assert Asset(cert_valid_until=future).cert_is_expired is False
    assert Asset(cert_valid_until=None).cert_is_expired is None


def test_merge_asset_unions_services_and_sources_by_ip():
    result = DiscoveryResult(domain="example.com")
    result.merge_asset(
        Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp")], sources={"netlas"})
    )
    result.merge_asset(
        Asset(ip="1.2.3.4", services=[Service(port=22, protocol="tcp")], sources={"internetdb"})
    )

    assert len(result.assets) == 1
    merged = result.assets[0]
    assert merged.sources == {"netlas", "internetdb"}
    assert {(s.port, s.protocol) for s in merged.services} == {(443, "tcp"), (22, "tcp")}


def test_merge_asset_does_not_duplicate_same_service():
    result = DiscoveryResult(domain="example.com")
    result.merge_asset(Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp")]))
    result.merge_asset(Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp")]))

    assert len(result.assets[0].services) == 1


def test_merge_asset_without_ip_is_appended_not_merged():
    result = DiscoveryResult(domain="example.com")
    result.merge_asset(Asset(ip=None))
    result.merge_asset(Asset(ip=None))

    assert len(result.assets) == 2


def test_merge_asset_fills_missing_fields_without_overwriting_existing():
    result = DiscoveryResult(domain="example.com")
    result.merge_asset(Asset(ip="1.2.3.4", country="NG"))
    result.merge_asset(Asset(ip="1.2.3.4", country="US", as_name="Some ISP"))

    merged = result.assets[0]
    assert merged.country == "NG"
    assert merged.as_name == "Some ISP"
