# Backend Database Schema (Initial Draft)

**Issue:** #003 Define the initial database schema  
**Status:** Draft (for team review)  
**DB:** PostgreSQL + PostGIS  
**Migrations:** `backend/migrations/000001_init_schema.up.sql` / `.down.sql`

## Principles
- Store investigation metadata, execution state, configurations, and **references/metadata** for scientific outputs.
- **Do not store bulk NASA datasets** in PostgreSQL. Large scientific arrays/artifacts belong in appropriate formats/services (e.g. NetCDF/Zarr/object storage) referenced by URI/metadata.
- Preserve provenance (dataset/version, retrieval info, period, bounds, methods, software/methodology version, quality).
- Distinguish states clearly: `pending | queued | running | completed | failed` (no fabricated "completed" results).

## Entity overview

| Table | Purpose | Key relationships |
|---|---|---|
| `investigations` | Predefined investigation definitions (INV-001 precipitation MVP seeded as `planned`) | Parent of executions/data sources |
| `data_sources` | Dataset/source references and metadata (NASA/CMR/Harmony/local refs) | Optional FK to investigation; referenced by executions |
| `geographical_selections` | User/exec geography (PostGIS geometry or bbox/region preset) | Referenced by executions |
| `processing_configurations` | Analysis parameters (aggregation, tests, thresholds, corrections) | Referenced by executions |
| `investigation_executions` | One user-submitted run/configuration and its lifecycle | FK to investigation + selection/config/source; parent of jobs/results/reports |
| `jobs` | Execution/processing jobs and engine tracking (`engine_job_reference`, attempts, errors) | FK to execution |
| `analysis_results` | Result container/metadata/provenance + optional external `storage_uri` | 1:1 per execution (MVP) |
| `grid_cell_results` | Per-cell metrics/classifications (geometry/centroid, stats, p-values, slope/CI, classification) | FK to analysis_results |
| `time_series_results` | Cell/region/aggregate series as JSONB + metadata | FK to analysis_results |
| `reports` | Report status/content/reference per execution | FK to execution |

## Execution states
- **pending:** accepted/created, not yet queued.
- **queued:** enqueued for processing.
- **running:** retrieval/analysis in progress.
- **completed:** processing finished successfully and result state recorded (only when valid per engine/output rules).
- **failed:** processing failed or could not produce a valid result (error details recorded).

State transitions must be enforced consistently by the backend/service layer.

## Geographical storage (PostGIS)
- `geographical_selections.geometry`: `GEOMETRY(GEOMETRY,4326)` with GIST index for spatial queries.
- Bounding box columns and `region_code` supported for presets/simple inputs.
- Grid cell geometries/centroids stored in `grid_cell_results` for map rendering when available.

## Grid results
`grid_cell_results` captures key per-cell fields (counts, completeness, mean, trend, Sen’s slope + CI, Mann–Kendall/p-values, adjusted p-value, classification, flags/metrics JSONB). Exact scientific fields and delivery format for large grids (DB rows vs external artifact like GeoJSON/tiles/Zarr referenced by `storage_uri`) should be finalized with Members 3 and 5.

## Migrations
- Apply: `000001_init_schema.up.sql` (enables `postgis`, `pgcrypto`).
- Rollback: `000001_init_schema.down.sql`.
- Use a migration tool adopted by the project (e.g. `golang-migrate`, `goose`) in implementation; files are provided in compatible plain-SQL form.

## Open items / team review needed
- Confirm execution/job state enum values and allowed transitions with frontend/integration needs.
- Finalize API contract field names and result payload shapes (#014/#015/#016/#040/#043).
- Decide grid/time-series storage strategy for large result sets (DB vs external artifacts + references).
- Align `investigations` seed/definitions with product catalogue and dataset metadata from Members 1/2.
- Add indexes/partitioning as data volumes and query patterns become known.