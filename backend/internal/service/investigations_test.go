package service

import (
	"context"
	"testing"

	"github.com/asoyovick/GreenGen/backend/internal/repository"
)

func TestValidateExecutionRequest_INV001Planned(t *testing.T) {
	svc := NewInvestigationService(repository.NewInvestigationRepository(nil))
	issues, inv := svc.ValidateExecutionRequest(context.Background(), ExecutionRequest{
		InvestigationID: "INV-001",
		Bounds:          &Bounds{MinLon: 33.9, MinLat: -4.7, MaxLon: 41.9, MaxLat: 5.5},
		Period:          &Period{Start: "2001-01-01", End: "2020-12-31"},
	})
	if inv == nil || inv.ID != "INV-001" {
		t.Fatalf("expected INV-001, got %#v", inv)
	}
	if len(issues) != 1 {
		t.Fatalf("expected 1 issue (planned/unavailable), got %#v", issues)
	}
	if issues[0].Field != "investigation_id" {
		t.Fatalf("expected investigation_id issue, got %#v", issues[0])
	}
}

func TestValidateExecutionRequest_MissingFields(t *testing.T) {
	svc := NewInvestigationService(repository.NewInvestigationRepository(nil))
	issues, _ := svc.ValidateExecutionRequest(context.Background(), ExecutionRequest{})
	if len(issues) == 0 {
		t.Fatalf("expected validation issues")
	}
}

func TestValidateExecutionRequest_InvalidBoundsAndPeriod(t *testing.T) {
	svc := NewInvestigationService(repository.NewInvestigationRepository(nil))
	issues, _ := svc.ValidateExecutionRequest(context.Background(), ExecutionRequest{
		InvestigationID: "INV-001",
		Bounds:          &Bounds{MinLon: 200, MinLat: -100, MaxLon: -10, MaxLat: 10},
		Period:          &Period{Start: "2020-12-31", End: "2020-01-01"},
	})
	if len(issues) < 3 {
		t.Fatalf("expected multiple issues, got %#v", issues)
	}
}
