"""Quick throwaway visualization of WP1 (discovery) + WP2 (enrichment) working live against a real
domain. NOT the WP5 React demo UI from docs/22_BUILD_PLAN.md — that's still a separate, later
deliverable. This exists only so the pipeline can be seen working end-to-end before WP5.

Run from the project root: streamlit run demo/streamlit_app.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from m516.config import load_config
from m516.enrichment.nvd import lookup_cves
from m516.enrichment.scoring import score_finding
from m516.findings import Finding
from m516.models import DiscoveryResult
from m516.providers.base import detect_waf
from m516.providers.registry import get_enabled_providers

st.set_page_config(page_title="M516 Live Scan Demo", layout="wide")

st.title("M516 — Live Scan Demo")
st.caption(
    "Dev visualization of WP1 (discovery) + WP2 (CVE enrichment) working against real, live provider "
    "data. Strictly passive lookups only (ADR-001) — never touches the target domain directly."
)

domain = st.text_input("Domain", value="nitda.gov.ng")
run = st.button("Run live scan", type="primary")

if run:
    config = load_config()
    providers = get_enabled_providers(config)

    if not providers:
        st.error("No providers enabled — check NETLAS_API_KEY / CRIMINALIP_API_KEY in .env.")
        st.stop()

    start = time.monotonic()

    # --- Module 1: discovery, one provider at a time so progress is visible live ---
    result = DiscoveryResult(domain=domain)
    with st.status("Running discovery...", expanded=True) as status:
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
            label=f"Discovery complete — {len(result.assets)} merged asset(s)", state="complete"
        )

    st.subheader(f"Discovered assets ({len(result.assets)})")
    if result.assets:
        st.dataframe(
            [
                {
                    "IP": asset.ip,
                    "Hostname": asset.hostname,
                    "Country": asset.country,
                    "Behind WAF": asset.is_behind_waf,
                    "Sources": ", ".join(sorted(asset.sources)),
                    "Open ports": ", ".join(
                        f"{s.port}/{s.protocol}" + (f" ({s.version_string})" if s.version_string else "")
                        for s in asset.services
                    ),
                    "Cert subject": asset.cert_subject,
                    "Cert expired": asset.cert_is_expired,
                }
                for asset in result.assets
            ],
            use_container_width=True,
        )
    else:
        st.info("No assets discovered for this domain.")

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
        f"Running CVE enrichment (NVD) on {len(eligible)} eligible service(s)...", expanded=True
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
                )
            )
            st.write(f"{label}: {len(matches)} CVE(s) found — scored {contextual_score} ({severity})")

        findings.sort(key=lambda f: f.contextual_score, reverse=True)
        status.update(label=f"Enrichment complete — {len(findings)} finding(s)", state="complete")

    st.subheader(f"Findings, ranked by risk ({len(findings)})")
    if findings:
        st.dataframe(
            [
                {
                    "Severity": f.severity.upper(),
                    "Score": f.contextual_score,
                    "Asset": f.asset.ip,
                    "Port": f"{f.service.port}/{f.service.protocol}",
                    "CVSS": f.cvss,
                    "CVE IDs": ", ".join(f.cve_ids[:5]) + (" ..." if len(f.cve_ids) > 5 else ""),
                    "Explanation": f.explanation,
                }
                for f in findings
            ],
            use_container_width=True,
        )
    else:
        st.info("No findings — no CVE-eligible services matched a known CVE.")

    if enrichment_errors:
        for err in enrichment_errors:
            st.warning(err)

    st.caption(f"Scan completed in {time.monotonic() - start:.1f}s")
