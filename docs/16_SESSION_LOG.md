# 16 · Session Log

> **Status:** Living · **The continuity backbone.** Every session appends an entry at the TOP. A fresh
> session reads CLAUDE.md → 15_PROGRESS.md → this top entry, and can continue with NO chat history.
> Template at the bottom.

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
