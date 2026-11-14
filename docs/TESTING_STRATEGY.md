# Testing Strategy

**Purpose:** Define what is tested, how, by whom, and with what data so the team can deliver a reliable, scientifically defensible MVP (issue #050).  
**Status:** Draft — to be agreed by all members; evolves with implementation.

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

> Update this section as components are added; keep commands runnable and documented.

### Current prototype (Python/FastAPI + frontend)
- **Python tests:** `make test` (runs `pytest -q` via `.venv`) or `python -m pytest -q`
- **Frontend build check:** `cd frontend && npm run build`
- **Pipeline (synthetic, no network):** `make synthetic && make pipeline`
- **Real-data dry-run (CMR search only, no auth/download):** `python scripts/run_pipeline.py --real --dry-run`
- **Earthdata verification:** `make verify-earthdata` (requires network/credentials as applicable)

### Planned target components (to be added when implemented)
- **Scientific engine:** `pytest` (or agreed runner) in `scientific-engine/` with unit + validation suites; deterministic reference comparisons recorded.
- **Go backend:** `go test ./...` (plus integration tests with test DB/mocks as defined).
- **Contract tests:** schema/spec checks run in CI or via a single documented command (e.g. `make test-contracts`) (#051).
- **E2E:** agreed tool (e.g. Playwright/Cypress or API-driven workflow tests) against a test environment (#022).

## 5. What must be tested (by area)

### Data integration (#004–#007, #030–#033, #052)
- Retrieval for known area/period (real, when credentials available) and reproducible sample extraction.
- Spatial/temporal subsetting correctness vs source.
- Missing values, quality flags, completeness, and failure handling.
- Grid alignment preserved (no unintended resampling).

### Scientific engine (#008–#013, #034–#039, #021/#038/#053)
- Temporal aggregation (monthly/annual/seasonal) including incomplete periods.
- Mann–Kendall and Sen's slope vs independent reference implementations/known datasets.
- Confidence intervals, autocorrelation handling, multiple-testing/FDR behavior.
- Classifications: significant increase/decrease, no significant trend, insufficient data, inconclusive.
- Determinism and full metadata/provenance in outputs.

### Backend (#014–#016, #040–#045, #051)
- Request validation, state transitions, idempotency/duplicate protection as designed.
- Job lifecycle (queued/retrieving/analysing/completed/failed), timeouts/retries, error recording.
- Persistence of results and provenance; API correctness, pagination/limits.
- Integration with Python service (mocked and, where possible, real/local).

### Frontend (#017–#020, #046–#049, #022)
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

## 10. Agreement

This strategy is considered "agreed" when reviewed by all members (or recorded decision in the repo). Track revisions in git history and note major changes in PRs/issues.
