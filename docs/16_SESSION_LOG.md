# 16 · Session Log

> **Status:** Living · **The continuity backbone.** Every session appends an entry at the TOP. A fresh
> session reads CLAUDE.md → 15_PROGRESS.md → this top entry, and can continue with NO chat history.
> Template at the bottom.

---

## Session 006 — 2026-07-21 — MFB triage, Streamlit overhaul, mockup-informed engine additions

- **Objective:** Three follow-on asks in one continuous session after Session 005: (1) triage a list of
  10 real CBN-licensed Nigerian microfinance banks the user provided, to pick a demo domain; (2) do that
  analysis via the Streamlit demo instead of ad hoc scripts, and make it non-technical-readable; (3)
  incorporate 3 UI mockups the user placed in `ui screens/` to close real data gaps.
- **Files changed:** `demo/streamlit_app.py` (multi-domain input + comparison table; full rewrite of
  findings/services from raw dataframes to plain-language cards/summaries; port-risk-label column; CVSS
  sub-score display); `demo/requirements.txt` (+pandas); `m516/enrichment/nvd.py` (`CVEMatch.
  exploitability_score`/`impact_score`); `m516/enrichment/port_risk.py` (new); `m516/findings.py`
  (`Finding.exploitability_score`/`impact_score`); tests extended in `test_nvd.py`/`test_findings.py`;
  new `test_port_risk.py`.
- **Design/architecture changes:** None architectural. Port-risk labels follow `detection_level.py`'s
  established pattern (deterministic, no LLM, "no informed opinion → None, never fabricate"). CVSS
  sub-scores are display-only — `scoring.py`'s formula untouched. `findings.py` and the Streamlit script
  both locally recompute the primary (highest-CVSS) match to pull sub-scores, matching the existing
  `cvss=max(...)` duplication pattern rather than widening `score_finding()`'s return contract.
- **New decisions:** None architectural (no new ADR). Three conflicts between the UI mockups and
  `01_REQUIREMENTS.md` were flagged; client resolved two same-session: **confirmed not building Breach
  Monitor or Users & Roles for the POC** — both mockup sidebar items get dropped when WP5 frontend work
  starts, and `01_REQUIREMENTS.md`'s existing exclusions stand as correct (the mockups were wrong, not
  the requirements doc). The "Port Scanner" naming/passive-vs-active concern is still open.
- **Pending work:** WP3 (compliance pack loader + mapping) still not started — this whole session was
  another detour, not a WP, same as Session 005. **Demo domain recommendation now exists**:
  `mutualtrustmfb.com` (richest real exposure found across 6 verified bank domains — 22 open ports,
  FTP/mail/database/cPanel admin panels directly exposed, no WAF) — still needs the user's actual sign-off
  as the gating decision, but it's no longer a cold open question.
- **Next session starting point (SINGLE NEXT ACTION):** Begin **WP3 · Compliance pack loader + mapping**
  per `22_BUILD_PLAN.md` (same next action as Sessions 004/005 — still not started). Still needs
  NDPR/CBN source documents (open gating decision) before real mapping can be validated.
- **Context summary (rehydrate):** M516 = passive attack-surface + compliance-mapping platform. Modules
  1 (discovery, 4 providers) and 2 (enrichment, now with CVSS sub-scores + confidence tracking) are
  built and live-verified. `demo/streamlit_app.py` is a real, working multi-domain triage tool with
  plain-language output and a red/yellow/green comparison view — useful for picking/demoing targets, not
  the WP5 React UI. `m516/enrichment/port_risk.py` gives CVE-independent risk signal for services with
  no version data. Golden rule and passive-only constraint unchanged throughout.
- **Open questions:** NDPR/CBN source docs (still blocking real WP3 start)? Who validates mappings? IP
  ownership? Does the user want to formally confirm `mutualtrustmfb.com` as the demo domain? How should
  the "Port Scanner" naming (passive engine, active-sounding label) be resolved before WP5? (Breach
  Monitor / Users & Roles — resolved same session, see New decisions above; no longer open.)

