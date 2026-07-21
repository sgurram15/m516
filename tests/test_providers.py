import json
from pathlib import Path

from m516.config import Config
from m516.models import Asset
from m516.providers import censys, criminalip, internetdb, netlas
from m516.providers.base import detect_waf
from m516.providers.registry import get_enabled_providers

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    with (FIXTURES / name).open() as fh:
        return json.load(fh)


def test_netlas_from_records_parses_services_whois_and_certificate():
    assets = netlas.from_records(_load("netlas_host.json"), domain="example-ng.gov.ng")

    assert len(assets) == 1
    asset = assets[0]
    assert asset.ip == "197.211.60.10"
    assert asset.isp == "MainOne Cable Company"
    assert asset.country == "NG"
    assert asset.as_name == "MAINONE-AS"
    assert asset.cert_subject == "CN=example-ng.gov.ng"
    assert asset.cert_is_expired is True
    assert asset.sources == {"netlas"}

    smtp = next(s for s in asset.services if s.port == 25)
    assert smtp.product == "MailEnable"
    assert smtp.version == "10.57"
    assert smtp.version_string == "MailEnable 10.57"
    assert "MailEnable" in smtp.banner


def test_netlas_from_records_handles_empty_response():
    assert netlas.from_records({}, domain="example.com") == []


def test_criminalip_from_records_parses_reports():
    assets = criminalip.from_records(
        _load("criminalip_domain_reports.json"), domain="example-ng.gov.ng", ip="197.211.60.10"
    )

    assert len(assets) == 1
    asset = assets[0]
    assert asset.ip == "197.211.60.10"
    assert asset.country == "NG"
    assert asset.sources == {"criminalip"}
    product_names = {s.product for s in asset.services}
    assert product_names == {"WordPress", "PHP", "Nginx"}
    assert all(s.port == 80 for s in asset.services)


def test_criminalip_from_records_handles_empty_response():
    assert criminalip.from_records({}, domain="example.com", ip="197.211.60.10") == []


def test_criminalip_from_records_without_resolved_ip_returns_nothing():
    assert (
        criminalip.from_records(_load("criminalip_domain_reports.json"), domain="example.com", ip=None)
        == []
    )


def test_internetdb_from_records_parses_ports_and_hostname():
    assets = internetdb.from_records(_load("internetdb_ip.json"), domain="example-ng.gov.ng")

    assert len(assets) == 1
    asset = assets[0]
    assert asset.ip == "197.211.60.10"
    assert asset.hostname == "mail.example-ng.gov.ng"
    assert {s.port for s in asset.services} == {22, 25, 443}
    assert asset.sources == {"internetdb"}


def test_censys_from_records_parses_services_and_certificate():
    assets = censys.from_records(_load("censys_host.json"), domain="example-ng.gov.ng")

    assert len(assets) == 1
    asset = assets[0]
    assert asset.ip == "154.113.7.30"
    assert asset.country == "NG"
    assert asset.as_name == "Main one Cable Company Nigeria Limited"
    assert asset.cert_subject == "CN=charming-goldberg.154-113-7-30.plesk.page"
    assert asset.cert_is_expired is False
    assert asset.sources == {"censys"}

    ftp = next(s for s in asset.services if s.port == 21)
    assert ftp.product == "proftpd"
    assert ftp.cpe == "cpe:2.3:a:proftpd_project:proftpd:*:*:*:*:*:*:*:*"
    assert ftp.sources == {"censys"}

    dns_service = next(s for s in asset.services if s.port == 53)
    assert dns_service.product is None  # no software[] entry for this port


def test_censys_from_records_skips_type_only_software_entries():
    """Plesk's port has a {"type": ["WEB_UI"]} entry before the real vendor/product one — must not
    be mistaken for a product name."""
    assets = censys.from_records(_load("censys_host.json"), domain="example-ng.gov.ng")
    plesk = next(s for s in assets[0].services if s.port == 8443)

    assert plesk.product == "parallels_plesk_panel"


def test_censys_from_records_handles_empty_response():
    assert censys.from_records({}, domain="example.com") == []


def test_detect_waf_matches_known_vendor_in_as_name():
    assert detect_waf(Asset(as_name="CLOUDFLARENET"))
    assert detect_waf(Asset(isp="Imperva Inc"))
    assert not detect_waf(Asset(as_name="MAINONE-AS"))


def test_registry_enables_only_providers_with_keys_present():
    config = Config(
        log_level="INFO",
        database_url=None,
        netlas_api_key="key",
        criminalip_api_key=None,
        censys_api_key=None,
        nvd_api_key=None,
        cache_ttl_seconds=86400,
    )

    providers = get_enabled_providers(config)
    names = {p.name for p in providers}

    assert "netlas" in names
    assert "criminalip" not in names
    assert "censys" not in names
    assert "internetdb" in names  # no key required (ADR-011)
