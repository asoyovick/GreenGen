# GreenGen Backend (Go)

Initial Go backend scaffold for GreenGen / Global Change Explorer.

## Status
- **Phase 1 (assessment):** completed (no prior Go backend found).
- **Phase 2 (database foundation, #003 draft):** initial PostgreSQL + PostGIS schema and migrations added in `backend/migrations/` with documentation in `backend/docs/DATABASE_SCHEMA.md` (for team review).
- **Phase 3/4 (early scaffold):** basic HTTP server, config, middleware, health endpoint, investigation catalogue/detail endpoints backed by seeded definitions, and explicit `501 NOT_IMPLEMENTED` stubs for execution/results/report endpoints (no fabricated results).
- **Not yet implemented:** DB connection/repository layer, migrations runner integration, execution/job orchestration, Python engine client/contract, real result persistence/retrieval, full validation, and comprehensive tests.

## Structure
```text
backend/
  cmd/api/            # application entrypoint
  internal/
    config/           # environment-based configuration
    domain/           # domain models and seeded definitions
    errors/           # API error helpers
    handlers/         # HTTP handlers
    middleware/       # logging, recovery, CORS
    routes/           # route registration
    repository/       # (planned) data access
    db/               # (planned) DB connections/migrations
    service/          # (planned) business logic
    engine/           # (planned) Python scientific engine client
  migrations/         # SQL migrations (up/down)
  docs/               # schema/API notes
  tests/              # (planned)
```

## Requirements
- Go 1.22+
- PostgreSQL 14+ with PostGIS (for DB-backed features)

## Configuration
Environment variables (see repository `.env.example` / set locally):
- `APP_ENV` (default `development`)
- `HTTP_PORT` (default `8080`)
- `DATABASE_URL` (PostgreSQL DSN, required once DB features enabled)
- `HTTP_READ_TIMEOUT`, `HTTP_WRITE_TIMEOUT`, `HTTP_SHUTDOWN_TIMEOUT`, `REQUEST_TIMEOUT` (seconds or duration)
- `PYTHON_ENGINE_URL`, `PYTHON_ENGINE_TIMEOUT` (for #016 integration)
- `CORS_ALLOWED_ORIGINS` (comma-separated)

## Run locally
```bash
cd backend
go run ./cmd/api
```
Health checks:
- `GET /api/health`
- `GET /api/v1/health`

Investigation endpoints (seeded catalogue, draft):
- `GET /api/v1/investigations`
- `GET /api/v1/investigations/{id}`

Execution/results endpoints currently return `501 NOT_IMPLEMENTED` until contracts and orchestration are implemented.

## Database migrations (#003)
SQL migrations are in `backend/migrations/`:
```bash
# example with golang-migrate (install separately)
migrate -path backend/migrations -database "$DATABASE_URL" up
```
Review `backend/docs/DATABASE_SCHEMA.md` before applying in shared environments.

## Testing
```bash
cd backend
go test ./...
```
(Additional unit/integration tests to be added as handlers, validation, repositories, and engine integration are implemented.)

## Notes
- Scientific calculations are performed by the Python scientific engine/service (not reimplemented in Go).
- The backend must not fabricate NASA observations or scientific results; unavailable/unimplemented functionality returns explicit states/errors.
- API paths/shapes follow the draft contract direction and must be finalized with frontend/scientific team members (`docs/CONTRIBUTION.md`, team issue discussions).