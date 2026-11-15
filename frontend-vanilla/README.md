# GreenGen Frontend (Vanilla)

Vanilla HTML5/CSS3/JavaScript (ES modules) frontend for GreenGen (Global Change Explorer). It integrates with the Go backend draft contract (`/api/v1`, see `docs/API_CONTRACTS.md`) and can use labeled prototype `/api/*` read-only endpoints for exploration when available.

## Stack and constraints
- **Allowed:** HTML5, CSS3, vanilla JavaScript (ES6+ modules), MapLibre GL JS, Chart.js
- **Not used:** React/Next.js/Vue/Angular/TypeScript/Tailwind/Bootstrap/build system
- **Integration:** browser Fetch to Go backend REST APIs only (no direct Python engine/DB access)
- **Scientific integrity:** no frontend trend/statistical calculations, no fabricated observations/results, **no synthetic data used/presented**. Unavailable/unverified/missing data and contract gaps are shown explicitly.

## Application structure
- `index.html` — landing page
- `pages/` — `investigations`, `investigation-details`, `configure-investigation`, `results`, `explore`, `analysis`, `reports`
- `css/` — `variables`, `main`, `layout`, `components`, `map`, `charts`, `responsive`
- `js/config.js` — centralized runtime/API/map config
- `js/api/` — `client.js`, `investigations.js`, `analysis.js`, `reports.js`
- `js/components/` — navigation, notifications
- `js/features/` — shared feature modules (e.g. investigation normalization; map/chart adapters extensible)
- `js/pages/` — per-page controllers
- `js/utils/` — helpers, formatting, validation

## Run locally
ES modules and API requests require a local HTTP server (not `file://`).

```bash
# from repo root
python3 -m http.server 5174 --directory frontend-vanilla
# open http://127.0.0.1:5174
```

Start/configure the Go backend separately (default local example: `http://127.0.0.1:8080`). Ensure CORS allows the frontend origin when served from a different host/port.

## Configuration
Configure via `<meta>` tags in HTML or `window.GREENGEN_CONFIG` before module load:
- `meta[name="greengen-api-base"]` / `GREENGEN_CONFIG.apiBaseUrl`: backend base URL (e.g. `http://127.0.0.1:8080`, empty for same-origin)
- `meta[name="greengen-api-prefix"]` / `GREENGEN_CONFIG.apiPrefix`: prototype/read prefix (default `/api`)
- Contract prefix is `/api/v1` (`config.contractApiPrefix`)
- `GREENGEN_CONFIG.map.styleUrl`: MapLibre style URL (default demo tiles; configure an approved style/tiles for deployment)

## Implemented workflows (incremental)
- **Landing/catalogue/details:** backend-driven investigation list/details with availability/coverage/methodology/limitations; planned/unavailable investigations cannot be executed.
- **Configure investigation:** load investigation metadata, geographical selection (preset/point/manual coords + buffer-derived bbox, clear/update), historical period validation, parameter summary, backend validation (`POST /api/v1/executions/validate`) and submission (`POST /api/v1/executions`) with explicit error/unavailable handling.
- **Execution monitoring/results:** status load/refresh/polling (`/api/v1/executions/{id}`, `/refresh`), timeline/metadata, summary/results/cell/report retrieval with 409/404 unavailable handling, best-effort contract-driven map rendering when recognizable GeoJSON/cell geometry is returned, backend-provided time-series chart rendering when present.
- **Explore (location/precomputed):** labeled prototype read-only point inspection/time-series when available (not execution-based scientific results).
- **Reports:** load/render available report payload sections and JSON export attempt when supported by backend.

## Dependencies and known limitations
- **Real scientific E2E requires:** PostgreSQL+PostGIS, real NASA GPM IMERG data/retrieval + verified provenance, contract-compliant Python scientific engine, and verified (non-synthetic) result ingestion. Without these, executions/results are unavailable by design.
- **Contract-dependent (open/TBD):** grid delivery format for MapLibre (GeoJSON/tiles/raster), final per-cell schema, time-series payload, and report/export formats. UI renders only recognized backend-provided structures and reports unknown/unavailable formats explicitly.
- **Geographical UX:** preset/point/coordinate bbox selection implemented; place-name search/geocoding and polygon-draw tools are not included (no approved external service/dependency). Supported area/period are enforced by backend validation/metadata.
- **Testing:** JS syntax checks and API-level integration checks performed against seed-only backend; browser/manual E2E, accessibility/responsive QA, and validation against verified result payloads remain required when the full stack/contracts are available.

## Deployment notes
- Serve `frontend-vanilla/` as static files (any static server/CDN) over HTTP(S).
- Set `greengen-api-base` (or `window.GREENGEN_CONFIG.apiBaseUrl`) to the deployed Go backend URL and configure backend CORS for the frontend origin.
- Provide a production-appropriate MapLibre style/tiles/source configuration and ensure required CDN/library access or approved self-hosting for MapLibre/Chart.js.
- Do not deploy with fabricated/synthetic data or claims of completed analyses without verified backend outputs/provenance.
