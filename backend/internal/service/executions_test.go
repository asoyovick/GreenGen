package service

import (
	"context"
	"fmt"
	"testing"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
	"github.com/asoyovick/GreenGen/backend/internal/repository"
)

type fakeEngine struct {
	submitErr error
	status    string
	errCode   string
	errMsg    string
	results   map[string]any
}

func (f fakeEngine) Submit(context.Context, string, string, ExecutionRequest, map[string]any) (string, string, error) {
	if f.submitErr != nil {
		return "", "", f.submitErr
	}
	return "job-1", "queued", nil
}
func (f fakeEngine) GetStatus(context.Context, string) (string, string, string, map[string]any, error) {
	return f.status, f.errCode, f.errMsg, f.results, nil
}

type availableInvRepo struct{}

func (availableInvRepo) Available() bool                    { return false }
func (availableInvRepo) EnsureSeeded(context.Context) error { return nil }
func (availableInvRepo) List(context.Context) ([]domain.Investigation, error) {
	return []domain.Investigation{{ID: "INV-TEST", Code: "INV-TEST", Name: "Test", AvailabilityStatus: "available", SupportedGeographical: map[string]any{}, SupportedTemporal: map[string]any{}}}, nil
}
func (availableInvRepo) GetByID(_ context.Context, id string) (domain.Investigation, bool, error) {
	if id == "INV-TEST" {
		return domain.Investigation{ID: "INV-TEST", Code: "INV-TEST", Name: "Test", AvailabilityStatus: "available", SupportedGeographical: map[string]any{}, SupportedTemporal: map[string]any{}}, true, nil
	}
	return domain.Investigation{}, false, nil
}

// test helper: service using a repo-like wrapper isn't easy due to concrete type; instead test via seeded service by temporarily bypassing availability?
// We test behaviors we can: planned investigation rejected, store unavailable handled, etc.

func TestExecutionSubmit_PlannedRejected(t *testing.T) {
	invSvc := NewInvestigationService(repository.NewInvestigationRepository(nil))
	execSvc := NewExecutionService(invSvc, repository.NewMemoryExecutionStore(), nil)
	_, issues, err := execSvc.Submit(context.Background(), ExecutionRequest{
		InvestigationID: "INV-001",
		Bounds:          &Bounds{MinLon: 33.9, MinLat: -4.7, MaxLon: 41.9, MaxLat: 5.5},
		Period:          &Period{Start: "2001-01-01", End: "2020-12-31"},
	})
	if err != nil {
		t.Fatalf("unexpected err: %v", err)
	}
	if len(issues) == 0 {
		t.Fatalf("expected validation issues")
	}
}

func TestExecutionGet_NotFound(t *testing.T) {
	invSvc := NewInvestigationService(repository.NewInvestigationRepository(nil))
	execSvc := NewExecutionService(invSvc, repository.NewMemoryExecutionStore(), nil)
	_, ok, err := execSvc.Get(context.Background(), "missing")
	if err != nil || ok {
		t.Fatalf("expected not found, got ok=%v err=%v", ok, err)
	}
}

func TestExecutionRefresh_TerminalNoop(t *testing.T) {
	store := repository.NewMemoryExecutionStore()
	created, _ := store.Create(context.Background(), domain.InvestigationExecution{InvestigationID: "INV-001", Status: domain.ExecutionFailed, ErrorCode: "X"}, &domain.Job{JobType: "analysis", Status: domain.ExecutionFailed}, map[string]any{})
	invSvc := NewInvestigationService(repository.NewInvestigationRepository(nil))
	execSvc := NewExecutionService(invSvc, store, fakeEngine{status: "running"})
	ex, ok, err := execSvc.Refresh(context.Background(), created.ID)
	if err != nil || !ok {
		t.Fatalf("err=%v ok=%v", err, ok)
	}
	if ex.Status != domain.ExecutionFailed {
		t.Fatalf("expected failed unchanged, got %s", ex.Status)
	}
}

func TestExecutionRefresh_CompletedNotFabricated(t *testing.T) {
	store := repository.NewMemoryExecutionStore()
	created, _ := store.Create(context.Background(), domain.InvestigationExecution{InvestigationID: "INV-001", Status: domain.ExecutionQueued}, &domain.Job{JobType: "analysis", Status: domain.ExecutionQueued}, map[string]any{})
	invSvc := NewInvestigationService(repository.NewInvestigationRepository(nil))
	execSvc := NewExecutionService(invSvc, store, fakeEngine{status: "completed"})
	ex, ok, err := execSvc.Refresh(context.Background(), created.ID)
	if err != nil || !ok {
		t.Fatalf("err=%v ok=%v", err, ok)
	}
	if ex.Status == domain.ExecutionCompleted {
		t.Fatalf("must not mark completed without verified result ingestion")
	}
	_ = fmt.Sprint(ex.Status)
}
