# API and Data Contracts

**Purpose:** Record agreed cross-team interfaces so frontend, Go backend, Python scientific engine, and data integration can develop in parallel (issue #026).  
**Status:** **Draft v0.1** — proposed contracts to be reviewed/finalized in #031, #034, #016, #040, #043. Breaking changes must be versioned and communicated.

## 1. Versioning and conventions

- **Contract version:** `0.1-draft` (update when finalized).
- **Encoding:** UTF-8 JSON for HTTP/service payloads unless otherwise agreed; scientific arrays may use agreed binary/columnar formats for efficiency if documented.
- **Coordinates:** WGS84 longitude/latitude in decimal degrees unless specified. Preserve native dataset grid indices/coordinates.
- **Time:** ISO 8601 dates/timestamps (UTC where applicable). Periods expressed as inclusive bounds or explicit start/end with documented convention.
- **Units:** always explicit in metadata and/or fields (never implied).
- **Errors:** consistent machine-readable error object (see §4.4).
- **Synthetic data:** permitted only in clearly labelled tests/fixtures; never in real investigation results.

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

## 4. Backend ↔ Frontend HTTP API (proposed)
**Owners:** Members 4 & 5 (finalize in #040/#014/#043). Base path placeholder: `/api/v1` (subject to final decision).

### 4.1 Investigations
- `GET /investigations` — list investigations (id, title, question, variables, dataset info, availability/status: implemented vs planned).
- `GET /investigations/{id}` — details, supported bounds/period constraints, configuration schema.

### 4.2 Executions
- `POST /executions` — submit investigation execution.
  - Request: `investigation_id`, `bounds` (bbox/polygon or preset id), `period` (`start`, `end`), options.
  - Response: `execution_id`, initial `status`.
- `GET /executions/{id}` — status and progress (`queued|retrieving|analyzing|completed|failed` + timestamps/errors).
- `GET /executions/{id}/results` — grid-level results (GeoJSON/tiles/vector format TBD in #046) with classification and stats; supports filtering/pagination/tiling as needed.
- `GET /executions/{id}/cells/{cellId}` — single-cell statistics and time series (observations, annual/monthly as available, trend line inputs).
- `GET /executions/{id}/summary` — aggregate counts, provenance, methodology/config summary.
- `GET /executions/{id}/report` — report payload/metadata and export links/formats (TBD).

### 4.3 Legend/classification semantics (frontend-backend-engine alignment)
- `significant_increase`: statistically significant increasing trend per agreed method/threshold.
- `significant_decrease`: statistically significant decreasing trend.
- `no_significant_trend`: evidence does not establish a significant trend (**do not label "stable"**).
- `insufficient_data`: inadequate observations/completeness for reliable analysis.
- `inconclusive`: sensitive to assumptions or otherwise not interpretable as a clear class (criteria documented).

### 4.4 Error format (proposed)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable summary",
    "details": [{"field": "period.start", "issue": "outside supported range"}],
    "request_id": "optional-correlation-id"
  }
}
```
HTTP status codes should reflect the failure (400 validation, 404 not found, 409 conflict, 422 unprocessable, 500/503 server/service issues, etc.).

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
