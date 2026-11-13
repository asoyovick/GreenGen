# Decisions

Key implementation and scientific decisions, with rationale. Dates refer to
this build (2026-11-13 UTC context).

## 1. Synthetic-first, but real-pipeline ready

- **Decision:** Default mode is synthetic; real mode is fully scripted but only
  runs with credentials and explicit `--real`.
- **Why:** NASA CMR was reachable but no Earthdata Login credentials were
  available, so authenticated downloads could not be run or honestly claimed.
  Synthetic mode keeps the app, tests, and demo functional offline.
- **Guardrails:** `synthetic=true` in artifacts, persistent UI banner, API
  headers/payload flags, and config prevents mixing modes in one layer set.

## 2. Verified NASA dataset identities, but no invented DOIs

- **Decision:** Record CMR-verified short names/versions/DAACs and dry-run
  granule counts in config/docs; leave DOIs as explicit TODOs.
- **Why:** CMR collection responses used here did not provide DOI values.
  Inventing citations would be worse than a clear gap.

## 3. Credential-free CMR dry-run for the real pipeline

- **Decision:** `download_granules.py --dry-run` and
  `run_pipeline.py --real --dry-run` skip Earthdata login and perform public
  CMR searches only.
- **Why:** Catalog verification is useful even without credentials. The earlier
  behaviour blocked on login before searching, making dry-run unusable on
  uncredentialed machines.
- **Result (2026-11-13):** IMERG 276, MOD13C2 299, M2TMNXSLV 276,
  TELLUS_GRAC-GRFO_MASCON_GRID_RL06.3_V4 1.

## 4. Common grid and period, no gap filling

- **Decision:** 0.5° global grid, 2002-01..2024-12 for all configured
  variables; missing months/years remain gaps.
- **Why:** Click reports and overlays require aligned cells. Filling gaps or
  interpolating mission breaks (especially GRACE 2017–2018) would fabricate
  data and bias trends.

## 5. Statistical method follows the bundled skills

- **Decision:** Monthly anomalies → annual means (with minimum valid months) →
  per-cell Theil–Sen slope, Mann–Kendall with Hamed–Rao autocorrelation
  correction, Benjamini–Hochberg FDR across tested cells.
- **Why:** Seasonal cycles and autocorrelation make naive regression/p-values
  misleading; multiple testing over many cells requires correction.
- **Implementation note:** A process-parallel `--jobs` path was added for
  performance but preserves the same per-cell logic and results. `fdr_significant`
  was extracted for direct testing and reuse.

## 6. Significance comes only from corrected results

- **Decision:** API/report/chart verdicts use the stored FDR-corrected
  `significant` and `class` fields; raw p-values are not exposed as the
  decision criterion.
- **Why:** The challenge and good practice require honest significance; showing
  or implying raw p-values would invite false positives at map scale.
- **Wording:** “No statistically significant change detected” is never phrased
  as “no change”.

## 7. NDVI real path is explicit, not silently skipped

- **Decision:** MOD13C2 remains configured as HDF4; real non-dry-run processing
  logs that it must be converted (Harmony/rioxarray/pyhdf) before prep.
- **Why:** Pretending HDF4 is directly usable, or quietly omitting a core
  variable, would be misleading. The conversion requires tools/data access not
  exercised here.

## 8. Precompute everything; API is lookup-only

- **Decision:** Trends, classes, overlays, and annual anomaly series are stored
  in `layers/`; FastAPI loads once and serves point queries/timeseries/static
  overlays.
- **Why:** Global trend computation is expensive and must not run per click.
  This also makes demo behaviour deterministic and inspectable.

## 9. Offline-first frontend assets

- **Decision:** React + Vite + MapLibre GL JS + Plotly; offline Natural Earth
  base geometry and offline gazetteer/coordinate entry; no external map tiles or
  geocoding.
- **Why:** Demos and tests must work without third-party runtime services.
- **Performance:** Plotly chart is lazy-loaded and a React error boundary was
  added; MapLibre still dominates bundle size and is a candidate for further
  splitting.

## 10. Root serves the built app, `/api` serves metadata

- **Decision:** When `frontend/dist` exists, FastAPI serves it at `/` and moves
  API index metadata to `/api`.
- **Why:** A single `make demo` process is simpler for handover, while keeping
  the API contract discoverable.

## 11. Provenance and honesty in every mode

- **Decision:** Reports carry period, years, units, surface, model-based flags,
  synthetic flags, source/version/DOI fields when known, and “not a forecast”.
- **Why:** The main risk in this domain is overclaiming. Provenance and careful
  wording are treated as product features, not afterthoughts.
