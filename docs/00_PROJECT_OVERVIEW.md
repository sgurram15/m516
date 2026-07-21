# 00 · Project Overview

> **Status:** Living document · **Version:** 1.0 · **Last updated:** 2026-07 · **Owner:** Shraddha Gurram
>
> This is the entry point for the project. Any new session (human or AI) should read this first,
> then `15_PROGRESS.md` and `16_SESSION_LOG.md` to know where things stand.

---

## Vision

M516 is a Cyber Exposure, Attack Surface, and Compliance Intelligence platform built specifically
for Nigeria's security and regulatory landscape, and designed to scale across Africa. It discovers an
organisation's externally-visible assets, assesses their risk, maps findings to Nigerian regulatory
requirements, and produces audit-ready reports — out of the box.

## What we are building right now

A **Proof of Concept (POC)**, not the full product. The POC proves one capability end to end:

> Enter a domain → discover its external attack surface → enrich findings with known vulnerabilities
> → map them to Nigerian regulatory requirements → produce an audit-ready report.

Everything in this repository is scoped to that POC. The full product vision exists, but its features
are deliberately deferred (see **Out of Scope** below and `01_REQUIREMENTS.md`).

## Why it matters (the differentiator)

EASM scanning and CVE lookups are commodity capabilities — several global tools do them well. What no
tool currently does is **map technical findings to Nigerian regulatory clauses** (NDPR, CBN
Cybersecurity Framework, NCC, etc.) automatically and continuously. That regulatory-mapping layer is
the defensible core of M516. The POC exists primarily to prove that layer works.

## Product summary

| | |
|---|---|
| **Current stage** | Proof of Concept |
| **Primary market** | Nigerian organisations (banks, fintechs, PSPs, government / MDAs) |
| **Model** | Passive external assessment + compliance mapping |
| **POC frameworks** | NDPR + CBN Cybersecurity Framework (two only) |
| **Deployment** | Single cloud instance (no cluster, no multi-region) |

## Major capabilities (POC)

1. **Asset & exposure discovery** — find a domain's external footprint via passive data providers.
2. **CVE enrichment & risk scoring** — map exposed services to known vulnerabilities, prioritise.
3. **Compliance mapping** — tie findings to specific Nigerian regulatory clauses (the differentiator).
4. **Report generation** — produce an audit-ready PDF.
5. **Demo UI** — five screens driven by real scan data.

## High-level architecture (summary)

A single instance running a FastAPI backend that orchestrates four sequential modules, backed by
PostgreSQL and a ChromaDB vector store, calling external data providers (Netlas, Criminal IP, NVD) and
an LLM over their APIs. Full detail in `02_ARCHITECTURE.md`.

```
domain → [1 discovery] → [2 CVE enrichment] → [3 compliance mapping] → [4 report] → PDF
```

## User personas

- **Compliance officer / CISO** (Nigerian bank, fintech, or MDA) — the primary buyer. Wants findings
  translated into regulator-ready language and reports they can hand to CBN / NITDA.
- **Security analyst** — wants the technical findings (assets, ports, CVEs) accurately.
- **Demo audience / investor** — wants to see the end-to-end flow work live on a real domain.

## Business objectives (POC stage)

- Prove the end-to-end capability works on real Nigerian infrastructure.
- Produce a credible demo that can secure an anchor pilot client and/or investment conversation.
- Serve as a portfolio-grade demonstration of agentic RAG + regulated-domain engineering.

## Out of scope (POC)

Breach / dark-web monitoring · scheduled/continuous scanning · multi-tenancy · authentication &
user roles · white-labelling · SIEM/SOC integrations · healthcare (NCDC) scope · **any active
scanning**. See `01_REQUIREMENTS.md` for the full list and rationale.

## Key constraints (non-negotiable)

- **Strictly passive.** Query third-party indexes only; never actively scan a target. (See `08_SECURITY.md`.)
- **Free-tier first.** The POC runs on free API tiers; providers are pluggable and optional.
- **Compliance mappings require human validation** before any client relies on them.
- **Secrets live in environment variables**, never in source control.

## Related documents

- `01_REQUIREMENTS.md` — what it must do
- `02_ARCHITECTURE.md` — how it's structured
- `03_DOMAIN_MODEL.md` — the core data objects
- `07_BACKEND_ARCHITECTURE.md` — module boundaries & patterns
- `12_DECISION_LOG.md` — why key choices were made
- `15_PROGRESS.md` — current state
- `16_SESSION_LOG.md` — session-by-session continuity
