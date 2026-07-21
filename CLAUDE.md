# CLAUDE.md — M516 Project Context (READ FIRST, EVERY SESSION)

> **This file is auto-loaded by Claude Code. It is the single most important file.**
> Read it fully before doing anything. Then read `docs/15_PROGRESS.md` and the latest entry in
> `docs/16_SESSION_LOG.md` to know exactly where we are. Do not re-derive context from chat history —
> the markdown files ARE the memory.

---

## What this project is (one paragraph)

M516 is a **passive external attack-surface + compliance-intelligence platform**. It takes a domain,
discovers its internet-facing assets, finds known vulnerabilities, **maps those findings to the
regulations that apply to that organisation**, and produces an audit-ready report. The compliance
mapping is the differentiator — no other tool does it for Nigerian frameworks. We are building a
**Proof of Concept** for a paying client, targeting **small Nigerian banks** (frameworks: NDPR + CBN),
but architected so it scales to **any sector, any country** by authoring new "compliance packs" — not
by rewriting the engine.

## The golden architectural rule (never violate)

> **The ENGINE is universal. The KNOWLEDGE is a swappable pack.**
> No engine code may hard-code "Nigeria", "CBN", "NDPR", or "banking". Anything sector- or
> country-specific lives in a **compliance pack** (see `docs/03_DOMAIN_MODEL.md` and
> `docs/21_COMPLIANCE_PACKS.md`). For the POC we author exactly one pack: `nigeria-banking`.

If you ever find yourself typing a Nigerian regulator's name into engine logic, stop — it belongs in a
pack.

## The five hard constraints (never violate)

1. **Strictly passive.** Query third-party indexes only. NEVER actively scan/probe/touch a target. (ADR-001)
2. **Free-tier first.** Providers are pluggable and optional; a missing API key means skip, not fail. (ADR-002)
3. **Secrets in env vars only.** `.env` is git-ignored. Never commit keys. Never print them.
4. **Compliance output needs human validation** before any client relies on it. Reports carry a disclaimer.
5. **Tenant-aware data model, no auth built.** Every core record carries a nullable `tenant_id`; we do
   NOT build login/roles in the POC. (ADR-010)

## The pipeline (what we're building)

```
domain → [1 Discovery] → [2 CVE Enrichment] → [3 Compliance Mapping] → [4 Report] → PDF
                                                      ▲
                                          loads a Compliance Pack
                                          (POC: nigeria-banking)
```

## How to work in this repo (the loop)

**Every session, in order:**
1. Read this file, then `docs/15_PROGRESS.md`, then the top entry of `docs/16_SESSION_LOG.md`.
2. Confirm the current phase and the "next action" noted there.
3. Do the work — one work package at a time, never run ahead.
4. Write tests for what you built.
5. **Update docs before ending:** `15_PROGRESS.md` (status), `16_SESSION_LOG.md` (new entry),
   `12_DECISION_LOG.md` (if any decision was made), `18_REPOSITORY_STRUCTURE.md` (if files added).
6. State the single "next action" for the following session.

**Never:**
- Never build beyond the current work package without being asked.
- Never hard-code pack-specific knowledge into the engine.
- Never add active-scanning capability.
- Never leave docs stale — if code and docs disagree, that's a bug.

## Tech stack (see ADRs for rationale)

- **Backend:** Python + FastAPI
- **Vector store:** ChromaDB (POC scale)
- **DB:** PostgreSQL (SQLite acceptable for earliest phases)
- **Providers (passive):** Netlas, Criminal IP, Shodan InternetDB (free, no-key) — pluggable
- **Vulns:** NVD/CVE (free)
- **LLM:** used only for compliance-mapping reasoning + report narrative (NOT for risk scoring)
- **Frontend:** React (Phase 5 only)

## Where everything is documented

| Need | File |
|---|---|
| Vision, scope, personas | `docs/00_PROJECT_OVERVIEW.md` |
| What it must do | `docs/01_REQUIREMENTS.md` |
| How it's structured (+ diagrams) | `docs/02_ARCHITECTURE.md` |
| Core objects & the pack interface | `docs/03_DOMAIN_MODEL.md` |
| DB schema | `docs/04_DATABASE_DESIGN.md` |
| API endpoints | `docs/05_API_DESIGN.md` |
| Frontend | `docs/06_FRONTEND_ARCHITECTURE.md` |
| Backend layout & patterns | `docs/07_BACKEND_ARCHITECTURE.md` |
| Security & legal | `docs/08_SECURITY.md` |
| Testing approach | `docs/10_TESTING_STRATEGY.md` |
| **Why** decisions were made (ADRs) | `docs/12_DECISION_LOG.md` |
| Risks | `docs/13_RISK_REGISTER.md` |
| **Current state** | `docs/15_PROGRESS.md` |
| **Session-to-session memory** | `docs/16_SESSION_LOG.md` |
| Repo tree | `docs/18_REPOSITORY_STRUCTURE.md` |
| **Compliance pack format** | `docs/21_COMPLIANCE_PACKS.md` |
| Build order & work packages | `docs/22_BUILD_PLAN.md` |
| Glossary (NDPR, CBN, CPE, RAG…) | `docs/20_GLOSSARY.md` |

## Context-economy rules (to not waste usage)

- Trust the docs; don't re-read the whole codebase each session — read the file you're changing plus
  its doc.
- `15_PROGRESS.md` and `16_SESSION_LOG.md` are designed to rehydrate you in ~2 minutes. Start there.
- When in doubt about a past decision, check `12_DECISION_LOG.md` before asking the user to repeat it.
