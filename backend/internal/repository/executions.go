package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
)

type ExecutionStore interface {
	Available() bool
	Create(ctx context.Context, ex domain.InvestigationExecution, job *domain.Job, requestPayload any) (domain.InvestigationExecution, error)
	Get(ctx context.Context, id string) (domain.InvestigationExecution, bool, error)
	GetByIdempotencyKey(ctx context.Context, key string) (domain.InvestigationExecution, bool, error)
	UpdateStatus(ctx context.Context, id string, status domain.ExecutionStatus, errCode, errMsg, engineJobRef string) error
}

type DBExecutionStore struct {
	db *sql.DB
}

func NewDBExecutionStore(db *sql.DB) *DBExecutionStore { return &DBExecutionStore{db: db} }

func (s *DBExecutionStore) Available() bool { return s != nil && s.db != nil }

func (s *DBExecutionStore) Create(ctx context.Context, ex domain.InvestigationExecution, job *domain.Job, requestPayload any) (domain.InvestigationExecution, error) {
	if !s.Available() {
		return domain.InvestigationExecution{}, fmt.Errorf("database not configured")
	}
	payload, _ := json.Marshal(requestPayload)
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return domain.InvestigationExecution{}, err
	}
	defer func() { _ = tx.Rollback() }()

	// Resolve investigation UUID by code/id
	var invUUID string
	if err := tx.QueryRowContext(ctx, `SELECT id::text FROM investigations WHERE code=$1 OR id::text=$1 LIMIT 1`, ex.InvestigationID).Scan(&invUUID); err != nil {
		return domain.InvestigationExecution{}, fmt.Errorf("resolve investigation: %w", err)
	}

	var execID string
	var requestedAt, updatedAt time.Time
	idKey := extractIdempotencyKey(payload)
	// try insert with idempotency_key (schema 000002); fallback for older schema
	if _, spErr := tx.ExecContext(ctx, `SAVEPOINT sp_exec_insert`); spErr == nil {
		err = tx.QueryRowContext(ctx, `
INSERT INTO investigation_executions (
	investigation_id, status, scientific_variable, period_start, period_end, request_payload,
	error_code, error_message, idempotency_key, requested_at, updated_at
) VALUES ($1::uuid,$2,$3,$4::date,$5::date,$6::jsonb,$7,$8,NULLIF($9,''),NOW(),NOW())
RETURNING id::text, requested_at, updated_at
`, invUUID, ex.Status, ex.InvestigationID, nullIfEmpty(ptrString(ex.PeriodStart)), nullIfEmpty(ptrString(ex.PeriodEnd)), string(payload), nullIfEmpty(ex.ErrorCode), nullIfEmpty(ex.ErrorMessage), idKey).Scan(&execID, &requestedAt, &updatedAt)
		if err != nil {
			_, _ = tx.ExecContext(ctx, `ROLLBACK TO SAVEPOINT sp_exec_insert`)
			err = tx.QueryRowContext(ctx, `
INSERT INTO investigation_executions (
	investigation_id, status, scientific_variable, period_start, period_end, request_payload,
	error_code, error_message, requested_at, updated_at
) VALUES ($1::uuid,$2,$3,$4::date,$5::date,$6::jsonb,$7,$8,NOW(),NOW())
RETURNING id::text, requested_at, updated_at
`, invUUID, ex.Status, ex.InvestigationID, nullIfEmpty(ptrString(ex.PeriodStart)), nullIfEmpty(ptrString(ex.PeriodEnd)), string(payload), nullIfEmpty(ex.ErrorCode), nullIfEmpty(ex.ErrorMessage)).Scan(&execID, &requestedAt, &updatedAt)
		} else {
			_, _ = tx.ExecContext(ctx, `RELEASE SAVEPOINT sp_exec_insert`)
		}
	} else {
		err = tx.QueryRowContext(ctx, `
INSERT INTO investigation_executions (
	investigation_id, status, scientific_variable, period_start, period_end, request_payload,
	error_code, error_message, requested_at, updated_at
) VALUES ($1::uuid,$2,$3,$4::date,$5::date,$6::jsonb,$7,$8,NOW(),NOW())
RETURNING id::text, requested_at, updated_at
`, invUUID, ex.Status, ex.InvestigationID, nullIfEmpty(ptrString(ex.PeriodStart)), nullIfEmpty(ptrString(ex.PeriodEnd)), string(payload), nullIfEmpty(ex.ErrorCode), nullIfEmpty(ex.ErrorMessage)).Scan(&execID, &requestedAt, &updatedAt)
	}
	if err != nil {
		return domain.InvestigationExecution{}, err
	}

	if job != nil {
		jobPayload, _ := json.Marshal(map[string]any{"reason": "engine integration pending", "issue": "#016"})
		_, err = tx.ExecContext(ctx, `
INSERT INTO jobs (investigation_execution_id, job_type, status, attempt, max_attempts, payload, error_code, error_message, created_at, updated_at)
VALUES ($1::uuid,$2,$3,0,1,$4::jsonb,$5,$6,NOW(),NOW())
`, execID, job.JobType, job.Status, string(jobPayload), nullIfEmpty(job.ErrorCode), nullIfEmpty(job.ErrorMessage))
		if err != nil {
			return domain.InvestigationExecution{}, err
		}
	}

	if err := tx.Commit(); err != nil {
		return domain.InvestigationExecution{}, err
	}
	ex.ID = execID
	ex.RequestedAt = requestedAt
	ex.UpdatedAt = updatedAt
	return ex, nil
}

