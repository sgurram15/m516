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

## In progress

- Nothing in active build yet. Awaiting start of WP3.

## Blocked / gating decisions (resolve with client)

- [ ] Confirm demo domain (small Nigerian bank or safe proxy).
- [ ] Obtain/confirm NDPR + CBN source documents (needed for WP3).
- [x] Confirm first providers to wire live — done: Netlas + Criminal IP + InternetDB, all live-verified.
- [ ] Agree who validates compliance mappings.
- [ ] Confirm IP-ownership position (SOW §12).

## Metrics

| Metric | Value |
|---|---|
| WPs complete | 3 of 6 |
| Modules built | 2 of 4 |
| Providers live | 3 (Netlas, Criminal IP, InternetDB) |
| Frameworks ingested | 0 of 2 |
| Packs authored | 0 of 1 (`nigeria-banking`) |
| Tests passing | 43 |

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
