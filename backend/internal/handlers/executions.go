package handlers

import (
	"encoding/json"
	"fmt"
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
	if res, ok, _ := h.svc.GetResult(r.Context(), id); ok {
		resp := map[string]any{
			"execution_id": id,
			"execution":    ex,
			"result":       res.Raw,
			"provenance":   res.Provenance,
			"quality":      res.Quality,
			"synthetic":    res.Synthetic,
		}
		if res.Synthetic {
			resp["warning"] = "SYNTHETIC/UNVERIFIED TEST DATA - not NASA observations and not real scientific results."
		}
		writeJSON(w, http.StatusOK, resp)
		return
	}
	writeJSON(w, http.StatusConflict, map[string]any{
		"error": map[string]any{
			"code":    "RESULTS_UNAVAILABLE",
			"message": "No scientific results are available for this execution.",
			"details": map[string]any{"execution_id": ex.ID, "status": ex.Status, "reason": ex.ErrorMessage},
		},
		"execution": ex,
	})
}

func (h *ExecutionHandler) GetSummary(w http.ResponseWriter, r *http.Request, id string) {
	ex, ok, err := h.svc.Get(r.Context(), id)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to retrieve execution.", map[string]any{"id": id, "error": err.Error()})
		return
	}
	if !ok {
		writeError(w, "NOT_FOUND", "Execution not found.", map[string]any{"id": id})
		return
	}
	if res, ok, _ := h.svc.GetResult(r.Context(), id); ok {
		summary := map[string]any{
			"status":       ex.Status,
			"execution_id": id,
			"provenance":   res.Provenance,
			"synthetic":    res.Synthetic,
			"run_metadata": res.Raw["run_metadata"],
			"cells_count":  0,
			"warning":      nil,
		}
		if cells, ok := res.Raw["cells"].([]any); ok {
			summary["cells_count"] = len(cells)
		}
		if res.Synthetic {
			summary["warning"] = "SYNTHETIC/UNVERIFIED TEST DATA - not NASA observations and not real scientific results."
		}
		writeJSON(w, http.StatusOK, map[string]any{"execution": ex, "summary": summary, "provenance": res.Provenance, "synthetic": res.Synthetic})
		return
	}
	writeJSON(w, http.StatusConflict, map[string]any{
		"error": map[string]any{
			"code":    "SUMMARY_UNAVAILABLE",
			"message": "No analysis summary is available for this execution (no verified results).",
			"details": map[string]any{"execution_id": ex.ID, "status": ex.Status},
		},
		"execution": ex,
	})
}

func (h *ExecutionHandler) GetCell(w http.ResponseWriter, r *http.Request, id, cellID string) {
	ex, ok, err := h.svc.Get(r.Context(), id)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to retrieve execution.", map[string]any{"id": id, "error": err.Error()})
		return
	}
	if !ok {
		writeError(w, "NOT_FOUND", "Execution not found.", map[string]any{"id": id})
		return
	}
	if res, ok, _ := h.svc.GetResult(r.Context(), id); ok {
		if cells, ok := res.Raw["cells"].([]any); ok {
			for _, c := range cells {
				if cm, ok := c.(map[string]any); ok {
					if fmt.Sprint(cm["cell_id"]) == cellID {
						resp := map[string]any{"execution": ex, "cell": cm, "provenance": res.Provenance, "synthetic": res.Synthetic}
						if res.Synthetic {
							resp["warning"] = "SYNTHETIC/UNVERIFIED TEST DATA - not NASA observations and not real scientific results."
						}
						writeJSON(w, http.StatusOK, resp)
						return
					}
				}
			}
		}
		writeError(w, "NOT_FOUND", "Cell not found in execution results.", map[string]any{"execution_id": id, "cell_id": cellID})
		return
	}
	writeJSON(w, http.StatusConflict, map[string]any{
		"error": map[string]any{
			"code":    "CELL_RESULTS_UNAVAILABLE",
			"message": "No cell-level results are available for this execution.",
			"details": map[string]any{"execution_id": ex.ID, "cell_id": cellID, "status": ex.Status},
		},
		"execution": ex,
	})
}

func (h *ExecutionHandler) GetReport(w http.ResponseWriter, r *http.Request, id string) {
	ex, ok, err := h.svc.Get(r.Context(), id)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to retrieve execution.", map[string]any{"id": id, "error": err.Error()})
		return
	}
	if !ok {
		writeError(w, "NOT_FOUND", "Execution not found.", map[string]any{"id": id})
		return
	}
	if res, ok, _ := h.svc.GetResult(r.Context(), id); ok {
		report := map[string]any{
			"execution_id": id,
			"status":       "available",
			"format":       "json",
			"synthetic":    res.Synthetic,
			"provenance":   res.Provenance,
			"run_metadata": res.Raw["run_metadata"],
			"summary":      map[string]any{},
			"results_ref":  map[string]any{"type": "inline", "note": "Full grid/cell details available via results endpoints; report export formats TBD."},
		}
		if res.Synthetic {
			report["warning"] = "SYNTHETIC/UNVERIFIED TEST DATA - not NASA observations and not real scientific results."
		}
		if cells, ok := res.Raw["cells"].([]any); ok {
			report["summary"] = map[string]any{"cells_count": len(cells)}
		}
		writeJSON(w, http.StatusOK, map[string]any{"execution": ex, "report": report, "available": true})
		return
	}
	writeJSON(w, http.StatusConflict, map[string]any{
		"error": map[string]any{
			"code":    "REPORT_UNAVAILABLE",
			"message": "No report is available for this execution (no verified results).",
			"details": map[string]any{"execution_id": ex.ID, "status": ex.Status},
		},
		"execution": ex,
	})
}

func (h *ExecutionHandler) RefreshExecution(w http.ResponseWriter, r *http.Request, id string) {
	ex, ok, err := h.svc.Refresh(r.Context(), id)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to refresh execution status.", map[string]any{"id": id, "error": err.Error()})
		return
	}
	if !ok {
		writeError(w, "NOT_FOUND", "Execution not found.", map[string]any{"id": id})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"execution": ex,
		"message":   "Status refresh attempted (draft). Completion requires verified result ingestion; no fabricated results.",
	})
}
