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
    sources: set[str] = field(default_factory=set)

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

    existing_by_key = {(s.port, s.protocol): s for s in existing.services}
    for service in incoming.services:
        key = (service.port, service.protocol)
        current = existing_by_key.get(key)
        if current is None:
            existing.services.append(service)
            existing_by_key[key] = service
        else:
            _merge_service_into(current, service)

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


def _merge_service_into(existing: Service, incoming: Service) -> None:
    """BR-6, at service granularity: two providers reporting the same open port is provenance to
    preserve (which API captured it), not a duplicate to discard.

    BR-5 (no fabrication): if providers disagree on *what product* is running on this port (e.g. one
    says "Caddy", another says "Fathom"), never graft one provider's version/cpe/banner onto another
    provider's product label — that would misattribute one product's CVEs to a different, unrelated one.
    Only combine fields when the providers agree on the product (or one side hasn't reported one)."""
    existing.sources |= incoming.sources

    products_conflict = (
        existing.product is not None
        and incoming.product is not None
        and existing.product.lower() != incoming.product.lower()
    )

    for attr in ("name", "product", "version", "cpe", "banner"):
        if products_conflict and attr in ("version", "cpe", "banner"):
            continue
        if getattr(existing, attr) is None and getattr(incoming, attr) is not None:
            setattr(existing, attr, getattr(incoming, attr))
