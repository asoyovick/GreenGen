# Data Sources

This document records the datasets the project is configured to use, what was
verified, and what was **not** run. Synthetic mode uses no NASA observations.

## Verification status (2026-11-13 UTC)

- **NASA CMR catalog:** reachable from this environment.
- **Earthdata Login credentials:** **not available** (`EARTHDATA_USERNAME` /
  `EARTHDATA_PASSWORD` and `~/.netrc` absent), so **no authenticated downloads
  were run** and **no real trend layers were produced**.
- **Real pipeline dry-run:** `python scripts/run_pipeline.py --real --dry-run`
  was run after enabling credential-free CMR search. It queried CMR only; it did
  not download files, prepare cubes, compute trends, or write a real pipeline
  manifest.

CMR short names/versions below were checked on 2026-11-13. **DOIs are
intentionally left as TODO** because the CMR collection endpoint used for this
verification did not return DOI values; confirm DOIs from the dataset landing
pages in Earthdata Search before publishing.

## Configured real datasets

| Variable | Role | Short name | Version | DAAC | Native resolution | Period in config | CMR dry-run granules | Format | Model-based | Notes / DOI |
|---|---|---|---|---|---|---|---|---|---|---|
| Precipitation | `precipitation` | `GPM_3IMERGM` | `07` | GES DISC | 0.1° | 2002-01..2024-12 | **276** | NetCDF4 | No | Monthly rate in mm/hr; convert to mm/month (`24 * days_in_month`). DOI: **TODO**. |
| Vegetation greenness (NDVI) | `vegetation` | `MOD13C2` | `061` | LP DAAC | 0.05° | 2000-02..2024-12 (app period clipped to 2002-01..2024-12) | **299** | **HDF4** | No | Requires Harmony/rioxarray/pyhdf conversion before prep; pipeline must not fabricate. Apply scale factor (0.0001) as configured. DOI: **TODO**. |
| Air temperature at 2 m | `temperature` | `M2TMNXSLV` | `5.12.4` | GES DISC | 0.5° × 0.625° | 2002-01..2024-12 | **276** | NetCDF4 | **Yes** | MERRA-2 reanalysis (`T2M`, K → °C). Label as model-based, not a direct observation. DOI: **TODO**. |
| Terrestrial water storage | `water_storage` | `TELLUS_GRAC-GRFO_MASCON_GRID_RL06.3_V4` | `RL06.3Mv04` | PO.DAAC | 0.5° grid, effective resolution hundreds of km | 2002-04..2024-12 | **1** | NetCDF4 | No | Mascon product; contains the 2017–2018 mission gap — leave missing, never interpolate. Longitudes may be 0–360 (normalized in prep). DOI: **TODO**. |

Source of record for pipeline settings: [`config/datasets.yaml`](../config/datasets.yaml).

## Synthetic mode

Synthetic layers are generated locally with no network access:

- Generator: `scripts/make_synthetic_data.py`
- Variables: `precipitation`, `vegetation`, `temperature`
- Grid/period: 0.5°, 2002-01..2024-12 (same as app config)
- Properties: planted opposite trends, seasonal cycle, noise, NaN NDVI over
  ocean, `synthetic=true` in every artifact
- UI/API disclosure: persistent banner and `X-GCE-Synthetic`/payload flags

Synthetic data must never be mixed with real layers and must never be cited as
NASA data.

## Other bundled assets

| Asset | Path | Purpose | License / provenance |
|---|---|---|---|
| Land geometry | `assets/ne_110m_land.geojson` | Offline base-map and land/ocean applicability mask for synthetic generation | Natural Earth 110m, public domain |
| Frontend base geometry | `frontend/public/data/land.geojson` | Offline map rendering in the browser | Committed copy derived from Natural Earth public-domain data |
| Offline gazetteer | `frontend/src/data/places.js` | Small built-in place list for demos | Curated project data, not a geocoding service |

## How to produce a real, citable run

1. Create an Earthdata Login and approve GES DISC, LP DAAC, and PO.DAAC
   applications.
2. Provide credentials via `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` or
   `~/.netrc`.
3. Run `make verify-earthdata` and `make pipeline-real` (or stepwise with
   `scripts/run_pipeline.py --real`).
4. Record the generated `layers/real/pipeline_manifest.json`, exact file counts,
   commit hash, and confirmed DOIs from Earthdata Search in this file and in
   `docs/VALIDATION.md`.
5. Do **not** commit downloaded raw data, caches, or generated layers (`data/`,
   `layers/` are git-ignored by design).

## Acknowledgement

If real NASA data are used, acknowledge NASA and the relevant DAACs (GES DISC,
LP DAAC, PO.DAAC) and cite each dataset by its confirmed DOI/version. The
current repository state does not include a completed real-data citation set.
