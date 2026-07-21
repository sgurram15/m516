# 18 · Repository Structure

> **Status:** Living · Updated whenever files are added/moved (per `CLAUDE.md` end-of-session
> checklist). Reflects the tree as of the real `nigeria-banking` pack being authored (see
> `docs/15_PROGRESS.md`).

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
│   ├── 05_API_DESIGN.md       # FastAPI endpoint contracts (authored in WP5's backend half)
│   ├── 06_FRONTEND_ARCHITECTURE.md  # frontend/ tooling, structure, palette (WP5's frontend half)
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
│   ├── README.md               # Explains the nigeria-banking pack's provenance + validation status
│   └── nigeria-banking/        # The real POC pack (NDPR + CBN) — authored from genuine source docs
│       ├── pack.yaml
│       ├── frameworks/
│       │   ├── ndpr.yaml       # 9 real clauses, each citing an actual NDPR article/section
│       │   └── cbn.yaml        # 12 real clauses, each citing an actual CBN framework section
│       └── documents/
│           ├── ndpr_implementation_framework.pdf   # NITDA, Nov 2020 (source of truth for ndpr.yaml)
│           └── cbn_cybersecurity_framework.pdf     # CBN Banking Supervision, Oct 2018 (source for cbn.yaml)
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
│   ├── pipeline.py            # WP5: run_scan() wires Modules 1-4 in sequence, on_stage() progress hook
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
│   ├── compliance/             # Module 3 (engine machinery done; real nigeria-banking pack authored)
│   │   ├── pack_loader.py     # CompliancePack/Framework/Clause + load_pack() (docs/21_COMPLIANCE_PACKS.md)
│   │   ├── ingest.py          # Embeds clauses into ChromaDB (local ONNX embedding, no API key)
│   │   ├── retrieve.py        # retrieve_clauses(): finding -> candidate ClauseMatch[]
│   │   └── mapper.py          # ComplianceMapping + map_finding(); LLM step stubbed (llm_client=None)
│   ├── report/                 # Module 4 (WP4) — pack-agnostic, no LLM narrative (none wired yet)
│   │   ├── template.py        # build_report_data(): DiscoveryResult+Finding[]+pack -> ReportData
│   │   └── render.py          # render_pdf(): ReportData -> audit-ready PDF (reportlab)
│   └── api/                    # WP5 backend half — FastAPI, no business logic (thin over pipeline.py)
│       ├── state.py           # In-memory ScanState dict — deliberately not Postgres, see 15_PROGRESS.md
│       ├── schemas.py          # Pydantic response models, each a thin projection of an engine dataclass
│       ├── routes.py           # POST /api/scans, GET .../{dashboard,assets,findings,compliance,report.pdf}, /api/packs, /api/health
│       └── app.py              # create_app() factory — `uvicorn m516.api.app:create_app --factory`
│
├── frontend/                   # WP5 frontend half — the real demo UI (docs/06_FRONTEND_ARCHITECTURE.md)
│   ├── package.json, tsconfig.json, vite.config.ts, index.html, .env.example
│   └── src/
│       ├── main.tsx, App.tsx  # App.tsx: no scan yet -> ScanInitiation; else -> Shell (Sidebar + tab)
│       ├── api/{types.ts,client.ts}  # types mirror m516/api/schemas.py; client = typed fetch wrapper
│       ├── hooks/useScan.ts    # createScan() + polls GET /api/scans/{id} for FR-5.1 live progress
│       ├── components/         # Sidebar, StatTile, SeverityBadge, StatusBadge, ProgressBanner, Waiting
│       ├── pages/              # ScanInitiation, Dashboard, AssetDiscovery, RiskScoring, Compliance
│       └── styles/theme.css    # shared palette — see docs/06_FRONTEND_ARCHITECTURE.md
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
    ├── test_nigeria_banking_pack.py  # Real pack loads, real citations present, retrieval sanity-check
    ├── test_report_template.py # build_report_data(): counts, gap grouping, honest-unmapped, roadmap
    ├── test_report_render.py   # render_pdf(): real PDF produced, text-extractable via pypdf
    ├── test_pipeline.py        # run_scan(): stage order, honest-unmapped compliance, pdf naming
    ├── test_api_scans.py       # FastAPI TestClient: full scan lifecycle, 404/400/409 error paths
    └── fixtures/
        ├── netlas_host.json, criminalip_domain_reports.json, internetdb_ip.json, censys_host.json,
        │   nvd_log4j.json, nvd_empty.json   # Captured/representative provider JSON, offline
        └── packs/test-stub/    # Fictional "ACME-STD" pack — proves the compliance engine is generic
            ├── pack.yaml
            ├── frameworks/acme.yaml
            └── documents/acme.txt
```

## Notes

- `packs/nigeria-banking/` is now authored from genuine NDPR/CBN source documents — see
  `packs/README.md` and `docs/15_PROGRESS.md` for provenance and the still-open compliance-professional
  validation step required before any client relies on the output.
- `m516/report/` (WP4), `m516/pipeline.py` + `m516/api/` (WP5 backend half), and `frontend/` (WP5
  frontend half) are all now built — `run_scan()` wires discovery → findings → compliance mapping →
  report end-to-end, and `frontend/` is the real client-facing demo UI. `demo/` is a separate,
  permanent dev convenience, not a precursor to `frontend/`. **Not yet done:** a human has not clicked
  through `frontend/` in a real browser (this environment has no browser automation — see
  `docs/06_FRONTEND_ARCHITECTURE.md`'s verification note and `docs/15_PROGRESS.md`'s WP5 frontend
  entry for exactly what was and wasn't verified).
- `test_ingest.py`/`test_retrieve.py` are the only tests in this repo that need network access (first
  run downloads ChromaDB's `all-MiniLM-L6-v2` ONNX model, ~80MB, one-time, then fully offline).
