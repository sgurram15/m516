# 18 · Repository Structure

> **Status:** Living · Updated whenever files are added/moved (per `CLAUDE.md` end-of-session
> checklist). Reflects the tree as of WP1 completion.

```
M516/
├── CLAUDE.md                  # Auto-loaded project context — read first, every session
├── README.md                  # Entry point for a new engineer
├── requirements.txt           # Python dependencies
├── .env.example                # Documents required env vars; copy to .env (git-ignored)
├── .gitignore
│
├── docs/                      # All numbered docs — the project's durable memory
│   ├── 00_PROJECT_OVERVIEW.md
│   ├── 01_REQUIREMENTS.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_DOMAIN_MODEL.md
│   ├── 07_BACKEND_ARCHITECTURE.md
│   ├── 12_DECISION_LOG.md     # ADRs
│   ├── 15_PROGRESS.md         # Current state — read second, every session
│   ├── 16_SESSION_LOG.md      # Session-to-session memory — read third, every session
│   ├── 18_REPOSITORY_STRUCTURE.md  # This file
│   ├── 21_COMPLIANCE_PACKS.md # Compliance pack format
│   └── 22_BUILD_PLAN.md       # Work-package build order
│
├── m516/                      # The engine (package name matches the project)
│   ├── __init__.py            # __version__
│   ├── __main__.py            # CLI entry point: `python -m m516`
│   ├── config.py              # Env-var config loader (ADR-002: missing key = skip, not fail)
│   ├── logging.py             # Structured logging setup
│   ├── models.py              # Service / Asset / DiscoveryResult (docs/03_DOMAIN_MODEL.md §1)
│   ├── discovery.py           # Module 1 orchestrator: run providers, merge by IP, WAF detection
│   └── providers/
│       ├── base.py            # BaseProvider interface + detect_waf()
│       ├── cache.py           # Disk cache keyed by (provider, identifier), TTL-based
│       ├── dns_resolve.py     # Shared passive DNS helper (InternetDB, Criminal IP)
│       ├── netlas.py          # Deep banners/CPEs/certs (ADR-004)
│       ├── criminalip.py      # Summary/risk/tech-stack cross-check (ADR-004)
│       ├── internetdb.py      # Free, no-key IP enrichment (ADR-011)
│       └── registry.py        # Enable-by-env-var-key provider registration
│
└── tests/
    ├── __init__.py
    ├── test_scaffold.py       # WP0 smoke tests: config, logging, CLI
    ├── test_models.py         # Derived fields, merge-by-IP logic
    ├── test_providers.py      # Adapter from_records() against fixtures, registry, WAF detection
    ├── test_discovery.py      # Orchestration: merge, per-provider error isolation, WAF applied
    └── fixtures/               # Captured/representative provider JSON for offline adapter tests
        ├── netlas_host.json
        ├── criminalip_domain_reports.json
        └── internetdb_ip.json
```

## Notes

- `packs/` (compliance packs, e.g. `nigeria-banking/`) is introduced in WP3 — not present yet.
- `m516/enrichment/`, `m516/findings.py`, `m516/compliance/`, `m516/report/`, `m516/pipeline.py`,
  `m516/api/` are introduced module-by-module across WP2–WP5 per `docs/22_BUILD_PLAN.md`. Don't create
  them ahead of the WP that needs them.
- `frontend/` is introduced in WP5 only.
