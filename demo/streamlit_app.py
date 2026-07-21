"""Quick throwaway visualization of WP1 (discovery) + WP2 (enrichment) + the post-WP2 detection-level
overlay, working live against real domains. NOT the WP5 React demo UI from docs/22_BUILD_PLAN.md —
that's still a separate, later deliverable. This exists only so the pipeline can be seen working
end-to-end before WP5.

Supports multiple domains at once (one per line) for triage/comparison across candidate targets —
e.g. picking a demo domain by seeing which one actually shows real findings. Findings/services are
rendered plain-language-first (raw CVE IDs/CPE strings tucked into "Technical details" expanders) so a
non-technical reader can follow along; nothing about the underlying data changes.

Run from the project root: streamlit run demo/streamlit_app.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from m516.config import load_config
from m516.enrichment.detection_level import cert_detection_level, finding_detection_level
from m516.enrichment.nvd import lookup_cves
from m516.enrichment.port_risk import port_risk_label
from m516.enrichment.scoring import score_finding
from m516.findings import Finding
from m516.models import Asset, DiscoveryResult
from m516.providers.base import detect_waf
from m516.providers.registry import get_enabled_providers

DEFAULT_DOMAINS = [
    "finatrustmfbank.com",
    "finatrustlolcmfbank.com",
    "mutualtrustmfb.com",
    "assetsmfb.com",
    "abmfbnigeria.com",
    "lapo-nigeria.org",
]

_LEVEL_STYLE = {
    "red": ("#f8d7da", "#842029"),
    "yellow": ("#fff3cd", "#664d03"),
    "green": ("#d1e7dd", "#0f5132"),
    "neutral": ("#e2e3e5", "#41464b"),
}

_LEVEL_META = {
    "red": ("🟥", "Needs attention"),
    "yellow": ("🟨", "Worth checking"),
    "green": ("🟩", "Looks fine"),
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


def _level_css(level: str | None) -> str:
    bg, fg = _LEVEL_STYLE.get(level or "neutral", _LEVEL_STYLE["neutral"])
    return f"background-color: {bg}; color: {fg}; font-weight: 600;"


def _style_level_column(df: pd.DataFrame, column: str) -> "pd.io.formats.style.Styler":
    return df.style.map(_level_css, subset=[column])


def _render_finding_card(f: Finding) -> None:
    level = finding_detection_level(f)
    icon, label = _LEVEL_META.get(level, ("⬜", "Not evaluated"))
    service_name = _friendly_service_name(f.service.port, f.service.protocol)

    with st.container(border=True):
        st.markdown(f"##### {icon} {label} — {service_name} on `{f.asset.ip}`")

        exposure = (
            "protected by a detected firewall/CDN"
            if f.asset.is_behind_waf
            else "directly exposed to the internet, with no firewall/CDN detected"
        )
        confidence_note = (
            "the exact software version couldn't be confirmed, so this is a signal to verify manually, "
            "not a confirmed hole"
            if f.match_confidence == "broad"
            else "the software version was confirmed, so this is a real, actionable issue"
        )
        st.write(
            f"This service ({f.service.product or 'unidentified software'}) is {exposure}. We found "
            f"**{len(f.cve_ids)} known security issue(s)** associated with this software; the most "
            f"serious would rate **{f.severity}** (CVSS {f.cvss}/10) — but {confidence_note}."
        )

        with st.expander("Technical details"):
            st.write(f"**CPE:** `{f.service.cpe or '—'}`")
            st.write(f"**CVE IDs:** {', '.join(f.cve_ids)}")
            st.write(f"**Contextual score:** {f.contextual_score}/100 · **Confidence:** {f.match_confidence}")
            st.write(
                f"**Exploitability:** {f.exploitability_score if f.exploitability_score is not None else '—'} "
                f"· **Impact:** {f.impact_score if f.impact_score is not None else '—'} "
                "(CVSS sub-scores from NVD, for the most severe matched CVE)"
            )
            st.write(f"**Full explanation:** {f.explanation}")


st.set_page_config(page_title="M516 Live Scan Demo", layout="wide")

st.title("M516 — Live Scan Demo")
st.caption(
    "Dev visualization of WP1 (discovery) + WP2 (enrichment) + detection-level rules, against real, "
    "live provider data. Strictly passive lookups only (ADR-001) — never touches a target directly. "
    "No 'live scan / rescan' feature exists anywhere in this engine; every provider only queries "
    "third-party indexes."
)

domains_input = st.text_area(
    "Domains (one per line) — pre-filled with the small-Nigerian-MFB triage set",
    value="\n".join(DEFAULT_DOMAINS),
    height=150,
)
run = st.button("Run live scan", type="primary")

with st.expander("How detection levels are assigned (rule criteria)"):
    st.markdown(
        """
