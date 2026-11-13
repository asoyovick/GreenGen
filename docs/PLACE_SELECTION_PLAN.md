# Place Selection Plan

**Date:** 2026-11-13 (UTC)  
**Branch:** `docs/place-selection-plan` (from `develop` @ `7996f56`)  
**Scope:** Implement named-place selection (country/region/city/sea) on a real world map with place-level, precomputed change reports. Synthetic layers are the build/test baseline; real layers are not present.

## 1. Reconnaissance (what exists)

### Data & analysis
- **Precomputed layers:** `layers/synthetic/{precipitation,vegetation,temperature}_trend.zarr` (0.5°, 360×720, 2002-01–2024-12, 23 annual anomalies). Fields: `slope_per_year`, `slope_per_decade`, `p_value`, `significant` (BH-FDR), `class` (1/-1/0/NaN), `std_trend`, `n_years`, `low_confidence`, `annual_anomaly(year,lat,lon)`. Attrs include `units`, `alpha`, `min_years`, `ok_years`, synthetic/model/surface/provenance.
- **Trend logic (reuse):** `src/skills/compute_trends.py` (`anomalies_annual`, `make_trend_fn` Theil–Sen + Hamed–Rao MK, `fdr_significant` BH-FDR) and skill copies in `trend-significance/scripts/`. `src/skills/prep_cube.py` for grid/coords conventions.
- **Report logic (reuse/extend):** `src/skills/change_report.py` (`build_report`, `neighbor_shares`, wording/sorting; extended to accept open datasets and emit `class/key/model_based/synthetic/period/source`). Skill copy in `change-report/scripts/`. Wording rules in `change-report/references/wording_rules.md`.

### Backend
- **FastAPI:** `src/api/main.py`, `src/api/layer_store.py`. Loads all mode layers once at startup; serves `/api`, `/api/health`, `/api/variables`, `/api/layers`, `/api/report?lat&lon&window`, `/api/timeseries?lat&lon&variable`, `/overlays/*`, and built frontend at `/` when `frontend/dist` exists. Report/timeseries are point lookups against `annual_anomaly` and per-cell stats.
- **Config:** `config/app.yaml` (mode/grid/period/analysis/paths), `config/datasets.yaml`.

### Frontend
- **React + Vite + MapLibre GL JS + Plotly:** `frontend/src/` (`Explorer.jsx`, `WorldMap.jsx`, offline `LAND_URL` GeoJSON base + graticule, `SearchControl.jsx` with small offline gazetteer `data/places.js` + coordinate parsing, `ReportPanel.jsx`, `LayerSwitcher/Legend`, `api.js`, `lib/url.js` stores `?lat&lon&layer`). Overlay images under labels; click selects arbitrary point; no place polygons/levels/hover selection.

### Tests & tooling
- `pytest` suite (`tests/`, synthetic fixtures, no network). `Makefile` targets: install/synthetic/pipeline/overlays/api/frontend/test/demo. `data/`, `layers/`, `frontend/dist/` git-ignored.

## 2. What will be added

| Area | Additions |
|---|---|
| **Gazetteer** | `src/places/` package; `scripts/build_gazetteer.py` to fetch/read Natural Earth (1:50m admin-0, admin-1, populated places, marine areas), normalize records (stable ids, names/alt/native, level, hierarchy/parents, centroid, bbox, simplified + mask geometry), build offline search index and spatial index, emit `data/places/*` (GeoParquet/GeoJSON + index). Resolver `resolve(lat,lon,level)` with antimeridian/microstate/open-ocean handling. |
| **Place analysis** | `src/places/masks.py` (sparse cell indices + covered fractions, cos(lat) weights), `src/places/regional.py` (area-weighted regional annual series from `annual_anomaly`, coverage threshold, Theil–Sen/Hamed–Rao via trend-significance funcs, BH-FDR across places per level/variable, standardized trend, low-confidence), `src/places/divergence.py` (inside-place area-weighted class shares, divergent flag, neighbor comparison via adjacency), `src/places/report.py` / extend `change-report` with `build_place_report` (+ scale, n_cells, coverage, inside_place, divergent, neighbors) and wording additions. |
| **Precompute** | `scripts/build_place_results.py` (resumable; per-variable, masks reused) writing `layers/places/{mode}/` (compact Zarr/Parquet, synthetic-marked, separate from real). Optional hook in `run_pipeline.py`. |
| **API** | `GET /api/places/search?q=&level=&limit=`, `GET /api/places/at?lat=&lon=&level=`, `GET /api/places/{id}`, `GET /api/report?place_id=` (keep lat/lon), `GET /api/places/{id}/timeseries?variable=`. Validate inputs, load/cached results at startup, <300ms report/<100ms search targets (from cache). |
| **Frontend** | Real basemap tiles (open/free, OSM attribution) + bundled Natural Earth offline fallback; per-level GeoJSON place layers with hover/click/feature-state and dashed selection outline; “Select by” (City/Region/Country, default Region); accessible search combobox + lat,lon resolving to place; report panel with hierarchy, scale badge, inside-place shares/divergence, neighbors, plain-language + export; URL `?place=&var=&level=` (restore/share), keep point compat where sensible; footer credits/disclaimer; loading/error/empty/tile-failure states; keyboard/aria-live/non-color/mobile. |
| **Tests/docs** | Resolver, masks, regional trend recovery, divergence, search, wording, API, frontend/manual checks, performance notes; `docs/PLACE_SELECTION.md`, updated `docs/DATA_SOURCES.md`, `README.md`, neutrality/attribution notes, `docs/DECISIONS.md`. |

