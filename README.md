# M516 — Passive Attack-Surface + Compliance Intelligence (POC)

Takes a domain → discovers its external attack surface → finds vulnerabilities → **maps them to the
regulations that apply** → produces an audit-ready report. POC targets small Nigerian banks (NDPR + CBN),
architected to scale to any sector/country via swappable **compliance packs**.

## Start here (for Claude Code or any engineer)
1. Read `CLAUDE.md` (auto-loaded by Claude Code).
2. Read `docs/15_PROGRESS.md` and the top of `docs/16_SESSION_LOG.md`.
3. Follow `docs/22_BUILD_PLAN.md` — one work package at a time.

## Golden rule
The **engine** is universal. All Nigeria/CBN/banking knowledge lives in the `nigeria-banking`
**compliance pack**. Never hard-code pack knowledge into engine code.

## Constraints
Strictly passive · free-tier first · secrets in env only · compliance output human-validated ·
tenant-aware data model, no auth. See `CLAUDE.md`.
