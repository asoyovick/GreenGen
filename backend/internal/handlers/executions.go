package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/asoyovick/GreenGen/backend/internal/service"
)

type ExecutionHandler struct {
	svc *service.ExecutionService
}

func NewExecutionHandler(svc *service.ExecutionService) *ExecutionHandler {
	return &ExecutionHandler{svc: svc}
}

func (h *ExecutionHandler) SubmitExecution(w http.ResponseWriter, r *http.Request) {
	var req service.ExecutionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, "VALIDATION_ERROR", "Invalid JSON request body.", map[string]any{"error": err.Error()})
		return
	}
	req.InvestigationID = strings.TrimSpace(req.InvestigationID)
	if req.IdempotencyKey == "" {
		req.IdempotencyKey = strings.TrimSpace(r.Header.Get("Idempotency-Key"))
	}
	if req.IdempotencyKey == "" {
		req.IdempotencyKey = strings.TrimSpace(r.Header.Get("X-Idempotency-Key"))
	}
	res, issues, err := h.svc.Submit(r.Context(), req)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to submit execution.", map[string]any{"error": err.Error()})
		return
	}
	if len(issues) > 0 {
		status := http.StatusUnprocessableEntity
		if len(issues) == 1 && issues[0].Field == "execution" {
			status = http.StatusServiceUnavailable
		}
		writeJSON(w, status, map[string]any{
			"error": map[string]any{
				"code":    "VALIDATION_ERROR",
				"message": "Execution request could not be accepted.",
				"details": issues,
			},
		})
		return
	}
	writeJSON(w, http.StatusAccepted, map[string]any{
		"execution_id": res.Execution.ID,
		"status":       res.Execution.Status,
		"execution":    res.Execution,
		"accepted":     res.Accepted,
		"message":      res.Message,
	})
}

func (h *ExecutionHandler) GetExecution(w http.ResponseWriter, r *http.Request, id string) {
	ex, ok, err := h.svc.Get(r.Context(), id)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to retrieve execution.", map[string]any{"id": id, "error": err.Error()})
		return
	}
	if !ok {
		writeError(w, "NOT_FOUND", "Execution not found.", map[string]any{"id": id})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"execution": ex})
}

func (h *ExecutionHandler) GetResults(w http.ResponseWriter, r *http.Request, id string) {
	ex, ok, err := h.svc.Get(r.Context(), id)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to retrieve execution.", map[string]any{"id": id, "error": err.Error()})
		return
	}
	if !ok {
		writeError(w, "NOT_FOUND", "Execution not found.", map[string]any{"id": id})
		return
	}
	writeJSON(w, http.StatusConflict, map[string]any{
		"error": map[string]any{
			"code":    "RESULTS_UNAVAILABLE",
			"message": "No scientific results are available for this execution.",
			"details": map[string]any{"execution_id": ex.ID, "status": ex.Status, "reason": ex.ErrorMessage},
		},
	})
}
