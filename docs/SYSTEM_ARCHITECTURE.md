# System Architecture and Integration Plan

**Purpose:** Describe the target architecture, component responsibilities, interfaces, and integration checkpoints (issue #026).  
**Status:** Draft — reflects planned target and current prototype notes.

## 1. Architecture overview

The target system separates concerns into four main components:

1. **Next.js frontend** — investigation workflows, configuration, maps, charts, reports.
2. **Go backend** — API, validation, orchestration, persistence, job/status management.
3. **Python scientific engine** — data processing, quality checks, statistics, grid-level analysis.
4. **PostgreSQL (+ PostGIS)** — investigation metadata, executions, configurations, results/provenance (not bulk NASA archives).

NASA observations are discovered/retrieved via appropriate NASA services (e.g. CMR/Harmony/direct access as determined by #004/#030/#005) and passed in validated, structured form to the scientific engine. Large scientific arrays should be handled in suitable formats/services rather than stored wholesale in PostgreSQL.

### Target data flow (conceptual)
```text
User -> Frontend -> Go API -> (validate/store execution)
                         -> Data retrieval/subsetting (NASA services; owner/component per contract)
                         -> Python scientific engine (validated observations + config)
                         -> Persist results/provenance -> API -> Frontend (map/timeseries/report)
```

**Current prototype note:** this repository contains a working Python/FastAPI + React/Vite prototype (`src/api`, `frontend/`, `scripts/`) for synthetic/precomputed exploration. Target backlog issues (#014–#016, #040–#045, #034, frontend milestone issues) evolve this toward the architecture above; contracts in this document and `docs/API_CONTRACTS.md` are the agreed integration targets.

## 2. Component responsibilities

### Frontend (target: Next.js)
- Display investigation catalogue and details (implemented vs planned).
- Geographical and historical-period selection; validate inputs client-side where helpful.
- Submit executions, show progress/status, and handle errors/empty states.
- Render grid-level trend map (MapLibre GL JS), legends, and cell inspection.
- Render time series and statistical results (observations vs trend context, uncertainty, completeness).
- Present/export reports with provenance and limitations; never fabricate data.

### Go backend (target)
- REST/JSON APIs (see `docs/API_CONTRACTS.md`), request validation, consistent errors.
- Investigation definitions and execution lifecycle/state tracking.
- Orchestrate retrieval/analysis (async jobs/queue as needed, #042/#015).
- Integrate with Python engine and persist structured results + provenance (#016/#044).
- Store/retrieve results efficiently for map, cell detail, time series, and reports (#043).

### Python scientific engine (target)
- Accept validated observations and analysis configuration per contract (#031/#034).
- Temporal aggregation (monthly/annual/seasonal), quality/completeness handling.
- Grid-level analysis: Mann–Kendall/trend tests, Sen's slope, confidence intervals, assumptions (autocorrelation, multiple testing/FDR) per methodology (#008–#013, #036).
- Emit per-cell classifications and full reproducibility metadata (#037).
- Deterministic, testable, and independently validated.

### Database (target: PostgreSQL + PostGIS)
- Store: investigations, executions, data source references, geographical selections, processing configs, grid/cell results, report metadata, provenance.
- Use PostGIS for spatial metadata/queries where appropriate.
- **Do not** store entire NASA datasets in PostgreSQL.

## 3. Integration plan and cross-team contracts (#026)

Interfaces must be agreed before dependent implementation. Required contract areas:

| Contract | Owners | Recorded in | Status |
|---|---|---|---|
| **Observation handoff** (validated observations → engine): dimensions, variables, coords, units, quality mask, metadata (dataset/version, retrieval date, bounds, period), missing/invalid marking | Members 2 & 3 | `docs/DATA_SOURCES.md`, `docs/API_CONTRACTS.md` | Draft (to be finalized in #031) |
| **Python analysis request/response** (Go ↔ Python): protocol, schemas, per-cell measurements, classification, run metadata, versioning | Members 3 & 4 | `docs/API_CONTRACTS.md` | Draft (to be finalized in #034/#016) |
| **API response format** (Go ↔ Frontend): investigations, execution/status, grid results, cell details, timeseries, report/provenance, errors, pagination/limits | Members 4 & 5 | `docs/API_CONTRACTS.md` | Draft (to be finalized in #014/#040/#043) |
| **Grid-level output schema** (engine → backend → frontend): cell geometry/coords, stats, classification, quality, legend semantics | Members 3, 4 & 5 | `docs/API_CONTRACTS.md` | Draft (to be finalized in #034/#036/#043/#019) |

**Contract rules:** version schemas; provide example payloads with real-data-shaped fields (synthetic fixtures only when clearly labelled in tests); preserve native grid coordinates; keep "no significant trend detected" distinct from "stable".

## 4. Integration checkpoints (7-day intensive plan, adjustable)

| Day | Objective | Expected output | Checkpoint |
|---|---|---|---|
| 1 | Foundation and technical agreements | Repo, issues, architecture, methodology drafts, contracts outlined | Contracts discussion held; docs updated |
| 2 | NASA data integration | Real precipitation observations retrieved (sample/subset) | Sample + metadata documented (#032) |
| 3 | Scientific analysis pipeline | Temporal aggregation and trend calculations on real observations | **Critical:** real NASA observations pass through analysis pipeline end-to-end (at least for a limited area/period) |
| 4 | Grid-level analysis and backend | Structured geographical results, persistence/API shaping | Grid schema flowing backend↔engine↔frontend |
| 5 | Frontend integration | Investigation UI and trend map wired to APIs | Visuals driven by backend results |
| 6 | Validation and bug fixing | Tested end-to-end investigation | Functional + scientific checks |
| 7 | Deployment and presentation | Working demo and documentation | Limitations and provenance clear |

**Fallback if Day 3 checkpoint missed:** freeze feature expansion, narrow geography/period/resolution as needed, and prioritize one complete, reproducible, scientifically defensible precipitation investigation over additional UI/features.

## 5. Key dependencies

- NASA retrieval depends on dataset research (#004) and credentials/access paths.
- Scientific engine depends on validated observations and agreed handoff (#031).
- Backend integration depends on Python request/response contract (#034/#016).
- Frontend map/timeseries depend on API + grid schema (#043/#019/#020).
- Validation depends on engine outputs and reference methods (#021/#038/#053).

## 6. Repository structure (target, create as developed)

```text
frontend/                 # Next.js app (target) / current prototype UI
backend/                  # Go services, APIs, storage, migrations, jobs
scientific-engine/        # Python analysis package/service
docs/                     # PRD, methodology, architecture, contracts, data, testing, user guide
.github/                  # Issue/PR templates and workflows
scripts/                  # Utilities/pipeline helpers
tests/                    # Cross-cutting or shared test assets as applicable
```

(Existing prototype directories such as `src/`, `scripts/`, and `frontend/` remain part of the current implementation; migrate/refactor in line with agreed contracts.)

## 7. Risks and mitigations (summary)

| Risk | Mitigation |
|---|---|
| NASA access/credentials/latency | Early sample extraction (#032), documented access steps, clear failure handling |
| Contract drift | Versioned schemas, examples, contract tests (#051) |
| Statistical validity | Methodology review (#008/#028), independent validation (#021/#038/#053), report limitations |
| False precision / misleading maps | Preserve native grid, explain classifications, show uncertainty/insufficient data |
| Integration delays | Early interface agreement, Day 3 checkpoint, scope reduction rule |

## 8. Related documents

- `docs/API_CONTRACTS.md`
- `docs/DATA_SOURCES.md`
- `docs/PRODUCT_REQUIREMENTS.md`
- `docs/INVESTIGATION_CATALOGUE.md`
- `docs/TESTING_STRATEGY.md`
- `docs/CONTRIBUTION.md`
