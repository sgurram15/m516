# 01 · Requirements

> **Status:** Living document · **Version:** 1.0 · **Last updated:** 2026-07
>
> Requirements are the source of truth for *what* the POC must do. If requirements change, update this
> file **first**, then architecture, then code. See `02_ARCHITECTURE.md` for *how*.

---

## 1. Functional Requirements

Grouped by the four pipeline modules plus the demo UI. Each has an ID for traceability.

### FR-1 · Asset & Exposure Discovery
- **FR-1.1** Accept a single domain name as input.
- **FR-1.2** Discover subdomains, IP addresses, and open services via passive data providers.
- **FR-1.3** Capture, per service: port, protocol, product, version, CPE, and banner where available.
- **FR-1.4** Capture, per asset: ASN, AS name, ISP, country, and certificate data.
- **FR-1.5** Flag assets fronted by a CDN/WAF (e.g. Imperva) distinct from origin infrastructure.
- **FR-1.6** Derive whether an asset is locally hosted (Nigerian infra) vs on a global CDN.
- **FR-1.7** Query multiple providers and merge results by IP, recording provenance (which provider(s)).
- **FR-1.8** Never actively scan a target; only query providers' existing indexes. (See NFR-SEC.)

### FR-2 · CVE Enrichment & Risk Scoring
- **FR-2.1** For each discovered service, look up known vulnerabilities via NVD/CVE (by CPE preferred).
- **FR-2.2** Attach CVE IDs and CVSS base scores to each finding.
- **FR-2.3** Compute a contextual risk score via a deterministic rules engine (exposure, port
  sensitivity, staleness) — not an LLM.
- **FR-2.4** Produce a plain-English explanation of each high-risk finding.
- **FR-2.5** Rank findings by contextual risk.

### FR-3 · Compliance Mapping (differentiator)
- **FR-3.1** Ingest and embed the POC regulatory documents (NDPR + CBN Cybersecurity Framework).
- **FR-3.2** For each finding, retrieve the most relevant regulatory clauses (RAG).
- **FR-3.3** Map each finding to specific articles and state a compliance position
  (compliant / partially / non-compliant) with remediation guidance.
- **FR-3.4** Support additional frameworks via configuration (extensible, but only 2 loaded for POC).

### FR-4 · Report Generation
- **FR-4.1** Generate an audit-ready report containing: executive summary, asset inventory, ranked
  findings, compliance gap analysis, remediation roadmap, technical appendix.
- **FR-4.2** Render to PDF and expose a download endpoint.
- **FR-4.3** Report content must be grounded entirely in real scan data (no fabricated findings).

### FR-5 · Demo UI (five screens)
- **FR-5.1** Scan Initiation — enter a domain, start a scan, show live progress.
- **FR-5.2** Dashboard — summary KPIs from the scan.
- **FR-5.3** Asset Discovery — the discovered asset table.
- **FR-5.4** Risk Scoring — ranked findings with exploitation narrative.
- **FR-5.5** Compliance — the framework matrix + PDF export.

---

## 2. Non-Functional Requirements

### NFR-SEC · Security & Legal *(highest priority — see `08_SECURITY.md`)*
- **Strictly passive.** The system must never send active scan traffic to a target's infrastructure.
- Only providers' search/lookup (indexed) endpoints may be used against non-owned domains.
- Client engagements require explicit written authorisation (Nigeria Cybercrimes Act 2015).
- API keys and secrets in environment variables only; never committed.
- Compliance outputs must carry disclaimers and be validated by a qualified professional before reliance.
- No third-party PII processing in the POC (breach data is out of scope).

### NFR-COST · Cost
- POC must run on free API tiers. One optional one-off purchase (Shodan $49) permitted, not required.
- Target running cost during build: ~£150–230/month (LLM usage + one small instance).

### NFR-PERF · Performance
- A single-domain scan should complete within a few minutes (bounded by provider API latency).
- Cache provider responses to avoid burning free-tier quotas on repeated runs.
- No hard throughput target for POC (single-tenant, one scan at a time is acceptable).

### NFR-REL · Reliability
- One provider failing must not fail the whole scan; degrade gracefully and record the error.
- The pipeline must be re-runnable and produce consistent results from the same inputs.

### NFR-MAINT · Maintainability & Extensibility
- Providers are pluggable behind a common interface; adding one is a one-file change.
- Modules are cleanly separated so each could later become an independent service.
- Regulatory frameworks are configuration-driven, not hard-coded.

### NFR-OBS · Observability
- Structured logging of each pipeline stage and each provider call.
- Errors surfaced in the `DiscoveryResult` rather than swallowed.
- (Full monitoring/tracing deferred beyond POC — see stubs.)

### NFR-PORT · Portability / Deployment
- Runs on a single instance; containerised via Docker for reproducibility.
- No Kubernetes, no multi-region for POC.

---

## 3. Out of Scope (with rationale)

| Feature | Why deferred |
|---|---|
| Breach / dark-web monitoring | Needs a separate data pipeline; also raises PII concerns |
| Scheduled / continuous scanning | Not needed to prove the capability; a triggered demo suffices |
| Multi-tenancy, auth, roles | Weeks of secure-auth work with zero demo value |
| White-labelling | Cosmetic; no proof-of-value |
| SIEM / SOC integration | Enterprise plumbing for a later stage |
| Healthcare (NCDC) scope | Different buyer, different regulatory domain |
| Active scanning | Legal risk; the passive model is a deliberate design choice |

---

## 4. Assumptions

- Free-tier provider coverage of Nigerian infrastructure is adequate for the demo domain
  (validated by the coverage test — see `12_DECISION_LOG.md` ADR-004).
- A controlled or explicitly-authorised demo domain will be available to build and demo against.
- A qualified person will validate the NDPR/CBN mappings before any client-facing use.

## 5. Open Requirements Questions

Tracked here until resolved; mirror in `16_SESSION_LOG.md` open questions.

- [ ] Confirm the demo domain (controlled/authorised target).
- [ ] Confirm NDPR + CBN are the two POC frameworks (and NCDC/others deferred).
- [ ] Confirm which providers to enable first (recommend Netlas + Criminal IP).
- [ ] Define "SELM" from the vision doc, or drop it.
- [ ] Confirm who validates compliance-mapping accuracy.
- [ ] Resolve IP-ownership position before further build.