## 3. Interfaces & contracts

- **Place record:** `{id, name, name_native, alt_names[], level, parent_ids[], hierarchy, centroid:[lon,lat], bbox:[w,s,e,n], geometry_simplified, geometry_mask}`.
- **Resolver:** `resolve(lat, lon, level) -> {place, nearest_city?, marine_or_open_ocean}` using STRtree/point-in-polygon; antimeridian-aware.
- **Regional series:** area-weighted mean of per-cell `annual_anomaly` over valid cells with weights `cos(lat)*covered_fraction`; year used only if valid coverage ≥ 70% of polygon weight. Trend via `make_trend_fn(min_years)` on regional series; FDR via BH across places of same level per variable; `std_trend = slope_per_decade / std(regional_series)`.
- **Place report:** same ranked variable structure as point report plus `place{...}`, `scale` (`region_average`|`grid_cell`), `n_cells`, `coverage`, `inside_place{up,down,none}`, `divergent`, `neighbors[]/summary`, `not_a_forecast`, synthetic markers.
- **Storage:** `data/places/` (gazetteer/index, git-ignored unless small & documented), `layers/places/<mode>/` (precomputed results, git-ignored). Synthetic never mixed with real.

## 4. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Natural Earth download unavailable / versions unclear | Fetch from official/nvkelso sources, verify filenames, record source/version/date in `docs/DATA_SOURCES.md`; fall back to minimal bundled subset if needed and document. |
| Masking/rasterization slow or complex at 0.5° | Subgrid (e.g. 4×4) rasterization or `rasterio.features`/`regionmask`; store sparse masks once; process by variable; profile and record. |
| Antimeridian, microstates, duplicate names | Split/shift geometries for resolver/masking, nearest/point handling for tiny polygons, hierarchy in search results. |
| Large GeoJSON payloads | Separate simplified display vs mask geometries; per-level files, lazy load, consider compact encoding/tiling if needed. |
| Tile provider outage / no keys | Open provider (e.g. OpenFreeMap/Protomaps) + mandatory Natural Earth offline fallback. |
| Spatial autocorrelation vs FDR | Document limitation (FDR corrects multiplicity, not spatial dependence). |
| Scope (many branches/features) | Implement incrementally, keep API/UI backward-compatible with point flow, precompute for MVP variable/level subsets if needed and document. |

## 5. Performance targets (to measure & record)

- Hover/resolve: responsive (<~100 ms perceived). Report from cache: <300 ms. Search: <100 ms. Initial place payload: keep per-level downloads small (few MB target for simplified layers). Record actual timings in this doc as phases complete.

## 6. Working notes

- **Statistics:** deterministic; reuse `trend-significance`/`change-report` code paths; significance only from FDR-corrected results; non-significant ≠ “no change”.
- **Neutrality/attribution:** boundaries/names as provided, disclaimer shown, OSM + Natural Earth credits visible.
- **Git:** never touch `main`; one branch per feature, Conventional Commits, `--no-ff` merges into `develop`, tests before commit/merge.
- **Current gaps to confirm during build:** Natural Earth fetch tooling availability in `.venv` (shapely/pyproj/geopandas/rasterio/regionmask may need adding), exact tile/fallback asset choices, and feasible MVP place counts at 1:50m.

## 7. Progress

- [x] Reconnaissance and plan committed.
- [ ] Phase 1–6 per branch plan in the feature prompt.
