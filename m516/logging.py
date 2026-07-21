"""Structured logging setup (docs/07_BACKEND_ARCHITECTURE.md §5).

One formatter, one entry point. Modules get a logger via `get_logger(__name__)`; level is driven by
`Config.log_level` so it stays environment-controlled rather than hard-coded per call site.
"""

from __future__ import annotations

import logging

from m516.config import load_config

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    config = load_config()
    logging.basicConfig(level=config.log_level, format=_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(name)
