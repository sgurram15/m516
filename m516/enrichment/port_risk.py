"""Deterministic, CVE-independent port-type risk labels — no LLM (ADR-007 spirit). Informed by the
Port Scanner UI mockup (`ui screens/portscanner.jpg`): a short category + one-line reason, shown even
for services with no CPE/version data (i.e. no CVE check could run). This is deliberately independent
of CVE matching — an exposed database port is worth flagging on its own, regardless of whether a
specific vulnerability can be confirmed.

Universal infra knowledge, not pack/sector-specific (golden rule) — mirrors the same port set as
`m516/enrichment/scoring.py`'s `_SENSITIVE_PORTS`. A port with no informed opinion returns `None`;
never fabricate a label just to fill a cell.
"""

from __future__ import annotations

_UNENCRYPTED_CREDENTIALS = (
    "Unencrypted Credential Transmission",
    "Login credentials are sent in plaintext — interceptable via network sniffing.",
)
_WEAK_AUTH = (
    "Weak Authentication",
    "Exposed to the internet, this is a common target for credential brute-forcing.",
)
_UNENCRYPTED_REMOTE_ACCESS = (
    "Unencrypted Remote Access",
    "All traffic, including credentials, is transmitted in plaintext.",
)
_UNENCRYPTED_TRAFFIC = (
    "Unencrypted Traffic",
    "Unencrypted traffic is vulnerable to interception and man-in-the-middle attacks.",
)
_FILE_SHARING_EXPOSURE = (
    "File Sharing Exposure",
    "Exposed file-sharing services have been the entry point for major ransomware campaigns (e.g. WannaCry).",
)
_OPEN_DATABASE = (
    "Open Database",
    "A database reachable from the internet is a target for data exfiltration or injection.",
)
_EXPOSED_REMOTE_DESKTOP = (
    "Exposed Remote Desktop",
    "Remote desktop access exposed to the internet enables exploitation and lateral movement if compromised.",
)
_EXPOSED_ADMIN_PANEL = (
    "Exposed Admin Panel",
    "A hosting control panel reachable from the internet is a high-value target if credentials are weak or default.",
)

_PORT_RISK_CATALOG: dict[int, tuple[str, str]] = {
    21: _UNENCRYPTED_CREDENTIALS,
    22: _WEAK_AUTH,
    23: _UNENCRYPTED_REMOTE_ACCESS,
    80: _UNENCRYPTED_TRAFFIC,
    445: _FILE_SHARING_EXPOSURE,
    1433: _OPEN_DATABASE,
    3306: _OPEN_DATABASE,
    3389: _EXPOSED_REMOTE_DESKTOP,
    5432: _OPEN_DATABASE,
    6379: _OPEN_DATABASE,
    9200: _OPEN_DATABASE,
    27017: _OPEN_DATABASE,
}
for _admin_port in (2077, 2078, 2079, 2080, 2082, 2083, 2086, 2087):
    _PORT_RISK_CATALOG[_admin_port] = _EXPOSED_ADMIN_PANEL


def port_risk_label(port: int, protocol: str) -> tuple[str, str] | None:
    """Returns (label, description) for a known-risky port type, or None if we have no informed
    opinion on this port — absence of a label is not a claim that the port is safe."""
    return _PORT_RISK_CATALOG.get(port)