func (s *DBExecutionStore) GetByIdempotencyKey(ctx context.Context, key string) (domain.InvestigationExecution, bool, error) {
	if !s.Available() || strings.TrimSpace(key) == "" {
		return domain.InvestigationExecution{}, false, nil
	}
	row := s.db.QueryRowContext(ctx, `
SELECT e.id::text, i.code, e.status, e.period_start::text, e.period_end::text, e.error_code, e.error_message,
       e.requested_at, e.started_at, e.completed_at, e.updated_at
FROM investigation_executions e
JOIN investigations i ON i.id = e.investigation_id
WHERE e.idempotency_key = $1
LIMIT 1`, key)
	var ex domain.InvestigationExecution
	var periodStart, periodEnd, errCode, errMsg sql.NullString
	var startedAt, completedAt sql.NullTime
	err := row.Scan(&ex.ID, &ex.InvestigationID, &ex.Status, &periodStart, &periodEnd, &errCode, &errMsg,
		&ex.RequestedAt, &startedAt, &completedAt, &ex.UpdatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return domain.InvestigationExecution{}, false, nil
	}
	if err != nil {
		// column/table may not exist yet in some environments
		return domain.InvestigationExecution{}, false, nil
	}
	if periodStart.Valid {
		ex.PeriodStart = &periodStart.String
	}
	if periodEnd.Valid {
		ex.PeriodEnd = &periodEnd.String
	}
	if errCode.Valid {
		ex.ErrorCode = errCode.String
	}
	if errMsg.Valid {
		ex.ErrorMessage = errMsg.String
	}
	if startedAt.Valid {
		ex.StartedAt = &startedAt.Time
	}
	if completedAt.Valid {
		ex.CompletedAt = &completedAt.Time
	}
	return ex, true, nil
}

func (s *DBExecutionStore) Get(ctx context.Context, id string) (domain.InvestigationExecution, bool, error) {
	if !s.Available() {
		return domain.InvestigationExecution{}, false, fmt.Errorf("database not configured")
	}
	row := s.db.QueryRowContext(ctx, `
SELECT e.id::text, i.code, e.status, e.period_start::text, e.period_end::text, e.error_code, e.error_message,
       e.requested_at, e.started_at, e.completed_at, e.updated_at
FROM investigation_executions e
JOIN investigations i ON i.id = e.investigation_id
WHERE e.id::text = $1
LIMIT 1`, id)
	var ex domain.InvestigationExecution
	var periodStart, periodEnd, errCode, errMsg sql.NullString
	var startedAt, completedAt sql.NullTime
	err := row.Scan(&ex.ID, &ex.InvestigationID, &ex.Status, &periodStart, &periodEnd, &errCode, &errMsg,
		&ex.RequestedAt, &startedAt, &completedAt, &ex.UpdatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return domain.InvestigationExecution{}, false, nil
	}
	if err != nil {
		return domain.InvestigationExecution{}, false, err
	}
	if periodStart.Valid {
		ex.PeriodStart = &periodStart.String
	}
	if periodEnd.Valid {
		ex.PeriodEnd = &periodEnd.String
	}
	if errCode.Valid {
		ex.ErrorCode = errCode.String
	}
	if errMsg.Valid {
		ex.ErrorMessage = errMsg.String
	}
	if startedAt.Valid {
		ex.StartedAt = &startedAt.Time
	}
	if completedAt.Valid {
		ex.CompletedAt = &completedAt.Time
	}
	return ex, true, nil
}

