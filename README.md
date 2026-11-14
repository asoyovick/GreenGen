# Global Change Explorer

A map-first tool for exploring **observed change** in gridded Earth-science
variables. Click a location to see which variables changed there, by how much
per decade, and whether the trend is **statistically significant after
Benjamini–Hochberg FDR correction** (Mann–Kendall with Hamed–Rao
autocorrelation correction).

> **Observed change only, not a forecast.** “No statistically significant
> change detected” means the evidence is insufficient after correction — not
> that nothing changed.

## Status

- **Synthetic mode (default): fully working offline.** Deterministic fake cubes
  with planted trends power the full pipeline, API, and frontend.
- **Real NASA mode: scripted and catalog-verified, not executed here.** NASA
  CMR is reachable and dataset IDs/versions/granule counts were checked via a
  credential-free dry-run on 2026-11-13, but **no Earthdata credentials were
  available**, so no authenticated downloads, no real prep, and no real trend
  layers were produced in this environment. NDVI (MOD13C2, HDF4) also requires
  conversion before prep. See [docs/VALIDATION.md](docs/VALIDATION.md) and
  [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

## Quick start (synthetic demo)

```bash
make install          # create .venv, install Python deps, install frontend deps
make synthetic        # generate clearly fake 0.5° monthly cubes
make pipeline         # prep + trends + overlays (takes a few minutes)
make demo             # build frontend and serve UI+API on http://127.0.0.1:8000
```

For development:

```bash
make api              # FastAPI on :8000 (serves built frontend if present)
make frontend         # Vite dev server on :5173, proxies /api and /overlays
```

## What the app shows

- **Offline world map** with precomputed trend overlays (class/significance
  layers and change-score view), layer switcher, legend, and opacity control.
- **Click / search / coordinate entry** to select a 0.5° cell.
- **Ranked change report**: applicable variables, rate per decade with units,
  FDR-corrected verdict, standardized trend, years used, low-confidence flag,
  nearby comparison/divergence, and provenance (period, source, model-based /
  synthetic labels).
- **Annual anomaly time series** (Plotly) with the Theil–Sen trend line
  reconstructed from stored values.
- **Export:** Markdown, JSON, and copyable share link (URL encodes location and
  layer).
- **Persistent synthetic banner** and metadata when running in synthetic mode.

Synthetic planted examples (useful for demo): increasing trends around
~55°N,55°E and decreasing/opposite patterns around ~55°N,85°E for
precipitation/vegetation, land-only vegetation excluded over ocean, and
divergence near the boundary.

## API

The API only reads precomputed layers; it never downloads data or computes
trends on demand.

| Endpoint | Description |
|---|---|
| `GET /api` | API metadata and endpoint list |
| `GET /api/health` | Mode, loaded variables, overlays, grid/period, errors |
| `GET /api/variables` | Variable metadata (units, surface, model-based, period, provenance) |
| `GET /api/layers` | Overlay image URLs, bounds, legends, default layer |
| `GET /api/report?lat=&lon=&window=` | Ranked per-cell report and nearby comparison |
| `GET /api/timeseries?lat=&lon=&variable=` | Annual anomalies and stored trend line |
| `GET /` | Built frontend (when `frontend/dist` exists) |
| `GET /overlays/*` | Precomputed PNG overlay tiles/images |

Notes: `lat`/`lon` validated (`[-90,90]`, `[-180,180]`), unknown variables return
404, missing layers return 503 with guidance. Raw p-values are not the
significance criterion; verdicts use stored FDR-corrected results.

## Real NASA pipeline (requires credentials)

```bash
make verify-earthdata
python scripts/run_pipeline.py --real --dry-run   # CMR search only, no login/download
# export EARTHDATA_USERNAME=... EARTHDATA_PASSWORD=...  (or configure ~/.netrc)
make pipeline-real
```

Configured datasets (verified in CMR on 2026-11-13; DOIs TODO):

| Variable | Dataset | Version | DAAC | Dry-run granules | Notes |
|---|---|---:|---|---:|---|
| Precipitation | `GPM_3IMERGM` | 07 | GES DISC | 276 | mm/hr → mm/month |
| Vegetation (NDVI) | `MOD13C2` | 061 | LP DAAC | 299 | **HDF4**: convert before prep |
| 2 m air temperature | `M2TMNXSLV` | 5.12.4 | GES DISC | 276 | Model-based reanalysis |
| Terrestrial water storage | `TELLUS_GRAC-GRFO_MASCON_GRID_RL06.3_V4` | RL06.3Mv04 | PO.DAAC | 1 | 2017–2018 gap, coarse effective resolution |

Details: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md),
[docs/NASA_DATA_GUIDE.md](docs/NASA_DATA_GUIDE.md).

## Methodology

- Common grid/period: 0.5°, 2002-01..2024-12 (config-driven).
- Prep: coordinate/unit standardization, regridding, missing months recorded
  (never filled).
- Analysis: monthly anomalies → annual means → Theil–Sen slope and Mann–Kendall
  with Hamed–Rao correction → Benjamini–Hochberg FDR significance/classes and
  standardized trends.
- Product rule: synthetic and real layers are never mixed.

## Repository layout

```text
config/                 app and dataset configuration
assets/                 Natural Earth land geometry (public domain source)
scripts/                synthetic generation, pipeline orchestration, overlay export, checks
src/api/                FastAPI app and layer store
src/common/             shared config loading
src/skills/             prep, trend, download, and report helpers
frontend/               React + Vite + MapLibre + Plotly UI
tests/                  pytest suite (synthetic fixtures, no network)
docs/                   data sources, limitations, decisions, validation, demo, NASA guide
```

Generated artifacts (`data/`, `layers/`, `frontend/dist/`, caches) are
git-ignored.

## Testing and verification

```bash
make test             # pytest suite
cd frontend && npm run build
.venv/bin/python scripts/run_pipeline.py --real --dry-run
```

See [docs/VALIDATION.md](docs/VALIDATION.md) for exact results, the 2026-11-13
CMR dry-run counts, and what was **not** validated.

## Documentation

- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — demo walkthrough
- [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) — datasets, verification, DOIs TODO
- [docs/LIMITATIONS.md](docs/LIMITATIONS.md) — scientific and product caveats
- [docs/DECISIONS.md](docs/DECISIONS.md) — key design decisions
- [docs/VALIDATION.md](docs/VALIDATION.md) — what was and wasn’t validated
- [docs/NASA_DATA_GUIDE.md](docs/NASA_DATA_GUIDE.md) — practical NASA data guide
- [docs/PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md) — PRD, MVP scope, and project rules
- [docs/INVESTIGATION_CATALOGUE.md](docs/INVESTIGATION_CATALOGUE.md) — predefined investigations (MVP: precipitation)
- [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) — target architecture and integration plan
- [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md) — cross-team interface contracts (draft)
- [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) — testing, validation, and data policy
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — contribution workflow (see also [docs/CONTRIBUTION.md](docs/CONTRIBUTION.md) for the full handbook)

## License and attribution

Choose and add a repository license before publishing. NASA Earth science data
are generally open, but each dataset has its own citation/DOI and terms — do
not ship DOI placeholders as final citations. Natural Earth data used for
offline land geometry is public domain.
