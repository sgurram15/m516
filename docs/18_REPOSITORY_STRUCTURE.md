# 18 · Repository Structure

> **Status:** Living · Updated whenever files are added/moved (per `CLAUDE.md` end-of-session
> checklist). Reflects the tree as of the WP3 scaffolding addition (engine machinery only, no real
> pack content — see `docs/15_PROGRESS.md`).

```
M516/
├── CLAUDE.md                  # Auto-loaded project context — read first, every session
├── README.md                  # Entry point for a new engineer
├── requirements.txt           # Python dependencies (engine only)
├── .env.example                # Documents required env vars; copy to .env (git-ignored)
├── .gitignore
├── .streamlit/
│   └── config.toml            # Dark theme for demo/streamlit_app.py, matches ui screens/ palette
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
│   ├── asset.jpg               # 06_FRONTEND_ARCHITECTURE.md.
│   ├── portscanner.jpg
│   └── riskscoring.jpg
│
├── packs/
│   └── README.md               # Explains nigeria-banking is pending real NDPR/CBN documents —
│                                # do NOT draft placeholder regulatory content here (see docs/15_PROGRESS.md)
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
│   ├── enrichment/
│   │   ├── nvd.py             # NVD/CVE lookup by CPE (ADR-006), CVEMatch (+ confidence, sub-scores)
│   │   ├── scoring.py         # Deterministic contextual risk scoring (ADR-007, BR-3 — no LLM)
│   │   ├── detection_level.py # Red/yellow/green rules for findings + certificate status
│   │   └── port_risk.py       # CVE-independent port-type risk labels (mockup-informed)
│   └── compliance/            # Module 3 — WP3 scaffolding (engine machinery; no real pack yet)
│       ├── pack_loader.py     # CompliancePack/Framework/Clause + load_pack() (docs/21_COMPLIANCE_PACKS.md)
│       ├── ingest.py          # Embeds clauses into ChromaDB (local ONNX embedding, no API key)
│       ├── retrieve.py        # retrieve_clauses(): finding -> candidate ClauseMatch[]
│       └── mapper.py          # ComplianceMapping + map_finding(); LLM step stubbed (llm_client=None)
│
├── demo/                       # Dev visualization tool — NOT the WP5 React UI
│   ├── streamlit_app.py       # `streamlit run demo/streamlit_app.py` — dark theme, sidebar-navigated
│   │                           # Dashboard/Asset Discovery/Port Findings/Risk Scoring views;
│   │                           # single-domain-select scan, results accumulate in session_state
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
    ├── test_pack_loader.py    # Pack YAML parsing + malformed-pack error handling
    ├── test_ingest.py         # Clause embedding into ChromaDB, idempotent re-ingest
    ├── test_retrieve.py       # Semantic clause retrieval for a Finding (needs the ONNX model, see below)
    ├── test_mapper.py         # map_finding() with/without an llm_client
    └── fixtures/
        ├── netlas_host.json, criminalip_domain_reports.json, internetdb_ip.json, censys_host.json,
        │   nvd_log4j.json, nvd_empty.json   # Captured/representative provider JSON, offline
        └── packs/test-stub/    # Fictional "ACME-STD" pack — proves the compliance engine is generic
            ├── pack.yaml
            ├── frameworks/acme.yaml
            └── documents/acme.txt
```

## Notes

- `packs/nigeria-banking/` does **not** exist yet — deliberately. See `packs/README.md` and
  `docs/15_PROGRESS.md`: drafting placeholder NDPR/CBN clause content risks it being mistaken for real
  regulatory guidance. Author it only once real source documents arrive from the client.
- `m516/report/`, `m516/pipeline.py`, `m516/api/` are introduced module-by-module across WP4–WP5 per
  `docs/22_BUILD_PLAN.md`. Don't create them ahead of the WP that needs them.
- `frontend/` is introduced in WP5 only — `demo/` is a separate, permanent dev convenience, not a
  precursor to it.
- `test_ingest.py`/`test_retrieve.py` are the only tests in this repo that need network access (first
  run downloads ChromaDB's `all-MiniLM-L6-v2` ONNX model, ~80MB, one-time, then fully offline).
