# API and Data Contracts

**Purpose:** Record cross-team interfaces for frontend, Go backend, Python scientific engine, and data integration (issue #026).  
**Status:** **Backend-finalized draft (v0.2, implementation-aligned)** — reflects the current Go backend implementation in `backend/` for team review/final sign-off. Items dependent on real NASA data, the scientific engine, and team decisions remain draft/TBD. Breaking changes must be versioned and communicated.

> **Scientific integrity:** Go backend does not perform scientific calculations and does not fabricate NASA observations or scientific results. `completed`/results/summary/cells/report are only valid when backed by verified engine outputs and agreed ingestion rules. **No synthetic data is used.**



## 1. Versioning and conventions

- **Contract version:** `0.1-draft` (update when finalized).
- **Encoding:** UTF-8 JSON for HTTP/service payloads unless otherwise agreed; scientific arrays may use agreed binary/columnar formats for efficiency if documented.
- **Coordinates:** WGS84 longitude/latitude in decimal degrees unless specified. Preserve native dataset grid indices/coordinates.
- **Time:** ISO 8601 dates/timestamps (UTC where applicable). Periods expressed as inclusive bounds or explicit start/end with documented convention.
- **Units:** always explicit in metadata and/or fields (never implied).
- **Errors:** consistent machine-readable error object (see §4.4).
- **Synthetic data:** not used. All investigation data/results must come from verified, contract-compliant sources (real NASA observations and agreed scientific processing).

## 2. Observation handoff contract (Data integration → Scientific engine)
**Owners:** Member 2 & 3 (finalize in #031). **Record details also in:** `docs/DATA_SOURCES.md`.

### 2.1 Required content
- **Dimensions/coordinates:** e.g. `time`, `lat`, `lon` (and/or cell id) matching native grid; coordinate reference and resolution documented.
- **Variables:** precipitation (and quality-related variables/flags) with units and fill/missing semantics.
- **Quality/mask:** per-observation or per-cell quality indicators sufficient to compute completeness and exclusions.
- **Metadata:** dataset short name/title, version, DOI (when available), retrieval/access timestamp, spatial bounds, temporal period, processing/subsetting notes.

### 2.2 Missing/invalid handling
- Missing values must be explicitly represented (e.g. NaN/mask/fill value documented) — never silently imputed.
- Invalid/excluded observations must be traceable (reason or flag).
- Provide observation counts and completeness inputs for downstream analysis.

### 2.3 Example (illustrative, not final)
```json
{
  "contract": "observation-handoff",
  "version": "0.1-draft",
  "dataset": {"short_name": "GPM_3IMERGM", "version": "07", "source": "NASA"},
  "retrieved_at": "2026-11-14T00:00:00Z",
  "bounds": {"min_lon": 33.9, "min_lat": -4.7, "max_lon": 41.9, "max_lat": 5.5},
  "period": {"start": "2001-01-01", "end": "2020-12-31"},
  "grid": {"crs": "EPSG:4326", "resolution_deg": 0.1, "ordering": "row-major"},
  "variables": {
    "precipitation": {"units": "mm/month", "description": "monthly precipitation"}
  },
  "quality": {"flags": "documented per #031", "completeness_method": "documented per #031"}
}
```
(Actual array payload format/file reference to be agreed in #031/#034.)

## 3. Python analysis request/response (Go backend ↔ Scientific engine)
**Owners:** Members 3 & 4 (finalize in #034/#016).

### 3.1 Transport (to be agreed)
- Option A: HTTP service (recommended for clear contracts/timeouts). Option B: CLI/worker invocation.  
- **Decision placeholder:** record chosen protocol, base URL/command, auth (if any), and timeout/retry expectations here when agreed.

### 3.2 Request (proposed fields)
- `execution_id` / correlation id
- `investigation_id` (e.g. `INV-001`)
- `dataset` + `version` references
- `observation_ref` (path/URI/object reference or inline pointer to handoff payload)
- `bounds`, `period`
- `config`: aggregation (monthly/annual/seasonal), season definitions (if any), minimum completeness thresholds, trend test options, autocorrelation handling, multiple-testing/FDR settings, significance level(s)
- `engine_version`/`schema_version`

### 3.3 Response (proposed fields)
Per-cell results must support all MVP measurements:
- identifiers/coordinates (cell id, lat/lon or geometry reference)
- `n_observations`, `completeness`
- `mean_precipitation` (+ units)
- `trend_direction`
- `sens_slope` (+ units, confidence interval)
- `mann_kendall` statistic/tau as applicable, `p_value`
- adjusted significance / FDR fields (as applicable)
- `classification` ∈ {`significant_increase`, `significant_decrease`, `no_significant_trend`, `insufficient_data`, `inconclusive`}
- quality/assumption flags
- `run_metadata`: methods, parameters, software/methodology version, timestamps, dataset/version, bounds, period

### 3.4 Example response fragment (illustrative)
```json
{
  "contract": "analysis-response",
  "version": "0.1-draft",
  "execution_id": "exec_123",
  "status": "completed",
  "cells": [
    {
      "cell_id": "r120c045",
      "lat": -1.35,
      "lon": 36.85,
      "n_observations": 240,
      "completeness": 0.98,
      "mean": {"value": 85.2, "units": "mm/month"},
      "sens_slope": {"value": -1.4, "units": "mm/month/year", "ci_lower": -2.6, "ci_upper": -0.2},
      "mann_kendall": {"p_value": 0.01},
      "classification": "significant_decrease",
      "flags": []
    }
  ],
  "run_metadata": {
    "methods": ["mann_kendall", "sens_slope", "fdr_bh"],
    "alpha": 0.05,
    "engine_version": "TBD"
  }
}
```

## 4. Backend ↔ Frontend HTTP API (implemented draft)
**Base path:** `/api/v1` (also `GET /api/health` for compatibility).

### 4.1 Health
- `GET /health`, `GET /api/v1/health` → `200 {"status":"ok","service":"greengen-backend","database":{"status":"ok|unavailable|not_configured", ...}}`

### 4.2 Investigations
- `GET /api/v1/investigations` → `200 {"investigations":[...], "count": n}` (DB-backed when configured, seeded fallback; no fabricated results)
- `GET /api/v1/investigations/{id}` → `200 {"investigation": {...}}` or `404 NOT_FOUND`
- `POST /api/v1/executions/validate` — draft validation
  - Request: `{"investigation_id":"INV-001","bounds":{"min_lon","min_lat","max_lon","max_lat"},"period":{"start":"YYYY-MM-DD","end":"YYYY-MM-DD"},"options"?:{}}`
  - Response: `200 {"valid":true, ...}` or `422 {"valid":false,"issues":[{"field","issue"}],"error":{"code":"VALIDATION_ERROR",...}}`
  - Enforces shape/range/order, availability status, and draft investigation-scoped suggested bounds/period when present. Only investigations with `availability_status=available` can be executed. No synthetic data is used.

### 4.3 Executions
- `POST /api/v1/executions` — submit (validated)
  - Headers/body: supports `Idempotency-Key` / `X-Idempotency-Key` or `idempotency_key` (draft; in-memory replay implemented, DB persistence via migration `000002` when applied)
  - Success (accepted/recorded): `202 {"execution_id","status","execution":{id,investigation_id,status,period_start,period_end,error_code?,error_message?,requested_at,started_at?,completed_at?,updated_at},"accepted":true,"message"}`
  - Validation failure: `422 VALIDATION_ERROR` with issues/details (no execution created for invalid/unavailable requests)
  - Behavior: engine unconfigured/submission failure → recorded as `failed` with explicit error (`ENGINE_UNAVAILABLE`/`ENGINE_SUBMISSION_FAILED`), no fabricated results; draft engine submit success → `queued`.
- `GET /api/v1/executions/{id}` → `200 {"execution": {...}}` or `404 NOT_FOUND`
- `POST /api/v1/executions/{id}/refresh` → `200 {"execution": {...}, "message": "..."}` or `404` (best-effort engine status sync; **completed not auto-applied without verified result ingestion**)

### 4.4 Results and reports (implemented draft, integrity-preserving)
- `GET /api/v1/executions/{id}/results` → `200` with stored result payload/provenance when verified results are ingested, else `409 {"error":{"code":"RESULTS_UNAVAILABLE",...},"execution":{...}}` or `404`
- `GET /api/v1/executions/{id}/summary` → `200` with derived summary/provenance when results ingested, else `409 SUMMARY_UNAVAILABLE` or `404`
- `GET /api/v1/executions/{id}/cells/{cellId}` → `200` with matched cell/provenance when present, `404` if cell missing in ingested results, or `409 CELL_RESULTS_UNAVAILABLE` if no results ingested
- `GET /api/v1/executions/{id}/report` → `200` with draft JSON report/provenance when results ingested, else `409 REPORT_UNAVAILABLE` or `404`
- **Provenance/integrity:** no synthetic data is used. Synthetic results (if provided by any source) are rejected and not ingested/served. Ingested results must be from verified, contract-compliant sources; final payload formats (grid/GeoJSON/tiles, full time series, export formats) remain subject to team agreement (#041/#043/#046/#048).

### 4.5 Execution statuses (implemented)
`pending | queued | running | completed | failed`.
- Submission without engine → `failed` (`ENGINE_UNAVAILABLE`); engine submit accepted → `queued`.
- Refresh performs best-effort engine sync for non-terminal states. `completed` is set only when verified, non-synthetic results are ingested/persisted; auto-completion without ingested results is not performed. Synthetic results are rejected (`SYNTHETIC_DATA_REJECTED`) and not used.
- **Real-science finalization:** ingestion must enforce verified provenance and agreed scientific output contracts before serving as finalized scientific results. No synthetic data is used.


### 4.3 Legend/classification semantics (frontend-backend-engine alignment)
- `significant_increase`: statistically significant increasing trend per agreed method/threshold.
- `significant_decrease`: statistically significant decreasing trend.
- `no_significant_trend`: evidence does not establish a significant trend (**do not label "stable"**).
- `insufficient_data`: inadequate observations/completeness for reliable analysis.
- `inconclusive`: sensitive to assumptions or otherwise not interpretable as a clear class (criteria documented).

### 4.6 Error format (implemented draft)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable summary",
    "details": [{"field": "period.start", "issue": "outside supported range"}]
  }
}
```
Common codes: `VALIDATION_ERROR` (422/400), `NOT_FOUND` (404), `RESULTS_UNAVAILABLE`/`SUMMARY_UNAVAILABLE`/`CELL_RESULTS_UNAVAILABLE`/`REPORT_UNAVAILABLE` (409), `INTERNAL_ERROR` (500), `ENGINE_UNAVAILABLE`/`ENGINE_SUBMISSION_FAILED` (execution state/errors). HTTP status codes reflect failure.


### 4.5 Current prototype endpoints (informative)
The existing prototype exposes read-only precomputed endpoints under `/api/*` (e.g. `/api/health`, `/api/variables`, `/api/layers`, `/api/report`, `/api/timeseries`) and serves overlays/static assets. These inform UX but are **not** the final execution-based contract above.

## 5. Security and operational notes (to refine)
- No secrets in repo; use environment variables for credentials/endpoints.
- Apply timeouts, retries with backoff for external calls, and idempotent execution handling where possible.
- Rate/size limits for large grid responses (pagination/tiling/compression).

## 6. Open decisions

- [ ] Final observation handoff format (NetCDF/Zarr/Parquet/JSON metadata + array store) (#031)
- [ ] Go↔Python protocol and deployment model (#016/#034)
- [ ] Grid delivery format for MapLibre (GeoJSON, vector tiles, raster/PNG layers, or hybrid) (#046/#019)
- [ ] Report export formats and generation ownership (#048/#043)
- [ ] Authentication/authorization (if required beyond hackathon demo)

## 7. Change history

| Date | Version | Notes |
|---|---|---|
| 2026-11-14 | 0.1-draft | Initial draft contracts and examples for #026. |
| 2026-11-15 | 0.2-backend-draft | Aligned with current Go backend implementation (endpoints, validation, execution lifecycle, idempotency/refresh drafts, explicit unavailable result states, dev/test flags). Pending team sign-off and real data/engine/result ingestion contracts. |

