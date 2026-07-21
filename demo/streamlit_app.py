"""Quick throwaway visualization of WP1 (discovery) + WP2 (enrichment) + the post-WP2 detection-level
overlay, working live against real domains. NOT the WP5 React demo UI from docs/22_BUILD_PLAN.md —
that's still a separate, later deliverable. This exists only so the pipeline can be seen working
end-to-end before WP5.

Supports multiple domains at once (one per line) for triage/comparison across candidate targets —
e.g. picking a demo domain by seeing which one actually shows real findings.

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


def _level_css(level: str | None) -> str:
    bg, fg = _LEVEL_STYLE.get(level or "neutral", _LEVEL_STYLE["neutral"])
    return f"background-color: {bg}; color: {fg}; font-weight: 600;"


def _style_level_column(df: pd.DataFrame, column: str) -> "pd.io.formats.style.Styler":
    return df.style.map(_level_css, subset=[column])


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
                findings.append(
                    Finding(
                        asset=asset,
                        service=service,
                        cve_ids=[m.id for m in matches],
                        cvss=max((m.cvss_score or 0) for m in matches),
                        contextual_score=contextual_score,
                        severity=severity,
                        explanation=explanation,
                        match_confidence=matches[0].match_confidence,
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

        # --- Per-domain detail ---
        red = sum(1 for f in findings if finding_detection_level(f) == "red")
        yellow = sum(1 for f in findings if finding_detection_level(f) == "yellow")
        green_findings = sum(1 for f in findings if finding_detection_level(f) == "green")
        clean_services = len(eligible) - len(findings)  # checked, zero CVEs
        not_evaluated = sum(len(a.services) for a in result.assets) - len(eligible)

        summary_rows.append(
            {
                "Domain": domain,
                "IP(s)": ", ".join(sorted({a.ip for a in result.assets if a.ip})) or "—",
                "WAF/CDN": "Yes" if any(a.is_behind_waf for a in result.assets) else "No",
                "Open ports": sum(len(a.services) for a in result.assets),
                "Red": red,
                "Yellow": yellow,
                "Green (clean)": green_findings + clean_services,
                "Not evaluated": not_evaluated,
            }
        )

        st.subheader(f"Discovered assets ({len(result.assets)})")
        if not result.assets:
            st.info("No assets discovered for this domain.")
        for asset in result.assets:
            cert_level = cert_detection_level(asset)
            st.markdown(
                f"**{asset.ip or '(no IP)'}**"
                + (f" &middot; {asset.hostname}" if asset.hostname else "")
                + f" &middot; country: {asset.country or 'unknown'}"
                + f" &middot; WAF/CDN: {'yes' if asset.is_behind_waf else 'no'}"
                + f" &middot; as: {asset.as_name or 'unknown'}",
                unsafe_allow_html=True,
            )
            st.caption(
                f"Asset captured by: {', '.join(sorted(asset.sources)) or 'unknown'}"
                + (f" · cert detection level: {cert_level}" if cert_level else " · cert: not evaluated")
            )

            services_df = pd.DataFrame(
                [
                    {
                        "Port": s.port,
                        "Protocol": s.protocol,
                        "Product": s.product or "—",
                        "CPE": s.cpe or "—",
                        "Captured by": ", ".join(sorted(s.sources)) or "unknown",
                        "CVE-eligible": "Yes" if s.is_cve_eligible else "No",
                    }
                    for s in asset.services
                ]
            )
            if not services_df.empty:
                st.dataframe(services_df, use_container_width=True, hide_index=True)

        st.subheader(f"Findings, ranked by risk ({len(findings)})")
        if findings:
            findings_df = pd.DataFrame(
                [
                    {
                        "Level": finding_detection_level(f),
                        "Severity": f.severity.upper(),
                        "Score": f.contextual_score,
                        "Confidence": f.match_confidence,
                        "Asset": f.asset.ip,
                        "Port": f"{f.service.port}/{f.service.protocol}",
                        "CVSS": f.cvss,
                        "CVE IDs": ", ".join(f.cve_ids[:5]) + (" ..." if len(f.cve_ids) > 5 else ""),
                        "Explanation": f.explanation,
                    }
                    for f in findings
                ]
            )
            st.dataframe(
                _style_level_column(findings_df, "Level"), use_container_width=True, hide_index=True
            )
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
