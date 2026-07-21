# 15 · Progress

> **Status:** Living · **READ THIS SECOND (after CLAUDE.md).** The current state at a glance. Update at
> the END of every session alongside `16_SESSION_LOG.md`.

## Current position

**Phase:** WP2 complete → ready to start **WP3 (compliance pack loader + mapping)**.
**Next action:** See top entry of `16_SESSION_LOG.md`.

## Work package status

| WP | Description | Status |
|---|---|---|
| WP0 | Project scaffold | ✅ Done |
| WP1 | Discovery engine + providers | ✅ Done |
| WP2 | CVE enrichment + risk scoring | ✅ Done |
| WP3 | Compliance pack loader + mapping (differentiator) | ⬜ Not started |
| WP4 | Report generation (PDF) | ⬜ Not started |
| WP5 | API + demo UI | ⬜ Not started |

Legend: ✅ done · 🟡 in progress · ⬜ not started · 🔴 blocked

## Completed (pre-build)

- **Coverage test.** Passive lookups vs gtbank.com (Tier-1 bank), interswitchgroup.com (payments),
  nitda.gov.ng (government). Finding: Tier-1 banks WAF-hidden (little origin exposure); government/local
  targets on MainOne reveal real CVE-mappable findings (exposed MailEnable 10.57, expired TLS cert,
  WordPress stack). → ADR-004; demo should target government/mid-tier-style domain.
- **Documentation set + CLAUDE.md.** Full project memory authored (this set). Engine+pack architecture
  decided (ADR-009), tenant-aware model (ADR-010), InternetDB provider (ADR-011), pack format (ADR-012).
- **WP0 · Project scaffold.** `m516/` package (`config.py`, `logging.py`, `__main__.py`), `tests/`
  with passing smoke tests, `.env.example`, `.gitignore`, `requirements.txt`. `pytest` passes (4/4);
  `python -m m516 --help` works. Git repo initialised. Docs moved into `docs/` to match documented
  paths; `docs/18_REPOSITORY_STRUCTURE.md` created.
- **WP1 · Discovery engine + providers.** `m516/models.py` (`Service`/`Asset`/`DiscoveryResult` per
  domain model), `m516/providers/{base,cache,dns_resolve,netlas,criminalip,internetdb,registry}.py`,
  `m516/discovery.py` orchestrator (merge-by-IP, WAF detection, per-provider error isolation).
  Netlas + Criminal IP wired live with real API keys; InternetDB needs none. `pytest` passes (24/24,
  fixture-driven, no network). Verified end-to-end against a real live call (`nitda.gov.ng`, ADR-004's
  domain) — see note below on what changed since ADR-004 was written.
- **WP2 · CVE enrichment + risk scoring.** `m516/enrichment/{nvd,scoring}.py`, `m516/findings.py`
  (`Finding`, `build_findings`). NVD lookup routes `cpeName` (exact) vs `virtualMatchString` (broad,
  for wildcarded CPEs) vs `keywordSearch` (no CPE) based on what the service actually has. Deterministic
  scoring: CVSS base ×10, × port-sensitivity multiplier, × WAF-exposure multiplier, + staleness bonus for
  CVEs known >2 years (ADR-007/BR-3: no LLM). `pytest` passes (43/43). Live-verified end-to-end (Log4j
  CPE → 10 real CVEs → CVE-2021-44228 picked as primary → contextual_score 100/critical with a correct
  plain-English explanation).
- **Refactor: `m516/providers/cache.py` → `m516/cache.py`.** Same generic disk cache, moved to shared
  infra now that both discovery providers and NVD enrichment use it — keeps `07_BACKEND_ARCHITECTURE.md`
  §2's "no module imports a sibling module's internals" rule honoured as a second module started reusing
  Module 1's cache.
