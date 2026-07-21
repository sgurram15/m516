# 18 · Repository Structure

> **Status:** Living · Updated whenever files are added/moved (per `CLAUDE.md` end-of-session
> checklist). Reflects the tree as of the mockup-informed CVSS sub-scores + port-risk-labels addition.

```
M516/
├── CLAUDE.md                  # Auto-loaded project context — read first, every session
├── README.md                  # Entry point for a new engineer
├── requirements.txt           # Python dependencies (engine only)
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
├── ui screens/                 # UI mockups from the user — informs (not-yet-authored)
│   ├── asset.jpg               # 06_FRONTEND_ARCHITECTURE.md. Two items conflict with
│   ├── portscanner.jpg         # 01_REQUIREMENTS.md's explicit out-of-scope list
│   └── riskscoring.jpg         # (Breach Monitor, Users & Roles) — see 15_PROGRESS.md Notes.
│
├── m516/                      # The engine (package name matches the project)
│   ├── __init__.py            # __version__
│   ├── __main__.py            # CLI entry point: `python -m m516`
│   ├── config.py              # Env-var config loader (ADR-002: missing key = skip, not fail)
│   ├── logging.py             # Structured logging setup
│   ├── cache.py               # Shared disk cache keyed by (namespace, identifier), TTL-based
│   ├── models.py              # Service / Asset / DiscoveryResult (docs/03_DOMAIN_MODEL.md §1)
│   ├── discovery.py           # Module 1 orchestrator: run providers, merge by IP, WAF detection
│   ├── findings.py            # Module 2 orchestrator + Finding: services -> ranked findings
│   ├── providers/
│   │   ├── base.py            # BaseProvider interface + detect_waf()
│   │   ├── dns_resolve.py     # Shared passive DNS helper (InternetDB, Criminal IP, Censys)
│   │   ├── netlas.py          # Deep banners/CPEs/certs (ADR-004)
│   │   ├── criminalip.py      # Summary/risk/tech-stack cross-check (ADR-004)
│   │   ├── censys.py          # Free-tier host-lookup-by-IP (added post-WP1)
│   │   ├── internetdb.py      # Free, no-key IP enrichment (ADR-011)
│   │   └── registry.py        # Enable-by-env-var-key provider registration
│   └── enrichment/
│       ├── nvd.py             # NVD/CVE lookup by CPE (ADR-006), CVEMatch (+ confidence, sub-scores)
│       ├── scoring.py         # Deterministic contextual risk scoring (ADR-007, BR-3 — no LLM)
│       ├── detection_level.py # Red/yellow/green rules for findings + certificate status
│       └── port_risk.py       # CVE-independent port-type risk labels (mockup-informed)
│
├── demo/                       # Dev visualization tool — NOT the WP5 React UI
│   ├── streamlit_app.py       # `streamlit run demo/streamlit_app.py` — multi-domain triage,
│   │                           # plain-language findings/services, red/yellow/green comparison
│   └── requirements.txt       # streamlit + pandas (kept out of the engine's own requirements.txt)
│
└── tests/
    ├── __init__.py
    ├── test_scaffold.py       # WP0 smoke tests: config, logging, CLI
    ├── test_models.py         # Derived fields, merge-by-IP logic, service-level provenance/backfill
    ├── test_providers.py      # Adapter from_records() against fixtures, registry, WAF detection
    ├── test_discovery.py      # Orchestration: merge, per-provider error isolation, WAF applied
    ├── test_nvd.py            # NVD parsing, query routing, CVSS sub-score extraction
    ├── test_scoring.py        # Scoring formula: port/exposure/staleness factors, severity buckets
    ├── test_findings.py       # build_findings orchestration: ranking, BR-2 skip, error isolation
    ├── test_detection_level.py # Red/yellow/green rule criteria for findings + certificates
    ├── test_port_risk.py      # Port-type risk label catalog
    └── fixtures/               # Captured/representative provider JSON for offline adapter tests
        ├── netlas_host.json
        ├── criminalip_domain_reports.json
        ├── internetdb_ip.json
        ├── censys_host.json
        ├── nvd_log4j.json
        └── nvd_empty.json
```

## Notes

- `packs/` (compliance packs, e.g. `nigeria-banking/`) is introduced in WP3 — not present yet.
- `m516/compliance/`, `m516/report/`, `m516/pipeline.py`, `m516/api/` are introduced module-by-module
  across WP3–WP5 per `docs/22_BUILD_PLAN.md`. Don't create them ahead of the WP that needs them.
- `frontend/` is introduced in WP5 only — `demo/` is a separate, permanent dev convenience, not a
  precursor to it.
