package service

import (
	"context"
	"strings"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
	"github.com/asoyovick/GreenGen/backend/internal/repository"
)

type ExecutionService struct {
	inv   *InvestigationService
	store repository.ExecutionStore
}

func NewExecutionService(inv *InvestigationService, store repository.ExecutionStore) *ExecutionService {
	return &ExecutionService{inv: inv, store: store}
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
	// inv is validated and found
	_ = inv
	ex := domain.InvestigationExecution{
		InvestigationID: strings.TrimSpace(req.InvestigationID),
		Status:          domain.ExecutionFailed,
		ErrorCode:       "ENGINE_UNAVAILABLE",
		ErrorMessage:    "Scientific engine integration is not available yet (#016). No analysis was executed and no scientific results were generated.",
	}
	if req.Period != nil {
		ps, pe := req.Period.Start, req.Period.End
		ex.PeriodStart = &ps
		ex.PeriodEnd = &pe
	}
	job := &domain.Job{
		JobType:      "analysis",
		Status:       domain.ExecutionFailed,
		ErrorCode:    "ENGINE_UNAVAILABLE",
		ErrorMessage: ex.ErrorMessage,
	}
	if s.store == nil || !s.store.Available() {
		// return an ephemeral-style response is not possible without ID; require store
		return SubmitExecutionResult{}, []ValidationIssue{{Field: "execution", Issue: "execution store unavailable"}}, nil
	}
	created, err := s.store.Create(ctx, ex, job, req)
	if err != nil {
		return SubmitExecutionResult{}, nil, err
	}
	return SubmitExecutionResult{
		Execution: created,
		Accepted:  true,
		Message:   "Execution recorded but not processed because scientific engine integration is unavailable. No fabricated results.",
	}, nil, nil
}

func (s *ExecutionService) Get(ctx context.Context, id string) (domain.InvestigationExecution, bool, error) {
	if s.store == nil || !s.store.Available() {
		return domain.InvestigationExecution{}, false, nil
	}
	return s.store.Get(ctx, id)
}
