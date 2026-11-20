package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
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
	res, ok, _ := h.svc.GetResult(r.Context(), id)
	if !ok {
		writeJSON(w, http.StatusConflict, map[string]any{
			"error": map[string]any{
				"code":    "RESULTS_UNAVAILABLE",
				"message": "No scientific results are available for this execution.",
				"details": map[string]any{"execution_id": ex.ID, "status": ex.Status, "reason": ex.ErrorMessage},
			},
			"execution": ex,
		})
		return
	}
	if res.Synthetic {
		writeJSON(w, http.StatusConflict, map[string]any{
			"error":     map[string]any{"code": "SYNTHETIC_DATA_REJECTED", "message": "Synthetic data is not permitted and cannot be used.", "details": map[string]any{"execution_id": ex.ID}},
			"execution": ex,
		})
		return
	}

	resultPayload := cloneAnyMap(res.Raw)
	cells, hasCells := asAnySlice(resultPayload["cells"])
	classFilter := parseClassificationFilter(r)
	limit, offset, pageErr := parsePagination(r, 1000, 5000)
	if pageErr != "" {
		writeError(w, "VALIDATION_ERROR", "Invalid pagination parameters.", map[string]any{"error": pageErr})
		return
	}

	pagination := map[string]any{}
	if hasCells {
		filtered := filterCellsByClassification(cells, classFilter)
		total := len(cells)
		filteredTotal := len(filtered)
		if offset > filteredTotal {
			offset = filteredTotal
		}
		end := offset + limit
		if end > filteredTotal {
			end = filteredTotal
		}
		page := filtered[offset:end]
		resultPayload["cells"] = page
		pagination = map[string]any{
			"total":          total,
			"filtered_total": filteredTotal,
			"limit":          limit,
			"offset":         offset,
			"returned":       len(page),
		}
		if len(classFilter) > 0 {
			pagination["classification_filter"] = sortedStringSet(classFilter)
		}
	}

	resp := map[string]any{
		"execution_id": id,
		"execution":    ex,
		"result":       resultPayload,
		"provenance":   res.Provenance,
		"quality":      res.Quality,
	}
	if hasCells {
		resp["pagination"] = pagination
	}
	writeJSON(w, http.StatusOK, resp)
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
		if res.Synthetic {
			writeJSON(w, http.StatusConflict, map[string]any{"error": map[string]any{"code": "SYNTHETIC_DATA_REJECTED", "message": "Synthetic data is not permitted and cannot be used."}, "execution": ex})
			return
		}
		summary := map[string]any{
			"status":       ex.Status,
			"execution_id": id,
			"provenance":   res.Provenance,
			"run_metadata": res.Raw["run_metadata"],
			"cells_count":  0,
		}
		if cells, ok := res.Raw["cells"].([]any); ok {
			summary["cells_count"] = len(cells)
		}
		if engineSummary, ok := res.Raw["summary"].(map[string]any); ok {
			summary["analysis"] = engineSummary
		}
		writeJSON(w, http.StatusOK, map[string]any{"execution": ex, "summary": summary, "provenance": res.Provenance})
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
	res, ok, _ := h.svc.GetResult(r.Context(), id)
	if !ok {
		writeJSON(w, http.StatusConflict, map[string]any{
			"error": map[string]any{
				"code":    "CELL_RESULTS_UNAVAILABLE",
				"message": "No cell-level results are available for this execution.",
				"details": map[string]any{"execution_id": ex.ID, "cell_id": cellID, "status": ex.Status},
			},
			"execution": ex,
		})
		return
	}
	if res.Synthetic {
		writeJSON(w, http.StatusConflict, map[string]any{"error": map[string]any{"code": "SYNTHETIC_DATA_REJECTED", "message": "Synthetic data is not permitted and cannot be used."}, "execution": ex})
		return
	}
	if cells, ok := asAnySlice(res.Raw["cells"]); ok {
		for _, c := range cells {
			cm, ok := c.(map[string]any)
			if !ok {
				continue
			}
			if fmt.Sprint(cm["cell_id"]) != cellID {
				continue
			}
			cell := cloneAnyMap(cm)
			timeSeriesAvailable := false
			if _, exists := cell["time_series"]; exists {
				timeSeriesAvailable = true
			}
			if _, exists := cell["observations"]; exists {
				timeSeriesAvailable = true
			}
			if !timeSeriesAvailable {
				cell["time_series"] = nil
			}
			writeJSON(w, http.StatusOK, map[string]any{
				"execution":             ex,
				"cell":                  cell,
				"provenance":            res.Provenance,
				"time_series_available": timeSeriesAvailable,
			})
			return
		}
	}
	writeError(w, "NOT_FOUND", "Cell not found in execution results.", map[string]any{"execution_id": id, "cell_id": cellID})
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
		if res.Synthetic {
			writeJSON(w, http.StatusConflict, map[string]any{"error": map[string]any{"code": "SYNTHETIC_DATA_REJECTED", "message": "Synthetic data is not permitted and cannot be used."}, "execution": ex})
			return
		}
		report := map[string]any{
			"execution_id": id,
			"status":       "available",
			"format":       "json",
			"provenance":   res.Provenance,
			"run_metadata": res.Raw["run_metadata"],
			"summary":      res.Raw["summary"],
			"results": map[string]any{
				"cells_count": 0,
				"note":        "Full grid/cell details available via results and cell endpoints; export formats TBD.",
			},
			"limitations": []string{
				"Statistical significance does not imply causation or practical importance.",
				"Non-significant trends do not imply stability/no change.",
				"Results depend on validated input observations, completeness, and methodological assumptions.",
			},
		}
		if cells, ok := res.Raw["cells"].([]any); ok {
			if rm, ok := report["results"].(map[string]any); ok {
				rm["cells_count"] = len(cells)
			}
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

func parseClassificationFilter(r *http.Request) map[string]bool {
	q := r.URL.Query()
	vals := q["classification"]
	if len(vals) == 0 {
		if v := strings.TrimSpace(q.Get("classification")); v != "" {
			vals = []string{v}
		}
	}
	out := map[string]bool{}
	for _, v := range vals {
		for _, part := range strings.Split(v, ",") {
			part = strings.TrimSpace(part)
			if part == "" {
				continue
			}
			out[part] = true
		}
	}
	return out
}

func parsePagination(r *http.Request, defaultLimit, maxLimit int) (limit, offset int, errMsg string) {
	limit = defaultLimit
	offset = 0
	if v := strings.TrimSpace(r.URL.Query().Get("limit")); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 0 {
			return 0, 0, "limit must be a non-negative integer"
		}
		limit = n
	}
	if v := strings.TrimSpace(r.URL.Query().Get("offset")); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 0 {
			return 0, 0, "offset must be a non-negative integer"
		}
		offset = n
	}
	if limit == 0 {
		limit = defaultLimit
	}
	if limit > maxLimit {
		limit = maxLimit
	}
	return limit, offset, ""
}

func asAnySlice(v any) ([]any, bool) {
	s, ok := v.([]any)
	return s, ok
}

func cloneAnyMap(in map[string]any) map[string]any {
	if in == nil {
		return map[string]any{}
	}
	out := make(map[string]any, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}

func filterCellsByClassification(cells []any, allowed map[string]bool) []any {
	if len(allowed) == 0 {
		out := make([]any, len(cells))
		copy(out, cells)
		return out
	}
	out := make([]any, 0, len(cells))
	for _, c := range cells {
		cm, ok := c.(map[string]any)
		if !ok {
			continue
		}
		cls := fmt.Sprint(cm["classification"])
		if allowed[cls] {
			out = append(out, c)
		}
	}
	return out
}

func sortedStringSet(m map[string]bool) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	if len(out) > 1 {
		// simple insertion sort for small sets
		for i := 1; i < len(out); i++ {
			j := i
			for j > 0 && out[j-1] > out[j] {
				out[j-1], out[j] = out[j], out[j-1]
				j--
			}
		}
	}
	return out
}
