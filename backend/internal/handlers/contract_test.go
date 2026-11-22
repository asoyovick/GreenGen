package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// Contract tests (Issue #51): verify API responses include required fields
// from docs/API_CONTRACTS.md. These tests fail on contract drift.

func assertErrorEnvelope(t *testing.T, body map[string]any) {
	t.Helper()
	errObj, ok := body["error"].(map[string]any)
	if !ok {
		t.Fatalf("expected error envelope, got: %v", body)
	}
	if _, ok := errObj["code"].(string); !ok {
		t.Fatalf("expected error.code string, got: %v", errObj)
	}
	if _, ok := errObj["message"].(string); !ok {
		t.Fatalf("expected error.message string, got: %v", errObj)
	}
}

func TestContract_HealthShape(t *testing.T) {
	r := newTestRouter()
	for _, path := range []string{"/api/health", "/api/v1/health"} {
		req := httptest.NewRequest(http.MethodGet, path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Code != 200 {
			t.Fatalf("%s: expected 200, got %d", path, w.Code)
		}
		var body map[string]any
		if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
			t.Fatalf("%s: invalid json: %v", path, err)
		}
		if body["status"] != "ok" {
			t.Fatalf("%s: expected status ok, got %v", path, body["status"])
		}
		if body["service"] != "greengen-backend" {
			t.Fatalf("%s: expected service greengen-backend, got %v", path, body["service"])
		}
		db, ok := body["database"].(map[string]any)
		if !ok {
			t.Fatalf("%s: expected database object, got %v", path, body["database"])
		}
		if _, ok := db["status"].(string); !ok {
			t.Fatalf("%s: expected database.status string, got %v", path, db)
		}
	}
}

func TestContract_InvestigationsListShape(t *testing.T) {
	r := newTestRouter()
	req := httptest.NewRequest(http.MethodGet, "/api/v1/investigations", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var body map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid json: %v", err)
	}
	if _, ok := body["investigations"].([]any); !ok {
		t.Fatalf("expected investigations array, got %T", body["investigations"])
	}
	if _, ok := body["count"].(float64); !ok {
		t.Fatalf("expected count number, got %T", body["count"])
	}
}

func TestContract_ValidateExecutionErrorShape(t *testing.T) {
	r := newTestRouter()
	req := httptest.NewRequest(http.MethodPost, "/api/v1/executions/validate", bytes.NewBufferString(`{}`))
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != 422 {
		t.Fatalf("expected 422, got %d: %s", w.Code, w.Body.String())
	}
	var body map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid json: %v", err)
	}
	if valid, ok := body["valid"].(bool); !ok || valid {
		t.Fatalf("expected valid=false, got %v", body["valid"])
	}
	if _, ok := body["issues"].([]any); !ok {
		t.Fatalf("expected issues array, got %T", body["issues"])
	}
	assertErrorEnvelope(t, body)
}

func TestContract_NotFoundErrorShape(t *testing.T) {
	r := newTestRouter()
	for _, path := range []string{
		"/api/v1/investigations/NOPE",
		"/api/v1/executions/missing",
		"/api/v1/executions/missing/results",
		"/api/v1/executions/missing/summary",
		"/api/v1/executions/missing/report",
		"/api/v1/executions/missing/cells/c1",
	} {
		req := httptest.NewRequest(http.MethodGet, path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Code != 404 {
			t.Fatalf("%s: expected 404, got %d: %s", path, w.Code, w.Body.String())
		}
		var body map[string]any
		if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
			t.Fatalf("%s: invalid json: %v", path, err)
		}
		assertErrorEnvelope(t, body)
	}
}
