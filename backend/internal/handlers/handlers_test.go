package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

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