- **Post-WP2 extension (user-requested, not a new WP): Censys + provenance + detection levels.**
  Extended already-shipped WP1/WP2 code rather than starting WP3 early:
  - `m516/providers/censys.py` — 4th provider, live-verified. Censys's free tier **cannot** use the
    domain-search endpoint (403, paid-only: "Free users can only access this endpoint through the
    Platform UI") but the direct host-lookup-by-IP endpoint works and returned the richest per-service
    data of any provider so far (independently confirmed Netlas's nginx finding, plus ProFTPD/Postfix/
    Dovecot/Plesk that Netlas didn't surface for the same host). Same domain→IP self-resolution pattern
    as InternetDB.
  - `Service.sources` (new field, mirrors `Asset.sources`) — WP1 only tracked provenance at the asset
    level; "which API captured this specific port" needed service-level tracking. All 4 adapters now
    tag it; `DiscoveryResult._merge_into` now unions sources and backfills missing service fields on a
    port collision instead of silently dropping the second provider's data.
  - **Correctness fix found via this extension, not before:** the naive service-field backfill let one
    provider's `cpe` get grafted onto a *different* provider's `product` label when they disagreed on
    what was actually running on a port (observed live: one provider said "Fathom", another's CPE was
    for "Caddy" — an unrelated product — on the same port of `abmfbnigeria.com`). Fixed
    `_merge_service_into` to only combine `version`/`cpe`/`banner` across providers when they *agree* on
    the product name; a genuine disagreement is now left un-combined rather than fabricating a coherent-
    looking but false finding (BR-5). Regression test added.
  - `CVEMatch.match_confidence` / `Finding.match_confidence` ("exact" vs "broad") — makes the
    version-confirmed-vs-not distinction (previously only expressed ad hoc in a hand-written report) a
    real field. `scoring._explain()` now appends the verification caveat automatically for broad matches.
  - `m516/enrichment/detection_level.py` (new) — deterministic red/yellow/green rules for findings and
    certificate status; full criteria documented in the module docstring. Pure functions, fully tested,
    no LLM (ADR-007).
  - Ran live against 2 real small-bank domains for the user's own understanding (not client-facing —
    output stayed a local file, not published). Result: both came back with **zero CVE-eligible
    services** after the attribution fix — neither exposed enough fingerprintable version/CPE data for a
    responsible NVD match. That's a "not evaluated" data-availability result, not a "green/clean" one;
    the provenance tracking and the Caddy/Fathom catch were the actual value of that run.
  - `pytest` passes (60/60).
- **6-domain MFB triage + `demo/streamlit_app.py` overhaul.** User supplied a list of 10 real CBN-
  licensed Nigerian microfinance banks; verified domains via search + content fetch (one of the user's
  guessed domains, `finatrustbank.com`, was wrong — real domain is `finatrustmfbank.com`, Cloudflare-
  fronted, with a second live LOLC-branded site at `finatrustlolcmfbank.com` that isn't). Ran the passive
  pipeline against 6 verified domains. Result: `finatrustlolcmfbank.com` and `mutualtrustmfb.com` (both
  on generic US shared/cPanel hosting, no WAF) showed rich exposure — 15-22 open ports each including
  FTP, raw mail ports, MariaDB, and cPanel admin panels — while the Cloudflare-fronted Fina Trust domain
  and 3 others showed little to nothing. **Recommended demo target: `mutualtrustmfb.com`.** Streamlit app
  extended to take multiple domains (one per line) with a colored red/yellow/green comparison table for
  exactly this kind of triage, and rewritten so findings/services render as plain-language cards+summary
  banners instead of raw dataframes (CVE IDs/CPE strings moved into "Technical details" expanders).
- **CVSS sub-scores + port-risk labels, informed by 3 UI mockups (`ui screens/*.jpg`).** User provided
  Asset Discovery / Port Scanner / Risk Scoring mockups. Two real gaps closed: `CVEMatch`/`Finding` now
  carry `exploitability_score`/`impact_score` (NVD already returns these as siblings of `cvssData` — we
  were calling the API and not parsing them); new `m516/enrichment/port_risk.py` gives a deterministic,
  CVE-independent risk label per port type (SSH → "Weak Authentication", exposed DB ports → "Open
  Database", etc.) — usable even for the "not evaluated" services that have no CVE data at all, which is
  exactly the gap it closes. Both wired into the Streamlit demo. `pytest` passes (64/64). **Two scope
  conflicts flagged** (see Notes below): the mockups include a "Breach Monitor" and "Users & Roles"
  sidebar item, both explicitly out of scope per `01_REQUIREMENTS.md` — **client confirmed 2026-07-21:
  neither is being built for the POC**, resolving both. The "Port Scanner" name/"Scan Date" label reading
  as active scanning (engine is strictly passive, ADR-001) is still open, not yet raised with the client.

## In progress

- Nothing in active build yet. Awaiting start of WP3.

## Blocked / gating decisions (resolve with client)

- [ ] Confirm demo domain (small Nigerian bank or safe proxy) — **`mutualtrustmfb.com` recommended**
  based on the 6-domain triage (richest real exposure, single unambiguous domain). See Completed above.
- [ ] Obtain/confirm NDPR + CBN source documents (needed for WP3).
- [x] Confirm first providers to wire live — done: Netlas + Criminal IP + InternetDB, all live-verified.
- [ ] Agree who validates compliance mappings.
- [ ] Confirm IP-ownership position (SOW §12).

## Metrics

| Metric | Value |
|---|---|
| WPs complete | 3 of 6 |
| Modules built | 2 of 4 |
| Providers live | 4 (Netlas, Criminal IP, Censys, InternetDB) |
| Frameworks ingested | 0 of 2 |
| Packs authored | 0 of 1 (`nigeria-banking`) |
| Tests passing | 64 |

## Notes

- The earlier throwaway Module 1 prototype (from a prior exploratory session) is NOT in this repo; WP1
  rebuilt it cleanly against these docs, not reused. Don't assume prior code exists — build per
  `22_BUILD_PLAN.md`.
- **ADR-004's `nitda.gov.ng` finding may be stale.** A live WP1 verification call (2026-07-21) against
  `nitda.gov.ng` via Netlas returned nginx on port 80 only — no MailEnable, no certificate data (current
  Netlas plan/dataset didn't return `asn`/`net`/`certificate` fields for a domain-type query on this
  host, unlike what the original coverage test reported). Infra may have changed since ADR-004, or
  richer IP-level data needs a different query shape/plan tier. **Don't assume `nitda.gov.ng` still
  demonstrates the MailEnable/expired-cert finding — re-validate before using it in a client demo.**
- **Adapter design note (found during live verification, not from provider docs):** actual Netlas
  domain-type responses nest product/version under `software[].tag[]` (keyed to a port only via the
  item's `uri`, not a direct field) and Criminal IP's `domain/reports` technologies carry no port,
  version, or IP at all — `m516/providers/criminalip.py` resolves domain→IP itself (like InternetDB)
  and assumes port 80/tcp for its HTTP-fingerprinted tech stack. See file docstrings for detail.
- **WP2 scoring-formula assumption (FR-2.3 doesn't define this precisely).** "Staleness" is interpreted
  as: the matched CVE has been publicly known for >2 years and the service is still exposed — treated as
  a proxy for poor patch hygiene, not CVE age alone. "Exposure" is interpreted narrowly as WAF/CDN
  presence (`is_behind_waf`), not `is_locally_hosted`, since the latter needs a pack's `home_country`
  and no pack is loaded until WP3. If the client has a specific scoring methodology in mind, revisit
  `m516/enrichment/scoring.py` — the formula is isolated in one pure function specifically so it's easy
  to swap without touching NVD lookup or orchestration code.
- **UI mockups vs `01_REQUIREMENTS.md` — resolved 2026-07-21.** The 3 mockups in `ui screens/` (informing
  `06_FRONTEND_ARCHITECTURE.md`, not yet authored) surfaced three conflicts with existing scope:
  1. ✅ **Resolved — descoped.** A **"Breach Monitor"** sidebar item — client confirmed: **not building
     Breach Monitor for the POC.** Matches `01_REQUIREMENTS.md`'s existing exclusion ("needs a separate
     data pipeline; also raises PII concerns") — the mockup was wrong on this point, not the requirements
     doc. When WP5 frontend work starts against these mockups, drop this sidebar item.
  2. ✅ **Resolved — descoped.** A **"Users & Roles"** sidebar item — client confirmed: **not building
     Users & Roles for the POC.** Matches `01_REQUIREMENTS.md`'s existing exclusion and ADR-010
     (tenant-aware model, no auth built — "weeks of secure-auth work with zero demo value"). Drop this
     sidebar item too when WP5 frontend work starts.
  3. ⬜ **Still open.** The mockup screen is named **"Port Scanner"** with a "Scan Date" filter — reads
     as active scanning. The engine is strictly passive (ADR-001) and has no scan/rescan feature at all;
     if this mockup becomes the real WP5 frontend spec, the labeling should say "Port Findings" or
     similar, not "Scanner", to avoid implying active probing to a client. Not yet raised with the client.
