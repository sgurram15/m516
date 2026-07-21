# 07 · Backend Architecture

> **Status:** Living document · **Version:** 1.0 · **Last updated:** 2026-07
>
> How the backend code is organised. Realises `02_ARCHITECTURE.md` in concrete modules and patterns.
> The repository tree lives in `18_REPOSITORY_STRUCTURE.md` (stub until Phase 1 completes).

---

## 1. Layering

The POC follows a light clean-architecture split. Business logic never depends on a specific provider
or framework SDK; it depends on interfaces.

```
┌───────────────────────────────────────────────┐
│  API layer (FastAPI)   — endpoints, DTOs        │
├───────────────────────────────────────────────┤
│  Orchestration         — the 4-module pipeline  │
├───────────────────────────────────────────────┤
│  Domain / business     — models, rules, scoring │
├───────────────────────────────────────────────┤
│  Adapters              — providers, NVD, LLM,    │
│                          vector store, PDF       │
└───────────────────────────────────────────────┘
```

Dependencies point downward only. Adapters implement interfaces defined in the domain layer.

## 2. Module boundaries

| Module | Package (planned) | Depends on | Produces |
|---|---|---|---|
| 1 · Discovery | `m516/discovery.py` + `m516/providers/` | provider interface | `DiscoveryResult` |
| 2 · Enrichment | `m516/enrichment/` | NVD adapter, rules engine | ranked `Finding[]` |
| 3 · Compliance | `m516/compliance/` | vector store, LLM | `ComplianceMapping[]` |
| 4 · Report | `m516/report/` | LLM, PDF renderer | PDF file |
| Orchestration | `m516/pipeline.py` | modules 1–4 | full result + PDF |
| API | `m516/api/` | orchestration | HTTP responses |

Each module is independently testable and imports **only** the layer(s) below it. No module imports a
sibling module's internals; they communicate through the domain objects in `03_DOMAIN_MODEL.md`.

## 3. The provider-adapter pattern (implemented)

The one pattern that matters most, because it delivers provider independence (ADR-002).

- `providers/base.py` — `BaseProvider` abstract class with `discover(domain) -> Asset[]`, plus WAF
  detection helper. Every adapter subclasses it and tags results with its own name.
- `providers/netlas.py`, `providers/criminalip.py` — concrete adapters. Each knows only its own
  provider's response shape and normalises into `Asset`/`Service`.
- `providers/registry.py` — the single place providers are registered and switched on/off. A provider
  is enabled iff its API-key env var is set. Adding a provider = one line here + one adapter file.
- `discovery.py` — the orchestrator: runs enabled providers, merges by IP, cross-checks, returns a
  `DiscoveryResult`. One provider failing is caught and recorded, never fatal (NFR-REL).

### Adding a provider (the extensibility contract)
1. Create `providers/<name>.py`, subclass `BaseProvider`, implement `discover()`.
2. Add one line to `_BUILDERS` in `registry.py` mapping name → (class, env-var).
3. Add the key to `.env`. Nothing else changes.

## 4. Configuration & secrets

- All config via environment variables; loaded once at startup.
- Provider API keys: `NETLAS_API_KEY`, `CRIMINALIP_API_KEY`, (future: `CENSYS_API_KEY`, `SHODAN_API_KEY`).
- `.env` is git-ignored; `.env.example` documents required vars. Keys never in source (NFR-SEC).
- No hard-coded constants for anything environment-specific (endpoints, model names, thresholds live in config).

## 5. Error handling & logging

- Provider errors are captured into `DiscoveryResult.errors`, not raised, so a scan degrades
  gracefully (NFR-REL).
- Structured logging per pipeline stage and per external call (NFR-OBS).
- Domain-level validation failures raise explicit, typed errors surfaced by the API layer as clear
  4xx responses.

## 6. Caching

- Provider responses cached on disk keyed by (provider, domain) to conserve free-tier quota (NFR-COST).
- Cache is a POC convenience; a productised version would use a proper cache store.

## 7. Async / background work

- **None in the POC.** The pipeline is synchronous. Queues, workers, and schedulers are explicitly
  deferred (they belong to the out-of-scope scheduled-scan feature). Documented so their absence is a
  choice, not an oversight.

## 8. Testing hooks

- Adapters expose offline parse paths (`from_records` / `from_report` / `from_file`) so they can be
  tested against captured real data without live API calls — used already in `demo_coverage.py`.
- See `10_TESTING_STRATEGY.md` (stub) for the full approach.

## 9. Current state

Module 1 foundation is prototyped and tested offline against real coverage-test data (Netlas +
Criminal IP adapters, merge/cross-check, WAF detection). See `15_PROGRESS.md`. Remaining Phase 1 work:
wire live API calls and add caching.