func (s *DBExecutionStore) UpdateStatus(ctx context.Context, id string, status domain.ExecutionStatus, errCode, errMsg, engineJobRef string) error {
	if !s.Available() {
		return fmt.Errorf("database not configured")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()
	_, err = tx.ExecContext(ctx, `
UPDATE investigation_executions
SET status=$2, error_code=$3, error_message=$4, updated_at=NOW(),
    started_at = CASE WHEN $2 IN ('queued','running') AND started_at IS NULL THEN NOW() ELSE started_at END,
    completed_at = CASE WHEN $2 IN ('completed','failed') THEN NOW() ELSE completed_at END
WHERE id::text=$1
`, id, status, nullIfEmpty(errCode), nullIfEmpty(errMsg))
	if err != nil {
		return err
	}
	_, err = tx.ExecContext(ctx, `
UPDATE jobs
SET status=$2, error_code=$3, error_message=$4, engine_job_reference=COALESCE(NULLIF($5,''), engine_job_reference), updated_at=NOW(),
    queued_at = CASE WHEN $2='queued' AND queued_at IS NULL THEN NOW() ELSE queued_at END,
    started_at = CASE WHEN $2='running' AND started_at IS NULL THEN NOW() ELSE started_at END,
    completed_at = CASE WHEN $2 IN ('completed','failed') THEN NOW() ELSE completed_at END
WHERE investigation_execution_id::text=$1
`, id, status, nullIfEmpty(errCode), nullIfEmpty(errMsg), engineJobRef)
	if err != nil {
		return err
	}
	return tx.Commit()
}

type MemoryExecutionStore struct {
	mu          sync.RWMutex
	items       map[string]domain.InvestigationExecution
	idempotency map[string]string // key -> execution id
	seq         int
}

func NewMemoryExecutionStore() *MemoryExecutionStore {
	return &MemoryExecutionStore{items: map[string]domain.InvestigationExecution{}, idempotency: map[string]string{}}
}

func (s *MemoryExecutionStore) Available() bool { return s != nil }

func (s *MemoryExecutionStore) Create(_ context.Context, ex domain.InvestigationExecution, _ *domain.Job, requestPayload any) (domain.InvestigationExecution, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	key := extractIdempotencyKey(requestPayload)
	if key != "" {
		if id, ok := s.idempotency[key]; ok {
			if existing, ok := s.items[id]; ok {
				return existing, nil
			}
		}
	}
	s.seq++
	ex.ID = fmt.Sprintf("exec-%d", s.seq)
	now := time.Now().UTC()
	ex.RequestedAt = now
	ex.UpdatedAt = now
	s.items[ex.ID] = ex
	if key != "" {
		s.idempotency[key] = ex.ID
	}
	return ex, nil
}

func (s *MemoryExecutionStore) Get(_ context.Context, id string) (domain.InvestigationExecution, bool, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	ex, ok := s.items[id]
	return ex, ok, nil
}

func (s *MemoryExecutionStore) GetByIdempotencyKey(_ context.Context, key string) (domain.InvestigationExecution, bool, error) {
	if key == "" {
		return domain.InvestigationExecution{}, false, nil
	}
	s.mu.RLock()
	id, ok := s.idempotency[key]
	if !ok {
		s.mu.RUnlock()
		return domain.InvestigationExecution{}, false, nil
	}
	ex, ok := s.items[id]
	s.mu.RUnlock()
	return ex, ok, nil
}

func (s *MemoryExecutionStore) UpdateStatus(_ context.Context, id string, status domain.ExecutionStatus, errCode, errMsg, _ string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	ex, ok := s.items[id]
	if !ok {
		return fmt.Errorf("execution not found")
	}
	ex.Status = status
	ex.ErrorCode = errCode
	ex.ErrorMessage = errMsg
	now := time.Now().UTC()
	ex.UpdatedAt = now
	if (status == domain.ExecutionQueued || status == domain.ExecutionRunning) && ex.StartedAt == nil {
		ex.StartedAt = &now
	}
	if status == domain.ExecutionCompleted || status == domain.ExecutionFailed {
		ex.CompletedAt = &now
	}
	s.items[id] = ex
	return nil
}

func nullIfEmpty(s string) any {
	if s == "" {
		return nil
	}
	return s
}

func ptrString(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

type ExecutionRequestPayload struct {
	IdempotencyKey string `json:"idempotency_key,omitempty"`
}

func extractIdempotencyKey(payload any) string {
	switch p := payload.(type) {
	case map[string]any:
		for _, k := range []string{"idempotency_key", "idempotencyKey", "IdempotencyKey"} {
			if v, ok := p[k].(string); ok && strings.TrimSpace(v) != "" {
				return strings.TrimSpace(v)
			}
		}
	case []byte:
		var m map[string]any
		if json.Unmarshal(p, &m) == nil {
			return extractIdempotencyKey(m)
		}
	case string:
		return extractIdempotencyKey([]byte(p))
	default:
		b, err := json.Marshal(p)
		if err == nil {
			var m map[string]any
			if json.Unmarshal(b, &m) == nil {
				return extractIdempotencyKey(m)
			}
		}
	}
	return ""
}
