package service

import (
	"context"
	"fmt"
	"strings"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
	"github.com/asoyovick/GreenGen/backend/internal/repository"
)

type Engine interface {
	Submit(ctx context.Context, executionID, investigationID string, req ExecutionRequest, dataset map[string]any) (engineJobRef string, status string, err error)
}

type ExecutionService struct {
	inv    *InvestigationService
	store  repository.ExecutionStore
	engine Engine
}

func NewExecutionService(inv *InvestigationService, store repository.ExecutionStore, engine Engine) *ExecutionService {
	return &ExecutionService{inv: inv, store: store, engine: engine}
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
		_, engStatus, engErr := s.engine.Submit(ctx, created.ID, strings.TrimSpace(req.InvestigationID), req, inv.Dataset)
		if engErr != nil {
			// Reflect failure in returned object (persistence of status update depends on store implementation)
			created.Status = domain.ExecutionFailed
			created.ErrorCode = "ENGINE_SUBMISSION_FAILED"
			created.ErrorMessage = fmt.Sprintf("Engine submission failed: %v. No scientific results were generated.", engErr)
			return SubmitExecutionResult{
				Execution: created,
				Accepted:  true,
				Message:   "Execution was recorded but engine submission failed; no fabricated results.",
			}, nil, nil
		}
		_ = engStatus
		created.Status = domain.ExecutionQueued
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
