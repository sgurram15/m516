"""Shared passive DNS resolution helper — used by providers that need domain -> IP themselves
(InternetDB, Criminal IP's domain/reports which returns no IP)."""

from __future__ import annotations

import socket

from m516.logging import get_logger

logger = get_logger(__name__)


def resolve(domain: str) -> list[str]:
    try:
        _, _, ips = socket.gethostbyname_ex(domain)
    except OSError as exc:
        logger.warning("DNS resolution failed for %s: %s", domain, exc)
        return []
    return ips