---

## Session 005 — 2026-07-21 — Post-WP2: Censys + service provenance + detection levels

- **Objective:** User-requested extension (not a new WP): wire up a newly-provided `CENSYS_API_KEY`,
  add red/yellow/green "detection level" classification with explainable rules, track which API
  captured each piece of data, and run the result against 2 real small-bank domains for the user's own
  understanding (explicitly not client-facing this time).
- **Files changed:** `m516/providers/censys.py` (new, 4th provider); `m516/models.py` (`Service.sources`,
  merge-logic fix); `m516/providers/{netlas,criminalip,internetdb}.py` (tag `Service.sources`);
  `m516/providers/registry.py` (censys entry); `m516/config.py` + `.env.example` (`CENSYS_API_KEY`);
  `m516/enrichment/nvd.py` (`CVEMatch.match_confidence`, `_build_query` now returns confidence too);
  `m516/enrichment/scoring.py` (`_explain()` appends broad-match caveat); `m516/findings.py`
  (`Finding.match_confidence`); `m516/enrichment/detection_level.py` (new). Tests extended across
  `test_models.py`, `test_providers.py`, `test_nvd.py`, `test_scoring.py`, `test_findings.py`; new
  `test_detection_level.py`. `tests/fixtures/censys_host.json` added.
- **Design/architecture changes:** See `15_PROGRESS.md`'s "Post-WP2 extension" entry for full detail.
  Headline: Censys free tier can only use direct host-lookup-by-IP, not domain search (403 on the
  latter, confirmed live). Service-level provenance was a real gap in WP1 (BR-6 was only honoured at
  asset level), not scope creep. **A real correctness bug was found and fixed during this work**: naive
  field-backfill on merge let one provider's CPE get grafted onto a different provider's product label
  when they disagreed on what was running on a port — fixed to only combine fields when providers agree
  on the product (BR-5, no fabrication).
- **New decisions:** None architectural (no new ADR) — this extends already-decided patterns
  (ADR-002 provider-agnostic, ADR-007 deterministic scoring). The detection-level rule criteria are
  documented in `m516/enrichment/detection_level.py`'s docstring, not a formal ADR, since they're a
  presentation overlay on existing severity/confidence data, not a new business rule.
- **Pending work:** WP3 (compliance pack loader + mapping) not started — still the actual next WP.
  Gating decisions unchanged and still open.
- **Next session starting point (SINGLE NEXT ACTION):** Begin **WP3 · Compliance pack loader +
  mapping** per `22_BUILD_PLAN.md` (same next action as Session 004 — this session was a detour, not a
  WP). Needs NDPR/CBN source documents before real mapping can be validated.
- **Context summary (rehydrate):** M516 = passive attack-surface + compliance-mapping platform. Modules
  1 (discovery, now 4 providers) and 2 (enrichment) are built, live-verified, and now also produce
  per-service provenance and a red/yellow/green detection-level overlay. Golden rule and passive-only
  constraint unchanged. WP3 (compliance pack) is still the next real work package.
