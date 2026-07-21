"""Netlas adapter (ADR-004: deep banners/CPEs/certs). https://docs.netlas.io/api-reference/

GET https://app.netlas.io/api/host/{host}/ , `Authorization: Bearer <key>`. Accepts a domain directly.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

import requests

from m516.logging import get_logger
from m516.models import Asset, Service
from m516.providers.base import BaseProvider
from m516.cache import cache_get, cache_set

_BASE_URL = "https://app.netlas.io/api/host"

logger = get_logger(__name__)


class NetlasProvider(BaseProvider):
    name = "netlas"

    def __init__(self, api_key: str, cache_ttl_seconds: int = 86400) -> None:
        self._api_key = api_key
        self._cache_ttl_seconds = cache_ttl_seconds

    def discover(self, domain: str) -> list[Asset]:
        data = cache_get(self.name, domain, self._cache_ttl_seconds)
        if data is None:
            response = requests.get(
                f"{_BASE_URL}/{domain}/",
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            cache_set(self.name, domain, data)

        return from_records(data, domain)


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


_DEFAULT_PORT_BY_SCHEME = {"http": 80, "https": 443}


def _port_from_uri(uri: str | None) -> int | None:
    if not uri:
        return None
    parsed = urlparse(uri)
    if parsed.port:
        return parsed.port
    return _DEFAULT_PORT_BY_SCHEME.get(parsed.scheme)


def _software_by_port(data: dict) -> dict[int, dict]:
    """Real response nests product/version/cpe under `software[].tag[]`, keyed to a port only via
    the item's `uri` (e.g. "http://host:80/") — not a direct `port` field."""
    by_port: dict[int, dict] = {}
    for item in data.get("software", []) or []:
        port = _port_from_uri(item.get("uri"))
        if port is None:
            continue
        tags = item.get("tag") or []
        if not tags:
            continue
        tag = tags[0]
        name = tag.get("name")
        version = (tag.get(name) or {}).get("version") if name else None
        cpes = tag.get("cpe") or []
        by_port[port] = {
            "product": tag.get("fullname") or name,
            "version": version or None,
            "cpe": cpes[0] if cpes else None,
        }
    return by_port


def from_records(data: dict, domain: str) -> list[Asset]:
    """Offline parse path — testable against captured real data without a live API call
    (docs/07_BACKEND_ARCHITECTURE.md §8). Field layout confirmed against a live Netlas response for a
    domain-type query; IP-type queries may carry additional fields (certificate/asn) not present for
    every domain depending on what Netlas has indexed."""
    if not data:
        return []

    software_by_port = _software_by_port(data)

    services: list[Service] = []
    for port_entry in data.get("ports", []) or []:
        port = port_entry.get("port")
        if port is None:
            continue
        software = software_by_port.get(port, {})
        services.append(
            Service(
                port=port,
                protocol=port_entry.get("prot4", "tcp"),
                name=port_entry.get("prot7") or port_entry.get("protocol"),
                product=software.get("product"),
                version=software.get("version"),
                cpe=software.get("cpe"),
                banner=port_entry.get("banner"),
            )
        )

    ip = data.get("ip")
    if ip is None:
        a_records = (data.get("dns", {}) or {}).get("a") or []
        ip = a_records[0] if a_records else None

    whois = data.get("whois", {}) or {}
    net = whois.get("net", {}) or {}
    asn = whois.get("asn", {}) or {}

    cert_subject = cert_issuer = cert_valid_until = None
    certificates = data.get("certificate", []) or []
    if certificates:
        cert = certificates[0]
        cert_subject = cert.get("subject_dn")
        cert_issuer = cert.get("issuer_dn")
        cert_valid_until = _parse_datetime((cert.get("validity", {}) or {}).get("end"))

    asset = Asset(
        ip=ip,
        domain=domain,
        services=services,
        asn=str(asn.get("number")) if asn.get("number") is not None else None,
        as_name=asn.get("name"),
        isp=net.get("organization"),
        country=net.get("country"),
        cert_subject=cert_subject,
        cert_issuer=cert_issuer,
        cert_valid_until=cert_valid_until,
        sources={"netlas"},
    )
    return [asset]
