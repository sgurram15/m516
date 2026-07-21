"""Criminal IP adapter (ADR-004: summary/risk/tech stack cross-check — deep banner data is Netlas's
job). https://www.criminalip.io/developer/api/get-domain-reports

GET https://api.criminalip.io/v1/domain/reports?query={domain} , `x-api-key: <key>`.

Confirmed against a live response: `data.data.reports[]` carries `technologies[]` (tech_name only — no
port/version) and `country_code` (a list, not a string), and — importantly — **no IP field at all**.
Since `Asset` is IP-keyed (docs/03_DOMAIN_MODEL.md), this adapter resolves domain -> IP itself (same
passive DNS lookup as InternetDB) so its findings still merge into the same asset as other providers.
"""

from __future__ import annotations

import requests

from m516.logging import get_logger
from m516.models import Asset, Service
from m516.providers.base import BaseProvider
from m516.cache import cache_get, cache_set
from m516.providers.dns_resolve import resolve

_URL = "https://api.criminalip.io/v1/domain/reports"

# Criminal IP's domain/reports technologies are detected via HTTP fingerprinting (Wappalyzer-style)
# and carry no port of their own — HTTP is the only reasonable assumption.
_ASSUMED_PORT = 80
_ASSUMED_PROTOCOL = "tcp"

logger = get_logger(__name__)


class CriminalIPProvider(BaseProvider):
    name = "criminalip"

    def __init__(self, api_key: str, cache_ttl_seconds: int = 86400) -> None:
        self._api_key = api_key
        self._cache_ttl_seconds = cache_ttl_seconds

    def discover(self, domain: str) -> list[Asset]:
        data = cache_get(self.name, domain, self._cache_ttl_seconds)
        if data is None:
            response = requests.get(
                _URL,
                headers={"x-api-key": self._api_key},
                params={"query": domain},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            cache_set(self.name, domain, data)

        ips = resolve(domain)
        return from_records(data, domain, ip=ips[0] if ips else None)


def from_records(data: dict, domain: str, ip: str | None) -> list[Asset]:
    """Offline parse path (docs/07_BACKEND_ARCHITECTURE.md §8)."""
    if not data or ip is None:
        return []

    reports = ((data.get("data") or {}).get("reports")) or []

    assets: list[Asset] = []
    for report in reports:
        technologies = report.get("technologies") or []
        services = [
            Service(
                port=_ASSUMED_PORT,
                protocol=_ASSUMED_PROTOCOL,
                name=tech.get("tech_name"),
                product=tech.get("tech_name"),
                sources={"criminalip"},
            )
            for tech in technologies
            if tech.get("tech_name")
        ]

        country_codes = report.get("country_code") or []
        country = country_codes[0] if isinstance(country_codes, list) and country_codes else None

        assets.append(
            Asset(
                ip=ip,
                domain=domain,
                services=services,
                country=country,
                sources={"criminalip"},
            )
        )

    return assets
