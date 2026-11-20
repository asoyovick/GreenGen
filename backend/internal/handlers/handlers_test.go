package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
	"github.com/asoyovick/GreenGen/backend/internal/repository"
	"github.com/asoyovick/GreenGen/backend/internal/routes"
	"github.com/asoyovick/GreenGen/backend/internal/service"
)

func newTestRouter() http.Handler {
	invRepo := repository.NewInvestigationRepository(nil)
	invSvc := service.NewInvestigationService(invRepo)
	execSvc := service.NewExecutionService(invSvc, repository.NewMemoryExecutionStore(), nil)
	return routes.NewRouter(routes.Services{Investigations: invSvc, Executions: execSvc, DB: nil})
}

func TestHealth(t *testing.T) {
	r := newTestRouter()
	req := httptest.NewRequest(http.MethodGet, "/api/v1/health", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var body map[string]any
	_ = json.Unmarshal(w.Body.Bytes(), &body)
	if body["status"] != "ok" {
		t.Fatalf("unexpected body: %v", body)
	}
}

func TestListInvestigations(t *testing.T) {
	r := newTestRouter()
	req := httptest.NewRequest(http.MethodGet, "/api/v1/investigations", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var body map[string]any
	_ = json.Unmarshal(w.Body.Bytes(), &body)
	if body["count"].(float64) < 1 {
		t.Fatalf("expected investigations, got %v", body)
	}
}

func TestGetInvestigation_NotFound(t *testing.T) {
	r := newTestRouter()
	req := httptest.NewRequest(http.MethodGet, "/api/v1/investigations/NOPE", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 404 {
		t.Fatalf("expected 404, got %d: %s", w.Code, w.Body.String())
	}
}

func TestValidateExecution_Invalid(t *testing.T) {
	r := newTestRouter()
	req := httptest.NewRequest(http.MethodPost, "/api/v1/executions/validate", bytes.NewBufferString(`{}`))
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 422 {
		t.Fatalf("expected 422, got %d: %s", w.Code, w.Body.String())
	}
}

func TestSubmitExecution_PlannedRejected(t *testing.T) {
	r := newTestRouter()
	payload := `{"investigation_id":"INV-001","bounds":{"min_lon":33.9,"min_lat":-4.7,"max_lon":41.9,"max_lat":5.5},"period":{"start":"2001-01-01","end":"2020-12-31"}}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1/executions", bytes.NewBufferString(payload))
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 422 {
		t.Fatalf("expected 422, got %d: %s", w.Code, w.Body.String())
	}
}

func TestExecutionNotFoundEndpoints(t *testing.T) {
	r := newTestRouter()
	for _, path := range []string{"/api/v1/executions/missing", "/api/v1/executions/missing/results", "/api/v1/executions/missing/summary", "/api/v1/executions/missing/report"} {
		req := httptest.NewRequest(http.MethodGet, path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Code != 404 {
			t.Fatalf("%s: expected 404, got %d: %s", path, w.Code, w.Body.String())
		}
	}
	req := httptest.NewRequest(http.MethodGet, "/api/v1/executions/missing/cells/c1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 404 {
		t.Fatalf("cells: expected 404, got %d: %s", w.Code, w.Body.String())
	}
}

func TestRefreshNotFound(t *testing.T) {
	r := newTestRouter()
	req := httptest.NewRequest(http.MethodPost, "/api/v1/executions/missing/refresh", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 404 {
		t.Fatalf("expected 404, got %d: %s", w.Code, w.Body.String())
	}
}

func TestResultsSummaryCellReport_WithIngestedResults(t *testing.T) {
	invRepo := repository.NewInvestigationRepository(nil)
	invSvc := service.NewInvestigationService(invRepo)
	store := repository.NewMemoryExecutionStore()
	execSvc := service.NewExecutionService(invSvc, store, nil)
	r := routes.NewRouter(routes.Services{Investigations: invSvc, Executions: execSvc, DB: nil})

	ctx := httptest.NewRequest(http.MethodGet, "/", nil).Context()
	created, err := store.Create(ctx, domain.InvestigationExecution{
		InvestigationID: "INV-TEST",
		Status:          domain.ExecutionQueued,
	}, &domain.Job{JobType: "analysis", Status: domain.ExecutionQueued}, map[string]any{})
	if err != nil {
		t.Fatalf("create exec: %v", err)
	}
	raw := map[string]any{
		"status": "completed",
		"cells": []any{
			map[string]any{"cell_id": "c1", "classification": "significant_increase", "n_observations": 120},
			map[string]any{"cell_id": "c2", "classification": "no_significant_trend", "n_observations": 120},
			map[string]any{"cell_id": "c3", "classification": "significant_decrease", "n_observations": 120},
		},
		"summary":      map[string]any{"cells_total": 3},
		"run_metadata": map[string]any{"engine_version": "0.1.0-draft"},
	}
	if err := store.SaveResult(ctx, domain.ExecutionResult{
		ExecutionID: created.ID,
		Status:      "available",
		Raw:         raw,
		Provenance:  map[string]any{"source": "engine", "synthetic": false},
		Synthetic:   false,
	}); err != nil {
		t.Fatalf("save result: %v", err)
	}
	_ = store.UpdateStatus(ctx, created.ID, domain.ExecutionCompleted, "", "", "")

	// Results with classification filter + pagination
	req := httptest.NewRequest(http.MethodGet, "/api/v1/executions/"+created.ID+"/results?classification=significant_increase&limit=1&offset=0", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("results expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var resBody map[string]any
	_ = json.Unmarshal(w.Body.Bytes(), &resBody)
	pag, _ := resBody["pagination"].(map[string]any)
	if pag["filtered_total"].(float64) != 1 || pag["returned"].(float64) != 1 {
		t.Fatalf("unexpected pagination: %#v", pag)
	}

	// Summary
	req = httptest.NewRequest(http.MethodGet, "/api/v1/executions/"+created.ID+"/summary", nil)
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("summary expected 200, got %d: %s", w.Code, w.Body.String())
	}

	// Cell (no time series present)
	req = httptest.NewRequest(http.MethodGet, "/api/v1/executions/"+created.ID+"/cells/c2", nil)
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("cell expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var cellBody map[string]any
	_ = json.Unmarshal(w.Body.Bytes(), &cellBody)
	if v, ok := cellBody["time_series_available"].(bool); !ok || v {
		t.Fatalf("expected time_series_available false, got %#v", cellBody["time_series_available"])
	}

	// Report
	req = httptest.NewRequest(http.MethodGet, "/api/v1/executions/"+created.ID+"/report", nil)
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("report expected 200, got %d: %s", w.Code, w.Body.String())
	}
}
