# GreenGen Backend (Go)

Go backend scaffold for GreenGen / Global Change Explorer (NASA GPM IMERG precipitation MVP, Kenya focus).

## Status (incremental, draft)
- **#003 (database foundation, draft):** PostgreSQL + PostGIS schema and migrations in `backend/migrations/` (`000001` initial schema/seed, `000002` idempotency key draft) with docs in `backend/docs/DATABASE_SCHEMA.md`. DB connection and SQL migration runner implemented (`AUTO_MIGRATE`, `MIGRATIONS_PATH`, `schema_migrations`). **Full apply/validation requires a PostgreSQL+PostGIS environment** (not all environments have PostGIS available).
- **#014 (investigation/configuration, draft):** investigation catalogue/detail APIs backed by repository/service (DB-backed when configured, seeded fallback otherwise), plus execution request validation (`POST /api/v1/executions/validate`) including draft investigation-scoped bounds/period constraints and availability checks.
- **#015 (execution flow, draft):** execution submission/status/refresh APIs with in-memory and DB-backed stores, draft idempotency handling, persisted engine submission outcomes, and explicit non-fabricated error/unavailable states. No real scientific results are generated/returned.
- **#016 (Go↔Python integration, draft):** engine client interface + HTTP adapter scaffold (`PYTHON_ENGINE_URL`, `PYTHON_ENGINE_TIMEOUT`) and status lookup/refresh integration; protocol/schemas remain draft and must be finalized with Members 2/3 (#031/#034).
- **Not yet implemented/finalized:** agreed contracts and schemas, PostGIS-validated migration runs in shared env, full orchestration/state machine with real engine/data, verified result ingestion/persistence, results/summary/cells/report delivery, and comprehensive DB/integration/contract tests.

**Scientific integrity:** Go does not perform scientific calculations and must not fabricate NASA observations or results. Execution/completion/results are only valid when backed by verified engine outputs and agreed ingestion rules.

## Structure
```text
backend/
  cmd/api/                # application entrypoint
  internal/
    config/               # environment-based configuration
    db/                   # DB connection and migration runner
    domain/               # domain models and seeded definitions
    engine/               # Python scientific engine client scaffold (draft)
    errors/               # API error helpers
    handlers/             # HTTP handlers
    middleware/           # logging, recovery, CORS
    repository/           # investigations/executions stores (DB + in-memory)
    routes/               # route registration
    service/              # business/validation/execution logic
  migrations/             # SQL migrations (up/down)
  docs/                   # schema/API notes
```


## Requirements
- Go 1.22+
- PostgreSQL 14+ with PostGIS (for DB-backed features)

## Configuration
Environment variables (see repository `.env.example`):
- `APP_ENV` (default `development`)
- `HTTP_PORT` (default `8080`)
- `DATABASE_URL` (PostgreSQL DSN; if unset, runs in seed-only/in-memory mode with no persistence)
- `AUTO_MIGRATE` (`true` to apply migrations on startup)
- `MIGRATIONS_PATH` (default `migrations`, relative to working directory or absolute)
- `HTTP_READ_TIMEOUT`, `HTTP_WRITE_TIMEOUT`, `HTTP_SHUTDOWN_TIMEOUT`, `REQUEST_TIMEOUT` (seconds or duration)
- `PYTHON_ENGINE_URL`, `PYTHON_ENGINE_TIMEOUT` (engine integration, draft)
- `CORS_ALLOWED_ORIGINS` (comma-separated)
- `ALLOW_PLANNED_EXECUTIONS` (`true` enables dev/test-only execution submission for `planned` investigations; does not produce real/NASA results and does not bypass verified result ingestion requirements)

## Run locally
```bash
cd backend
go run ./cmd/api
```
With DB (PostgreSQL+PostGIS required for schema):
```bash
cd backend
DATABASE_URL='postgres://user:pass@localhost:5432/greengen?sslmode=disable' AUTO_MIGRATE=true go run ./cmd/api
```

## API endpoints (draft)
- `GET /api/health`, `GET /api/v1/health` — service/DB status
- `GET /api/v1/investigations` — list investigations
- `GET /api/v1/investigations/{id}` — investigation details
- `POST /api/v1/executions/validate` — validate execution request (bounds/period/availability/draft constraints)
- `POST /api/v1/executions` — submit execution (validated; creates/stores execution state, no fabricated results; `Idempotency-Key`/`X-Idempotency-Key` supported draft)
- `GET /api/v1/executions/{id}` — execution status
- `POST /api/v1/executions/{id}/refresh` — draft engine status sync (safe; no fabricated completion without verified result ingestion)
- `GET /api/v1/executions/{id}/results` — returns ingested results with provenance/synthetic labelling, or explicit unavailable state
- `GET /api/v1/executions/{id}/summary` — derived summary when results ingested, else unavailable
- `GET /api/v1/executions/{id}/cells/{cellId}` — cell result when ingested, else unavailable/not found
- `GET /api/v1/executions/{id}/report` — draft JSON report when results ingested, else unavailable

## Database migrations (#003)
- `000001_init_schema.up.sql` / `.down.sql` — core PostGIS schema and seed
- `000002_execution_idempotency.up.sql` / `.down.sql` — draft idempotency key
Apply with your preferred tool or `AUTO_MIGRATE=true`. Review `backend/docs/DATABASE_SCHEMA.md` before applying in shared environments.

## Local integration stack (dev/test)
```bash
docker compose up --build
# backend: http://localhost:8080, mock engine (synthetic): http://localhost:8090, PostGIS: localhost:5432
# serve frontend: python -m http.server 5174 -d frontend-vanilla
```
Mock engine returns **SYNTHETIC/UNVERIFIED** test data only (not NASA observations).

## Testing
```bash
cd backend
go test ./...
```
Current automated coverage includes config, service validation/execution behavior, repository in-memory execution store, and handler/API integration tests (httptest). DB/PostGIS and engine contract integration tests require appropriate environments and finalized contracts.

Synthetic E2E workflow (mock engine + backend with `ALLOW_PLANNED_EXECUTIONS=true`) validates submit → queued → refresh/status sync → ingested synthetic-labelled results/summary/cells/report. Real NASA/scientific finalization requires verified data/engine outputs and team-agreed contracts.

## Notes
- Scientific calculations are performed by the Python scientific engine/service (not reimplemented in Go).
- Backend must not fabricate NASA observations or scientific results; unimplemented/unavailable paths return explicit errors/states.
- API paths/shapes and engine protocol follow draft contracts and must be finalized with team members (`docs/CONTRIBUTION.md`, `docs/API_CONTRACTS.md`).
