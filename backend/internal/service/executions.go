package service

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
	"github.com/asoyovick/GreenGen/backend/internal/repository"
)

type Engine interface {
	Submit(ctx context.Context, executionID, investigationID string, req ExecutionRequest, dataset map[string]any) (engineJobRef string, status string, err error)
	GetStatus(ctx context.Context, executionID string) (status string, errCode string, errMsg string, results map[string]any, err error)
}

type ExecutionService struct {
	inv           *InvestigationService
	store         repository.ExecutionStore
	engine        Engine
	EngineTimeout time.Duration
}

func NewExecutionService(inv *InvestigationService, store repository.ExecutionStore, engine Engine) *ExecutionService {
	return &ExecutionService{inv: inv, store: store, engine: engine, EngineTimeout: 120 * 1e9}
}

type SubmitExecutionResult struct {
	Execution domain.InvestigationExecution `json:"execution"`
	Accepted  bool                          `json:"accepted"`
	Message   string                        `json:"message,omitempty"`
}

func (s *ExecutionService) Submit(ctx context.Context, req ExecutionRequest) (SubmitExecutionResult, []ValidationIssue, error) {
	issues, inv := s.inv.ValidateExecutionRequest(ctx, req)
	if len(issues) > 0 {
		return SubmitExecutionResult{}, issues, nil
	}
	if s.store == nil || !s.store.Available() {
		return SubmitExecutionResult{}, []ValidationIssue{{Field: "execution", Issue: "execution store unavailable"}}, nil
	}
	if key := strings.TrimSpace(req.IdempotencyKey); key != "" {
		if existing, ok, _ := s.store.GetByIdempotencyKey(ctx, key); ok {
			return SubmitExecutionResult{Execution: existing, Accepted: true, Message: "Idempotent replay: existing execution returned."}, nil, nil
		}
	}

	ex := domain.InvestigationExecution{
		InvestigationID: strings.TrimSpace(req.InvestigationID),
		Status:          domain.ExecutionPending,
	}
	if req.Period != nil {
		ps, pe := req.Period.Start, req.Period.End
		ex.PeriodStart = &ps
		ex.PeriodEnd = &pe
	}
	job := &domain.Job{JobType: "analysis", Status: domain.ExecutionPending}

	if s.engine == nil {
		ex.Status = domain.ExecutionFailed
		ex.ErrorCode = "ENGINE_UNAVAILABLE"
		ex.ErrorMessage = "Scientific engine integration is not available yet (#016). No analysis was executed and no scientific results were generated."
		job.Status = domain.ExecutionFailed
		job.ErrorCode = ex.ErrorCode
		job.ErrorMessage = ex.ErrorMessage
	} else {
		// Pre-create record as pending, then attempt engine submission.
		// For stores that generate IDs on create, we create first with pending state.
		// Engine submission result will determine final initial state.
	}

	created, err := s.store.Create(ctx, ex, job, req)
	if err != nil {
		return SubmitExecutionResult{}, nil, err
	}

	// Attempt engine submission if configured and execution is pending (not pre-failed)
	if s.engine != nil && created.Status == domain.ExecutionPending {
		submitCtx := ctx
		cancel := func() {}
		if s.EngineTimeout > 0 {
			submitCtx, cancel = context.WithTimeout(ctx, s.EngineTimeout)
		}
		engineJobRef, engStatus, engErr := s.engine.Submit(submitCtx, created.ID, strings.TrimSpace(req.InvestigationID), req, inv.Dataset)
		cancel()
		if engErr != nil {
			_ = s.store.UpdateStatus(ctx, created.ID, domain.ExecutionFailed, "ENGINE_SUBMISSION_FAILED", fmt.Sprintf("Engine submission failed: %v. No scientific results were generated.", engErr), "")
			if updated, ok, _ := s.store.Get(ctx, created.ID); ok {
				created = updated
			} else {
				created.Status = domain.ExecutionFailed
				created.ErrorCode = "ENGINE_SUBMISSION_FAILED"
				created.ErrorMessage = fmt.Sprintf("Engine submission failed: %v. No scientific results were generated.", engErr)
			}
			return SubmitExecutionResult{
				Execution: created,
				Accepted:  true,
				Message:   "Execution was recorded but engine submission failed; no fabricated results.",
			}, nil, nil
		}
		_ = engStatus
		_ = s.store.UpdateStatus(ctx, created.ID, domain.ExecutionQueued, "", "", engineJobRef)
		if updated, ok, _ := s.store.Get(ctx, created.ID); ok {
			created = updated
		} else {
			created.Status = domain.ExecutionQueued
		}
		return SubmitExecutionResult{
			Execution: created,
			Accepted:  true,
			Message:   "Execution submitted to scientific engine (draft integration).",
		}, nil, nil
	}

	msg := "Execution recorded."
	if created.Status == domain.ExecutionFailed {
		msg = "Execution recorded but not processed because scientific engine integration is unavailable. No fabricated results."
	}
	return SubmitExecutionResult{Execution: created, Accepted: true, Message: msg}, nil, nil
}

