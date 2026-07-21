"""Environment-variable configuration loader.

All configuration is env-var based (see docs/07_BACKEND_ARCHITECTURE.md §4). Provider API keys are
optional: a missing key means that provider is skipped at registration time, not a startup failure
(ADR-002). Nothing here may hard-code a country, sector, or provider-specific business rule — that
belongs in a compliance pack or provider adapter, not the config loader.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    log_level: str
    database_url: str | None
    netlas_api_key: str | None
    criminalip_api_key: str | None
    censys_api_key: str | None
    nvd_api_key: str | None
    cache_ttl_seconds: int
    packs_root: str
    default_pack_id: str | None
    report_output_dir: str
    chroma_path: str


def load_config() -> Config:
    """Read configuration from the current environment (call after any `load_dotenv()`)."""
    return Config(
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        database_url=os.environ.get("DATABASE_URL") or None,
        netlas_api_key=os.environ.get("NETLAS_API_KEY") or None,
        criminalip_api_key=os.environ.get("CRIMINALIP_API_KEY") or None,
        censys_api_key=os.environ.get("CENSYS_API_KEY") or None,
        nvd_api_key=os.environ.get("NVD_API_KEY") or None,
        cache_ttl_seconds=int(os.environ.get("CACHE_TTL_SECONDS", 86400)),
        packs_root=os.environ.get("PACKS_ROOT", "packs"),
        default_pack_id=os.environ.get("DEFAULT_PACK_ID") or None,
        report_output_dir=os.environ.get("REPORT_OUTPUT_DIR", ".reports"),
        chroma_path=os.environ.get("CHROMA_PATH", ".chroma"),
    )
