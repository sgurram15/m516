"""Provider-adapter interface (ADR-002, docs/07_BACKEND_ARCHITECTURE.md §3).

The pipeline depends only on this interface. Every concrete adapter subclasses `BaseProvider` and
normalises its own response shape into `Asset`/`Service`. Adding a provider = one adapter file + one
line in `registry.py`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from m516.models import Asset

# Well-known CDN/WAF vendors — global infrastructure knowledge, not sector/country-specific, so this
# stays in the engine (golden rule). FR-1.5.
_WAF_CDN_VENDORS = (
    "cloudflare",
    "akamai",
    "imperva",
    "incapsula",
    "sucuri",
    "fastly",
)


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def discover(self, domain: str) -> list[Asset]:
        """Passively look up `domain` and return normalised Assets. Raise on failure — the
        orchestrator (`discovery.py`) is responsible for catching and recording errors (NFR-REL)."""
        raise NotImplementedError


def detect_waf(asset: Asset) -> bool:
    """BR-1: a WAF/CDN asset is never treated as locally-hosted origin infrastructure."""
    haystack = " ".join(filter(None, (asset.as_name, asset.isp))).lower()
    return any(vendor in haystack for vendor in _WAF_CDN_VENDORS)
