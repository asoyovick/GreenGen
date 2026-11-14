# Contributing to Earth System Trend Detective

This guide covers day-to-day development workflow for the repository. For the full project handbook (scope, team roles, backlog, scientific rules), see [`docs/CONTRIBUTION.md`](CONTRIBUTION.md).

## 1. Prerequisites

- **Git** and access to the repository.
- **Python 3.10+** (current prototype/scientific tooling) and `make`.
- **Node.js + npm** (for `frontend/`).
- **Go 1.22+** and **PostgreSQL/PostGIS** when backend components (#040+) are implemented (see those issues/docs for exact versions).
- Optional for real NASA runs: **Earthdata Login** credentials (see `docs/DATA_SOURCES.md`, `docs/NASA_DATA_GUIDE.md`).

## 2. Local setup (current prototype)

```bash
git clone <repo-url>
cd GreenGen
make install          # create .venv, install Python deps, install frontend deps
make synthetic        # generate labelled synthetic cubes (no NASA access)
make pipeline         # prep + trends + overlays
make demo             # build frontend and serve UI+API on http://127.0.0.1:8000
```

Development servers:
```bash
make api              # FastAPI on :8000
make frontend         # Vite dev server on :5173 (proxies /api, /overlays)
```

Tests and checks:
```bash
make test
cd frontend && npm run build
python scripts/run_pipeline.py --real --dry-run   # CMR search only
```

## 3. Environment configuration

- Copy `.env.example` to `.env` for local overrides (never commit `.env` or credentials).
- Key variables (see `.env.example`): `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD`, optional `CMR_*`/service URLs, and future backend/database settings as they are introduced.
- Real NASA downloads require Earthdata Login and approved applications as documented in `docs/DATA_SOURCES.md`.

## 4. Branch strategy

- `main` — stable, reviewed integration-ready history (no direct pushes).
- `develop` — integration branch for ongoing work (target for most PRs unless agreed otherwise).
- `feat/*` — new functionality
- `fix/*` — bug fixes
- `test/*` — testing/validation work
- `docs/*` — documentation changes

Create branches from the agreed base (`develop` for features) and keep them focused on a single issue/change.

## 5. Commit message conventions

Use clear, descriptive messages (Conventional Commits style encouraged):

```text
feat: add precipitation investigation definition

fix: handle missing precipitation observations

test: validate trend calculations against reference data

docs: document scientific methodology and assumptions

chore: update dependencies and tooling
```

Guidelines:
- One logical change per commit where practical; avoid large unrelated mixes.
- Reference the issue in the body or PR (e.g. `Refs #026`).
- Do not include secrets, credentials, or large generated datasets.

## 6. Pull request requirements

Every PR should include:
- **What** was implemented/changed
- **Why** it was needed
- **Issue** reference (e.g. `Closes #001`)
- **How to test** (commands, data, expected outcome)
- **Limitations / follow-ups**
- **Screenshots or sample outputs** for UI/visual changes (where relevant)

Review rules:
- At least **one reviewer** before merge.
- **Scientific/statistical changes require review from the scientific analysis owner** (Member 3) in addition to coordination review as needed.
- Contract or schema changes must be reflected in `docs/API_CONTRACTS.md` (or relevant doc) and communicated to dependent teams.

## 7. Definition of done (summary)

An issue/PR is done when: requirements implemented, acceptance criteria met, relevant tests pass, documentation updated, changes reviewed, and merged into the agreed integration branch. For scientific work, also include independent validation/reference checks and documented assumptions/limitations. See `docs/CONTRIBUTION.md` (Part 8) for full criteria.

## 8. Data and scientific integrity

- Do not fabricate scientific results. Use **actual NASA observations** for real investigations.
- Clearly label any **synthetic** test fixtures and never present them as real outputs.
- Do not hide uncertainty, missing data, or methodological limitations.
- Prefer reproducible workflows: record dataset/version, period, bounds, config, and method details.

## 9. Getting help

- Use issue/PR discussions for technical decisions that should be recorded.
- Post blockers and dependency needs in the team’s coordination channel and link relevant issues/PRs.
- For testing expectations, see `docs/TESTING_STRATEGY.md`; for interfaces, see `docs/API_CONTRACTS.md` and `docs/SYSTEM_ARCHITECTURE.md`.