- **Open questions:** demo domain? NDPR/CBN source docs? who validates mappings? IP ownership? (All
  unchanged from Session 004 — this session didn't resolve any of them, by design.)

---

## Session 004 — 2026-07-21 — WP2: CVE enrichment + risk scoring

- **Objective:** Execute WP2 per `22_BUILD_PLAN.md` — services → CVEs (NVD by CPE) + CVSS +
  deterministic contextual score → ranked `Finding[]`, rules-based and explainable, never an LLM
  (ADR-007, BR-3).
- **Files changed:** Added `m516/enrichment/{nvd,scoring}.py`, `m516/findings.py`
  (`Finding`, `build_findings`), `tests/{test_nvd,test_scoring,test_findings}.py` +
  `tests/fixtures/nvd_*.json`. Added `nvd_api_key` to `m516/config.py`, documented `NVD_API_KEY` in
  `.env.example`. **Refactor:** moved `m516/providers/cache.py` → `m516/cache.py` (shared infra now
  that NVD enrichment also needs it); updated 3 import sites + `test_providers.py`.
- **Design/architecture changes:** NVD lookup routes to `cpeName` (exact), `virtualMatchString`
  (broad — used when the CPE is wildcarded, as ours often are), or `keywordSearch` (no CPE, only a
  version string) based on what's actually available, confirmed against live NVD responses. Scoring
  formula lives in one pure function (`scoring.score_finding`) deliberately isolated from HTTP/orchestration
  so it's easy to swap if the client has a different methodology in mind.
- **New decisions:** None architectural (implements already-decided ADR-006/007, no new ADR). Two
  documented assumptions since `01_REQUIREMENTS.md` FR-2.3 doesn't define "exposure"/"staleness"
  precisely — see `15_PROGRESS.md` Notes: exposure = WAF/CDN presence only (not `is_locally_hosted`,
  which needs a pack not loaded until WP3); staleness = CVE known >2 years while still exposed.
- **Pending work:** WP3 (compliance pack loader + mapping) not started. Gating decisions in
  `15_PROGRESS.md` unchanged and still open (demo domain, NDPR/CBN source docs, mapping validator,
  IP-ownership position).
- **Next session starting point (SINGLE NEXT ACTION):** Begin **WP3 · Compliance pack loader +
  mapping** per `22_BUILD_PLAN.md` — `m516/compliance/{pack_loader,ingest,retrieve,mapper}.py`,
  `packs/nigeria-banking/**`. This is the differentiator module and needs NDPR + CBN source documents
  (still an open gating decision) before real mapping can be validated — flag this to the client before
  going deep on WP3. Engine must stay generic (golden rule) — the pack interface is already specified
  in `docs/03_DOMAIN_MODEL.md` §2.
- **Context summary (rehydrate):** M516 = passive attack-surface + compliance-mapping platform. POC for
  a paying client, target = small Nigerian banks, frameworks NDPR+CBN. Pipeline: discovery → CVE
  enrichment → compliance mapping (pack-driven) → report. **Golden rule:** engine is universal, all
  NG/CBN/banking knowledge lives in the `nigeria-banking` compliance pack. Strictly passive. Free-tier.
  Modules 1 (discovery) and 2 (enrichment) are now built and live-verified. WP3 is the first module to
  touch ChromaDB/RAG/LLM and the first pack-specific content.
- **Open questions:** demo domain (unresolved, and `nitda.gov.ng`'s previously-documented finding may
  no longer hold — see Session 003)? NDPR/CBN source docs (now blocking, needed to start WP3 for real)?
  who validates mappings? IP ownership?

---

## Session 003 — 2026-07-21 — WP1: Discovery engine + providers

- **Objective:** Execute WP1 per `22_BUILD_PLAN.md` — domain → normalised `DiscoveryResult` via
  multiple passive providers, merged by IP, one provider failing never fatal.
- **Files changed:** Added `m516/models.py` (`Service`, `Asset`, `DiscoveryResult`);
  `m516/providers/{base,cache,dns_resolve,netlas,criminalip,internetdb,registry}.py`;
  `m516/discovery.py`; `tests/{test_models,test_providers,test_discovery}.py` +
  `tests/fixtures/*.json`. Added `cache_ttl_seconds` to `m516/config.py`. Added `requests` to
  `requirements.txt`.
- **Design/architecture changes:** Uniform `BaseProvider.discover(domain) -> list[Asset]` interface for
  all three providers — InternetDB and Criminal IP both do their own passive DNS resolution internally
  (`m516/providers/dns_resolve.py`) rather than being special-cased in the orchestrator, since neither
  API returns an IP directly for a domain query. WAF detection (`detect_waf`) is a shared post-merge
  step in `discovery.py`, not per-adapter. Disk cache under `.cache/` keyed by `(provider, identifier)`
  with a TTL (`CACHE_TTL_SECONDS`, default 24h).
- **New decisions:** None architectural (no new ADR) — this is WP1 implementing already-decided
  ADR-002/004/011, not a new decision. Two non-architectural but important **discoveries during live
  verification**, logged in `15_PROGRESS.md` Notes:
  1. Netlas's and Criminal IP's real response shapes differ meaningfully from their public docs (see
     `m516/providers/netlas.py` and `criminalip.py` docstrings) — adapters were corrected against live
     data, not left matching the docs.
  2. `nitda.gov.ng` (ADR-004's example finding: MailEnable/expired cert) no longer shows that surface
     via Netlas as of 2026-07-21 — only nginx on port 80, no cert data returned. Flagged as needing
     re-validation before any client demo references it.
- **Pending work:** WP2 (CVE enrichment + risk scoring) not started. Gating decisions in
  `15_PROGRESS.md` (demo domain — now more urgent given the `nitda.gov.ng` staleness finding, NDPR/CBN
  source docs, mapping validator, IP-ownership position) remain unresolved.
- **Next session starting point (SINGLE NEXT ACTION):** Begin **WP2 · CVE enrichment + risk scoring**
  per `22_BUILD_PLAN.md` — `m516/enrichment/{nvd,scoring}.py`, `m516/findings.py`. NVD lookup by CPE
  (BR-2: a service needs `version_string` or `cpe` to be CVE-eligible — `Service.is_cve_eligible`
  already exists in `models.py` for this). Scoring must be a deterministic rules engine, never an LLM
  (ADR-007, BR-3).
- **Context summary (rehydrate):** M516 = passive attack-surface + compliance-mapping platform. POC for
  a paying client, target = small Nigerian banks, frameworks NDPR+CBN. Pipeline: discovery → CVE
  enrichment → compliance mapping (pack-driven) → report. **Golden rule:** engine is universal, all
  NG/CBN/banking knowledge lives in the `nigeria-banking` compliance pack. Strictly passive. Free-tier.
  Module 1 (discovery) is now built and live-verified — real Netlas/Criminal IP keys are in the
  git-ignored `.env`. WP2 is the first module to touch NVD/CVE data.
- **Open questions:** demo domain (now with added urgency — `nitda.gov.ng`'s previously-documented
  finding may no longer hold)? NDPR/CBN source docs? who validates mappings? IP ownership?

---

## Session 002 — 2026-07-21 — WP0: Project scaffold

- **Objective:** Execute WP0 per `22_BUILD_PLAN.md` — runnable skeleton with config loader, logging,
  CLI entry point, and a passing test runner.
- **Files changed:** Moved the 10 numbered docs from repo root into `docs/` (to match the paths
  `CLAUDE.md`/`README.md` already documented). Added `m516/__init__.py`, `m516/__main__.py`,
  `m516/config.py`, `m516/logging.py`, `tests/test_scaffold.py`, `.env.example`, `.gitignore`,
  `requirements.txt`, `docs/18_REPOSITORY_STRUCTURE.md`. Initialised git (`git init` + commits).
- **Design/architecture changes:** None — pure scaffold, no engine logic yet. Config loader follows
  ADR-002 (missing provider key = `None`, not an error).
- **New decisions:** None architectural; doc reorg and dependency pinning are housekeeping, not ADRs.
- **Pending work:** WP1 (discovery engine + providers) not started. Gating decisions in
  `15_PROGRESS.md` (demo domain, NDPR/CBN source docs, first live providers, mapping validator,
  IP-ownership position) remain unresolved — flag to the client.
- **Next session starting point (SINGLE NEXT ACTION):** Begin **WP1 · Discovery engine + providers**
  per `22_BUILD_PLAN.md` — `m516/models.py`, `m516/providers/{base,netlas,criminalip,internetdb,
  registry}.py`, `m516/discovery.py`, provider cache, tests. Start with `BaseProvider` + the domain
  models before wiring any live adapter.
- **Context summary (rehydrate):** M516 = passive attack-surface + compliance-mapping platform. POC for
  a paying client, target = small Nigerian banks, frameworks NDPR+CBN. Pipeline: discovery → CVE
  enrichment → compliance mapping (pack-driven) → report. **Golden rule:** engine is universal, all
  NG/CBN/banking knowledge lives in the `nigeria-banking` compliance pack. Strictly passive. Free-tier.
  Build order in `22_BUILD_PLAN.md`; do one WP at a time. Scaffold now exists and is tested — WP1 is
  the first WP that produces real engine code.
- **Open questions:** demo domain? NDPR/CBN source docs? which providers live first? who validates
  mappings? IP ownership? (Unchanged from Session 001 — still open.)

---

## Session 001 — [DATE] — Project memory established

- **Objective:** Stand up the full documentation set + CLAUDE.md so Claude Code can build across
  sessions without losing context.
- **Files changed:** Added `CLAUDE.md`; `docs/` set: 00, 01, 02, 03, 04, 05, 06, 07, 08, 10, 12, 13,
  15, 16, 18, 20, 21, 22.
- **Design/architecture changes:** Adopted engine+compliance-pack architecture (build-for-one,
  architect-for-many). Tenant-aware data model, no auth. InternetDB as free provider. Pack format =
  YAML + optional Python.
- **New decisions:** ADR-009 (engine+pack), ADR-010 (tenant-aware), ADR-011 (InternetDB), ADR-012 (pack
  format), ADR-013 (docs-first memory). (Plus carried ADR-001…008.)
- **Pending work:** Resolve gating decisions (demo domain, NDPR/CBN docs, providers, validator, IP).
  Then start WP0 (scaffold) → WP1 (discovery).
- **Next session starting point (SINGLE NEXT ACTION):** Begin **WP0 · Project scaffold** per
  `22_BUILD_PLAN.md` — create package layout, `config.py` (env-var loader), `logging.py`,
  `.env.example`, `.gitignore`, `requirements.txt`, and a passing empty `pytest`. Do NOT start WP1 in
  the same session unless WP0 is fully done + documented.
- **Context summary (rehydrate):** M516 = passive attack-surface + compliance-mapping platform. POC for
  a paying client, target = small Nigerian banks, frameworks NDPR+CBN. Pipeline: discovery → CVE
  enrichment → compliance mapping (pack-driven) → report. **Golden rule:** engine is universal, all
  NG/CBN/banking knowledge lives in the `nigeria-banking` compliance pack. Strictly passive. Free-tier.
  Build order in `22_BUILD_PLAN.md`; do one WP at a time.
- **Open questions:** demo domain? NDPR/CBN source docs? which providers live first? who validates
  mappings? IP ownership?

---

## Template (copy to top for each new session)

```
## Session NNN — YYYY-MM-DD — <short title>
- **Objective:**
- **Files changed:**
- **Design/architecture changes:**
- **New decisions:** (also add ADRs to 12_DECISION_LOG.md)
- **Pending work:**
- **Next session starting point (SINGLE NEXT ACTION):**
- **Context summary (rehydrate):**
- **Open questions:**
```

### End-of-session checklist (do EVERY time)
- [ ] Code for the current WP written + tests pass.
- [ ] `15_PROGRESS.md` status updated.
- [ ] New ADRs recorded in `12_DECISION_LOG.md` (if any).
- [ ] `18_REPOSITORY_STRUCTURE.md` updated (if files added).
- [ ] This log: new entry at top with a SINGLE clear next action.
- [ ] Golden rule honoured (no pack knowledge in engine).
