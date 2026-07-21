"""Module 1 orchestrator (docs/02_ARCHITECTURE.md §3): domain -> normalised DiscoveryResult.

Runs every enabled provider, merges results by IP, applies WAF detection. One provider failing is
caught and recorded, never fatal (NFR-REL).
"""

from __future__ import annotations

from m516.config import load_config
from m516.logging import get_logger
from m516.models import DiscoveryResult
from m516.providers.base import detect_waf
from m516.providers.registry import get_enabled_providers

logger = get_logger(__name__)


def run_discovery(domain: str) -> DiscoveryResult:
    result = DiscoveryResult(domain=domain)
    config = load_config()

    for provider in get_enabled_providers(config):
        try:
            assets = provider.discover(domain)
        except Exception as exc:  # noqa: BLE001 — a provider must never abort the scan (NFR-REL)
            logger.warning("%s failed for %s: %s", provider.name, domain, exc)
            result.errors.append(f"{provider.name}: {exc}")
            continue

        for asset in assets:
            result.merge_asset(asset)

    for asset in result.assets:
        asset.is_behind_waf = asset.is_behind_waf or detect_waf(asset)

    return result
