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


def test_merge_asset_unions_service_sources_on_same_port():
    """Two providers reporting the same open port is provenance to keep (which API captured it),
    not a duplicate to discard."""
    result = DiscoveryResult(domain="example.com")
    result.merge_asset(
        Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp", sources={"netlas"})])
    )
    result.merge_asset(
        Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp", sources={"censys"})])
    )

    assert len(result.assets[0].services) == 1
    assert result.assets[0].services[0].sources == {"netlas", "censys"}


def test_merge_asset_backfills_missing_service_fields_on_same_port():
    result = DiscoveryResult(domain="example.com")
    result.merge_asset(
        Asset(ip="1.2.3.4", services=[Service(port=80, protocol="tcp", product="nginx")])
    )
    result.merge_asset(
        Asset(
            ip="1.2.3.4",
            services=[Service(port=80, protocol="tcp", product="Nginx", cpe="cpe:2.3:a:f5:nginx:*")],
        )
    )

    merged_service = result.assets[0].services[0]
    assert merged_service.product == "nginx"  # existing value wins, never overwritten
    assert merged_service.cpe == "cpe:2.3:a:f5:nginx:*"  # missing field backfilled


def test_merge_asset_does_not_graft_cpe_from_a_disagreeing_product():
    """BR-5: if two providers disagree on what product is running on a port, never combine one
    provider's product label with another provider's cpe/version/banner — that would misattribute
    one product's CVEs to a different, unrelated one."""
    result = DiscoveryResult(domain="example.com")
    result.merge_asset(
        Asset(ip="1.2.3.4", services=[Service(port=80, protocol="tcp", product="Fathom")])
    )
    result.merge_asset(
        Asset(
            ip="1.2.3.4",
            services=[
                Service(
                    port=80,
                    protocol="tcp",
                    product="Caddy",
                    cpe="cpe:2.3:a:caddyserver:caddy:*:*:*:*:*:*:*:*",
                )
            ],
        )
    )

    merged_service = result.assets[0].services[0]
    assert merged_service.product == "Fathom"
    assert merged_service.cpe is None  # not grafted from the disagreeing "Caddy" report


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
