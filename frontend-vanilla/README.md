# GreenGen Frontend (Vanilla)

A vanilla HTML5/CSS3/JavaScript (ES modules) frontend for GreenGen, built to integrate with the Go backend API contracts in `docs/API_CONTRACTS.md` and to degrade gracefully against the current prototype precomputed `/api/*` endpoints.

## Requirements covered (incremental)
- No React/Next.js/Vue/Angular/TypeScript/Tailwind/Bootstrap
- Native browser APIs (Fetch, DOM, URL, AbortController) + modular ES modules
- MapLibre GL JS and Chart.js loaded as browser-compatible libraries on relevant pages
- Centralized API client/config (no hardcoded backend URLs in feature modules)
- Responsive, accessible layout foundations (skip link, focus states, semantic markup)
- Scientific integrity: no fabricated observations/results/classifications; missing/unavailable data shown explicitly

## Structure
- `index.html` — landing page
- `pages/` — investigations, investigation-details, explore, analysis, reports
- `css/` — variables, layout, components, map, charts, responsive
- `js/api/` — `client.js`, `investigations.js`, `analysis.js`, `reports.js`
- `js/components/` — navigation, notifications (plus map/charts/legend extensibility)
- `js/features/` — feature modules (to be expanded)
- `js/utils/` — validation, formatting, helpers
- `js/pages/` — per-page controllers

## Run locally (required: local dev server)
ES modules and API requests require a server (not `file://`).

```bash
# from repo root
python3 -m http.server 5174 --directory frontend-vanilla
# then open http://127.0.0.1:5174
```

Configure backend target via HTML meta tags or `window.GREENGEN_CONFIG` before module load:
- `greengen-api-base` (e.g. `http://127.0.0.1:8000`)
- `greengen-api-prefix` (default `/api`)

## Backend integration notes
- **Planned (draft) contract:** `/api/v1/investigations`, `/api/v1/executions`, results/cells/summary/report as defined in `docs/API_CONTRACTS.md`.
- **Current prototype fallback:** `/api/health`, `/api/variables`, `/api/layers`, `/api/report`, `/api/timeseries` for precomputed read-only exploration.
- Execution submission/status is only shown as successful when the backend returns an execution identifier/status; unavailable endpoints are reported clearly (no simulated success).

## Status
Implemented as a foundation/initial pass (Phase 1–2 + key page flows). Further work: full grid GeoJSON rendering from execution results, richer report/export handling per final contract, place/region selection tools, and deeper integration tests against the Go backend.