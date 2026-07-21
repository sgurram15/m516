"""Dev visualization of WP1 (discovery) + WP2 (enrichment) + the post-WP2 detection-level/port-risk
overlay, working live against real domains. NOT the WP5 React demo UI from docs/22_BUILD_PLAN.md — that
one doesn't exist yet. This is styled to sit "near" the UI mockups in `ui screens/*.jpg` (dark theme,
sidebar nav, stat tiles, per-port risk cards) so it's demo-able today, while staying honest about what
the engine actually does:

- The mockup's "Port Scanner" screen is called **"Port Findings"** here — the engine is strictly passive
  (ADR-001) and has no scan/rescan feature; "Scanner" implies active probing we never do.
- The mockup's "Exploitation Scenario" text is **"Why it matters"** here — that phrasing in the mockup
  reads like LLM-generated narrative, which is explicitly WP4 scope, not this deterministic module
  (ADR-007: no LLM in scoring/enrichment).
- "Breach Monitor" and "Users & Roles" (mockup sidebar items) are out of scope for the POC (confirmed
  with the client) and are not built here.

Run from the project root: streamlit run demo/streamlit_app.py
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from m516.config import Config, load_config
from m516.enrichment.detection_level import cert_detection_level, finding_detection_level
from m516.enrichment.nvd import lookup_cves
from m516.enrichment.port_risk import port_risk_label
from m516.enrichment.scoring import score_finding
from m516.findings import Finding
from m516.models import DiscoveryResult
from m516.providers.base import BaseProvider, detect_waf
from m516.providers.registry import get_enabled_providers

DEFAULT_DOMAINS = [
    "finatrustmfbank.com",
    "finatrustlolcmfbank.com",
    "mutualtrustmfb.com",
    "assetsmfb.com",
    "abmfbnigeria.com",
    "lapo-nigeria.org",
]

VIEWS = ["Dashboard", "Asset Discovery", "Port Findings", "Risk Scoring"]

_LEVEL_STYLE = {
    "red": ("#3B1B1E", "#F87171"),
    "yellow": ("#3A2E10", "#FBBF24"),
    "green": ("#12301E", "#4ADE80"),
    "neutral": ("#1E2635", "#94A3B8"),
}
_LEVEL_META = {
    "red": "Needs attention",
    "yellow": "Worth checking",
    "green": "Looks fine",
}

# Plain-English names for the ports people actually run into. Purely a display label — never used
# for scoring or CVE matching (that's still driven by product/CPE, see m516/enrichment/).
_FRIENDLY_SERVICE_NAMES = {
    21: "File Transfer (FTP)",
    22: "Remote Admin Access (SSH)",
    23: "Remote Admin Access (Telnet)",
    25: "Email Sending (SMTP)",
    53: "Domain Name System (DNS)",
    80: "Website (HTTP)",
    110: "Email Retrieval (POP3)",
    143: "Email Retrieval (IMAP)",
    443: "Website (HTTPS)",
    445: "File Sharing (SMB)",
    465: "Email Sending (SMTPS)",
    587: "Email Sending (Submission)",
    993: "Email Retrieval (IMAPS)",
    995: "Email Retrieval (POP3S)",
    1433: "Database (SQL Server)",
    2077: "Hosting Control Panel (cPanel)",
    2078: "Hosting Control Panel (cPanel, secure)",
    2079: "Hosting Control Panel (cPanel)",
    2080: "Hosting Control Panel (cPanel)",
    2082: "Hosting Control Panel (cPanel)",
    2083: "Hosting Control Panel (cPanel, secure)",
    2086: "Hosting Control Panel (WHM)",
    2087: "Hosting Control Panel (WHM, secure)",
    2095: "Webmail",
    2096: "Webmail (secure)",
    3306: "Database (MySQL/MariaDB)",
    3389: "Remote Desktop (RDP)",
    5432: "Database (PostgreSQL)",
    6379: "Database (Redis)",
    8080: "Website (alternate port)",
    8443: "Website (alternate port, secure)",
    8880: "Website (alternate port)",
    27017: "Database (MongoDB)",
}


def _friendly_service_name(port: int, protocol: str) -> str:
    return _FRIENDLY_SERVICE_NAMES.get(port, f"Network service ({protocol.upper()} port {port})")


@dataclass
class DomainScan:
    domain: str
    result: DiscoveryResult
    findings: list[Finding] = field(default_factory=list)
    discovery_errors: list[str] = field(default_factory=list)
    enrichment_errors: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Styling helpers — small HTML fragments, kept simple/compact so Streamlit's
# markdown renderer doesn't mangle them.
# ---------------------------------------------------------------------------

_CSS = """
<style>
.m516-stat { background:#141B2E; border:1px solid #223047; border-radius:10px; padding:16px 18px; }
.m516-stat .num { font-size:1.9rem; font-weight:700; line-height:1; color:#E5E7EB; }
.m516-stat .label { font-size:0.75rem; color:#94A3B8; margin-top:6px; text-transform:uppercase; letter-spacing:0.04em; }
.m516-pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.75rem; font-weight:700; }
.m516-port-row { display:flex; justify-content:space-between; align-items:flex-start; padding:12px 16px;
  background:#141B2E; border-radius:8px; margin-bottom:8px; border-left:4px solid #223047; gap:16px; }
.m516-port-row .port-num { font-family:monospace; font-size:1.25rem; font-weight:700; color:#22D3EE; }
.m516-port-row .port-name { font-size:0.8rem; color:#94A3B8; }
.m516-port-row .risk-title { font-weight:700; text-align:right; }
.m516-port-row .risk-detail { font-size:0.78rem; color:#94A3B8; text-align:right; max-width:360px; }
.m516-case { background:#141B2E; border:1px solid #223047; border-radius:10px; padding:18px 20px; margin-bottom:14px; }
.m516-case .title { font-weight:700; font-size:1.02rem; color:#E5E7EB; }
.m516-case .target { color:#94A3B8; font-family:monospace; font-size:0.82rem; margin-top:2px; }
.m516-metric-label { color:#94A3B8; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.04em; }
.m516-metric-value { font-weight:700; font-size:1rem; margin-top:2px; }
.m516-why { margin-top:14px; background:#0B1220; border-radius:6px; padding:12px 14px; font-size:0.85rem; color:#CBD5E1; }
</style>
"""


def _pill(text: str, level: str | None) -> str:
    bg, fg = _LEVEL_STYLE.get(level or "neutral", _LEVEL_STYLE["neutral"])
    return f'<span class="m516-pill" style="background:{bg};color:{fg};">{text}</span>'


def _stat_card(number: str, label: str) -> str:
    return f'<div class="m516-stat"><div class="num">{number}</div><div class="label">{label}</div></div>'


# ---------------------------------------------------------------------------
# Scan logic — the only place that talks to providers/NVD. Called once per
# button click; results are cached in st.session_state so switching between
# sidebar views afterward doesn't re-run anything or lose data (Streamlit
# re-runs the whole script on every widget interaction).
# ---------------------------------------------------------------------------


def run_scan(domains: list[str], config: Config, providers: list[BaseProvider]) -> dict[str, DomainScan]:
    scans: dict[str, DomainScan] = {}

    for domain in domains:
        domain_start = time.monotonic()
        result = DiscoveryResult(domain=domain)
        scan = DomainScan(domain=domain, result=result)

        with st.status(f"[{domain}] Running discovery...", expanded=False) as status:
            for provider in providers:
                st.write(f"Querying **{provider.name}**...")
                try:
                    assets = provider.discover(domain)
                except Exception as exc:  # noqa: BLE001 — mirrors m516/discovery.py's own isolation
                    st.warning(f"{provider.name} failed: {exc}")
                    scan.discovery_errors.append(f"{provider.name}: {exc}")
                    continue
                for asset in assets:
                    result.merge_asset(asset)
                st.write(f"{provider.name}: {len(assets)} asset record(s) returned")

            for asset in result.assets:
                asset.is_behind_waf = asset.is_behind_waf or detect_waf(asset)

            status.update(
                label=f"[{domain}] Discovery complete — {len(result.assets)} merged asset(s)",
                state="complete",
            )

        eligible = [
            (asset, service)
            for asset in result.assets
            for service in asset.services
            if service.is_cve_eligible
        ]

        with st.status(
            f"[{domain}] Running CVE enrichment on {len(eligible)} eligible service(s)...",
            expanded=False,
        ) as status:
            if not eligible:
                st.write("No services had enough data (CPE or product+version) to look up.")
            for asset, service in eligible:
                label = f"{asset.ip}:{service.port}/{service.protocol}"
                st.write(f"Checking **{label}**...")
                try:
                    matches = lookup_cves(service, config.nvd_api_key, config.cache_ttl_seconds)
                except Exception as exc:  # noqa: BLE001 — mirrors m516/findings.py's own isolation
                    st.warning(f"NVD lookup failed for {label}: {exc}")
                    scan.enrichment_errors.append(f"nvd: {label}: {exc}")
                    continue

                if not matches:
                    st.write(f"{label}: no known CVEs found")
                    continue

                contextual_score, severity, explanation = score_finding(service, asset, matches)
                primary = max(matches, key=lambda m: m.cvss_score or 0)
                scan.findings.append(
                    Finding(
                        asset=asset,
                        service=service,
                        cve_ids=[m.id for m in matches],
                        cvss=max((m.cvss_score or 0) for m in matches),
                        contextual_score=contextual_score,
                        severity=severity,
                        explanation=explanation,
                        match_confidence=primary.match_confidence,
                        exploitability_score=primary.exploitability_score,
                        impact_score=primary.impact_score,
                    )
                )
                st.write(f"{label}: {len(matches)} CVE(s) — scored {contextual_score} ({severity})")

            scan.findings.sort(key=lambda f: f.contextual_score, reverse=True)
            status.update(
                label=f"[{domain}] Enrichment complete — {len(scan.findings)} finding(s)", state="complete"
            )

        scan.elapsed_seconds = time.monotonic() - domain_start
        scans[domain] = scan

    return scans


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def render_dashboard(scans: dict[str, DomainScan]) -> None:
    st.title("Dashboard")
    st.caption("Portfolio summary across all scanned domains.")

    total_assets = sum(len(s.result.assets) for s in scans.values())
    total_ports = sum(len(a.services) for s in scans.values() for a in s.result.assets)
    all_findings = [f for s in scans.values() for f in s.findings]
    red = sum(1 for f in all_findings if finding_detection_level(f) == "red")
    yellow = sum(1 for f in all_findings if finding_detection_level(f) == "yellow")

    cols = st.columns(5)
    for col, (num, label) in zip(
        cols,
        [
            (str(len(scans)), "Domains scanned"),
            (str(total_assets), "Assets discovered"),
            (str(total_ports), "Open ports"),
            (str(red), "Needs attention"),
            (str(yellow), "Worth checking"),
        ],
    ):
        with col:
            st.markdown(_stat_card(num, label), unsafe_allow_html=True)

    st.write("")
    st.subheader("Comparison across domains")
    st.caption("Richest 'Needs attention'/'Worth checking' counts on non-WAF hosts make the best demo target.")
    rows = []
    for scan in scans.values():
        result = scan.result
        red_d = sum(1 for f in scan.findings if finding_detection_level(f) == "red")
        yellow_d = sum(1 for f in scan.findings if finding_detection_level(f) == "yellow")
        eligible_d = sum(1 for a in result.assets for s in a.services if s.is_cve_eligible)
        clean_d = eligible_d - len(scan.findings)
        rows.append(
            {
                "Domain": scan.domain,
                "IP(s)": ", ".join(sorted({a.ip for a in result.assets if a.ip})) or "—",
                "WAF/CDN": "Yes" if any(a.is_behind_waf for a in result.assets) else "No",
                "Open ports": sum(len(a.services) for a in result.assets),
                "Needs attention": red_d,
                "Worth checking": yellow_d,
                "Clean": clean_d,
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.map(lambda v: "font-weight:700;" if isinstance(v, int) and v > 0 else "", subset=["Needs attention", "Worth checking"]),
        use_container_width=True,
        hide_index=True,
    )

    st.write("")
    st.subheader("Most common exposure types")
    st.caption("Port/service types that showed up most often across every scanned domain.")
    counts: dict[str, int] = {}
    for scan in scans.values():
        for asset in scan.result.assets:
            for s in asset.services:
                risk = port_risk_label(s.port, s.protocol)
                if risk:
                    key = f"{risk[0]} — {_friendly_service_name(s.port, s.protocol)}"
                    counts[key] = counts.get(key, 0) + 1
    if counts:
        top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
        for label, count in top:
            c1, c2 = st.columns([5, 1])
            c1.write(label)
            c2.write(f"**{count}** instance(s)")
    else:
        st.info("No known-risky port types observed across the scanned domains.")


def render_asset_discovery(scans: dict[str, DomainScan]) -> None:
    st.title("Asset Discovery")
    st.caption("Every host discovered across all scanned domains, and which API captured it.")

    rows = []
    for scan in scans.values():
        for asset in scan.result.assets:
            cert_level = cert_detection_level(asset)
            rows.append(
                {
                    "Domain": scan.domain,
                    "IP": asset.ip or "—",
                    "Hostname": asset.hostname or "—",
                    "Country": asset.country or "unknown",
                    "Hosted by": asset.as_name or "unknown",
                    "WAF/CDN": "Yes" if asset.is_behind_waf else "No",
                    "Certificate": _LEVEL_META.get(cert_level, "Not evaluated"),
                    "Open ports": len(asset.services),
                    "Captured by": ", ".join(sorted(asset.sources)) or "unknown",
                }
            )

    if not rows:
        st.info("No assets discovered yet — run a scan from the sidebar.")
        return

    df = pd.DataFrame(rows)

    def _cert_style(v: str) -> str:
        level = {"Looks fine": "green", "Worth checking": "yellow", "Needs attention": "red"}.get(v, "neutral")
        bg, fg = _LEVEL_STYLE[level]
        return f"background-color:{bg};color:{fg};font-weight:600;"

    st.dataframe(df.style.map(_cert_style, subset=["Certificate"]), use_container_width=True, hide_index=True)
    st.caption(f"{len(rows)} asset(s) across {len(scans)} domain(s).")


def render_port_findings(scans: dict[str, DomainScan]) -> None:
    st.title("Port Findings")
    st.caption(
        "Every open port discovered per host, passively (ADR-001) — no scan/rescan feature exists in "
        "this engine. Findings with a confirmed CVE match show the finding's severity; everything else "
        "shows a CVE-independent risk label where one applies."
    )

    finding_by_key = {}
    for scan in scans.values():
        for f in scan.findings:
            finding_by_key[(scan.domain, f.asset.ip, f.service.port, f.service.protocol)] = f

    for scan in scans.values():
        for asset in scan.result.assets:
            if not asset.services:
                continue
            worst = "green"
            for s in asset.services:
                f = finding_by_key.get((scan.domain, asset.ip, s.port, s.protocol))
                if f:
                    level = finding_detection_level(f)
                    if level == "red":
                        worst = "red"
                    elif level == "yellow" and worst != "red":
                        worst = "yellow"

            header_col, badge_col = st.columns([5, 1])
            with header_col:
                st.markdown(f"**{scan.domain}** &middot; `{asset.ip or '(no IP)'}`" + (f" &middot; {asset.hostname}" if asset.hostname else ""), unsafe_allow_html=True)
            with badge_col:
                st.markdown(_pill(_LEVEL_META.get(worst, "Not evaluated"), worst), unsafe_allow_html=True)

            for s in sorted(asset.services, key=lambda x: x.port):
                f = finding_by_key.get((scan.domain, asset.ip, s.port, s.protocol))
                risk = port_risk_label(s.port, s.protocol)

                if f:
                    level = finding_detection_level(f)
                    _, fg = _LEVEL_STYLE.get(level, _LEVEL_STYLE["neutral"])
                    title = f"{f.severity.upper()} · {len(f.cve_ids)} known issue(s)"
                    detail = (
                        f"CVSS {f.cvss}/10, confidence: {f.match_confidence}. "
                        f"{'Version confirmed.' if f.match_confidence == 'exact' else 'Version unconfirmed — verify before treating as certain.'}"
                    )
                    stripe = _LEVEL_STYLE.get(level, _LEVEL_STYLE["neutral"])[1]
                elif risk:
                    fg = "#94A3B8"
                    title = risk[0]
                    detail = risk[1]
                    stripe = "#3A2E10"
                else:
                    fg = "#64748B"
                    title = "Not enough data"
                    detail = "No product/version captured for this port."
                    stripe = "#223047"

                st.markdown(
                    f'<div class="m516-port-row" style="border-left-color:{stripe};">'
                    f'<div><div class="port-num">{s.port}</div><div class="port-name">{_friendly_service_name(s.port, s.protocol)}'
                    f'{" · " + s.product if s.product else ""}</div></div>'
                    f'<div><div class="risk-title" style="color:{fg};">{title}</div><div class="risk-detail">{detail}</div></div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.write("")


def render_risk_scoring(scans: dict[str, DomainScan]) -> None:
    st.title("Risk Scoring")
    st.caption("CVSS-based vulnerability assessment — deterministic scoring, no LLM (ADR-007).")

    all_findings = [(scan.domain, f) for scan in scans.values() for f in scan.findings]
    total_assets = sum(len(s.result.assets) for s in scans.values())
    red = sum(1 for _, f in all_findings if finding_detection_level(f) == "red")
    yellow = sum(1 for _, f in all_findings if finding_detection_level(f) == "yellow")
    highest = max((f.cvss for _, f in all_findings), default=None)

    cols = st.columns(4)
    for col, (num, label) in zip(
        cols,
        [
            (f"{highest:.1f}" if highest is not None else "—", "Highest CVSS found"),
            (str(red), "Needs attention"),
            (str(yellow), "Worth checking"),
            (str(total_assets), "Assets scanned"),
        ],
    ):
        with col:
            st.markdown(_stat_card(num, label), unsafe_allow_html=True)

    st.write("")
    st.subheader("Findings, ranked by risk")

    ranked = sorted(all_findings, key=lambda df: df[1].contextual_score, reverse=True)
    if not ranked:
        st.info("No findings yet — run a scan from the sidebar.")
        return

    for domain, f in ranked:
        level = finding_detection_level(f)
        service_name = _friendly_service_name(f.service.port, f.service.protocol)
        confidence_note = (
            "Version could not be confirmed — treat as a signal to verify, not a confirmed hole."
            if f.match_confidence == "broad"
            else "Version was confirmed — this is a real, actionable issue."
        )
        st.markdown(
            f'<div class="m516-case">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div><div class="title">{domain} &mdash; {service_name}</div>'
            f'<div class="target">{f.asset.ip}:{f.service.port}/{f.service.protocol} &middot; {f.service.product or "unidentified software"}</div></div>'
            f"{_pill(f'{f.severity.upper()} &middot; {f.cvss}/10', level)}"
            f"</div>"
            f'<div style="display:flex;gap:32px;margin-top:16px;">'
            f'<div><div class="m516-metric-label">Exploitability</div><div class="m516-metric-value">{f.exploitability_score if f.exploitability_score is not None else "—"}</div></div>'
            f'<div><div class="m516-metric-label">Impact</div><div class="m516-metric-value">{f.impact_score if f.impact_score is not None else "—"}</div></div>'
            f'<div><div class="m516-metric-label">Risk level</div><div class="m516-metric-value">{f.severity.title()}</div></div>'
            f'<div><div class="m516-metric-label">Known CVEs</div><div class="m516-metric-value">{len(f.cve_ids)}</div></div>'
            f"</div>"
            f'<div class="m516-why"><strong>Why it matters:</strong> {confidence_note} '
            f"The most relevant CVE(s): {', '.join(f.cve_ids[:5])}{' ...' if len(f.cve_ids) > 5 else ''}.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.set_page_config(page_title="M516 — Live Scan Demo", layout="wide")
st.markdown(_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        '<div style="font-size:1.6rem;font-weight:800;color:#22D3EE;">M516</div>'
        '<div style="font-size:0.8rem;color:#94A3B8;margin-bottom:16px;">'
        "External Attack Surface &amp; Compliance Management</div>",
        unsafe_allow_html=True,
    )
    domain_choice = st.selectbox("Domain", DEFAULT_DOMAINS + ["Custom domain..."])
    if domain_choice == "Custom domain...":
        selected_domain = st.text_input("Enter a domain", placeholder="example.com").strip()
    else:
        selected_domain = domain_choice

    run = st.button("Run live scan", type="primary", use_container_width=True, disabled=not selected_domain)
    st.caption(
        "Scans only the selected domain — strictly passive (ADR-001), never touches a target directly. "
        "No live-scan/rescan feature exists anywhere in this engine; every provider only queries "
        "third-party indexes."
    )

    scanned_domains = list(st.session_state.get("m516_scans", {}).keys())
    if scanned_domains:
        st.caption(f"Scanned so far: {', '.join(scanned_domains)}")
        if st.button("Clear all results", use_container_width=True):
            st.session_state.pop("m516_scans", None)
            st.rerun()

    st.divider()
    view = st.radio("View", VIEWS, label_visibility="collapsed")
    with st.expander("Detection-level rule criteria"):
        st.markdown(
            """
**Findings:** Needs attention = critical/high severity, version-confirmed. Worth checking =
critical/high but unconfirmed version, or medium severity. Looks fine = low severity, or checked with
zero CVEs found.

**Certificates:** Needs attention = expired. Worth checking = expires within 30 days. Looks fine = valid,
>30 days remaining.
            """
        )

if run and selected_domain:
    config = load_config()
    providers = get_enabled_providers(config)
    if not providers:
        st.error("No providers enabled — check NETLAS_API_KEY / CRIMINALIP_API_KEY / CENSYS_API_KEY in .env.")
        st.stop()

    overall_start = time.monotonic()
    new_scan = run_scan([selected_domain], config, providers)
    st.session_state.setdefault("m516_scans", {}).update(new_scan)
    st.session_state["m516_scan_seconds"] = time.monotonic() - overall_start

scans: dict[str, DomainScan] | None = st.session_state.get("m516_scans")

if not scans:
    st.title("M516 — Live Scan Demo")
    st.info("Pick a domain in the sidebar and click **Run live scan** to begin — only that domain is scanned.")
else:
    if view == "Dashboard":
        render_dashboard(scans)
    elif view == "Asset Discovery":
        render_asset_discovery(scans)
    elif view == "Port Findings":
        render_port_findings(scans)
    elif view == "Risk Scoring":
        render_risk_scoring(scans)

    for scan in scans.values():
        if scan.discovery_errors or scan.enrichment_errors:
            with st.expander(f"Errors — {scan.domain}"):
                for err in scan.discovery_errors + scan.enrichment_errors:
                    st.warning(err)

    st.caption(f"Last scan took {st.session_state.get('m516_scan_seconds', 0):.1f}s total.")