func (s *ExecutionService) Get(ctx context.Context, id string) (domain.InvestigationExecution, bool, error) {
	if s.store == nil || !s.store.Available() {
		return domain.InvestigationExecution{}, false, nil
	}
	return s.store.Get(ctx, id)
}

func (s *ExecutionService) GetResult(ctx context.Context, id string) (domain.ExecutionResult, bool, error) {
	if s.store == nil || !s.store.Available() {
		return domain.ExecutionResult{}, false, nil
	}
	return s.store.GetResult(ctx, id)
}

func mapEngineStatus(status string) (domain.ExecutionStatus, bool) {
	switch strings.ToLower(strings.TrimSpace(status)) {
	case "pending":
		return domain.ExecutionPending, true
	case "queued":
		return domain.ExecutionQueued, true
	case "running", "analyzing", "retrieving", "processing":
		return domain.ExecutionRunning, true
	case "completed", "succeeded", "success":
		return domain.ExecutionCompleted, true
	case "failed", "error":
		return domain.ExecutionFailed, true
	default:
		return "", false
	}
}

func (s *ExecutionService) Refresh(ctx context.Context, id string) (domain.InvestigationExecution, bool, error) {
	ex, ok, err := s.Get(ctx, id)
	if err != nil || !ok {
		return ex, ok, err
	}
	// Only sync non-terminal states; never fabricate completion/results.
	if ex.Status == domain.ExecutionCompleted || ex.Status == domain.ExecutionFailed {
		return ex, true, nil
	}
	if s.engine == nil {
		return ex, true, nil
	}
	refreshCtx := ctx
	cancel := func() {}
	if s.EngineTimeout > 0 {
		refreshCtx, cancel = context.WithTimeout(ctx, s.EngineTimeout)
	}
	st, errCode, errMsg, results, engErr := s.engine.GetStatus(refreshCtx, id)
	cancel()
	if engErr != nil {
		return ex, true, nil // keep current state; sync best-effort
	}
	mapped, ok := mapEngineStatus(st)
	// Result ingestion: only accept verified, non-synthetic scientific results from the agreed engine/data pipeline.
	// Synthetic data must not be used.
	if len(results) > 0 {
		if synthetic, _ := results["synthetic"].(bool); synthetic {
			_ = s.store.UpdateStatus(ctx, id, domain.ExecutionFailed, "SYNTHETIC_DATA_REJECTED", "Synthetic data is not permitted. No results were ingested.", "")
			if updated, ok, _ := s.store.Get(ctx, id); ok {
				return updated, true, nil
			}
			ex.Status = domain.ExecutionFailed
			ex.ErrorCode = "SYNTHETIC_DATA_REJECTED"
			ex.ErrorMessage = "Synthetic data is not permitted. No results were ingested."
			return ex, true, nil
		}
		prov := map[string]any{"source": "engine", "synthetic": false}
		_ = s.store.SaveResult(ctx, domain.ExecutionResult{
			ExecutionID: id,
			Status:      "available",
			Raw:         results,
			Provenance:  prov,
			Synthetic:   false,
			Summary:     map[string]any{},
		})
		// If results are ingested and engine reports completed, mark completed.
		// NOTE: real NASA results must satisfy verified ingestion/provenance rules per agreed contracts.
		if mapped == domain.ExecutionCompleted || strings.EqualFold(strings.TrimSpace(st), "completed") {
			_ = s.store.UpdateStatus(ctx, id, domain.ExecutionCompleted, "", "", "")
			if updated, ok, _ := s.store.Get(ctx, id); ok {
				return updated, true, nil
			}
			ex.Status = domain.ExecutionCompleted
			return ex, true, nil
		}
	}
	if !ok || mapped == ex.Status {
		return ex, true, nil
	}
	// Without ingested results, do not mark completed.
	if mapped == domain.ExecutionCompleted {
		return ex, true, nil
	}
	_ = s.store.UpdateStatus(ctx, id, mapped, errCode, errMsg, "")
	if updated, ok, _ := s.store.Get(ctx, id); ok {
		return updated, true, nil
	}
	ex.Status = mapped
	ex.ErrorCode = errCode
	ex.ErrorMessage = errMsg
	return ex, true, nil
}
