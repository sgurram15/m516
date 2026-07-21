# 15 · Progress

> **Status:** Living · **READ THIS SECOND (after CLAUDE.md).** The current state at a glance. Update at
> the END of every session alongside `16_SESSION_LOG.md`.

## Current position

**Phase:** WP3 engineering complete (gated externally — see below); WP4 (report generation) built and
live-verified against the real `nigeria-banking` pack.
**Next action:** See top entry of `16_SESSION_LOG.md`.

## Work package status

| WP | Description | Status |
|---|---|---|
| WP0 | Project scaffold | ✅ Done |
| WP1 | Discovery engine + providers | ✅ Done |
| WP2 | CVE enrichment + risk scoring | ✅ Done |
| WP3 | Compliance pack loader + mapping (differentiator) | 🟡 Engineering complete — gated on (a) client's LLM provider choice (asked 2026-07-21, user said not yet decided) and (b) compliance-professional validation of pack content. Neither is code work. |
| WP4 | Report generation (PDF) | ✅ Done — content model + PDF render, live-verified against the real pack |
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
- **WP3 scaffolding started (engine machinery only — real pack content still gated).** Built
  `m516/compliance/{pack_loader,ingest,retrieve,mapper}.py` per `docs/21_COMPLIANCE_PACKS.md`/
  `03_DOMAIN_MODEL.md` §2. Deliberately did **not** draft NDPR/CBN clause content into
  `packs/nigeria-banking/` — that pack "must be complete and real" and validated by a compliance
  professional per the docs themselves; placeholder regulatory content under the real pack name risks
  being mistaken for authoritative material. Instead proved genericity with an obviously-fictional
  `tests/fixtures/packs/test-stub/` pack ("ACME-STD"), per `21_COMPLIANCE_PACKS.md`'s own explicit
  allowance for this. `packs/README.md` explains the pending status.
  - **Embedding:** ChromaDB's default `all-MiniLM-L6-v2` (local, ONNX, no API key — verified current
    behaviour before using it). Retrieval unit is **clauses** (title+summary+finding_hints embedded),
    not raw document text — a deliberate, documented scoping call, not the only valid reading of
    `21_COMPLIANCE_PACKS.md`'s flow.
  - **No LLM wired yet** (client chose to defer). `mapper.map_finding()` always does real retrieval;
    without an `llm_client` it returns honest partial results (`status="unmapped"`, no fabricated
    compliant/non-compliant verdict — BR-5). `LLMClient` is a small `Protocol` so wiring a real provider
    later is additive, not a redesign.
  - **chromadb installed at 1.5.9**, not the originally-planned 0.5.x — 0.5.x's `chroma-hnswlib`
    dependency has no prebuilt Windows/Python-3.12 wheel and needs MSVC build tools this machine doesn't
    have; 1.x ships a prebuilt backend. API re-verified live at 1.5.9 before writing real code against it
    (same discipline as every other provider this project).
  - **Live-verified against real WP2 data**: ingested the stub pack, retrieved clauses for all 19 real
    findings from `mutualtrustmfb.com` — retrieval sensibly matched cPanel findings to "No exposed
    administrative interfaces", FTP to "File transfer credentials...", etc. Every mapping correctly came
    back `status="unmapped"`.
  - `pytest` passes (75/75). First run of the new compliance tests downloads the ONNX embedding model
    (~80MB, one-time) — the only tests in this repo needing network access; every other test stays
    offline/fixture-driven.
