# 22 · Build Plan (work packages, in order)

> **Status:** Living · The authoritative build order. Do these **in sequence**. Do NOT start a WP until
> the previous is done + tested + docs updated. Each WP lists: goal, files, done-when.

## Rules of engagement (for Claude Code)

- One work package at a time. Finish, test, document, then stop and report the next action.
- Every WP ends by updating `15_PROGRESS.md` and adding a `16_SESSION_LOG.md` entry.
- Never build beyond the current WP without being asked.
- Keep the engine free of pack-specific knowledge (golden rule).

---

## WP0 · Project scaffold  ✅/⬜
- **Goal:** runnable skeleton: package layout, config loader (env vars), logging, `.env.example`,
  `.gitignore`, `requirements.txt`, test runner.
- **Done when:** `pytest` runs (even with 0 tests) and `python -m m516 --help` (or equivalent) works;
  no secrets in repo.

## WP1 · Discovery engine + providers (Module 1)
- **Goal:** domain → normalised `DiscoveryResult` from multiple **passive** providers, merged + cross-checked.
- **Files:** `m516/models.py`, `m516/providers/{base,netlas,criminalip,internetdb,registry}.py`,
  `m516/discovery.py`, provider cache, tests.
- **Notes:** InternetDB takes an IP (enrich after resolving), not a domain. WAF detection required.
- **Done when:** runs against the demo domain returning correct, de-duplicated assets with CPEs/versions;
  one provider failing doesn't abort; tests pass.

## WP2 · CVE enrichment + risk scoring (Module 2)
- **Goal:** services → CVEs (NVD by CPE) + CVSS + **deterministic** contextual score + ranked findings.
- **Files:** `m516/enrichment/{nvd,scoring}.py`, `m516/findings.py`, tests.
- **Done when:** demo domain's services resolve to real CVEs with reproducible ranking; scoring is
  rules-based and explainable (no LLM).

## WP3 · Compliance pack loader + mapping (Module 3 — the differentiator)
- **Goal:** load `nigeria-banking` pack; embed its documents; map each finding → clause(s) via RAG;
  produce `ComplianceMapping[]`.
- **Files:** `m516/compliance/{pack_loader,ingest,retrieve,mapper}.py`, `packs/nigeria-banking/**`, tests.
- **Notes:** engine stays generic; all NDPR/CBN specifics live in the pack. Validate mapping quality on
  a few known findings before wiring on.
- **Done when:** demo findings map to correct NDPR/CBN clauses with status + remediation; swapping in a
  stub pack proves the engine is generic.

## WP4 · Report generation (Module 4)
- **Goal:** all findings → audit-ready PDF (exec summary, assets, findings, compliance gaps, remediation,
  appendix), using pack `report_labels`. Carries disclaimer.
- **Files:** `m516/report/{template,render}.py`, tests.
- **Done when:** one action produces a coherent PDF grounded in real data, addressed per pack labels.

## WP5 · API + demo UI (Module 5)
- **Goal:** FastAPI endpoints (`05_API_DESIGN.md`) + five React screens on real data, incl. live scan
  progress. Assemble end-to-end demo.
- **Files:** `m516/api/**`, `frontend/**`, tests.
- **Done when:** end-to-end demo runs reliably on the demo domain; "show me a live scan" works.

---

## Phase → WP mapping & estimates (part-time, realistic)

| Phase | WPs | Estimate |
|---|---|---|
| Design & docs | (this set) | mostly done |
| Build A | WP0–WP2 | ~6–8 weeks |
| Build B | WP3–WP4 | ~8–10 weeks (largest buffer — RAG iteration) |
| Build C | WP5 | ~3–4 weeks |

Commercial milestones (SOW): WP1–WP2 = 30%, WP3–WP4 = 40%, WP5 = 30%.
