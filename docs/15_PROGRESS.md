# 15 · Progress

> **Status:** Living · **READ THIS SECOND (after CLAUDE.md).** The current state at a glance. Update at
> the END of every session alongside `16_SESSION_LOG.md`.

## Current position

**Phase:** WP0 complete → ready to start **WP1 (discovery)**.
**Next action:** See top entry of `16_SESSION_LOG.md`.

## Work package status

| WP | Description | Status |
|---|---|---|
| WP0 | Project scaffold | ✅ Done |
| WP1 | Discovery engine + providers | ⬜ Not started |
| WP2 | CVE enrichment + risk scoring | ⬜ Not started |
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

## In progress

- Nothing in active build yet. Awaiting start of WP1.

## Blocked / gating decisions (resolve with client)

- [ ] Confirm demo domain (small Nigerian bank or safe proxy).
- [ ] Obtain/confirm NDPR + CBN source documents (needed for WP3).
- [ ] Confirm first providers to wire live (recommend Netlas + Criminal IP + InternetDB).
- [ ] Agree who validates compliance mappings.
- [ ] Confirm IP-ownership position (SOW §12).

## Metrics

| Metric | Value |
|---|---|
| WPs complete | 1 of 6 |
| Modules built | 0 of 4 |
| Providers live | 0 |
| Frameworks ingested | 0 of 2 |
| Packs authored | 0 of 1 (`nigeria-banking`) |
| Tests passing | 4 |

## Notes

- The earlier throwaway Module 1 prototype (from a prior exploratory session) is NOT in this repo; WP1
  rebuilds it cleanly against these docs. Don't assume prior code exists — build per `22_BUILD_PLAN.md`.
