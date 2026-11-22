# Reproducibility Procedures

**Purpose:** Document how to reproduce results from recorded provenance (issue #054).  
**Rule:** Reproduction must use real, verified data sources and recorded configuration. No synthetic data may be presented as real NASA observations/results.

## 1. Reproducibility requirements

Every investigation execution/result should record enough provenance to reproduce:
- dataset short name, version, DOI (when available)
- retrieval timestamp and query/subsetting parameters
- geographical bounds and temporal period
- observation reference/manifest/checksums
- processing configuration (aggregation, min months/years, completeness thresholds)
- statistical methods (Mann-Kendall variant, Theil-Sen, FDR, alpha, CI level)
- software/methodology versions (engine version, dependency versions, git commit)
- data quality/completeness summary and exclusions
- known limitations

## 2. Environment setup

```bash
# Clone and enter repo
git clone <repo-url>
cd GreenGen

# Python (scientific engine / scripts)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Go backend
cd backend && go test ./... && cd ..

# Frontend
cd frontend && npm ci && npm run build && cd ..
```

Record versions:
```bash
git rev-parse HEAD
python --version
go version
node --version
```

## 3. Reproduce a data retrieval (real NASA sample)

Prerequisites: NASA Earthdata Login credentials.

```bash
# Discover metadata
python scripts/discover_imerg_cmr.py --short-name GPM_3IMERGM --version 07 \
  --bbox 33.9 -4.7 41.9 5.5 --start 2001-01-01 --end 2020-12-31 \
  --out docs/nasa-data-guides/imerg_cmr_discovery.json

# Dry-run granule lookup
python nasa-earthdata-access/scripts/download_granules.py \
  --short-name GPM_3IMERGM --version 07 \
  --start 2018-01-01 --end 2018-12-31 \
  --bbox 33.9 -4.7 41.9 5.5 --dry-run

# Download small real sample
python nasa-earthdata-access/scripts/download_granules.py \
  --short-name GPM_3IMERGM --version 07 \
  --start 2018-01-01 --end 2018-12-31 \
  --bbox 33.9 -4.7 41.9 5.5 \
  --out data/raw/imerg_kenya_sample
```

Verify:
- `manifest.json` contains expected granule count/files.
- Fill in DOI from dataset landing page.
- Record checksums: `sha256sum data/raw/imerg_kenya_sample/* > data/raw/imerg_kenya_sample/SHA256SUMS`.
- Update `docs/DATA_SOURCES.md` sample status.

## 4. Reproduce a scientific analysis (from observation payload)

Given a contract-compliant observation payload/reference and config:

```bash
# Start scientific engine
PYTHONPATH=. python -m uvicorn scientific_engine.service:app --host 127.0.0.1 --port 8090

# Submit analysis (example shape - use real observation_ref and recorded config)
curl -s http://127.0.0.1:8090/v1/analyses \
  -H 'Content-Type: application/json' \
  -d '{
    "execution_id":"repro-example",
    "investigation_id":"INV-001",
    "observation_ref":"data/raw/imerg_kenya_sample/<file>.nc",
    "variable":"precipitation",
    "bounds":{"min_lon":33.9,"min_lat":-4.7,"max_lon":41.9,"max_lat":5.5},
    "period":{"start":"2018-01-01","end":"2018-12-31"},
    "config":{"min_months":9,"min_years":10,"ok_years":15,"alpha":0.05},
    "dataset":{"short_name":"GPM_3IMERGM","version":"07"}
  }'
```

Compare reproduced output against original:
- same `run_metadata.methods` and `run_metadata.parameters`
- same dataset/version/bounds/period
- same per-cell classification for identical inputs
- numeric differences explained only by documented software/version differences

## 5. Reproduce backend execution flow

```bash
# Run backend (configure DB/engine env as needed)
cd backend
go run ./cmd/api

# Submit execution
curl -s http://127.0.0.1:8080/api/v1/executions \
  -H 'Content-Type: application/json' \
  -d '{"investigation_id":"INV-001","bounds":{"min_lon":33.9,"min_lat":-4.7,"max_lon":41.9,"max_lat":5.5},"period":{"start":"2001-01-01","end":"2020-12-31"}}'

# Poll status/results
curl -s http://127.0.0.1:8080/api/v1/executions/<id>
curl -s http://127.0.0.1:8080/api/v1/executions/<id>/results
```

## 6. Worked example (controlled, labeled synthetic fixture for unit-test reproducibility only)

> **Synthetic fixture disclaimer:** The following is a programmatically generated test fixture used only to verify statistical behavior. It is **not** a NASA observation and must not be presented as a real investigation result.

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_scientific_engine.py -q
```

This verifies deterministic behavior for controlled inputs (trend detection, insufficient data, FDR, metadata). For real scientific claims, reproduce using actual NASA observations and record provenance.

## 7. Known reproducibility limitations

- Real NASA retrieval requires credentials and external service availability.
- Upstream dataset versions/reprocessing may change values; record version/DOI/retrieval date.
- Floating-point and dependency version differences can cause minor numeric drift; document tolerances.
- Some environments may lack Python/Go dependencies; use documented versions and lockfiles where available.
