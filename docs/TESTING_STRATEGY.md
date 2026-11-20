# Testing Strategy

**Purpose:** Define what is tested, how, by whom, and with what data so the team can deliver a reliable, scientifically defensible MVP (issue #050).  
**Status:** Finalized (team testing strategy document; track agreement/revisions in git history/issues/PRs).  
**Last updated:** 2026-11-20

## 1. Principles

- **Real vs synthetic data:** real NASA observations are required for real investigations and end-to-end scientific claims. **Synthetic fixtures** are allowed only in isolated/unit/controlled tests and must be **clearly labelled as synthetic** (never presented as real results).
- **Reproducibility:** tests and validation runs must be repeatable (fixed seeds/inputs, recorded versions/config where applicable).
- **Scientific validity:** plausible-looking outputs are insufficient; statistical results require independent checks and documented assumptions/limitations.
- **No hidden uncertainty:** tests should cover missing data, insufficient data, and inconclusive cases.

## 2. Test levels

| Level | Scope | Primary owners | Examples | When required |
|---|---|---|---|---|
| **Unit** | Individual functions/modules in isolation | Component owner (Members 2–5) | aggregation math, slope/MK helpers, validators, serializers, UI utils | For new logic and bug fixes |
| **Component / service** | A service or package boundary | Component owner | Python engine API/CLI behavior, Go handlers, data retrieval adapters | For API/engine changes |
| **Contract** | Interface compatibility between teams | Member 6 with 3/4/5 | Go↔Python schema, Go API responses vs spec, frontend client vs API | When contracts or schemas change (#051) |
| **Integration** | Multiple components together | Members 4/6 (+ others) | submission → retrieval → analysis → persistence → results API | For workflow features (#015/#016/#022) |
| **End-to-end (E2E)** | User-visible workflows | Member 6 with 1/4/5 | configure investigation, run, view map/cell/timeseries/report | Before milestones/demo (#022/#057) |
| **Scientific validation** | Correctness of statistical/geospatial results | Members 3 & 6 (independent) | reference datasets, independent implementations, grid alignment checks | For analysis changes (#021/#038/#052/#053) |

## 3. Test data policy

| Data type | Allowed use | Labelling/handling |
|---|---|---|
| **Real NASA observations** | Integration/E2E and scientific validation where feasible; required to substantiate real-investigation claims | Record dataset/version, period, bounds, retrieval metadata; store small samples in-repo only if size/licensing appropriate, otherwise document access/regeneration steps |
| **Synthetic/controlled fixtures** | Unit tests, controlled statistical cases, UI states, offline dev | Filename/metadata must include `synthetic` or equivalent label; tests must assert labeling where relevant; never mixed into "real" result artifacts |
| **Reference/expected results** | Scientific validation comparisons | Document source (independent library/calculation), parameters, and tolerance criteria |

## 4. Tools and commands (current + planned)

> Update this section as components evolve; keep commands runnable and documented.

### Current (implemented in this repository)
- **Python tests (repo root):** `PYTHONPATH=. .venv/bin/python -m pytest -q` (or `python -m pytest -q` in an activated environment with dependencies installed). Runs current Python/scientific-engine tests (e.g. `tests/test_scientific_engine.py`) and other active Python tests present.
- **Scientific engine tests (targeted):** `PYTHONPATH=. .venv/bin/python -m pytest tests/test_scientific_engine.py -q`
- **Scientific engine service (local):** `PYTHONPATH=. python -m scientific_engine` or `PYTHONPATH=. python -m uvicorn scientific_engine.service:app --host 0.0.0.0 --port 8090`
- **Go backend tests:** `cd backend && go test ./...`
- **Go backend (local):** `cd backend && go run ./cmd/api` (see `backend/README.md` for DB/env options)
- **Frontend build check:** `cd frontend && npm run build` (Vite/React frontend currently present in `frontend/`)
- **Integration stack (local, draft):** `docker compose up --build` (see root/backend docs; requires contract-compliant components/config)

### Planned / to be finalized as components mature
- **Contract tests:** schema/spec checks run in CI or via a single documented command (e.g. `make test-contracts`) (#051), covering Go API and Go↔Python request/response schemas.
- **E2E tests:** agreed tool (e.g. Playwright/Cypress or API-driven workflow tests) against a test environment (#022).
- **DB/PostGIS integration tests:** run against PostgreSQL+PostGIS with migrations applied (shared/CI environment as available).
- **Scientific validation runs:** independent reference comparisons and real-data validation recorded with provenance (#021/#038/#052/#053).

> **Note:** Obsolete legacy prototype tests/scripts that depended on removed synthetic-data pipeline modules are not part of the active test suite. Active tests must follow the project rule: no synthetic data presented as real NASA observations/results.

## 5. What must be tested (by area / issue type)

Each issue type has a stated test expectation. PRs should include/run the relevant checks for the areas they change.

| Issue type / area | Minimum expected tests/checks | Related issues (examples) |
|---|---|---|
| **Data integration / NASA retrieval** | Automated tests for retrieval/subsetting/missing+quality handling/failure paths where feasible; real-data checks documented with provenance when credentials/environment available; no synthetic data presented as real observations | #004–#007, #030–#033, #052 |
| **Scientific engine / statistics** | Unit tests for aggregation/statistics/classification; deterministic behavior with fixed inputs; independent/reference comparisons recorded for critical methods; controlled fixtures clearly labeled synthetic and never used as runtime results | #008–#013, #034–#039, #021, #038, #053 |
| **Backend API / services** | Unit/service tests for validation and state transitions; handler/API tests for contracts and error states; integration tests for DB/persistence and Python engine client (mocked and/or real/local) as environments allow | #014–#016, #040–#045, #051 |
| **Frontend / visualization** | Component/integration tests or reproducible manual checks for key flows, status/loading/error states, and rendering correctness; build/lint checks; accessibility/responsive checks for UI changes | #017–#020, #046–#049, #022 |
| **Contracts / schemas** | Contract tests that fail on field/type/shape mismatches across Go API, Python engine schema, and frontend client usage | #026, #031, #034, #051 |
| **Documentation / reproducibility / delivery** | Commands verified to run; reproducibility steps exercised on a clean environment when claimed; quality/validation evidence linked in docs/issues | #023, #039, #050, #053, #054, #056, #057 |

### Area-specific expectations (detail)

#### Data integration (#004–#007, #030–#033, #052)
- Retrieval for known area/period (real, when credentials available) and reproducible sample extraction.
- Spatial/temporal subsetting correctness vs source.
- Missing values, quality flags, completeness, and failure handling.
- Grid alignment preserved (no unintended resampling).

#### Scientific engine (#008–#013, #034–#039, #021/#038/#053)
- Temporal aggregation (monthly/annual/seasonal) including incomplete periods.
- Mann–Kendall and Sen's slope vs independent reference implementations/known datasets.
- Confidence intervals, autocorrelation handling, multiple-testing/FDR behavior.
- Classifications: significant increase/decrease, no significant trend, insufficient data, inconclusive.
- Determinism and full metadata/provenance in outputs.

#### Backend (#014–#016, #040–#045, #051)
- Request validation, state transitions, idempotency/duplicate protection as designed.
- Job lifecycle (queued/retrieving/analysing/completed/failed), timeouts/retries, error recording.
- Persistence of results and provenance; API correctness, pagination/limits/filtering where specified.
- Integration with Python service (mocked and, where possible, real/local).

#### Frontend (#017–#020, #046–#049, #022)
- Investigation catalogue/config flows and validation feedback.
- Status/progress, loading/empty/error states (no fabricated data).
- Map rendering, legend semantics (non-significant ≠ stable), cell selection, charts/reports match API.
- Accessibility basics (keyboard, labels, color-safe palette) and responsive layouts.

## 6. Pull request and review expectations

- Every PR states **what/why/issue/how to test/limitations** (and screenshots for UI where relevant).
- Run relevant tests locally; CI must pass when configured.
- **Scientific/methodology changes require review by the scientific analysis owner (Member 3)**; Member 1 coordinates but does not approve statistical methods alone.
- Contract changes require notification/review from affected owners (2/3/4/5) and updated docs/examples.
- Bug fixes include a regression test where feasible.

## 7. CI/CD (recommended)

- Automated checks on PRs: lint/format (per language), unit tests, contract/schema checks, and build steps where fast.
- Nightly or on-demand jobs for heavier integration/E2E or real-data checks (when credentials/environments available).
- Store validation artifacts (reports, logs, manifests) for scientific traceability; do not commit large raw datasets.

## 8. Environments

- **Local dev:** synthetic mode/default fixtures; `.env.example` documents required variables.
- **Integration/test:** isolated DB/services; may use real NASA access in controlled runs with credentials and recorded provenance.
- **Demo/production:** only verified configurations; display data source, limitations, and provenance.

## 9. Known gaps / follow-ups

- Finalize contract test tooling and CI wiring (#051).
- Define Go/Python/frontend test scaffolding as those components land (#038/#045).
- Produce scientific validation report and reproducibility procedures (#053/#054).
- Run full quality assessment against MVP acceptance criteria (#057).

## 10. Agreement and review

- This document defines the team testing strategy, test data policy, tools/commands, PR expectations, and per-issue-type test expectations required for #050.
- Treat this as the baseline strategy for ongoing work; record team agreement/approvals and future revisions in git history, PR reviews, and/or a decision log entry when available.
- **Scientific/methodology validation expectations** must be reviewed with the scientific analysis owner (Member 3) for analysis changes. Member 1 coordinates but does not approve statistical methods alone.
