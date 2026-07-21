"""Engine domain entities (docs/03_DOMAIN_MODEL.md §1). Universal — no pack/sector knowledge (golden rule)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Service:
    port: int
    protocol: str
    name: str | None = None
    product: str | None = None
    version: str | None = None
    cpe: str | None = None
    banner: str | None = None

    @property
    def version_string(self) -> str | None:
        if self.product and self.version:
            return f"{self.product} {self.version}"
        return None

    @property
    def is_cve_eligible(self) -> bool:
        """BR-2: a service needs a version_string or cpe to be CVE-eligible."""
        return bool(self.version_string or self.cpe)


@dataclass
class Asset:
    ip: str | None = None
    hostname: str | None = None
    domain: str | None = None
    services: list[Service] = field(default_factory=list)
    asn: str | None = None
    as_name: str | None = None
    isp: str | None = None
    country: str | None = None
    is_behind_waf: bool = False
    cert_subject: str | None = None
    cert_issuer: str | None = None
    cert_valid_until: datetime | None = None
    sources: set[str] = field(default_factory=set)
    last_seen: datetime | None = None
    tenant_id: str | None = None

    def is_locally_hosted(self, home_country: str) -> bool:
        """BR-8: compare against the loaded pack's home_country — never hard-coded."""
        return self.country == home_country and not self.is_behind_waf

    @property
    def cert_is_expired(self) -> bool | None:
        if self.cert_valid_until is None:
            return None
        valid_until = self.cert_valid_until
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        return valid_until < datetime.now(timezone.utc)


@dataclass
class DiscoveryResult:
    domain: str
    assets: list[Asset] = field(default_factory=list)
    subdomains: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def merge_asset(self, asset: Asset) -> None:
        """Merge by IP (BR-6: provenance preserved through merges). No IP means no merge key —
        appended as-is."""
        if asset.ip is None:
            self.assets.append(asset)
            return

        for existing in self.assets:
            if existing.ip == asset.ip:
                _merge_into(existing, asset)
                return

        self.assets.append(asset)


def _merge_into(existing: Asset, incoming: Asset) -> None:
    existing.sources |= incoming.sources

    existing_keys = {(s.port, s.protocol) for s in existing.services}
    for service in incoming.services:
        if (service.port, service.protocol) not in existing_keys:
            existing.services.append(service)
            existing_keys.add((service.port, service.protocol))

    for attr in (
        "hostname",
        "domain",
        "asn",
        "as_name",
        "isp",
        "country",
        "cert_subject",
        "cert_issuer",
        "cert_valid_until",
    ):
        if getattr(existing, attr) is None and getattr(incoming, attr) is not None:
            setattr(existing, attr, getattr(incoming, attr))

    existing.is_behind_waf = existing.is_behind_waf or incoming.is_behind_waf

    if incoming.last_seen is not None and (
        existing.last_seen is None or incoming.last_seen > existing.last_seen
    ):
        existing.last_seen = incoming.last_seen
