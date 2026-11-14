package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
)

type ExecutionStore interface {
	Available() bool
	Create(ctx context.Context, ex domain.InvestigationExecution, job *domain.Job, requestPayload any) (domain.InvestigationExecution, error)
	Get(ctx context.Context, id string) (domain.InvestigationExecution, bool, error)
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
	err = tx.QueryRowContext(ctx, `
INSERT INTO investigation_executions (
	investigation_id, status, scientific_variable, period_start, period_end, request_payload,
	error_code, error_message, requested_at, updated_at
) VALUES ($1::uuid,$2,$3,$4::date,$5::date,$6::jsonb,$7,$8,NOW(),NOW())
RETURNING id::text, requested_at, updated_at
`, invUUID, ex.Status, ex.InvestigationID, nullIfEmpty(ptrString(ex.PeriodStart)), nullIfEmpty(ptrString(ex.PeriodEnd)), string(payload), nullIfEmpty(ex.ErrorCode), nullIfEmpty(ex.ErrorMessage)).Scan(&execID, &requestedAt, &updatedAt)
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

type MemoryExecutionStore struct {
	mu    sync.RWMutex
	items map[string]domain.InvestigationExecution
	seq   int
}

func NewMemoryExecutionStore() *MemoryExecutionStore {
	return &MemoryExecutionStore{items: map[string]domain.InvestigationExecution{}}
}

func (s *MemoryExecutionStore) Available() bool { return s != nil }

func (s *MemoryExecutionStore) Create(_ context.Context, ex domain.InvestigationExecution, _ *domain.Job, _ any) (domain.InvestigationExecution, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.seq++
	ex.ID = fmt.Sprintf("exec-%d", s.seq)
	now := time.Now().UTC()
	ex.RequestedAt = now
	ex.UpdatedAt = now
	s.items[ex.ID] = ex
	return ex, nil
}

func (s *MemoryExecutionStore) Get(_ context.Context, id string) (domain.InvestigationExecution, bool, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	ex, ok := s.items[id]
	return ex, ok, nil
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
