# Quality Assessment and Known Limitations

**Purpose:** Final quality assessment against MVP acceptance criteria and published known limitations (issue #057).  
**Status:** Draft assessment — update before demo/release with latest evidence.  
**Date:** 2026-11-22

## 1. MVP acceptance checklist

Legend: **Pass** = evidence exists in repo/tests/docs; **Partial** = implemented in part or pending external validation; **Fail** = not met; **Blocked** = requires external credentials/data/team action.

### Data

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| System retrieves actual NASA GPM IMERG observations for supported investigations | Partial | `docs/DATA_SOURCES.md`, `nasa-earthdata-access/scripts/download_granules.py`, `scripts/discover_imerg_cmr.py` | Retrieval procedure/scripts documented; real sample retrieval requires Earthdata credentials and has not been committed as an artifact in this environment. |
| User can select supported geographical area and historical period | Partial | Backend validation in `backend/internal/service/investigations.go`, API contracts, frontend explorer/prototype | Supported bounds/period validation exists in backend draft; UI coverage depends on frontend path used. |
| Dataset metadata, version, and quality information preserved | Partial | `docs/DATA_SOURCES.md`, `scientific_engine/grid_analysis.py` run_metadata, backend provenance handling | Metadata fields are modeled; real-source metadata preservation must be confirmed with actual retrieved granules. |

### Scientific analysis

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| Observations processed correctly with transparent missing/incomplete handling | Pass (controlled tests) | `scientific_engine/aggregation.py`, `tests/test_scientific_engine.py` | Missing != zero; incomplete years excluded. Real-product edge cases need real-data validation. |
| Eligible grid cells analysed independently; native grid preserved where practical | Pass (engine design/tests) | `scientific_engine/grid_analysis.py` uses lat/lon grid cells; no resampling in engine | Grid alignment against native IMERG source pending real sample verification. |
| Trend direction and magnitude calculated with units and confidence/uncertainty | Pass (controlled tests) | `scientific_engine/trend.py`, tests | Theil-Sen slope + CI; units propagated from input/config. |
| Statistical significance evaluated appropriately; multiple testing addressed | Pass (controlled tests) | `scientific_engine/trend.py`, `scientific_engine/reliability.py`, tests | Hamed-Rao MK + BH FDR implemented; independent reference comparison in tests. |
| Insufficient/inconclusive results identified and not mislabelled | Pass (controlled tests) | `scientific_engine/reliability.py`, tests | `no_significant_trend` != `stable`; `insufficient_data` and `inconclusive` supported. |

### User experience

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| Users browse predefined investigations and distinguish implemented vs planned | Partial | `docs/INVESTIGATION_CATALOGUE.md`, backend investigation endpoints, frontend/prototype | Catalogue documented; UI needs to clearly surface implemented vs planned in all paths. |
| Users configure area/period, execute, and explore results | Partial | Go backend execution endpoints, prototype frontend, `frontend/src/App.jsx` | Two frontend paths exist (prototype and Vite app); end-to-end wiring to Go execution flow needs consolidation. |
| Users can understand findings, limitations, and how results were produced | Partial | `docs/SCIENTIFIC_METHODOLOGY.md`, report/provenance fields in engine/backend | Report/export UI and limitations visibility need further verification. |

### Reproducibility

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| Every investigation result records required provenance | Partial | `scientific_engine/grid_analysis.py` run_metadata, backend execution/result models, `docs/REPRODUCIBILITY.md` | Fields modeled; complete provenance depends on real data ingestion and persistence path. |

## 2. Known limitations

1. **Real NASA sample not committed in this environment.** Extraction procedure is documented, but actual GPM IMERG Kenya sample retrieval requires Earthdata credentials/network access and must be completed and recorded by a credentialed team member.
2. **End-to-end real-data validation pending.** Controlled synthetic fixtures validate statistical logic; they do not substitute for real IMERG data quality, grid alignment, and retrieval behavior.
3. **Dual frontend/prototype stacks.** The repo contains `frontend/` (Vite React prototype) and `frontend-vanilla/`, plus `src/api` prototype API. Target Next.js/Go/Python architecture is partially implemented; users should not assume all paths are production-equivalent.
4. **Async job queue is draft-level.** Python engine uses in-memory background threads; Go backend tracks execution states but full durable queue/worker semantics and retries need hardening for production.
5. **Seasonal precipitation analysis is limited.** Seasonal aggregation/season definitions need full implementation and validation for INV-001 seasonal outputs.
6. **No causal claims.** Trend detection identifies statistical patterns in observations; it does not attribute causes.
7. **Dependency/environment variability.** Python dependencies (xarray/scipy/pymannkendall/statsmodels/etc.) must be installed for engine tests; not all environments have them preinstalled.
8. **Security/ops hardening pending.** Auth, rate limits, production CORS, secrets management, observability, and deployment hardening require review before public deployment.

## 3. Evidence commands

```bash
# Go backend tests
cd backend && go test ./...

# Scientific engine tests (requires Python deps installed)
PYTHONPATH=. .venv/bin/python -m pytest tests/test_scientific_engine.py -q

# Frontend build (requires node deps installed)
cd frontend && npm run build
```

## 4. Release/demo recommendation

- **Demo-ready for controlled/internal walkthrough:** Yes, with explicit limitations.
- **Claim as fully scientifically validated on real NASA data:** No, until real sample retrieval, grid alignment checks, and independent review are completed.
- **Claims to avoid:** "stable" for non-significant trends; causal attribution; real-data validation not yet performed.

## 5. Change log

| Date | Change |
|---|---|
| 2026-11-22 | Initial quality assessment and known limitations published. |
