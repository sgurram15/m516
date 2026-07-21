"""Shodan InternetDB adapter (ADR-011): free, no-key, IP-keyed enrichment; cross-checks other
providers. Non-commercial licence — flag before commercial launch (13_RISK_REGISTER.md).

GET https://internetdb.shodan.io/{ip} , no auth. Takes an IP, not a domain, so this adapter resolves
domain -> IP itself (stdlib DNS) to keep the same `discover(domain)` interface as every other provider.
"""

from __future__ import annotations

import requests

from m516.logging import get_logger
from m516.models import Asset, Service
from m516.providers.base import BaseProvider
from m516.providers.cache import cache_get, cache_set
from m516.providers.dns_resolve import resolve

_URL = "https://internetdb.shodan.io"

logger = get_logger(__name__)


class InternetDBProvider(BaseProvider):
    name = "internetdb"

    def __init__(self, cache_ttl_seconds: int = 86400) -> None:
        self._cache_ttl_seconds = cache_ttl_seconds

    def discover(self, domain: str) -> list[Asset]:
        ips = resolve(domain)
        assets: list[Asset] = []
        for ip in ips:
            data = cache_get(self.name, ip, self._cache_ttl_seconds)
            if data is None:
                response = requests.get(f"{_URL}/{ip}", timeout=30)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                data = response.json()
                cache_set(self.name, ip, data)

            assets.extend(from_records(data, domain))

        return assets


def from_records(data: dict, domain: str) -> list[Asset]:
    """Offline parse path (docs/07_BACKEND_ARCHITECTURE.md §8)."""
    if not data:
        return []

    services = [
        Service(port=port, protocol="tcp", cpe=_cpe_for_port(data, port))
        for port in data.get("ports", []) or []
    ]

    hostnames = data.get("hostnames") or []
    asset = Asset(
        ip=data.get("ip"),
        domain=domain,
        hostname=hostnames[0] if hostnames else None,
        services=services,
        sources={"internetdb"},
    )
    return [asset]


def _cpe_for_port(data: dict, port: int) -> str | None:
    """InternetDB's `cpes` isn't keyed per-port; best-effort single match when there's exactly one."""
    cpes = data.get("cpes") or []
    return cpes[0] if len(cpes) == 1 else None
