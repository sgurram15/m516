"""Single place providers are registered and switched on/off (docs/07_BACKEND_ARCHITECTURE.md §3).
A provider is enabled iff its API-key env var is set (or it needs no key). Adding a provider = one
line here + one adapter file.
"""

from __future__ import annotations

from m516.config import Config
from m516.providers.base import BaseProvider
from m516.providers.criminalip import CriminalIPProvider
from m516.providers.internetdb import InternetDBProvider
from m516.providers.netlas import NetlasProvider

# name -> factory(config) -> provider, or None if its required key is missing
_BUILDERS = {
    "netlas": lambda config: (
        NetlasProvider(config.netlas_api_key, config.cache_ttl_seconds)
        if config.netlas_api_key
        else None
    ),
    "criminalip": lambda config: (
        CriminalIPProvider(config.criminalip_api_key, config.cache_ttl_seconds)
        if config.criminalip_api_key
        else None
    ),
    "internetdb": lambda config: InternetDBProvider(config.cache_ttl_seconds),
}


def get_enabled_providers(config: Config) -> list[BaseProvider]:
    providers = []
    for build in _BUILDERS.values():
        provider = build(config)
        if provider is not None:
            providers.append(provider)
    return providers
