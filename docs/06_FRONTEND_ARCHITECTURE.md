# 06 · Frontend Architecture

> **Status:** Living · Authored in WP5's frontend half — this file didn't exist before, despite being
> referenced elsewhere (same gap `05_API_DESIGN.md` had before WP5's backend half). Describes
> `frontend/`. Mirrors `docs/05_API_DESIGN.md`'s contract — reconcile there first if they diverge.

## Tooling

**Vite + React + TypeScript**, no router, no state-management library (`frontend/package.json`).

- A router (React Router etc.) adds a dependency for URLs nothing in FR-5 needs — there's no
  deep-linking requirement, and the five screens are switched by local React state
  (`frontend/src/App.tsx`), mirroring `demo/streamlit_app.py`'s sidebar-nav pattern.
- No React Query/Redux — the whole app talks to one API around one concept (a scan). A small typed
  `fetch` wrapper (`src/api/client.ts`) plus `useEffect`/`setInterval` polling (`src/hooks/useScan.ts`)
  is enough.
- No UI framework (MUI/Tailwind/etc.) — plain CSS keeps the bundle small and avoids fighting a
  component library to match the exact look already established.

## Shared palette — one source of truth

`src/styles/theme.css` reuses colors that already exist elsewhere in the project rather than inventing
a new palette:
- Background/primary/text from `.streamlit/config.toml` (`#0B1220` bg, `#22D3EE` primary, `#E5E7EB`
  text) — the Streamlit dev tool and this UI now look like the same product.
- Severity/status colors from `m516/report/render.py` (`#c0392b` critical/non-compliant, `#e67e22`
  high, `#f1c40f` medium/partial, `#27ae60` low/compliant, `#95a5a6` unmapped/neutral) — so the exported
  PDF and the live UI never disagree about what "critical" looks like.

## App structure

```
frontend/src/
├── main.tsx, App.tsx        # App.tsx: no scan yet -> ScanInitiation; else -> Shell (Sidebar + tab)
├── api/
│   ├── types.ts             # mirrors m516/api/schemas.py field-for-field
│   └── client.ts             # one function per docs/05_API_DESIGN.md endpoint, throws ApiError on !ok
├── hooks/useScan.ts          # createScan() + polls GET /api/scans/{id} until done|error
├── components/               # Sidebar, StatTile, SeverityBadge, StatusBadge, ProgressBanner, Waiting
├── pages/                    # ScanInitiation, Dashboard, AssetDiscovery, RiskScoring, Compliance
└── styles/theme.css
```

State lives only in `App.tsx`/`useScan.ts` (React state) — the scan id is lost on page refresh, the
same POC-scope simplification as the backend's in-memory `ScanState` (`m516/api/state.py`). Acceptable
for a demo session, not for production.

## Screen ↔ requirement mapping

| Screen | FR | Data source |
|---|---|---|
| `ScanInitiation` | FR-5.1 | `POST /api/scans`, `GET /api/packs` for the pack picker |
| `Dashboard` | FR-5.2 | `GET /api/scans/{id}/dashboard` |
| `AssetDiscovery` | FR-5.3 | `GET /api/scans/{id}/assets` |
| `RiskScoring` | FR-5.4 | `GET /api/scans/{id}/findings` |
| `Compliance` | FR-5.5 | `GET /api/scans/{id}/compliance`, PDF export via `report.pdf` |

"Live progress" (FR-5.1) is `useScan.ts` polling `GET /api/scans/{id}` every 1.5s while
`status` is `pending`/`running`, rendering the current `stage` in `ProgressBanner` — there is no
push/websocket channel, matching the backend's own no-queue/no-worker design (`02_ARCHITECTURE.md`).

## Deliberate departures from the `ui screens/*.jpg` mockups

Carried over from decisions already made and confirmed with the client (`docs/15_PROGRESS.md`):
- **No "Breach Monitor" or "Users & Roles" sidebar items** — both out of scope for the POC (ADR-010:
  no auth built at all).
- **No separate "Port Scanner" screen.** It isn't one of FR-5's five screens. Per-service/port detail
  is only available through `AssetDiscovery`'s `service_count` and, for CVE-eligible services, the full
  port/product/CPE detail already shown per finding on `RiskScoring` — there's no raw "all discovered
  ports" endpoint to back a dedicated screen, and adding one wasn't asked for.
- **"Exploitation Scenario" → "Why it matters"** on `RiskScoring`. The mockup's phrase reads as an
  LLM-generated narrative; the actual field (`Finding.explanation`) is the deterministic, rules-based
  text from `m516/enrichment/scoring.py` (ADR-007, no LLM in scoring). Same naming call
  `demo/streamlit_app.py` already made.
- **Compliance status is rendered honestly, not just relabeled.** Per `docs/05_API_DESIGN.md`, every
  `ComplianceGapOut.status` reads `"unmapped"` until an LLM is wired into `m516/compliance/mapper.py`
  (WP3, still gated on the client's provider choice). `StatusBadge` renders `unmapped` as **"Not yet
  classified"**, and the `Compliance` page shows an explicit banner when nothing has been classified —
  never a false "compliant" badge (BR-5, no fabrication).

## A gap found while building, not before

The original plan called for an "expandable per-asset services" row on `AssetDiscovery`, extrapolating
from the mockup's nested port detail. Building it revealed the API doesn't expose a full per-asset
service list — `AssetSummaryOut` (from `m516/report/template.py`'s `AssetSummary`) only carries
`service_count`, an integer; full service/port detail only exists per-finding (CVE-eligible services),
already shown on `RiskScoring`. Rather than widening the API contract mid-frontend-build,
`AssetDiscovery` stays a plain table of what `AssetSummaryOut` actually has. If per-asset raw service
detail becomes a real requirement later, it needs a new field on `AssetSummary`/`AssetSummaryOut` (a
backend change), not a frontend-only fix.

## Verification note

This environment has no browser automation tool. What was actually verified when this was built:
`npm run build` (TypeScript compiles, Vite production build succeeds), `npm run dev` boots without
errors, every page module transforms cleanly under Vite's dev server (requested directly, no 500s),
and a full scan lifecycle exercised over real HTTP against a fixture-backed instance of the real
FastAPI app (`POST /scans` → poll → `dashboard`/`assets`/`findings`/`compliance`/`report.pdf`, plus
CORS and 404 checks) — confirming the JSON shapes match `src/api/types.ts` exactly. **The rendered UI
itself was never visually inspected** — see `docs/16_SESSION_LOG.md`'s entry for this session for what
still needs a human to click through in a real browser.