- **Real `nigeria-banking` pack authored.** The client placed the actual source documents into
  `regulations/` mid-session (not flagged in advance — discovered via `git status` while staging the
  WP3 scaffolding commit). Verified both by full read before acting on them:
  - `NDPR-Implementation-Framework.pdf` — genuine NITDA "Nigeria Data Protection Regulation 2019:
    Implementation Framework" (November 2020, signed DG Kashifu Inuwa Abdullahi).
  - `risk based cybersecurity framework final.pdf` — genuine CBN "Risk-Based Cybersecurity Framework
    and Guidelines for Deposit Money Banks and Payment Service Providers" (circular
    BSD/DIR/GEN/LAB/11/25, October 2018, effective January 1, 2019).
  - User confirmed (via explicit question, not assumed): author the real pack now, and commit the
    source PDFs — they're publicly issued by NITDA/CBN for compliance guidance, no confidentiality
    markings.
  - Built `packs/nigeria-banking/{pack.yaml, frameworks/{ndpr,cbn}.yaml, documents/*.pdf}` per
    `docs/21_COMPLIANCE_PACKS.md`'s layout. **9 NDPR clauses + 12 CBN clauses**, every `ref`/`title`/
    `summary` cites a real article/section re-read directly from the source PDFs (e.g. "NDPR Art. 4.1(5)
    — Annual data protection audit", "CBN Appendix IV §6 — Patch management and penetration testing") —
    none fabricated from memory. `finding_hints` chosen for relevance to passive attack-surface findings
    (exposed/unpatched services, admin panels, default credentials, breach/incident timelines, DPO/CISO
    governance gaps).
  - **Not yet done:** compliance-professional validation of the clause selection (`packs/README.md` and
    `21_COMPLIANCE_PACKS.md`'s validation note both flag this explicitly — don't let a client rely on
    the mapping output before that review happens).
  - Live-verified: pack loads (`load_pack`), ingests (21 clauses in the ChromaDB collection), and
    retrieval ranks sensibly — an exposed-cPanel-with-default-credentials finding correctly ranks
    "CBN Appendix IV §1 (Access Control)" first; CVE-bearing findings rank CBN's vulnerability-management/
    patch clauses highest. New `tests/test_nigeria_banking_pack.py` (4 tests) locks in pack structure and
    one retrieval-ranking case. `pytest` passes (79/79).

- **WP4 · Report generation.** Built `m516/report/{template,render}.py` per `22_BUILD_PLAN.md` FR-4.
  `template.py` assembles a pack-agnostic `ReportData` (asset inventory, ranked findings, compliance
  gap analysis grouped by clause, remediation roadmap, executive summary) purely from real pipeline
  output (`DiscoveryResult`, `Finding[]`, optional `CompliancePack`) — no LLM narrative, since none is
  wired (same honest-partial stance as `mapper.py`; BR-5, no fabrication). The executive summary and
  compliance-gap text are templated from computed counts, and explicitly say when clause references are
  "candidates only" because no LLM classifier is configured, rather than implying a verdict that wasn't
  made. `render.py` lays this out as a PDF via **reportlab 5.0.0** (pure-Python wheel, no MSVC/system
  toolchain needed — checked before adopting, same discipline as the chromadb pick below) — title page
  with disclaimer, executive summary, asset inventory table, ranked findings table (severity
  colour-coded), compliance gap table (status colour-coded), remediation roadmap, technical appendix.
  Report is addressed via `pack.report_labels` (`report_title`, `primary_regulator`) when a pack is
  passed — no hard-coded framework/country name in this module (golden rule).
  - **Live-verified against the real `nigeria-banking` pack** (not just the test-stub): built two
    representative findings (exposed cPanel, outdated ProFTPD), ran real retrieval (`map_finding` with
    `llm_client=None`) against the real pack, rendered a real PDF, and extracted its text with `pypdf` to
    confirm content — CBN clause refs/titles (e.g. "CBN §5.6 — 24-hour cyber-incident reporting", "CBN
    Appendix IV §2 — Secure System Configuration Management") render correctly in the actual PDF. (A
    console printout of the same data showed `�` for `§` — that was a PowerShell codepage artifact, not
    a bug; the PDF text itself, and the pack YAML on disk, are correct UTF-8.)
  - `pypdf==6.14.2` added as a dependency — used by `tests/test_report_render.py` to assert on real
    extracted PDF text rather than just "a file exists", same "no engine code should merely subsist on
    a mock" instinct as the rest of this project's test suite.
  - `pytest` passes (87/87, +8 new: `test_report_template.py`, `test_report_render.py`).

## In progress

- WP3: pack content authored and engine-verified; still needs (a) compliance-professional validation of
  clause content before client reliance, and (b) an LLM wired into `mapper.py`'s classification step
  (`llm_client` parameter is ready). **Asked the client directly this session (2026-07-21) which LLM
  provider to use — answer: not decided yet, revisit later.** Nothing further to build here until either
  gate clears.
- WP4: report generation is functionally complete against current data (compliance sections will read
  "unmapped"/candidate-only until WP3's LLM step is wired — this is intentional, not a WP4 gap). No API
  endpoint to trigger report generation yet — that's WP5 (`m516/api/**`).

## Blocked / gating decisions (resolve with client)

- [ ] Confirm demo domain (small Nigerian bank or safe proxy) — **`mutualtrustmfb.com` recommended**
  based on the 6-domain triage (richest real exposure, single unambiguous domain). See Completed above.
- [x] Obtain/confirm NDPR + CBN source documents — done: real documents received, verified genuine, and
  used to author `packs/nigeria-banking/`. See Completed above.
- [x] Confirm first providers to wire live — done: Netlas + Criminal IP + InternetDB, all live-verified.
- [ ] Agree who validates compliance mappings — pack content is authored but not yet reviewed by a
  qualified compliance professional (see Completed above).
- [ ] Confirm IP-ownership position (SOW §12).
- [ ] Choose an LLM provider for the compliance-mapping step (Anthropic recommended; asked client
  directly 2026-07-21, still not decided — revisit later, not blocking other work).

## Metrics

| Metric | Value |
|---|---|
| WPs complete | 4 of 6 (WP3 engineering-complete but gated externally; WP4 done) |
| Modules built | 4 of 4 (discovery, enrichment, compliance, report) — LLM classification step and API/UI remain |
| Providers live | 4 (Netlas, Criminal IP, Censys, InternetDB) |
| Frameworks ingested | 2 of 2 (real: NDPR + CBN) — plus 1 fictional test-stub framework for genericity proof |
| Packs authored | 1 of 1 (`nigeria-banking`) — plus 1 test-stub pack for genericity proof |
| Tests passing | 87 |

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
