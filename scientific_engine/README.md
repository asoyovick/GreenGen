# GreenGen Scientific Engine (Python)

Implements scientific processing for precipitation trend investigations (MVP: INV-001) per `docs/SCIENTIFIC_METHODOLOGY.md` and the draft Go↔Python contract in `docs/API_CONTRACTS.md`.

## Modules
- `aggregation.py` — monthly climatology/anomalies and annual aggregation with completeness thresholds (missing values never treated as zero).
- `trend.py` — Mann–Kendall trend test with Hamed–Rao autocorrelation correction and Theil–Sen slope + confidence interval.
- `reliability.py` — Benjamini–Hochberg FDR significance and grid-cell classification (`significant_increase`, `significant_decrease`, `no_significant_trend`, `insufficient_data`, `inconclusive`).
- `grid_analysis.py` — per-cell/grid analysis and run metadata/provenance assembly.
- `io.py` — loading verified observation inputs (NetCDF/Zarr); rejects synthetic-marked inputs.
- `service.py` — FastAPI HTTP service adapter for Go backend integration.

## HTTP contract (draft, implementation-aligned)
- `POST /v1/analyses` — submit analysis request, returns `{ "execution_id", "engine_job_reference", "status": "queued|..." }`
- `GET /v1/analyses/{id}` — returns `{ "execution_id", "status", "results"?, "error"? }`
- `GET /health` — service health

**Request (JSON, draft):**
```json
{
  "execution_id": "exec_123",
  "investigation_id": "INV-001",
  "observation_ref": "/path/to/verified_observations.zarr",
  "dataset": {"short_name": "GPM_3IMERGM", "version": "07"},
  "bounds": {"min_lon": 33.9, "min_lat": -4.7, "max_lon": 41.9, "max_lat": 5.5},
  "period": {"start": "2001-01-01", "end": "2020-12-31"},
  "config": {
    "variable": "precipitation",
    "min_months": 9,
    "min_years": 10,
    "ok_years": 15,
    "alpha": 0.05
  },
  "schema_version": "0.1-draft"
}
```

**Completed results (JSON, draft):** `results.status="completed"`, `results.cells[]` with per-cell identifiers/coordinates, `n_observations`, `n_years`, `completeness`, mean, `trend_direction`, `sens_slope` (value/units/CI), `mann_kendall` (p-value/tau/statistic/method), `significant_fdr`, `classification`, `flags`; plus `run_metadata` and `summary`. No synthetic data is emitted.

## Run
```bash
# from repo root (with dependencies installed)
PYTHONPATH=. uvicorn scientific_engine.service:app --host 0.0.0.0 --port 8090
# or
PYTHONPATH=. python -m uvicorn scientific_engine.service:app --host 0.0.0.0 --port 8090
```

Configure Go backend with `PYTHON_ENGINE_URL=http://<host>:8090`.

## Tests
```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_scientific_engine.py -q
```
Test fixtures are programmatically generated, clearly labeled synthetic arrays used only for isolated statistical validation (not NASA observations and not used as runtime results).
