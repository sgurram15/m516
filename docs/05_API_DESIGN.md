# 05 · API Design

> **Status:** Living · Authored in WP5 (backend half) — this file didn't exist before, despite being
> referenced elsewhere; see `docs/15_PROGRESS.md`'s WP5 entry. Describes the FastAPI contract the
> WP5 frontend builds against. Mirrors `m516/api/{routes,schemas,state}.py` — reconcile if they diverge.

## Design principles

- **Thin layer.** Every endpoint is a projection of what Modules 1–4 already produce (`DiscoveryResult`,
  `Finding[]`, `ReportData` — see `03_DOMAIN_MODEL.md` and `m516/report/template.py`). No business logic,
  aggregation, or scoring lives in `m516/api/`.
- **No new persistence.** Scan state is an in-memory dict (`m516/api/state.py`), not Postgres — the
  POC never wired a DB, and `02_ARCHITECTURE.md` documents "no queues/workers" as deliberate. State is
  lost on process restart; acceptable for a single demo session, not for production.
- **No auth.** Per ADR-010, the POC has no login/roles. Every endpoint is open. CORS is permissive
  (`allow_origins=["*"]`) for the same reason — nothing here needs protecting yet.
- **Pack-agnostic (golden rule).** No endpoint hard-codes `"nigeria-banking"`. A caller either supplies
  `pack_id` on `POST /scans`, or the deployment sets `DEFAULT_PACK_ID` (see `.env.example`).

## Scan lifecycle

```
POST /api/scans  →  status: pending
                     (BackgroundTasks runs the pipeline in a thread — not a queue/worker; see
                      m516/pipeline.py's stage callback)
                  →  status: running, stage: discovery → enrichment → compliance → report
                  →  status: done   (result available)
                     or
                     status: error (error field set)
```

`GET /api/scans/{scan_id}` is the poll endpoint the frontend uses for FR-5.1's live progress. Once
`status == "done"`, the four data endpoints and the PDF endpoint become available.

## Endpoints

### `POST /api/scans`
Start a scan.

Request body:
```json
{ "domain": "example.com", "pack_id": "nigeria-banking" }
```
`pack_id` is optional — falls back to `Config.default_pack_id` (env `DEFAULT_PACK_ID`); `400` if
neither is set, or if the resolved pack has no `pack.yaml` under `Config.packs_root` (env
`PACKS_ROOT`, default `packs/`).

Response `202`:
```json
{ "scan_id": "…", "domain": "example.com", "pack_id": "nigeria-banking",
  "status": "pending", "stage": null, "error": null,
  "started_at": "2026-07-21T12:00:00Z", "finished_at": null }
```

### `GET /api/scans/{scan_id}`
Same shape as the `POST` response, reflecting current state. `404` if `scan_id` is unknown.

### `GET /api/scans/{scan_id}/dashboard` (FR-5.2)
`409` if not yet `done` (body names the current `stage`), `409` with the error if `status == "error"`.
Otherwise the scan's `ReportData` summary fields: `domain`, `generated_at`, `report_title`,
`primary_regulator`, `pack_display_name`, `executive_summary`, `severity_counts`, `asset_count`,
`service_count`, `finding_count`.

### `GET /api/scans/{scan_id}/assets` (FR-5.3)
List of `report.template.AssetSummary`: `ip`, `hostname`, `domain`, `country`, `is_behind_waf`,
`service_count`, `cert_detection_level`, `sources`.

### `GET /api/scans/{scan_id}/findings` (FR-5.4)
Ranked list of findings: `asset` (ip/hostname/domain/country/is_behind_waf), `service`
(port/protocol/name/product/version/cpe), `cve_ids`, `cvss`, `contextual_score`, `severity`,
`explanation`, `match_confidence`, `exploitability_score`, `impact_score`, `compliance` (list of
`{framework, clause, status, remediation}`).

`explanation` is the deterministic, rules-based text from `m516/enrichment/scoring.py` — **not** an
LLM-generated "exploitation narrative"; the Streamlit demo made the same honesty call (calling it "Why
it matters" rather than the mockup's "Exploitation Scenario"). The frontend should follow the same
naming, not imply LLM narrative that doesn't exist yet.

### `GET /api/scans/{scan_id}/compliance` (FR-5.5)
List of compliance gaps grouped by clause: `framework`, `clause`, `clause_title`, `status`
(`compliant`/`partial`/`non-compliant`/`unmapped`), `remediation`, `finding_refs` (which findings cited
this clause). **Until an LLM is wired into `m516/compliance/mapper.py` (still open, see
`15_PROGRESS.md`), every `status` will read `"unmapped"`** — this is honest, not a bug; the frontend
must render `unmapped` as "candidate clause, not yet classified", never as a false "compliant".

### `GET /api/scans/{scan_id}/report.pdf` (FR-4.2 / FR-5.5)
The rendered PDF (`m516/report/render.py`) as `application/pdf`.

### `GET /api/packs`
Lists every pack under `Config.packs_root` that has a `pack.yaml`: `id`, `display_name`, `sector`,
`home_country`. Lets the frontend offer a pack picker without the API hard-coding pack names.

### `GET /api/health`
`{"status": "ok"}` — no external calls, used for basic liveness checks.

## Not built in this half of WP5

- The React frontend (next session) — this doc is what it should build against.
- Any authentication/authorization (ADR-010: out of scope for the POC).
- Persistence across restarts (see "No new persistence" above).
- Concurrency guarantees beyond Python's GIL-level dict safety — fine for a single demo user, not for
  multiple simultaneous scans of the same `scan_id` (impossible by construction — ids are UUIDs) or
  heavy concurrent load (out of scope for a POC demo).