**Finding (CVE) detection level:**
- 🟥 **Red** — severity critical/high **and** the CVE match is version-confirmed (exact CPE match).
- 🟨 **Yellow** — severity critical/high but the match is broad/unconfirmed — or severity is medium.
- 🟩 **Green** — severity low, or the service was checked and matched **zero** CVEs (real clean result).
- ⬜ **Not evaluated** — no CPE/version data at all, so no CVE check could run. Never colored green —
  "not checked" is a different claim than "checked and fine."

**Certificate detection level:** red = expired, yellow = expires within 30 days, green = valid >30 days,
not evaluated = no certificate data captured.
        """
    )

if run:
    domains = [d.strip() for d in domains_input.splitlines() if d.strip()]
    config = load_config()
    providers = get_enabled_providers(config)

    if not providers:
        st.error("No providers enabled — check NETLAS_API_KEY / CRIMINALIP_API_KEY / CENSYS_API_KEY in .env.")
        st.stop()

    summary_slot = st.container()
    summary_rows: list[dict] = []

    overall_start = time.monotonic()

    for domain in domains:
        st.divider()
        st.header(domain)
        domain_start = time.monotonic()

        # --- Module 1: discovery, one provider at a time so progress is visible live ---
        result = DiscoveryResult(domain=domain)
        with st.status(f"[{domain}] Running discovery...", expanded=False) as status:
            for provider in providers:
                st.write(f"Querying **{provider.name}**...")
                try:
                    assets = provider.discover(domain)
                except Exception as exc:  # noqa: BLE001 — mirrors m516/discovery.py's own isolation
                    st.warning(f"{provider.name} failed: {exc}")
                    result.errors.append(f"{provider.name}: {exc}")
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

        if result.errors:
            for err in result.errors:
                st.warning(err)

        # --- Module 2: enrichment, one CVE-eligible service at a time, live ---
        findings: list[Finding] = []
        enrichment_errors: list[str] = []
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
                    enrichment_errors.append(f"nvd: {label}: {exc}")
                    continue

                if not matches:
                    st.write(f"{label}: no known CVEs found")
                    continue

                contextual_score, severity, explanation = score_finding(service, asset, matches)
                primary = max(matches, key=lambda m: m.cvss_score or 0)
                findings.append(
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

            findings.sort(key=lambda f: f.contextual_score, reverse=True)
            status.update(
                label=f"[{domain}] Enrichment complete — {len(findings)} finding(s)", state="complete"
            )

        if enrichment_errors:
            for err in enrichment_errors:
                st.warning(err)

        # --- Plain-language summary for this domain ---
        red = sum(1 for f in findings if finding_detection_level(f) == "red")
        yellow = sum(1 for f in findings if finding_detection_level(f) == "yellow")
        green_findings = sum(1 for f in findings if finding_detection_level(f) == "green")
        clean_services = len(eligible) - len(findings)  # checked, zero CVEs
        total_ports = sum(len(a.services) for a in result.assets)
        not_evaluated = total_ports - len(eligible)

        if red:
            st.error(f"**{red} finding(s) need attention** — version-confirmed, high-severity issues.")
        elif yellow:
            st.warning(
                f"**{yellow} finding(s) worth checking** — real signals, but the exact software version "
                "couldn't be confirmed, so verify before treating these as certain."
            )
        elif findings or clean_services:
            st.success("Nothing concerning found — every service we could check came back clean.")
        else:
            st.info(
                f"Not enough data was available to check for known issues — {total_ports} open port(s) "
                "found, but none exposed a confirmable product/version."
            )

        summary_rows.append(
            {
                "Domain": domain,
                "IP(s)": ", ".join(sorted({a.ip for a in result.assets if a.ip})) or "—",
                "WAF/CDN": "Yes" if any(a.is_behind_waf for a in result.assets) else "No",
                "Open ports": total_ports,
                "Red": red,
                "Yellow": yellow,
                "Green (clean)": green_findings + clean_services,
                "Not evaluated": not_evaluated,
            }
        )

        # --- Discovered assets, plain-language first ---
        st.subheader(f"Discovered assets ({len(result.assets)})")
        if not result.assets:
            st.info("No assets discovered for this domain.")
        for asset in result.assets:
            cert_level = cert_detection_level(asset)
            cert_icon, cert_label = _LEVEL_META.get(cert_level, ("⬜", "Not evaluated"))
            st.markdown(
                f"**{asset.ip or '(no IP)'}**"
                + (f" &middot; {asset.hostname}" if asset.hostname else "")
                + f" &middot; country: {asset.country or 'unknown'}"
                + f" &middot; hosted by: {asset.as_name or 'unknown'}"
                + f" &middot; firewall/CDN: {'yes' if asset.is_behind_waf else 'no'}"
                + f" &middot; certificate: {cert_icon} {cert_label}",
                unsafe_allow_html=True,
            )
            st.caption(f"Captured by: {', '.join(sorted(asset.sources)) or 'unknown'}")

            checked = sum(1 for s in asset.services if s.is_cve_eligible)
            risky_unchecked = sum(
                1 for s in asset.services if not s.is_cve_eligible and port_risk_label(s.port, s.protocol)
            )
            st.write(
                f"{len(asset.services)} network door(s) found open on this server; {checked} had enough "
                "detail to check for known issues (see findings below)."
                + (
                    f" **{risky_unchecked}** more couldn't be CVE-checked but are still worth a look based "
                    "on what type of service they are."
                    if risky_unchecked
                    else ""
                )
            )

            simple_rows = []
            for s in asset.services:
                risk = port_risk_label(s.port, s.protocol)
                if s.is_cve_eligible:
                    status = "Yes — see findings below"
                elif risk:
                    status = f"Not CVE-checked — but {risk[0]}"
                else:
                    status = "Not enough data"
                simple_rows.append(
                    {
                        "Service": _friendly_service_name(s.port, s.protocol),
                        "Software": s.product or "Unidentified",
                        "Checked for issues?": status,
                        "Captured by": ", ".join(sorted(s.sources)) or "unknown",
                    }
                )
            if simple_rows:
                st.dataframe(pd.DataFrame(simple_rows), use_container_width=True, hide_index=True)

                with st.expander("Technical detail (raw ports, protocols, CPE, risk category)"):
                    tech_rows = []
                    for s in asset.services:
                        risk = port_risk_label(s.port, s.protocol)
                        tech_rows.append(
                            {
                                "Port": s.port,
                                "Protocol": s.protocol,
                                "Product": s.product or "—",
                                "CPE": s.cpe or "—",
                                "CVE-eligible": s.is_cve_eligible,
                                "Risk category": risk[0] if risk else "—",
                                "Why it matters": risk[1] if risk else "—",
                            }
                        )
                    st.dataframe(pd.DataFrame(tech_rows), use_container_width=True, hide_index=True)

        # --- Findings, plain-language cards ---
        st.subheader(f"Findings, ranked by risk ({len(findings)})")
        if findings:
            for f in findings:
                _render_finding_card(f)
        else:
            st.info("No findings — no CVE-eligible services matched a known CVE.")

        st.caption(f"{domain} completed in {time.monotonic() - domain_start:.1f}s")

    with summary_slot:
        st.subheader("Comparison summary")
        st.caption("Use this to pick a demo target — richest 'Red'/'Yellow' counts on non-WAF hosts.")
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(
            summary_df.style.map(lambda v: "font-weight: 700;" if isinstance(v, int) and v > 0 else "", subset=["Red", "Yellow"]),
            use_container_width=True,
            hide_index=True,
        )

    st.caption(f"All domains completed in {time.monotonic() - overall_start:.1f}s")
