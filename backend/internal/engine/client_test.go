package engine

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestHTTPClient_SubmitAndGetStatus(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.Method == http.MethodPost && r.URL.Path == "/v1/analyses":
			var req map[string]any
			_ = json.NewDecoder(r.Body).Decode(&req)
			_ = json.NewEncoder(w).Encode(map[string]any{
				"execution_id":         req["execution_id"],
				"engine_job_reference": "job-123",
				"status":               "queued",
			})
		case r.Method == http.MethodGet && r.URL.Path == "/v1/analyses/exec-1":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"status": "completed",
				"results": map[string]any{
					"status": "completed",
					"cells":  []any{map[string]any{"cell_id": "c1"}},
				},
			})
		default:
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer srv.Close()

	c := NewHTTPClient(srv.URL, 2*time.Second)
	acc, err := c.SubmitAnalysis(context.Background(), AnalysisRequest{ExecutionID: "exec-1", InvestigationID: "INV-001"})
	if err != nil {
		t.Fatalf("submit: %v", err)
	}
	if acc.EngineJobReference != "job-123" || acc.Status != "queued" {
		t.Fatalf("unexpected accepted: %#v", acc)
	}
	st, err := c.GetStatus(context.Background(), "exec-1")
	if err != nil {
		t.Fatalf("status: %v", err)
	}
	if st.Status != "completed" || st.Results == nil {
		t.Fatalf("unexpected status: %#v", st)
	}
}
