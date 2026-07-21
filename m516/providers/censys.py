"""Censys adapter, added post-WP1 (user-provided CENSYS_API_KEY). https://docs.censys.com/reference/get-started

Live-verified: the domain-search endpoint (`POST /v3/global/search/query`) is **paid-only** — a free-tier
key gets a 403 ("Free users can only access this endpoint through the Platform UI"). The direct
host-lookup-by-IP endpoint (`GET /v3/global/asset/host/{ip}`) *does* work on the free tier and returns
richer per-service data than any other provider here (independently confirmed nginx on port 80 that
Netlas also found, plus ProFTPD/Postfix/Dovecot/Plesk that Netlas didn't surface for the same host).
Same pattern as InternetDB: takes an IP, not a domain, so this adapter resolves domain -> IP itself.

`software[]` items give `vendor`/`product` but no version — a synthetic wildcarded CPE is built from
them so they route through the existing `virtualMatchString` path in `m516/enrichment/nvd.py` unchanged.
"""

from __future__ import annotations

from datetime import datetime

import requests

from m516.cache import cache_get, cache_set
from m516.logging import get_logger
from m516.models import Asset, Service
from m516.providers.base import BaseProvider
from m516.providers.dns_resolve import resolve

_URL = "https://api.platform.censys.io/v3/global/asset/host"

logger = get_logger(__name__)


class CensysProvider(BaseProvider):
    name = "censys"

    def __init__(self, api_key: str, cache_ttl_seconds: int = 86400) -> None:
        self._api_key = api_key
        self._cache_ttl_seconds = cache_ttl_seconds

    def discover(self, domain: str) -> list[Asset]:
        ips = resolve(domain)
        assets: list[Asset] = []
        for ip in ips:
            data = cache_get(self.name, ip, self._cache_ttl_seconds)
            if data is None:
                response = requests.get(
                    f"{_URL}/{ip}",
                    headers={"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"},
                    timeout=30,
                )
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                data = response.json()
                cache_set(self.name, ip, data)

            assets.extend(from_records(data, domain))

        return assets


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _primary_software(item: dict) -> dict | None:
    """`software[]` mixes type-only tags (e.g. {"type": ["WEB_UI"]}) with real vendor/product
    entries — take the first entry that actually names a product."""
    for entry in item.get("software", []) or []:
        if entry.get("vendor") and entry.get("product"):
            return entry
    return None


def _synthetic_cpe(vendor: str, product: str) -> str:
    return f"cpe:2.3:a:{vendor}:{product}:*:*:*:*:*:*:*:*"


def from_records(data: dict, domain: str) -> list[Asset]:
    """Offline parse path (docs/07_BACKEND_ARCHITECTURE.md §8)."""
    resource = ((data or {}).get("result") or {}).get("resource") or {}
    if not resource:
        return []

    services: list[Service] = []
    cert_subject = cert_issuer = cert_valid_until = None

    for item in resource.get("services", []) or []:
        port = item.get("port")
        if port is None:
            continue

        software = _primary_software(item)
        product = software.get("product") if software else None
        cpe = _synthetic_cpe(software["vendor"], software["product"]) if software else None

        services.append(
            Service(
                port=port,
                protocol=item.get("transport_protocol", "tcp"),
                name=(item.get("protocol") or "").lower() or None,
                product=product,
                cpe=cpe,
                sources={"censys"},
            )
        )

        if cert_subject is None:
            parsed_cert = (item.get("cert") or {}).get("parsed")
            if parsed_cert:
                cert_subject = parsed_cert.get("subject_dn")
                cert_issuer = parsed_cert.get("issuer_dn")
                cert_valid_until = _parse_datetime(
                    (parsed_cert.get("validity_period") or {}).get("not_after")
                )

    location = resource.get("location", {}) or {}
    asn = resource.get("autonomous_system", {}) or {}

    asset = Asset(
        ip=resource.get("ip"),
        domain=domain,
        services=services,
        asn=str(asn.get("asn")) if asn.get("asn") is not None else None,
        as_name=asn.get("name"),
        isp=asn.get("name"),
        country=location.get("country_code"),
        cert_subject=cert_subject,
        cert_issuer=cert_issuer,
        cert_valid_until=cert_valid_until,
        sources={"censys"},
    )
    return [asset]
