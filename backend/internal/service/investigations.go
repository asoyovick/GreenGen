package service

import (
	"context"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
	"github.com/asoyovick/GreenGen/backend/internal/repository"
)

type InvestigationService struct {
	repo *repository.InvestigationRepository
}

func NewInvestigationService(repo *repository.InvestigationRepository) *InvestigationService {
	return &InvestigationService{repo: repo}
}

func (s *InvestigationService) List(ctx context.Context) ([]domain.Investigation, error) {
	if s == nil || s.repo == nil {
		return domain.SeedInvestigations(), nil
	}
	return s.repo.List(ctx)
}

func (s *InvestigationService) Get(ctx context.Context, id string) (domain.Investigation, bool, error) {
	if s == nil || s.repo == nil {
		inv, ok := domain.FindInvestigationByID(id)
		return inv, ok, nil
	}
	return s.repo.GetByID(ctx, id)
}

// Execution request/validation (draft, aligned with docs/API_CONTRACTS.md; subject to team agreement)

type Bounds struct {
	MinLon float64 `json:"min_lon"`
	MinLat float64 `json:"min_lat"`
	MaxLon float64 `json:"max_lon"`
	MaxLat float64 `json:"max_lat"`
}

type Period struct {
	Start string `json:"start"` // YYYY-MM-DD
	End   string `json:"end"`   // YYYY-MM-DD
}

type ExecutionRequest struct {
	InvestigationID string         `json:"investigation_id"`
	Bounds          *Bounds        `json:"bounds,omitempty"`
	Period          *Period        `json:"period,omitempty"`
	Options         map[string]any `json:"options,omitempty"`
}

type ValidationIssue struct {
	Field string `json:"field"`
	Issue string `json:"issue"`
}

var dateRe = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`)

func (s *InvestigationService) ValidateExecutionRequest(ctx context.Context, req ExecutionRequest) ([]ValidationIssue, *domain.Investigation) {
	var issues []ValidationIssue
	if strings.TrimSpace(req.InvestigationID) == "" {
		issues = append(issues, ValidationIssue{Field: "investigation_id", Issue: "required"})
		return issues, nil
	}
	inv, ok, _ := s.Get(ctx, req.InvestigationID)
	if !ok {
		issues = append(issues, ValidationIssue{Field: "investigation_id", Issue: "investigation not found"})
		return issues, nil
	}
	if inv.AvailabilityStatus != "available" {
		issues = append(issues, ValidationIssue{Field: "investigation_id", Issue: fmt.Sprintf("investigation is not available for execution (status: %s)", inv.AvailabilityStatus)})
	}
	if req.Bounds == nil {
		issues = append(issues, ValidationIssue{Field: "bounds", Issue: "required"})
	} else {
		if req.Bounds.MinLon < -180 || req.Bounds.MaxLon > 180 || req.Bounds.MinLon > req.Bounds.MaxLon {
			issues = append(issues, ValidationIssue{Field: "bounds", Issue: "invalid longitude range"})
		}
		if req.Bounds.MinLat < -90 || req.Bounds.MaxLat > 90 || req.Bounds.MinLat > req.Bounds.MaxLat {
			issues = append(issues, ValidationIssue{Field: "bounds", Issue: "invalid latitude range"})
		}
	}
	if req.Period == nil {
		issues = append(issues, ValidationIssue{Field: "period", Issue: "required"})
	} else {
		if !dateRe.MatchString(req.Period.Start) {
			issues = append(issues, ValidationIssue{Field: "period.start", Issue: "must be YYYY-MM-DD"})
		}
		if !dateRe.MatchString(req.Period.End) {
			issues = append(issues, ValidationIssue{Field: "period.end", Issue: "must be YYYY-MM-DD"})
		}
		if dateRe.MatchString(req.Period.Start) && dateRe.MatchString(req.Period.End) {
			start, _ := time.Parse("2006-01-02", req.Period.Start)
			end, _ := time.Parse("2006-01-02", req.Period.End)
			if start.After(end) {
				issues = append(issues, ValidationIssue{Field: "period", Issue: "start must be <= end"})
			}
		}
	}
	return issues, &inv
}
