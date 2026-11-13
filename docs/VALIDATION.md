# Validation

This file records what was actually validated, how, and what remains unvalidated.
Dates are UTC.

## Summary

| Area | Status | Evidence |
|---|---|---|
| Synthetic data generation | **Validated** | `tests/test_synthetic_data.py`, generated manifests/attrs |
| Prep/trend pipeline (synthetic) | **Validated** | `tests/test_pipeline.py`, full synthetic run produced layers/overlays locally |
| Statistical helpers | **Validated (unit/targeted)** | `tests/test_quality.py` for FDR, anomaly/unit/coord helpers, wording/ranking |
| API contract and edge cases | **Validated** | `tests/test_api.py` on controlled fixtures (13 original + 7 added cases) |
| Real NASA catalog identities/counts | **Validated by CMR dry-run only** | `python scripts/run_pipeline.py --real --dry-run` on 2026-11-13 |
| Real NASA downloads/prep/trends | **Not run** | No Earthdata credentials in this environment |
| Real-result comparison against Giovanni/observations | **Not run** | Requires real layers; no real layers produced here |
| Frontend production build | **Validated** | `npm run build` succeeded (chart lazy-loaded) |
| Frontend interactive browser smoke | **Partially/previously validated** | Prior checkpoint records manual Playwright-core + system Chrome checks; not rerun as automated CI in this pass |

## Automated tests (this pass)

Command:

```bash
.venv/bin/python -m pytest -q
```

Result: **48 passed, 4 warnings in ~48s** (warnings: Starlette/httpx testclient
deprecation notice and Zarr consolidated-metadata user warnings).

Coverage added/relied on in this pass:

- **FDR:** `fdr_significant` keeps missing cells untested, suppresses/promotes
  only by BH-FDR result, and does not promote a lone non-significant p-value.
- **Units:** Kelvin→°C, IMERG-style mm/hr→mm/month using `days_in_month`, and
  scale-factor conversion; unknown ops rejected.
- **Coordinates:** 0–360→−180..180 normalization, lon sorting/value alignment,
  and `latitude/longitude` renaming/sorting.
- **Report wording/ranking:** significant increase/decrease text, non-significant
  text never claims “no change”, low-confidence caution, divergence wording, and
  significant rows ranked above larger but non-significant rows.
- **API:** `/api` contract, JSON 404, CORS preflight for dev origin, root
  serving built frontend when present, unknown-variable 404 lists available
  keys, and mode headers.

## Real pipeline dry-run (CMR only, 2026-11-13)

Command:

```bash
.venv/bin/python scripts/run_pipeline.py --real --dry-run
```

Outcome: **exit 0**. No credentials required, no files downloaded, no layers or
manifest written. CMR search results:

| Short name | Version | Granules found | Query window |
|---|---:|---:|---|
| `GPM_3IMERGM` | `07` | 276 | 2002-01-01..2024-12-31 |
| `MOD13C2` | `061` | 299 | 2000-02-01..2024-12-31 |
| `M2TMNXSLV` | `5.12.4` | 276 | 2002-01-01..2024-12-31 |
| `TELLUS_GRAC-GRFO_MASCON_GRID_RL06.3_V4` | `RL06.3Mv04` | 1 | 2002-04-01..2024-12-31 |

Notes:

- MOD13C2 is configured as HDF4; real prep would require conversion before use.
- TELLUS is a mascon time series product (1 granule in this query) with a known
  2017–2018 mission gap and coarse effective resolution.
- DOIs were not returned by the CMR endpoint used and remain TODO.

## Synthetic end-to-end state

The repository’s local working state (not committed) includes generated
synthetic layers/overlays used by the API and frontend checks:

- `layers/synthetic/*_trend.zarr`, `layers/synthetic/pipeline_manifest.json`
- `layers/overlays/synthetic/*.png` and metadata
- Prior manual API checks recorded in the checkpoint: land `(55,55)` returns 3
  variables with NDVI top; `(55,85)` shows NDVI decrease (`class=-1`);
  divergence at `(55,70)`; ocean `(0,-150)` excludes vegetation; no-data/invalid
  cases behave as specified.

## Not validated / blocked

- **Authenticated Earthdata download and real preprocessing:** blocked by missing
  credentials; cannot be claimed complete.
- **Real trend/significance outputs:** not generated.
- **Giovanni or literature comparison:** requires real outputs and was not run.
- **DOI correctness:** TODO pending manual confirmation on dataset landing
  pages.
- **Automated browser E2E:** Playwright browser binaries were not installed;
  prior smoke testing used a temporary Playwright-core run against system
  Chrome (per checkpoint) and was not rerun in this pass.

## Recommended validation after a credentialed real run

1. Re-run `make verify-earthdata`, `make pipeline-real`, and record manifests.
2. Spot-check unit ranges after prep (mm/month, °C, NDVI scaling, GRACE cm w.e.).
3. Compare selected locations/time series directions against Giovanni or source
   documentation.
4. Confirm FDR-significant area fractions are plausible (not near 0% or 100%
   without explanation).
5. Capture DOIs, versions, access date, and commit hash in `docs/DATA_SOURCES.md`
   and `docs/VALIDATION.md`.
